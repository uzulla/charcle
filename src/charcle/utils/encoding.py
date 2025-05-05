"""
エンコーディング検出・変換ユーティリティ

このモジュールは、ファイルのエンコーディングを検出し、
異なるエンコーディング間で変換するための機能を提供します。
"""

import chardet

SUPPORTED_ENCODINGS: list[str] = [
    "utf-8",
    "euc-jp",
    "shift-jis",  # Windows-31J
    "iso-2022-jp",  # JIS
]

ENCODING_ALIASES: dict[str, str] = {
    "shift_jis": "shift-jis",
    "sjis": "shift-jis",
    "windows-31j": "shift-jis",
    "cp932": "shift-jis",
    "eucjp": "euc-jp",
    "ujis": "euc-jp",
    "jis": "iso-2022-jp",
}

def normalize_encoding(encoding: str) -> str:
    """
    エンコーディング名を正規化します。

    Args:
        encoding: 正規化するエンコーディング名

    Returns:
        正規化されたエンコーディング名
    """
    encoding = encoding.lower()
    return ENCODING_ALIASES.get(encoding, encoding)


def is_supported_encoding(encoding: str) -> bool:
    """
    指定されたエンコーディングがサポートされているかを確認します。

    Args:
        encoding: 確認するエンコーディング名

    Returns:
        サポートされている場合はTrue、そうでない場合はFalse
    """
    normalized = normalize_encoding(encoding)
    return normalized in SUPPORTED_ENCODINGS


def detect_encoding(content: bytes, fallback: str = "utf-8") -> tuple[str, float]:
    """
    バイナリコンテンツのエンコーディングを検出します。

    Args:
        content: エンコーディングを検出するバイナリデータ
        fallback: 検出に失敗した場合のフォールバックエンコーディング

    Returns:
        (検出されたエンコーディング, 信頼度)のタプル
    """
    if not content:
        return fallback, 1.0

    result = chardet.detect(content) or {}
    encoding = result.get("encoding", fallback)
    confidence = result.get("confidence", 0.0)

    if encoding is None:
        return fallback, 0.0

    normalized = normalize_encoding(encoding)

    if not is_supported_encoding(normalized):
        return fallback, 0.0

    return normalized, confidence


def convert_encoding(
    content: bytes, from_encoding: str, to_encoding: str
) -> tuple[bytes, bool]:
    """
    コンテンツのエンコーディングを変換します。

    Args:
        content: 変換するバイナリデータ
        from_encoding: 元のエンコーディング
        to_encoding: 変換先のエンコーディング

    Returns:
        (変換されたコンテンツ, 変換成功フラグ)のタプル
    """
    if from_encoding == to_encoding:
        return content, True

    try:
        text = content.decode(from_encoding)
        result = text.encode(to_encoding)
        return result, True
    except (UnicodeDecodeError, UnicodeEncodeError):
        return content, False


def get_supported_encodings() -> list[str]:
    """
    サポートされているエンコーディングのリストを返します。

    Returns:
        サポートされているエンコーディングのリスト
    """
    return SUPPORTED_ENCODINGS.copy()
