"""
CLIモジュールのテスト
"""

import os
import shutil
import sys
import tempfile
import unittest
from io import StringIO
from typing import Any
from unittest.mock import patch

from charcle.cli import main


class TestCLI(unittest.TestCase):
    """
    CLIのテスト
    """

    def setUp(self) -> None:
        """
        テスト前の準備
        """
        self.test_dir = tempfile.mkdtemp()
        self.src_dir = os.path.join(self.test_dir, "src")
        self.dst_dir = os.path.join(self.test_dir, "dst")
        os.makedirs(self.src_dir)

        test_content = "こんにちは、世界！"
        self.test_file = os.path.join(self.src_dir, "test.txt")
        with open(self.test_file, "w", encoding="utf-8") as f:
            f.write(test_content)

    def tearDown(self) -> None:
        """
        テスト後のクリーンアップ
        """
        shutil.rmtree(self.test_dir)

    @patch("sys.argv")
    def test_list_encodings(self, mock_argv: Any) -> None:
        """
        エンコーディング一覧表示のテスト
        """
        mock_argv.__getitem__.side_effect = lambda i: ["charcle", "--list"][i]
        captured_output = StringIO()
        sys.stdout = captured_output
        try:
            main()
            output = captured_output.getvalue()
            self.assertIn("サポートするエンコーディング:", output)
            self.assertIn("utf-8", output)
            self.assertIn("shift-jis", output)
        finally:
            sys.stdout = sys.__stdout__

    @patch("sys.argv")
    def test_convert_directory(self, mock_argv: Any) -> None:
        """
        ディレクトリ変換のテスト
        """
        mock_argv.__getitem__.side_effect = lambda i: ["charcle", self.src_dir, self.dst_dir][i]
        exit_code = main()
        self.assertEqual(exit_code, 0)
        self.assertTrue(os.path.exists(os.path.join(self.dst_dir, "test.txt")))

    @patch("sys.argv")
    def test_fallback_charset_option(self, mock_argv: Any) -> None:
        """
        fallback_charsetオプションのテスト
        """
        mock_argv.__getitem__.side_effect = lambda i: [
            "charcle",
            "--fallback-charset=euc-jp",
            "--watch",
            self.src_dir,
            self.dst_dir
        ][i]
        with patch("charcle.cli.Watcher") as mock_watcher:
            with patch("time.sleep", side_effect=KeyboardInterrupt):
                try:
                    main()
                except KeyboardInterrupt:
                    pass
            converter = mock_watcher.call_args[1]["converter"]
            self.assertEqual(converter.fallback_charset, "euc-jp")

    @patch("sys.argv")
    def test_watch_with_no_destination_directory(self, mock_argv: Any) -> None:
        """
        宛先ディレクトリが存在しない場合のwatchオプションのテスト
        """
        self.assertFalse(os.path.exists(self.dst_dir))
        mock_argv.__getitem__.side_effect = lambda i: [
            "charcle",
            "--watch",
            self.src_dir,
            self.dst_dir
        ][i]
        with patch("charcle.cli.Watcher"):
            with patch("time.sleep", side_effect=KeyboardInterrupt):
                try:
                    main()
                except KeyboardInterrupt:
                    pass
            self.assertTrue(os.path.exists(self.dst_dir))
            self.assertTrue(os.path.exists(os.path.join(self.dst_dir, "test.txt")))
