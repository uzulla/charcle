"""
ファイルシステム操作ユーティリティ

このモジュールは、ファイルシステムの操作に関連する機能を提供します。
ファイルの読み書き、メタデータの保持、シンボリックリンクの処理などを含みます。
"""

import fnmatch
import os
import re
import shutil
from typing import Optional


def is_text_file(file_path: str, max_size: Optional[int] = None) -> bool:
    """
    ファイルがテキストファイルかどうかを判断します。

    Args:
        file_path: 判断するファイルのパス
        max_size: 処理する最大ファイルサイズ（バイト単位）

    Returns:
        テキストファイルの場合はTrue、そうでない場合はFalse
    """
    if not os.path.isfile(file_path):
        return False

    if max_size is not None:
        file_size = os.path.getsize(file_path)
        if file_size > max_size:
            return False

    try:
        with open(file_path, "rb") as f:
            chunk = f.read(4096)
            if b"\x00" in chunk:
                return False
            control_chars = sum(1 for b in chunk if b < 32 and b not in (9, 10, 13))
            if len(chunk) > 0 and control_chars / len(chunk) > 0.3:
                return False
            return True
    except OSError:
        return False


def parse_size(size_str: str) -> int:
    """
    サイズ文字列をバイト数に変換します。

    Args:
        size_str: サイズ文字列（例: "1M", "500K"）

    Returns:
        バイト数

    Raises:
        ValueError: サイズ文字列の形式が無効な場合
    """
    size_str = size_str.upper()
    match = re.match(r"^(\d+)([KMG])?$", size_str)
    if not match:
        raise ValueError(f"Invalid size format: {size_str}")

    size = int(match.group(1))
    unit = match.group(2)

    if unit == "K":
        return size * 1024
    elif unit == "M":
        return size * 1024 * 1024
    elif unit == "G":
        return size * 1024 * 1024 * 1024
    else:
        return size


def should_exclude(path: str, exclude_patterns: list[str]) -> bool:
    """
    パスが除外パターンに一致するかどうかを判断します。

    Args:
        path: 判断するパス
        exclude_patterns: 除外パターンのリスト

    Returns:
        除外する場合はTrue、そうでない場合はFalse
    """
    if not exclude_patterns:
        return False

    path_parts = path.split(os.sep)
    for pattern in exclude_patterns:
        if fnmatch.fnmatch(path, pattern):
            return True
        for part in path_parts:
            if fnmatch.fnmatch(part, pattern):
                return True
        if os.path.basename(path) == pattern or pattern in path.split(os.sep):
            return True
    return False


def copy_metadata(src_path: str, dst_path: str) -> None:
    """
    ファイルのメタデータをコピーします。

    Args:
        src_path: ソースファイルのパス
        dst_path: 宛先ファイルのパス
    """
    shutil.copymode(src_path, dst_path)

    src_stat = os.stat(src_path)
    os.utime(dst_path, (src_stat.st_atime, src_stat.st_mtime))

    try:
        shutil.chown(dst_path, os.stat(src_path).st_uid, os.stat(src_path).st_gid)
    except (OSError, AttributeError):
        pass


def handle_symlink(src_link: str, dst_link: str, src_base: str, dst_base: str) -> None:
    """
    シンボリックリンクを適切に処理します。

    Args:
        src_link: ソースリンクのパス
        dst_link: 宛先リンクのパス
        src_base: ソースディレクトリのベースパス
        dst_base: 宛先ディレクトリのベースパス
    """
    link_target = os.readlink(src_link)
    abs_link_target = os.path.abspath(os.path.join(os.path.dirname(src_link), link_target))

    if abs_link_target.startswith(os.path.abspath(src_base)):
        rel_path = os.path.relpath(abs_link_target, os.path.abspath(src_base))
        new_target = os.path.join(dst_base, rel_path)
        new_target = os.path.relpath(new_target, os.path.dirname(dst_link))
        os.symlink(new_target, dst_link)
    else:
        os.symlink(link_target, dst_link)

    try:
        copy_metadata(src_link, dst_link)
    except (OSError, AttributeError):
        pass
