"""
Converterモジュールのテスト
"""

import os
import shutil
import tempfile
import time
import unittest

from charcle.converter import Converter
from charcle.utils.encoding import convert_encoding


class TestConverter(unittest.TestCase):
    """
    Converterクラスのテスト
    """

    def setUp(self) -> None:
        """
        テスト前の準備
        """
        self.test_dir = tempfile.mkdtemp()
        self.src_dir = os.path.join(self.test_dir, "src")
        self.dst_dir = os.path.join(self.test_dir, "dst")
        os.makedirs(self.src_dir)

    def tearDown(self) -> None:
        """
        テスト後のクリーンアップ
        """
        shutil.rmtree(self.test_dir)

    def test_convert_utf8_file(self) -> None:
        """
        UTF-8ファイルの変換テスト
        """
        test_content = "こんにちは、世界！"
        test_file = os.path.join(self.src_dir, "test_utf8.txt")
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(test_content)

        converter = Converter(from_encoding="utf-8", to_encoding="utf-8")
        converter.convert_directory(self.src_dir, self.dst_dir)

        dst_file = os.path.join(self.dst_dir, "test_utf8.txt")
        self.assertTrue(os.path.exists(dst_file))
        with open(dst_file, encoding="utf-8") as f:
            content = f.read()
        self.assertEqual(content, test_content)

    def test_convert_sjis_to_utf8(self) -> None:
        """
        Shift-JISからUTF-8への変換テスト
        """
        test_content = "こんにちは、世界！"
        test_file = os.path.join(self.src_dir, "test_sjis.txt")
        utf8_bytes = test_content.encode("utf-8")
        sjis_bytes, _ = convert_encoding(utf8_bytes, "utf-8", "shift-jis")
        with open(test_file, "wb") as f:
            f.write(sjis_bytes)

        converter = Converter(from_encoding="shift-jis", to_encoding="utf-8")
        converter.convert_directory(self.src_dir, self.dst_dir)

        dst_file = os.path.join(self.dst_dir, "test_sjis.txt")
        self.assertTrue(os.path.exists(dst_file))
        with open(dst_file, encoding="utf-8") as f:
            content = f.read()
        self.assertEqual(content, test_content)

    def test_exclude_patterns(self) -> None:
        """
        除外パターンのテスト
        """
        test_content = "テストファイル"
        test_file1 = os.path.join(self.src_dir, "test1.txt")
        test_file2 = os.path.join(self.src_dir, "test2.bak")
        with open(test_file1, "w", encoding="utf-8") as f:
            f.write(test_content)
        with open(test_file2, "w", encoding="utf-8") as f:
            f.write(test_content)

        converter = Converter(
            from_encoding="utf-8",
            to_encoding="utf-8",
            exclude_patterns=["*.bak"]
        )
        converter.convert_directory(self.src_dir, self.dst_dir)

        dst_file1 = os.path.join(self.dst_dir, "test1.txt")
        dst_file2 = os.path.join(self.dst_dir, "test2.bak")
        self.assertTrue(os.path.exists(dst_file1))
        self.assertFalse(os.path.exists(dst_file2))

    def test_detect_ascii_file(self) -> None:
        """
        ASCII文字のみのファイルの検出と変換テスト
        """
        test_content = "Hello, world!"
        test_file = os.path.join(self.src_dir, "test_ascii.txt")
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(test_content)

        converter = Converter(from_encoding=None, to_encoding="utf-8", verbose=True)

        non_ascii_file = os.path.join(self.src_dir, "test_non_ascii.txt")
        with open(non_ascii_file, "w", encoding="utf-8") as f:
            f.write("こんにちは、世界！")

        with self.assertLogs(level="INFO") as log:
            converter.convert_directory(self.src_dir, self.dst_dir)

            warning_logs = [r for r in log.records if r.levelname == "WARNING"]

            # ASCII文字のみのファイルに関する警告がないことを確認
            for record in warning_logs:
                self.assertNotIn("test_ascii.txt", record.getMessage())

        dst_file = os.path.join(self.dst_dir, "test_ascii.txt")
        self.assertTrue(os.path.exists(dst_file))
        with open(dst_file, encoding="utf-8") as f:
            content = f.read()
        self.assertEqual(content, test_content)
    def test_skip_unmodified_files(self) -> None:
        """
        変更されていないファイルがスキップされるかのテスト
        """
        test_content = "こんにちは、世界！"
        test_file = os.path.join(self.src_dir, "test_skip.txt")
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(test_content)

        os.makedirs(self.dst_dir, exist_ok=True)

        converter = Converter(from_encoding="utf-8", to_encoding="utf-8", verbose=True)
        with self.assertLogs(level="INFO") as log:
            converter.convert_file(test_file, os.path.join(self.dst_dir, "test_skip.txt"))
            self.assertIn("Converted", log.output[0])

        time.sleep(0.1)

        with self.assertLogs(level="INFO") as log:
            converter.convert_file(test_file, os.path.join(self.dst_dir, "test_skip.txt"))
            self.assertIn("Skipped", log.output[0])

        with open(test_file, "w", encoding="utf-8") as f:
            f.write(test_content + " 更新されました！")

        with self.assertLogs(level="INFO") as log:
            converter.convert_file(test_file, os.path.join(self.dst_dir, "test_skip.txt"))
            self.assertIn("Converted", log.output[0])
