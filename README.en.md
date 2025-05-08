# Charcle

Charcle is a Python-based command-line tool for converting character encodings of text files on the file system. It specifically provides functionality to convert files written in non-UTF-8 character encodings (primarily Japanese text) to UTF-8, creating a "mirror" directory, and then converting them back to their original encoding after AI processing or other operations.

## Features

- Character encoding conversion for entire directory trees
- File change monitoring and automatic conversion (daemon mode)
- Proper handling of symbolic links
- Preservation of file system metadata (permissions, ownership, timestamps)
- Automatic skipping of unchanged files (performance optimization)

## Supported Encodings

- UTF-8
- EUC-JP
- Shift-JIS (Windows-31J)
- JIS (ISO-2022-JP)
- ASCII (automatically detected for files containing only ASCII characters)

## Installation

```bash
pip install charcle
```

## Usage

```bash
# Basic usage: Convert a directory to UTF-8
charcle /path/to/source /path/to/destination

# Convert from a specific encoding to UTF-8
charcle --from=SJIS /path/to/source /path/to/destination

# Convert from UTF-8 to EUC-JP (writing back)
charcle --to=EUC-JP /path/to/destination /path/to/source

# Files larger than 1MB are copied without conversion
charcle --max-size=1M /path/to/source /path/to/destination

# Exclude specific patterns
charcle --exclude=.git,*.bak,*.tmp /path/to/source /path/to/destination

# Monitor for changes and convert automatically (daemon mode)
charcle --watch /path/to/source /path/to/destination

# Change the monitoring interval (check every 5 seconds)
charcle --watch --watch-interval=5 /path/to/source /path/to/destination

# Output detailed logs
charcle --verbose /path/to/source /path/to/destination

# Display a list of supported encodings
charcle --list
```

### About Exclude Patterns

The `--exclude` option allows you to specify multiple patterns separated by commas. The patterns work as follows:

- Match directory names: `--exclude=.git` excludes all files under the `.git` directory
- Match file names: `--exclude=*.log` excludes all files with the `.log` extension
- Multiple patterns: You can specify multiple patterns like `--exclude=.git,*.bak,*tmp`

## Development

### Setting Up the Development Environment

```bash
# Clone the repository
git clone https://github.com/uzulla/charcle.git
cd charcle

# Python 3.9 or higher is required
python --version

# Install development dependencies
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
```

### Running Linters

```bash
ruff check .
```

## License

MIT License