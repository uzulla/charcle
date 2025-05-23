# Charcle

Charcleは、ファイルシステム上のテキストファイルの文字エンコーディングを変換するPythonベースのコマンドラインツールです。特にUTF-8以外の文字コードで書かれたファイル（主に日本語テキスト）をUTF-8に変換して「写像」ディレクトリを作成し、AI処理などの後に元のエンコーディングに戻す機能を提供します。

## 機能

- ディレクトリツリー全体のファイルエンコーディング変換
- ファイル変更の監視と自動変換（デーモンモード）
- シンボリックリンクの適切な処理
- ファイルシステムメタデータ（権限、所有者、タイムスタンプ）の保持
- 変更されていないファイルの自動スキップ機能（パフォーマンス向上）

## サポートするエンコーディング

- UTF-8
- EUC-JP
- Shift-JIS (Windows-31J)
- JIS (ISO-2022-JP)
- ASCII (ASCII文字のみのファイルは自動検出)

## インストール

```bash
pip install charcle
```

## 使用方法

```bash
# 基本的な使用法：ディレクトリをUTF-8に変換
charcle /path/to/source /path/to/destination

# 特定のエンコーディングからUTF-8に変換
charcle --from=SJIS /path/to/source /path/to/destination

# UTF-8からEUC-JPに変換（書き戻し）
charcle --to=EUC-JP /path/to/destination /path/to/source

# 1MB以上のファイルは変換せずにコピー
charcle --max-size=1M /path/to/source /path/to/destination

# 特定のパターンを除外
charcle --exclude=.git,*.bak,*.tmp /path/to/source /path/to/destination

# 変更を監視して自動変換（デーモンモード）
charcle --watch /path/to/source /path/to/destination

# 監視間隔を変更（5秒ごとにチェック）
charcle --watch --watch-interval=5 /path/to/source /path/to/destination

# 詳細なログを出力
charcle --verbose /path/to/source /path/to/destination

# サポートされているエンコーディングの一覧を表示
charcle --list
```

### 除外パターンについて

`--exclude`オプションは、カンマ区切りで複数のパターンを指定できます。パターンは以下のように動作します：

- ディレクトリ名にマッチ: `--exclude=.git` で `.git` ディレクトリ以下のすべてのファイルが除外されます
- ファイル名にマッチ: `--exclude=*.log` で拡張子が `.log` のすべてのファイルが除外されます
- 複数パターン: `--exclude=.git,*.bak,*tmp` のように複数のパターンを指定できます

## 開発

### 開発環境のセットアップ

```bash
# リポジトリのクローン
git clone https://github.com/uzulla/charcle.git
cd charcle

# Python 3.9以上が必要です
python --version

# 開発用依存関係のインストール
pip install -e ".[dev]"
```

### テストの実行

```bash
pytest
```

### リントの実行

```bash
ruff check .
```

## ライセンス

MIT License