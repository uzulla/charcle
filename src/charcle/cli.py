"""
コマンドラインインターフェース

このモジュールは、Charcleのコマンドラインインターフェースを提供します。
"""

import argparse
import logging
import os
import sys
import time

from charcle.converter import Converter
from charcle.utils.encoding import get_supported_encodings
from charcle.watcher import Watcher


def parse_args() -> argparse.Namespace:
    """
    コマンドライン引数を解析します。

    Returns:
        解析された引数
    """
    parser = argparse.ArgumentParser(
        prog="charcle",
        description="Python ファイルエンコーディング変換ツール",
    )

    parser.add_argument(
        "input_dir",
        nargs="?",
        help="入力ディレクトリ",
    )
    parser.add_argument(
        "output_dir",
        nargs="?",
        help="出力ディレクトリ",
    )
    parser.add_argument(
        "-f", "--from",
        dest="from_encoding",
        help="入力エンコーディングを指定（省略時は自動検出）",
    )
    parser.add_argument(
        "-t", "--to",
        dest="to_encoding",
        default="utf-8",
        help="出力エンコーディングを指定（デフォルト: UTF-8）",
    )
    parser.add_argument(
        "-l", "--list",
        action="store_true",
        help="サポートするエンコーディングの一覧表示",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="詳細なログ出力",
    )
    parser.add_argument(
        "--max-size",
        help="変換するファイルの最大サイズ（例：1M, 500K）",
    )
    parser.add_argument(
        "--exclude",
        help="除外するディレクトリやファイルのパターン（カンマ区切り）",
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="変更を監視し自動的に書き戻すデーモンモードで実行",
    )
    parser.add_argument(
        "--fallback-charset",
        help="新規ファイル作成時に使用するエンコーディング（省略時は--toの値を使用）",
    )
    parser.add_argument(
        "--watch-interval",
        type=float,
        default=1.0,
        help="監視間隔を秒単位で指定（デフォルト: 1.0）",
    )

    return parser.parse_args()


def main() -> int:
    """
    メイン関数

    Returns:
        終了コード
    """
    args = parse_args()

    logger = logging.getLogger("charcle")
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(levelname)s: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG if args.verbose else logging.INFO)

    if args.list:
        print("サポートするエンコーディング:")
        for encoding in get_supported_encodings():
            print(f"  {encoding}")
        return 0

    if not args.input_dir or not args.output_dir:
        logger.error("入力ディレクトリと出力ディレクトリを指定してください")
        return 1

    if not os.path.isdir(args.input_dir):
        logger.error(f"入力ディレクトリが存在しません: {args.input_dir}")
        return 1

    exclude_patterns = args.exclude.split(",") if args.exclude else []

    try:
        converter = Converter(
            from_encoding=args.from_encoding,
            to_encoding=args.to_encoding,
            max_size=args.max_size,
            exclude_patterns=exclude_patterns,
            verbose=args.verbose,
            fallback_charset=args.fallback_charset,
        )

        if args.watch:
            watcher = Watcher(
                src_dir=args.input_dir,
                dst_dir=args.output_dir,
                converter=converter,
                interval=args.watch_interval,
            )
            watcher.start()

            try:
                while watcher.running:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("Ctrl+C が押されました。終了します...")
            finally:
                watcher.stop()
        else:
            converter.convert_directory(args.input_dir, args.output_dir)

        return 0
    except Exception as e:
        logger.error(f"エラーが発生しました: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
