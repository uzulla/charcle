"""
Watcherモジュールのテスト
"""

import os
import shutil
import tempfile
import time
import unittest

from charcle.converter import Converter
from charcle.utils.encoding import convert_encoding
from charcle.watcher import Watcher


class TestWatcher(unittest.TestCase):
    """
    Watcherクラスのテスト
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

    def tearDown(self) -> None:
        """
        テスト後のクリーンアップ
        """
        shutil.rmtree(self.test_dir)

    def test_respects_source_encoding_on_write_back(self) -> None:
        """
        ソースファイルの文字コードが書き戻し時に尊重されるかのテスト
        """
        test_content = "こんにちは、世界！"
        utf8_bytes = test_content.encode("utf-8")
        eucjp_bytes, _ = convert_encoding(utf8_bytes, "utf-8", "euc-jp")

        src_file = os.path.join(self.src_dir, "test_eucjp.txt")
        with open(src_file, "wb") as f:
            f.write(eucjp_bytes)

        converter = Converter(to_encoding="utf-8")
        converter.convert_directory(self.src_dir, self.dst_dir)

        dst_file = os.path.join(self.dst_dir, "test_eucjp.txt")
        self.assertTrue(os.path.exists(dst_file))

        watcher = Watcher(self.src_dir, self.dst_dir, converter, interval=0.1)
        try:
            watcher.start()

            original_src_mtime = os.path.getmtime(src_file)
            original_dst_mtime = os.path.getmtime(dst_file)
            print(f"Original src mtime: {original_src_mtime}")
            print(f"Original dst mtime: {original_dst_mtime}")

            time.sleep(0.5)

            modified_content = "こんにちは、世界！これはUTF-8で編集されました。"
            with open(dst_file, "w", encoding="utf-8") as f:
                f.write(modified_content)
            new_dst_mtime = os.path.getmtime(dst_file)
            print(f"New dst mtime: {new_dst_mtime}")
            print(f"Timestamp difference: {new_dst_mtime - original_dst_mtime}")

            time.sleep(2.0)
            print("Waiting for watcher to process changes...")

            self.assertTrue(os.path.exists(src_file))

            with open(src_file, "rb") as f:
                content = f.read()

            decoded_content = content.decode("euc-jp")
            self.assertEqual(decoded_content, modified_content)

            with self.assertRaises(UnicodeDecodeError):
                content.decode("utf-8", errors="strict")
        finally:
            watcher.stop()

    def test_fallback_charset_for_new_files(self) -> None:
        """
        新規ファイル作成時にfallback_charsetが正しく使用されるかのテスト
        """
        test_content = "こんにちは、世界！"
        converter = Converter(to_encoding="utf-8", fallback_charset="euc-jp")
        watcher = Watcher(self.src_dir, self.dst_dir, converter, interval=0.1)
        try:
            watcher.start()
            time.sleep(0.5)
            dst_file = os.path.join(self.dst_dir, "new_file.txt")
            with open(dst_file, "w", encoding="utf-8") as f:
                f.write(test_content)
            time.sleep(2.0)
            src_file = os.path.join(self.src_dir, "new_file.txt")
            self.assertTrue(os.path.exists(src_file))
            with open(src_file, "rb") as f:
                content = f.read()
            decoded_content = content.decode("euc-jp")
            self.assertEqual(decoded_content, test_content)
            with self.assertRaises(UnicodeDecodeError):
                content.decode("utf-8", errors="strict")
        finally:
            watcher.stop()

    def test_fallback_charset_maintained_for_ascii_content(self) -> None:
        """
        ASCII文字のみの場合でもfallback_charsetが維持されるかのテスト
        """
        converter = Converter(to_encoding="utf-8", fallback_charset="euc-jp")
        watcher = Watcher(self.src_dir, self.dst_dir, converter, interval=0.1)
        try:
            watcher.start()
            time.sleep(0.5)

            dst_file = os.path.join(self.dst_dir, "ascii_file.txt")
            with open(dst_file, "w", encoding="utf-8") as f:
                pass

            time.sleep(2.0)

            src_file = os.path.join(self.src_dir, "ascii_file.txt")
            self.assertTrue(os.path.exists(src_file))

            with open(dst_file, "w", encoding="utf-8") as f:
                f.write("Hello, world!")

            time.sleep(2.0)

            with open(src_file, "rb") as f:
                content = f.read()

            decoded_content = content.decode("euc-jp")
            self.assertEqual(decoded_content, "Hello, world!")

            with open(dst_file, "w", encoding="utf-8") as f:
                f.write("Hello, world! こんにちは")

            time.sleep(2.0)

            with open(src_file, "rb") as f:
                content = f.read()

            decoded_content = content.decode("euc-jp")
            self.assertEqual(decoded_content, "Hello, world! こんにちは")
        finally:
            watcher.stop()
