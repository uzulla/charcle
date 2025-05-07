"""
Encodingモジュールのテスト
"""

import unittest

from charcle.utils.encoding import convert_encoding, detect_encoding


class TestEncoding(unittest.TestCase):
    """
    エンコーディング関連ユーティリティのテスト
    """

    def test_detect_ascii_encoding(self) -> None:
        """
        ASCII文字のみの検出テスト
        """
        ascii_content = b"Hello, world!"
        encoding, confidence = detect_encoding(ascii_content)

        self.assertEqual(encoding, "ascii")
        self.assertEqual(confidence, 1.0)

    def test_detect_non_ascii_encoding(self) -> None:
        """
        非ASCII文字を含むコンテンツの検出テスト
        """
        utf8_content = "こんにちは、世界！".encode()
        encoding, confidence = detect_encoding(utf8_content)

        self.assertEqual(encoding, "utf-8")
        self.assertGreater(confidence, 0.0)

    def test_convert_from_ascii(self) -> None:
        """
        ASCIIからの変換テスト
        """
        ascii_content = b"Hello, world!"
        converted, success = convert_encoding(ascii_content, "ascii", "shift-jis")

        self.assertTrue(success)
        decoded = converted.decode("shift-jis")
        self.assertEqual(decoded, "Hello, world!")

    def test_convert_to_ascii(self) -> None:
        """
        ASCIIへの変換テスト（ASCII互換の文字のみ）
        """
        content = b"Hello, world!"
        converted, success = convert_encoding(content, "utf-8", "ascii")

        self.assertTrue(success)
        decoded = converted.decode("utf-8")  # "ascii"として処理されるが、実際にはUTF-8
        self.assertEqual(decoded, "Hello, world!")
