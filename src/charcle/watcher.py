"""
ファイル変更監視モジュール

このモジュールは、ファイルシステムの変更を監視し、
自動的にエンコーディング変換を行うための機能を提供します。
"""

import logging
import os
import signal
import threading
import time
from typing import Any, Optional

from charcle.converter import Converter
from charcle.utils.encoding import detect_encoding
from charcle.utils.filesystem import should_exclude


class Watcher:
    """
    ファイル変更監視クラス
    """

    @staticmethod
    def _is_temp_editor_file(filename: str) -> bool:
        """
        一時的なエディタファイルかどうかをチェックします。

        Args:
            filename: チェックするファイル名

        Returns:
            一時的なエディタファイルの場合はTrue、そうでない場合はFalse
        """
        if filename.endswith('.swp') or filename.endswith('.swo'):
            return True
        if filename.startswith('#') and filename.endswith('#'):
            return True
        if filename.endswith('~'):
            return True
        if filename.startswith('.') and filename.endswith('.tmp'):
            return True
        return False

    def __init__(
        self,
        src_dir: str,
        dst_dir: str,
        converter: Converter,
        interval: float = 1.0,
    ):
        """
        ウォッチャーを初期化します。

        Args:
            src_dir: 監視するソースディレクトリのパス
            dst_dir: 変換先の宛先ディレクトリのパス
            converter: 使用するコンバーターインスタンス
            interval: 監視間隔（秒）
        """
        self.src_dir = os.path.abspath(src_dir)
        self.dst_dir = os.path.abspath(dst_dir)
        self.converter = converter
        self.interval = interval
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.file_mtimes: dict[str, float] = {}
        self.fallback_files: set[str] = set()  # fallback_charsetで作成されたファイルを追跡
        self.logger = logging.getLogger("charcle")
        self._initial_scan_complete = False

    def start(self) -> None:
        """
        監視を開始します。
        """
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._watch_loop)
        self.thread.daemon = True
        self.thread.start()

        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        self.logger.info(
            f"Watching {self.src_dir} and {self.dst_dir} for changes "
            f"(interval: {self.interval}s)"
        )

    def stop(self) -> None:
        """
        監視を停止します。
        """
        self.running = False
        if self.thread:
            self.thread.join()
        self.logger.info("Watching stopped")

    def is_scan_complete(self) -> bool:
        """
        初期スキャンが完了したかどうかを返します。

        Returns:
            初期スキャンが完了した場合はTrue、そうでない場合はFalse
        """
        return self._initial_scan_complete

    def _signal_handler(self, signum: int, frame: Any) -> None:
        """
        シグナルハンドラ

        Args:
            signum: シグナル番号
            frame: 現在のスタックフレーム
        """
        self.logger.info(f"Received signal {signum}, stopping...")
        self.stop()

    def _watch_loop(self) -> None:
        """
        監視ループ
        """
        self.logger.info("Initial scan of files")
        self._scan_files(self.src_dir, self.file_mtimes, "src")
        self._scan_files(self.dst_dir, self.file_mtimes, "dst")
        self.logger.debug(f"Initial files: {list(self.file_mtimes.keys())}")
        self._initial_scan_complete = True

        while self.running:
            try:
                self.logger.debug("Processing changes...")
                self._process_changes()
                time.sleep(self.interval)
            except Exception as e:
                self.logger.error(f"Error in watch loop: {str(e)}")
                time.sleep(self.interval)

    def _scan_files(self, directory: str, mtimes: dict[str, float], prefix: str) -> None:
        """
        ディレクトリ内のファイルのmtimeをスキャンします。

        除外パターンに一致するディレクトリとファイルは処理から除外されます。
        ディレクトリの除外は、そのディレクトリ自体のパスが除外パターンに一致する場合に行われ、
        その場合はそのディレクトリ以下のすべてのファイルとサブディレクトリが処理から除外されます。
        これにより、大規模なディレクトリ（例：.git）が除外パターンに一致する場合、
        そのディレクトリ内のファイルを個別に確認する必要がなくなり、パフォーマンスが向上します。

        Args:
            directory: スキャンするディレクトリのパス
            mtimes: mtime情報を格納する辞書
            prefix: キーのプレフィックス（"src"または"dst"）
        """
        if not os.path.exists(directory):
            return

        for root, _, files in os.walk(directory):
            rel_dir = os.path.relpath(root, directory)
            if rel_dir != "." and should_exclude(rel_dir, self.converter.exclude_patterns):
                continue

            for file in files:
                file_path = os.path.join(root, file)
                if os.path.islink(file_path):
                    continue  # シンボリックリンクはスキップ
                if self._is_temp_editor_file(file):
                    self.logger.debug(f"Skipping temporary editor file: {file}")
                    continue  # 一時的なエディタファイルはスキップ
                try:
                    rel_path = os.path.relpath(file_path, directory)
                    if should_exclude(rel_path, self.converter.exclude_patterns):
                        self.logger.debug(f"Skipping excluded file: {rel_path}")
                        continue
                    key = f"{prefix}:{rel_path}"
                    mtimes[key] = os.path.getmtime(file_path)
                except OSError:
                    pass  # ファイルにアクセスできない場合はスキップ

    def _handle_source_change(self, rel_path: str) -> None:
        """
        ソースファイルの変更を処理します。

        Args:
            rel_path: 変更されたファイルの相対パス
        """
        src_file = os.path.join(self.src_dir, rel_path)
        dst_file = os.path.join(self.dst_dir, rel_path)
        dst_dir = os.path.dirname(dst_file)
        if not os.path.exists(dst_dir):
            os.makedirs(dst_dir)
        self.logger.info(f"Source file changed: {rel_path}")
        try:
            self.converter.convert_file(src_file, dst_file)
        except Exception as e:
            self.logger.error(f"Error converting {rel_path}: {str(e)}")

    def _determine_encoding(self, src_file: str, rel_path: str) -> Optional[str]:
        """
        ソースファイルのエンコーディングを決定します。

        Args:
            src_file: ソースファイルのパス
            rel_path: ファイルの相対パス

        Returns:
            決定されたエンコーディング
        """
        to_encoding = self.converter.from_encoding
        is_fallback_file = rel_path in self.fallback_files

        if not os.path.exists(src_file):
            if self.converter.fallback_charset:
                to_encoding = self.converter.fallback_charset
                self.fallback_files.add(rel_path)
                self.logger.info(f"Using fallback charset for new file: {to_encoding}")
            return to_encoding

        if is_fallback_file and self.converter.fallback_charset:
            to_encoding = self.converter.fallback_charset
            self.logger.info(f"Using fallback charset for existing file: {to_encoding}")
            return to_encoding

        if os.path.isfile(src_file):
            try:
                with open(src_file, "rb") as f:
                    content = f.read()
                is_ascii_only = all(b <= 127 for b in content)
                if is_ascii_only and is_fallback_file and self.converter.fallback_charset:
                    to_encoding = self.converter.fallback_charset
                    self.logger.info(
                        f"File contains only ASCII, using fallback charset: {to_encoding}"
                    )
                else:
                    detected_encoding, confidence = detect_encoding(content)
                    if confidence >= 0.7:
                        to_encoding = detected_encoding
                        if is_fallback_file:
                            self.fallback_files.remove(rel_path)
                        self.logger.info(
                            f"Detected source file encoding: {to_encoding} "
                            f"(confidence: {confidence:.2f})"
                        )
            except Exception as e:
                self.logger.warning(f"Error detecting source file encoding: {str(e)}")

        return to_encoding

    def _handle_destination_change(self, rel_path: str) -> None:
        """
        宛先ファイルの変更を処理します。

        Args:
            rel_path: 変更されたファイルの相対パス
        """
        # 除外パターンに一致するファイルはスキップ
        if should_exclude(rel_path, self.converter.exclude_patterns):
            self.logger.debug(f"Skipping excluded destination file: {rel_path}")
            return

        dst_file = os.path.join(self.dst_dir, rel_path)
        src_file = os.path.join(self.src_dir, rel_path)
        src_dir = os.path.dirname(src_file)

        if not os.path.exists(dst_file) or not os.path.isfile(dst_file):
            return

        if not os.path.exists(src_dir):
            os.makedirs(src_dir)

        if os.path.exists(src_file):
            dst_mtime = os.path.getmtime(dst_file)
            src_mtime = os.path.getmtime(src_file)
            if dst_mtime <= src_mtime:
                return

        to_encoding = self._determine_encoding(src_file, rel_path)

        self.logger.info(f"Destination file changed: {rel_path}, writing back")
        reverse_converter = Converter(
            from_encoding=self.converter.to_encoding,
            to_encoding=to_encoding or "utf-8",
            max_size=None,  # 既に変換済みのファイルなのでサイズ制限は不要
            exclude_patterns=self.converter.exclude_patterns,
            verbose=self.converter.verbose,
        )
        try:
            reverse_converter.convert_file(dst_file, src_file)
        except Exception as e:
            self.logger.error(f"Error writing back {rel_path}: {str(e)}")

    def _handle_deleted_file(self, prefix: str, rel_path: str) -> None:
        """
        削除されたファイルを処理します。

        Args:
            prefix: ファイルのプレフィックス（"src"または"dst"）
            rel_path: 削除されたファイルの相対パス
        """
        # 一時的なエディタファイルはスキップ
        if self._is_temp_editor_file(os.path.basename(rel_path)):
            self.logger.info(f"Skipping temporary editor file: {rel_path}")
            return

        if prefix == "src":
            dst_file = os.path.join(self.dst_dir, rel_path)
            if os.path.exists(dst_file):
                self.logger.info(f"Source file deleted: {rel_path}, removing destination file")
                try:
                    os.remove(dst_file)
                except OSError as e:
                    self.logger.error(f"Error removing {dst_file}: {str(e)}")
        elif prefix == "dst":
            src_file = os.path.join(self.src_dir, rel_path)
            if os.path.exists(src_file):
                self.logger.info(f"Destination file deleted: {rel_path}, removing source file")
                try:
                    os.remove(src_file)
                except OSError as e:
                    self.logger.error(f"Error removing {src_file}: {str(e)}")

    def _process_changes(self) -> None:
        """
        変更されたファイルを検出して処理します。
        """
        current_mtimes: dict[str, float] = {}
        self._scan_files(self.src_dir, current_mtimes, "src")
        self._scan_files(self.dst_dir, current_mtimes, "dst")

        self.logger.debug(f"Current files: {list(current_mtimes.keys())}")
        self.logger.debug(f"Previous files: {list(self.file_mtimes.keys())}")

        for key, mtime in current_mtimes.items():
            prefix, rel_path = key.split(":", 1)
            if key not in self.file_mtimes:
                self.logger.debug(f"New file detected: {key}")
                if prefix == "src":
                    self._handle_source_change(rel_path)
                elif prefix == "dst":
                    self._handle_destination_change(rel_path)
            elif mtime > self.file_mtimes[key]:
                self.logger.debug(
                    f"Modified file detected: {key}, "
                    f"old mtime: {self.file_mtimes[key]}, new mtime: {mtime}"
                )
                if prefix == "src":
                    self._handle_source_change(rel_path)
                elif prefix == "dst":
                    self._handle_destination_change(rel_path)

        for key in list(self.file_mtimes.keys()):
            if key not in current_mtimes:
                prefix, rel_path = key.split(":", 1)
                self._handle_deleted_file(prefix, rel_path)
                del self.file_mtimes[key]

        self.file_mtimes = current_mtimes
