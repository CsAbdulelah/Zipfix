# ZipFix

A tool to fix corrupted or incomplete zip files and extract their contents.

## Features

- Attempts to repair corrupted ZIP files by finding file signatures
- Recovers files from ZIP archives even when the central directory is damaged
- Extracts files from both original and repaired ZIP archives
- Simple command-line interface

## Requirements

- Python 3.6 or higher

## Usage

```bash
# Basic usage
python zipfix.py your_corrupted_file.zip

# Specify output directory for extracted files
python zipfix.py your_corrupted_file.zip -o extracted_files

# Specify path for the fixed zip file
python zipfix.py your_corrupted_file.zip -f fixed.zip

# Only attempt to repair without extracting
python zipfix.py your_corrupted_file.zip --repair-only

# Only attempt to extract without repairing
python zipfix.py your_corrupted_file.zip --extract-only
```

## How it works

ZipFix works by:

1. First attempting a normal extraction with the Python zipfile module
2. If that fails, scanning the file for ZIP signatures to locate file entries
3. Reconstructing the ZIP file structure based on file headers
4. Creating a new, fixed ZIP file with the recoverable content
5. Extracting files from the repaired archive

## Examples

### Repairing a corrupted download

```bash
python zipfix.py incomplete_download.zip
```

### Extracting files directly

```bash
python zipfix.py damaged_archive.zip --extract-only -o recovered_files
```

### Creating a fixed ZIP file without extraction

```bash
python zipfix.py broken.zip --repair-only -f repaired.zip
``` 
