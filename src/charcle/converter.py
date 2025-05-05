"""
ファイルエンコーディング変換モジュール

このモジュールは、ファイルのエンコーディングを変換するための機能を提供します。
"""

import logging
import os
import shutil
from typing import List, Optional

from charcle.utils.encoding import convert_encoding, detect_encoding
from charcle.utils.filesystem import (
    copy_metadata,
    handle_symlink,
    is_text_file,
    parse_size,
    should_exclude,
)


class Converter:
    """
    ファイルエンコーディング変換クラス
    """

    def __init__(
        self,
        from_encoding: Optional[str] = None,
        to_encoding: str = "utf-8",
        max_size: Optional[str] = None,
        exclude_patterns: Optional[List[str]] = None,
        verbose: bool = False,
    ):
        """
        コンバーターを初期化します。

        Args:
            from_encoding: 入力エンコーディング（Noneの場合は自動検出）
            to_encoding: 出力エンコーディング
            max_size: 変換する最大ファイルサイズ（例: "1M", "500K"）
            exclude_patterns: 除外するファイルパターンのリスト
            verbose: 詳細なログ出力を有効にするかどうか
        """
        self.from_encoding = from_encoding
        self.to_encoding = to_encoding
        self.max_size_bytes = parse_size(max_size) if max_size else None
        self.exclude_patterns = exclude_patterns or []
        self.verbose = verbose

        self.logger = logging.getLogger("charcle")
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter("%(levelname)s: %(message)s")
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        self.logger.setLevel(logging.DEBUG if verbose else logging.INFO)

    def convert_directory(self, src_dir: str, dst_dir: str) -> None:
        """
        ディレクトリ全体のファイルエンコーディングを変換します。

        Args:
            src_dir: ソースディレクトリのパス
            dst_dir: 宛先ディレクトリのパス
        """
        src_dir = os.path.abspath(src_dir)
        dst_dir = os.path.abspath(dst_dir)

        if not os.path.exists(dst_dir):
            os.makedirs(dst_dir)

        for root, dirs, files in os.walk(src_dir):
            rel_path = os.path.relpath(root, src_dir)
            dst_root = os.path.join(dst_dir, rel_path) if rel_path != "." else dst_dir

            dirs[:] = [
                d for d in dirs
                if not should_exclude(os.path.join(rel_path, d), self.exclude_patterns)
            ]

            if not os.path.exists(dst_root):
                os.makedirs(dst_root)
                copy_metadata(root, dst_root)

            for file in files:
                src_file = os.path.join(root, file)
                dst_file = os.path.join(dst_root, file)
                rel_file_path = os.path.join(rel_path, file)

                if should_exclude(rel_file_path, self.exclude_patterns):
                    self.logger.debug(f"Skipping excluded file: {rel_file_path}")
                    continue

                try:
                    if os.path.islink(src_file):
                        self.logger.debug(f"Processing symlink: {rel_file_path}")
                        handle_symlink(src_file, dst_file, src_dir, dst_dir)
                    else:
                        self.convert_file(src_file, dst_file)
                except Exception as e:
                    self.logger.error(f"Error processing {rel_file_path}: {str(e)}")

    def convert_file(self, src_file: str, dst_file: str) -> None:
        """
        単一ファイルのエンコーディングを変換します。

        Args:
            src_file: ソースファイルのパス
            dst_file: 宛先ファイルのパス
        """
        if is_text_file(src_file, self.max_size_bytes):
            try:
                with open(src_file, "rb") as f:
                    content = f.read()

                from_encoding = self.from_encoding
                confidence = 1.0
                if from_encoding is None:
                    from_encoding, confidence = detect_encoding(content)

                if confidence < 0.7:
                    self.logger.warning(
                        f"Low confidence ({confidence:.2f}) in encoding detection for "
                        f"{src_file}: {from_encoding}"
                    )

                converted, success = convert_encoding(content, from_encoding, self.to_encoding)

                if success:
                    with open(dst_file, "wb") as f:
                        f.write(converted)
                    self.logger.info(
                        f"Converted {src_file} from {from_encoding} to {self.to_encoding}"
                    )
                else:
                    shutil.copy2(src_file, dst_file)
                    self.logger.warning(f"Failed to convert {src_file}, copied as binary")
            except Exception as e:
                shutil.copy2(src_file, dst_file)
                self.logger.error(f"Error converting {src_file}: {str(e)}")
        else:
            shutil.copy2(src_file, dst_file)
            self.logger.debug(f"Copied binary file: {src_file}")

        copy_metadata(src_file, dst_file)
