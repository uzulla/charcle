"""
Watcherモジュールの除外機能のテスト
"""

import os
import shutil
import tempfile
import time
import unittest

from charcle.converter import Converter
from charcle.watcher import Watcher


class TestWatcherExclude(unittest.TestCase):
    """
    Watcherクラスの除外機能のテスト
    """

    def setUp(self) -> None:
        """
        テスト前の準備
        """
        self.test_dir = tempfile.mkdtemp()
        self.src_dir = os.path.join(self.test_dir, "src")
        self.dst_dir = os.path.join(self.test_dir, "dst")
        os.makedirs(self.src_dir)
        os.makedirs(self.dst_dir)

        self.git_dir = os.path.join(self.src_dir, ".git")
        os.makedirs(self.git_dir)
        with open(os.path.join(self.git_dir, "config"), "w", encoding="utf-8") as f:
            f.write("test git config")

        self.normal_file = os.path.join(self.src_dir, "normal.txt")
        with open(self.normal_file, "w", encoding="utf-8") as f:
            f.write("normal file content")

        self.exclude_file = os.path.join(self.src_dir, "exclude.log")
        with open(self.exclude_file, "w", encoding="utf-8") as f:
            f.write("exclude file content")

    def tearDown(self) -> None:
        """
        テスト後のクリーンアップ
        """
        shutil.rmtree(self.test_dir)

    def test_exclude_patterns_in_watcher(self) -> None:
        """
        Watcherが除外パターンを正しく処理するかのテスト
        """
        exclude_patterns = [".git", "*.log"]
        converter = Converter(
            from_encoding="utf-8",
            to_encoding="utf-8",
            exclude_patterns=exclude_patterns
        )

        converter.convert_directory(self.src_dir, self.dst_dir)

        dst_normal_file = os.path.join(self.dst_dir, "normal.txt")
        self.assertTrue(os.path.exists(dst_normal_file))

        watcher = Watcher(self.src_dir, self.dst_dir, converter, interval=0.1)
        try:
            watcher.start()
            time.sleep(1.0)  # 初期スキャンを待つ

            dst_exclude_file = os.path.join(self.dst_dir, "exclude.log")
            self.assertFalse(os.path.exists(dst_exclude_file))

            dst_git_config = os.path.join(self.dst_dir, ".git", "config")
            self.assertFalse(os.path.exists(dst_git_config))

            time.sleep(0.5)
            with open(self.exclude_file, "w", encoding="utf-8") as f:
                f.write("updated exclude file content")
            time.sleep(1.0)  # 変更検出を待つ

            self.assertFalse(os.path.exists(dst_exclude_file))

            git_config_file = os.path.join(self.git_dir, "config")
            with open(git_config_file, "w", encoding="utf-8") as f:
                f.write("updated git config")
            time.sleep(1.0)  # 変更検出を待つ

            self.assertFalse(os.path.exists(dst_git_config))

        finally:
            watcher.stop()
