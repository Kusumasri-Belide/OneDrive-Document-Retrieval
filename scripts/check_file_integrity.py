#!/usr/bin/env python3
"""
Script to check file integrity and identify corrupted documents.
"""
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from backend.config import DOCS_DIR

def check_pdf_integrity(file_path):
    """Check if a PDF file is readable."""
    try:
        import fitz
        doc = fitz.open(file_path)
        page_count = len(doc)
        doc.close()
        return True, f"OK - {page_count} pages"
    except Exception as e:
        return False, str(e)

def check_office_integrity(file_path):
    """Check if an Office file is readable."""
    try:
        import zipfile
        with zipfile.ZipFile(file_path, 'r') as zip_file:
            # Try to read the file list
            file_list = zip_file.namelist()
            return True, f"OK - {len(file_list)} internal files"
    except Exception as e:
        return False, str(e)

def check_all_files():
    """Check integrity of all files in the docs directory."""
    print("Checking file integrity...\n")
    
    corrupted_files = []
    good_files = []
    
    for root, _, files in os.walk(DOCS_DIR):
        for filename in files:
            file_path = os.path.join(root, filename)
            rel_path = os.path.relpath(file_path, DOCS_DIR)
            
            if filename.lower().endswith('.pdf'):
                is_good, message = check_pdf_integrity(file_path)
            elif filename.lower().endswith(('.docx', '.pptx')):
                is_good, message = check_office_integrity(file_path)
            elif filename.lower().endswith(('.txt', '.csv')):
                # Text files - just check if readable
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read(100)  # Read first 100 chars
                    is_good, message = True, "OK - text file"
                except Exception as e:
                    is_good, message = False, str(e)
            else:
                is_good, message = True, "Skipped - unknown type"
            
            if is_good:
                print(f"{rel_path} - {message}")
                good_files.append(rel_path)
            else:
                print(f"{rel_path} - {message}")
                corrupted_files.append(rel_path)
    
    print(f"\nSummary:")
    print(f"Good files: {len(good_files)}")
    print(f"Corrupted files: {len(corrupted_files)}")
    
    if corrupted_files:
        print(f"\n Corrupted files that need attention:")
        for file in corrupted_files:
            print(f"   - {file}")
    
    return good_files, corrupted_files

if __name__ == "__main__":
    check_all_files()