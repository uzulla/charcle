# Charcle QA マニュアル

## 概要

このQAマニュアルは、Charcleの`--watch`オプションの機能を検証するためのテスト手順を提供します。特に、以下の機能を確認します：

1. ソースディレクトリ（EUC-JP）からデスティネーションディレクトリ（UTF-8）への自動変換
2. デスティネーションディレクトリ（UTF-8）からソースディレクトリ（EUC-JP）への書き戻し

## 前提条件

- Python 3.9以上がインストールされていること
- Charcleがインストールされていること（`pip install -e .`でインストール可能）

## テスト環境の準備

```bash
# テスト用ディレクトリの作成
mkdir -p ~/charcle-qa-test/src
mkdir -p ~/charcle-qa-test/dest

# テスト用のEUC-JPファイルを作成するためのPythonスクリプト
cat > ~/create_test_files.py << 'EOF'
import os

# テスト用のディレクトリパス
src_dir = os.path.expanduser("~/charcle-qa-test/src")

# サブディレクトリを作成
os.makedirs(os.path.join(src_dir, "subdir1"), exist_ok=True)
os.makedirs(os.path.join(src_dir, "subdir2"), exist_ok=True)

# テスト用のテキスト
test_texts = [
    "これはテスト文章です。",
    "日本語のEUC-JPエンコーディングのテストです。",
    "改行を含む\nテキストです。\n複数行あります。",
    "特殊文字: ！＃＄％＆（）＊＋，－．／：；＜＝＞？＠［＼］＾＿｀｛｜｝～",
]

# ファイルを作成
files = [
    os.path.join(src_dir, "test1.txt"),
    os.path.join(src_dir, "test2.txt"),
    os.path.join(src_dir, "subdir1", "test3.txt"),
    os.path.join(src_dir, "subdir2", "test4.txt"),
]

# EUC-JPでファイルを書き込む
for i, file_path in enumerate(files):
    with open(file_path, "wb") as f:
        f.write(test_texts[i % len(test_texts)].encode("euc-jp"))
    print(f"Created: {file_path} (EUC-JP)")

print("Test files created successfully.")
EOF

# テスト用ファイルの作成
python ~/create_test_files.py
```

## テストケース1: ソースディレクトリからデスティネーションディレクトリへの自動変換

### 手順

1. Charcleを`--watch`オプションで起動する

```bash
cd ~/repos/charcle
python -m charcle.cli --from=euc-jp --to=utf-8 --watch --verbose ~/charcle-qa-test/src ~/charcle-qa-test/dest
```

2. 別のターミナルで、ソースディレクトリに新しいEUC-JPファイルを追加する

```bash
# 新しいターミナルを開く
echo "新しいファイルのテスト" | iconv -f utf-8 -t euc-jp > ~/charcle-qa-test/src/new_file.txt
```

3. ソースディレクトリ内の既存ファイルを変更する

```bash
echo "既存ファイルの更新テスト" | iconv -f utf-8 -t euc-jp > ~/charcle-qa-test/src/test1.txt
```

### 期待される結果

- 新しく追加されたファイル`new_file.txt`がデスティネーションディレクトリに自動的にUTF-8で作成されること
- 変更された`test1.txt`がデスティネーションディレクトリで自動的に更新されること
- Charcleのログに変換処理が表示されること

### 確認方法

```bash
# ファイルの存在確認
ls -la ~/charcle-qa-test/dest/

# エンコーディングの確認
file -i ~/charcle-qa-test/dest/new_file.txt
file -i ~/charcle-qa-test/dest/test1.txt

# 内容の確認
cat ~/charcle-qa-test/dest/new_file.txt
cat ~/charcle-qa-test/dest/test1.txt
```

## テストケース2: デスティネーションディレクトリからソースディレクトリへの書き戻し

### 手順

1. Charcleが`--watch`オプションで実行中であることを確認する（テストケース1から継続）

2. デスティネーションディレクトリ内のファイルを変更する

```bash
echo "デスティネーションファイルの更新テスト" > ~/charcle-qa-test/dest/test2.txt
```

3. デスティネーションディレクトリに新しいファイルを作成する

```bash
echo "デスティネーションの新規ファイル" > ~/charcle-qa-test/dest/dest_new_file.txt
```

### 期待される結果

- 変更された`test2.txt`の内容がソースディレクトリのファイルにEUC-JPエンコーディングで書き戻されること
- 新しく作成された`dest_new_file.txt`がソースディレクトリにEUC-JPエンコーディングで作成されること
- Charcleのログに書き戻し処理が表示されること

### 確認方法

```bash
# ファイルの存在確認
ls -la ~/charcle-qa-test/src/

# エンコーディングの確認
file -i ~/charcle-qa-test/src/test2.txt
file -i ~/charcle-qa-test/src/dest_new_file.txt

# 内容の確認（EUC-JPからUTF-8に変換して表示）
iconv -f euc-jp -t utf-8 ~/charcle-qa-test/src/test2.txt
iconv -f euc-jp -t utf-8 ~/charcle-qa-test/src/dest_new_file.txt
```

## テストケース3: ディレクトリ構造の変更

### 手順

1. Charcleが`--watch`オプションで実行中であることを確認する

2. ソースディレクトリに新しいサブディレクトリを作成し、その中にファイルを追加する

```bash
mkdir -p ~/charcle-qa-test/src/new_subdir
echo "新しいサブディレクトリのテスト" | iconv -f utf-8 -t euc-jp > ~/charcle-qa-test/src/new_subdir/subdir_file.txt
```

3. デスティネーションディレクトリに新しいサブディレクトリを作成し、その中にファイルを追加する

```bash
mkdir -p ~/charcle-qa-test/dest/dest_new_subdir
echo "デスティネーションの新しいサブディレクトリのテスト" > ~/charcle-qa-test/dest/dest_new_subdir/dest_subdir_file.txt
```

### 期待される結果

- ソースディレクトリに作成された新しいサブディレクトリとファイルがデスティネーションディレクトリに自動的に作成されること
- デスティネーションディレクトリに作成された新しいサブディレクトリとファイルがソースディレクトリに自動的に作成されること
- すべてのファイルが適切なエンコーディングで変換されること

### 確認方法

```bash
# ディレクトリとファイルの存在確認
ls -la ~/charcle-qa-test/dest/new_subdir/
ls -la ~/charcle-qa-test/src/dest_new_subdir/

# エンコーディングの確認
file -i ~/charcle-qa-test/dest/new_subdir/subdir_file.txt
file -i ~/charcle-qa-test/src/dest_new_subdir/dest_subdir_file.txt

# 内容の確認
cat ~/charcle-qa-test/dest/new_subdir/subdir_file.txt
iconv -f euc-jp -t utf-8 ~/charcle-qa-test/src/dest_new_subdir/dest_subdir_file.txt
```

## テストケース4: ファイルの削除

### 手順

1. Charcleが`--watch`オプションで実行中であることを確認する

2. ソースディレクトリからファイルを削除する

```bash
rm ~/charcle-qa-test/src/test3.txt
```

3. デスティネーションディレクトリからファイルを削除する

```bash
rm ~/charcle-qa-test/dest/test4.txt
```

### 期待される結果

- ソースディレクトリから削除されたファイルがデスティネーションディレクトリからも自動的に削除されること
- デスティネーションディレクトリから削除されたファイルがソースディレクトリからも自動的に削除されること

### 確認方法

```bash
# ファイルが削除されたことを確認
ls -la ~/charcle-qa-test/dest/ | grep test3.txt
ls -la ~/charcle-qa-test/src/ | grep test4.txt
```

## テスト終了

1. Charcleのプロセスを終了する（Ctrl+C）

2. テスト環境のクリーンアップ（オプション）

```bash
rm -rf ~/charcle-qa-test
rm ~/create_test_files.py
```

## 注意事項

- テスト中にエラーが発生した場合は、Charcleのログを確認してください
- ファイルシステムの変更が反映されるまでに若干の遅延が発生する場合があります（監視間隔に依存）
- 大量のファイルを一度に変更すると、すべての変更が処理されるまでに時間がかかる場合があります
