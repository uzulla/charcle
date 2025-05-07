"""
ファイル変更監視モジュールのテスト
"""

import os
import shutil
import tempfile
import time
from unittest import TestCase

from charcle.converter import Converter
from charcle.watcher import Watcher


class TestWatcher(TestCase):
    """
    ウォッチャーのテストケース
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

    def test_respect_source_encoding(self) -> None:
        """
        ソースファイルの文字コードが尊重されるかテスト
        """
        test_content_eucjp = "こんにちは、世界".encode("euc-jp")
        test_file_eucjp = os.path.join(self.src_dir, "test_eucjp.txt")
        with open(test_file_eucjp, "wb") as f:
            f.write(test_content_eucjp)

        test_content_utf8 = "こんにちは、世界".encode()
        test_file_utf8 = os.path.join(self.src_dir, "test_utf8.txt")
        with open(test_file_utf8, "wb") as f:
            f.write(test_content_utf8)

        converter = Converter(from_encoding=None, to_encoding="utf-8")
        watcher = Watcher(
            src_dir=self.src_dir,
            dst_dir=self.dst_dir,
            converter=converter,
            interval=0.1,
        )
        converter.convert_directory(self.src_dir, self.dst_dir)
        dst_file_eucjp = os.path.join(self.dst_dir, "test_eucjp.txt")
        dst_file_utf8 = os.path.join(self.dst_dir, "test_utf8.txt")
        modified_content = "こんにちは、世界！変更しました".encode()
        with open(dst_file_eucjp, "wb") as f:
            f.write(modified_content)
        with open(dst_file_utf8, "wb") as f:
            f.write(modified_content)
        time.sleep(0.1)  # mtimeの差を確実にするため
        os.utime(dst_file_eucjp, None)
        os.utime(dst_file_utf8, None)
        watcher._handle_destination_change("test_eucjp.txt")
        watcher._handle_destination_change("test_utf8.txt")
        with open(test_file_eucjp, "rb") as f:
            content_eucjp = f.read()
        with open(test_file_utf8, "rb") as f:
            content_utf8 = f.read()
        try:
            decoded_eucjp = content_eucjp.decode("euc-jp")
            self.assertTrue("変更しました" in decoded_eucjp,
                           f"EUC-JPファイルに変更内容が含まれていません: {decoded_eucjp}")
        except UnicodeDecodeError as e:
            self.fail(f"ソースファイルがEUC-JPとして書き戻されていません: {str(e)}")
        try:
            decoded_utf8 = content_utf8.decode("utf-8")
            self.assertTrue("変更しました" in decoded_utf8,
                           f"UTF-8ファイルに変更内容が含まれていません: {decoded_utf8}")
        except UnicodeDecodeError as e:
            self.fail(f"ソースファイルがUTF-8として書き戻されていません: {str(e)}")
