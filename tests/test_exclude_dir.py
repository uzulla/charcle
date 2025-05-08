"""
ディレクトリ除外機能のテスト
"""

import os
import shutil
import tempfile
import unittest

from charcle.converter import Converter


class TestExcludeDirectory(unittest.TestCase):
    """
    ディレクトリ除外機能のテスト
    """

    def setUp(self) -> None:
        """
        テスト前の準備
        """
        self.test_dir = tempfile.mkdtemp()
        self.src_dir = os.path.join(self.test_dir, "src")
        self.dst_dir = os.path.join(self.test_dir, "dst")
        os.makedirs(self.src_dir)

        git_dir = os.path.join(self.src_dir, ".git")
        os.makedirs(git_dir)
        with open(os.path.join(git_dir, "config"), "w", encoding="utf-8") as f:
            f.write("test git config")

        with open(os.path.join(self.src_dir, "test.txt"), "w", encoding="utf-8") as f:
            f.write("test content")

        with open(os.path.join(self.src_dir, "test.log"), "w", encoding="utf-8") as f:
            f.write("test log")

    def tearDown(self) -> None:
        """
        テスト後のクリーンアップ
        """
        shutil.rmtree(self.test_dir)

    def test_exclude_directory(self) -> None:
        """
        ディレクトリ除外のテスト
        """
        converter = Converter(
            from_encoding="utf-8",
            to_encoding="utf-8",
            exclude_patterns=[".git"]
        )
        converter.convert_directory(self.src_dir, self.dst_dir)

        git_dir_path = os.path.join(self.dst_dir, ".git")
        self.assertFalse(os.path.exists(git_dir_path))

        test_file_path = os.path.join(self.dst_dir, "test.txt")
        self.assertTrue(os.path.exists(test_file_path))

    def test_exclude_file_pattern(self) -> None:
        """
        ファイルパターン除外のテスト
        """
        converter = Converter(
            from_encoding="utf-8",
            to_encoding="utf-8",
            exclude_patterns=["*.log"]
        )
        converter.convert_directory(self.src_dir, self.dst_dir)

        log_file_path = os.path.join(self.dst_dir, "test.log")
        self.assertFalse(os.path.exists(log_file_path))

        test_file_path = os.path.join(self.dst_dir, "test.txt")
        self.assertTrue(os.path.exists(test_file_path))
