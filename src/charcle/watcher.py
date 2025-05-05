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
from typing import Any, Dict, Optional

from charcle.converter import Converter


class Watcher:
    """
    ファイル変更監視クラス
    """

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
        self.file_mtimes: Dict[str, float] = {}
        self.logger = logging.getLogger("charcle")

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
        self._scan_files(self.src_dir, self.file_mtimes, "src")
        self._scan_files(self.dst_dir, self.file_mtimes, "dst")

        while self.running:
            try:
                self._process_changes()
                time.sleep(self.interval)
            except Exception as e:
                self.logger.error(f"Error in watch loop: {str(e)}")
                time.sleep(self.interval)

    def _scan_files(self, directory: str, mtimes: Dict[str, float], prefix: str) -> None:
        """
        ディレクトリ内のファイルのmtimeをスキャンします。

        Args:
            directory: スキャンするディレクトリのパス
            mtimes: mtime情報を格納する辞書
            prefix: キーのプレフィックス（"src"または"dst"）
        """
        if not os.path.exists(directory):
            return

        for root, _, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                if os.path.islink(file_path):
                    continue  # シンボリックリンクはスキップ
                try:
                    rel_path = os.path.relpath(file_path, directory)
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

    def _handle_destination_change(self, rel_path: str) -> None:
        """
        宛先ファイルの変更を処理します。

        Args:
            rel_path: 変更されたファイルの相対パス
        """
        dst_file = os.path.join(self.dst_dir, rel_path)
        src_file = os.path.join(self.src_dir, rel_path)
        if not os.path.exists(src_file):
            return
        dst_mtime = os.path.getmtime(dst_file)
        src_mtime = os.path.getmtime(src_file)
        if dst_mtime > src_mtime:
            self.logger.info(f"Destination file changed: {rel_path}, writing back")
            reverse_converter = Converter(
                from_encoding=self.converter.to_encoding,
                to_encoding=self.converter.from_encoding or "utf-8",
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
        if prefix == "src":
            dst_file = os.path.join(self.dst_dir, rel_path)
            if os.path.exists(dst_file):
                self.logger.info(f"Source file deleted: {rel_path}, removing destination file")
                try:
                    os.remove(dst_file)
                except OSError as e:
                    self.logger.error(f"Error removing {dst_file}: {str(e)}")

    def _process_changes(self) -> None:
        """
        変更されたファイルを検出して処理します。
        """
        current_mtimes: Dict[str, float] = {}
        self._scan_files(self.src_dir, current_mtimes, "src")
        self._scan_files(self.dst_dir, current_mtimes, "dst")

        for key, mtime in current_mtimes.items():
            prefix, rel_path = key.split(":", 1)
            if key not in self.file_mtimes or mtime > self.file_mtimes[key]:
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
