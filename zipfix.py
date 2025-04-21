#!/usr/bin/env python3
import os
import sys
import struct
import zipfile
import argparse
import shutil
from pathlib import Path

# Constants for ZIP file format
LOCAL_FILE_HEADER = b'PK\x03\x04'
CENTRAL_DIR_HEADER = b'PK\x01\x02'
END_OF_CENTRAL_DIR = b'PK\x05\x06'

def find_file_signatures(file_path):
    """Find all ZIP signature positions in the file."""
    signatures = {
        'local_headers': [],
        'central_dir_headers': [],
        'end_of_central_dir': None
    }
    
    with open(file_path, 'rb') as f:
        data = f.read()
        
    # Find all local file headers
    offset = 0
    while True:
        offset = data.find(LOCAL_FILE_HEADER, offset)
        if offset == -1:
            break
        signatures['local_headers'].append(offset)
        offset += 4
    
    # Find all central directory headers
    offset = 0
    while True:
        offset = data.find(CENTRAL_DIR_HEADER, offset)
        if offset == -1:
            break
        signatures['central_dir_headers'].append(offset)
        offset += 4
    
    # Find end of central directory record
    offset = data.rfind(END_OF_CENTRAL_DIR)
    if offset != -1:
        signatures['end_of_central_dir'] = offset
    
    return signatures

def extract_filename_from_header(data, offset):
    """Extract filename from a local file header."""
    try:
        filename_length = struct.unpack('<H', data[offset+26:offset+28])[0]
        filename = data[offset+30:offset+30+filename_length]
        return filename.decode('utf-8', errors='replace')
    except:
        return None

def repair_zip(file_path, output_path=None):
    """Try to repair a broken zip file."""
    if output_path is None:
        output_path = str(Path(file_path).with_suffix('.fixed.zip'))
    
    with open(file_path, 'rb') as f:
        data = f.read()
    
    signatures = find_file_signatures(file_path)
    
    if not signatures['local_headers']:
        print("No valid ZIP file headers found. Cannot repair.")
        return False
    
    print(f"Found {len(signatures['local_headers'])} file entries")
    
    # Create a new zip file
    with zipfile.ZipFile(output_path, 'w') as new_zip:
        for i, offset in enumerate(signatures['local_headers']):
            try:
                # Get the filename
                filename = extract_filename_from_header(data, offset)
                if not filename:
                    filename = f"recovered_file_{i}.bin"
                
                # Get the next header position to determine file size
                next_offset = None
                for next_header in signatures['local_headers']:
                    if next_header > offset:
                        next_offset = next_header
                        break
                
                # If we can't determine the file size, try a reasonable guess
                if next_offset is None:
                    # Try to get file size from header
                    try:
                        compressed_size = struct.unpack('<I', data[offset+18:offset+22])[0]
                        extra_field_length = struct.unpack('<H', data[offset+28:offset+30])[0]
                        file_data_offset = offset + 30 + filename_length + extra_field_length
                        file_data = data[file_data_offset:file_data_offset+compressed_size]
                    except:
                        # If that fails, just take the next 1MB max
                        filename_length = struct.unpack('<H', data[offset+26:offset+28])[0]
                        extra_field_length = struct.unpack('<H', data[offset+28:offset+30])[0]
                        file_data_offset = offset + 30 + filename_length + extra_field_length
                        file_data = data[file_data_offset:file_data_offset+1024*1024]
                else:
                    # Get data between this header and the next one
                    filename_length = struct.unpack('<H', data[offset+26:offset+28])[0]
                    extra_field_length = struct.unpack('<H', data[offset+28:offset+30])[0]
                    file_data_offset = offset + 30 + filename_length + extra_field_length
                    file_data = data[file_data_offset:next_offset]
                
                # Write to the new zip file
                new_zip.writestr(filename, file_data)
                print(f"Recovered file: {filename}")
            except Exception as e:
                print(f"Error processing file at offset {offset}: {e}")
    
    print(f"Repair attempt completed. Saved to {output_path}")
    return True

def extract_files(zip_path, output_dir=None):
    """Extract files from a zip file, even if it's partially corrupted."""
    if output_dir is None:
        output_dir = Path(zip_path).stem + "_extracted"
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    try:
        with zipfile.ZipFile(zip_path) as z:
            for file_info in z.infolist():
                try:
                    z.extract(file_info, output_dir)
                    print(f"Extracted: {file_info.filename}")
                except Exception as e:
                    print(f"Failed to extract {file_info.filename}: {e}")
        return True
    except Exception as e:
        print(f"Error opening zip file: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Fix and extract corrupted ZIP files')
    parser.add_argument('zip_file', help='Path to the corrupted ZIP file')
    parser.add_argument('-o', '--output', help='Output directory for extracted files')
    parser.add_argument('-f', '--fixed', help='Path for the fixed ZIP file')
    parser.add_argument('--extract-only', action='store_true', help='Only try to extract without repairing')
    parser.add_argument('--repair-only', action='store_true', help='Only repair without extracting')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.zip_file):
        print(f"Error: File {args.zip_file} does not exist")
        return 1
    
    if args.extract_only and args.repair_only:
        print("Error: Cannot use both --extract-only and --repair-only")
        return 1
    
    success = False
    
    # Try to extract directly first if not repair-only
    if not args.repair_only:
        print(f"Attempting to extract files from {args.zip_file}...")
        success = extract_files(args.zip_file, args.output)
        if success:
            print("Extraction successful!")
            if args.extract_only:
                return 0
        else:
            print("Direct extraction failed. Attempting repair...")
    
    # Repair if direct extraction failed or repair-only specified
    if not args.extract_only:
        fixed_zip = args.fixed if args.fixed else str(Path(args.zip_file).with_suffix('.fixed.zip'))
        print(f"Attempting to repair {args.zip_file}...")
        repair_success = repair_zip(args.zip_file, fixed_zip)
        
        if repair_success and not args.repair_only:
            print(f"Attempting to extract files from repaired zip...")
            extract_output = args.output if args.output else Path(args.zip_file).stem + "_extracted"
            extract_success = extract_files(fixed_zip, extract_output)
            
            if extract_success:
                print("Extraction from repaired zip successful!")
                success = True
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 