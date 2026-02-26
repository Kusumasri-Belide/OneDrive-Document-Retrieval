import os
import sys
from typing import List, Dict, Set
from datetime import datetime
import fitz  # PyMuPDF for file integrity testing

# Add parent directory to path for direct execution
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config import DOCS_DIR, ONEDRIVE_FOLDER_PATH, MICROSOFT_CLIENT_ID
from backend.auth import get_access_token
from backend.onedrive_client import list_folder_items, download_file

def _safe_name(name: str) -> str:
    """Create a safe filename by removing invalid characters."""
    return "".join(c for c in name if c not in '<>:"/\\|?*').strip() or "untitled"

def _ensure_dir(path: str):
    """Ensure directory exists."""
    os.makedirs(path, exist_ok=True)

def _test_file_integrity(file_path: str) -> bool:
    """Test if a downloaded file is not corrupted."""
    try:
        if file_path.lower().endswith('.pdf'):
            # Test PDF integrity
            doc = fitz.open(file_path)
            if len(doc) == 0:
                doc.close()
                return False
            # Try to extract text from first page
            page = doc[0]
            test_text = page.get_text()
            doc.close()
            return True  # If we can open and read, it's likely good
        elif file_path.lower().endswith(('.docx', '.pptx')):
            # Test Office file integrity
            import zipfile
            with zipfile.ZipFile(file_path, 'r') as zip_file:
                zip_file.namelist()  # This will fail if corrupted
            return True
        else:
            # For other files, just check if readable
            with open(file_path, 'rb') as f:
                f.read(1024)  # Try to read first 1KB
            return True
    except Exception:
        return False

def _download_with_retry(item: Dict, dest_path: str, max_retries: int = 3) -> bool:
    """Download file with retry mechanism and integrity checking."""
    name = item.get("name", "unknown")
    
    for attempt in range(max_retries):
        try:
            if attempt > 0:
                print(f"Retry {attempt}/{max_retries-1}: {name}")
            
            content = download_file(item)
            
            # Write as binary to preserve file integrity
            with open(dest_path, "wb") as f:
                f.write(content)
            
            # Test file integrity
            if _test_file_integrity(dest_path):
                file_size = len(content)
                print(f"Downloaded: {name} ({file_size:,} bytes)")
                return True
            else:
                print(f"Downloaded file appears corrupted: {name}")
                # Remove corrupted file
                if os.path.exists(dest_path):
                    os.remove(dest_path)
                
                if attempt < max_retries - 1:
                    print(f"Will retry download...")
                    continue
                else:
                    print(f"All retry attempts failed for: {name}")
                    return False
                    
        except Exception as e:
            print(f"Download attempt {attempt + 1} failed for {name}: {e}")
            if attempt < max_retries - 1:
                print(f"Retrying...")
                continue
            else:
                print(f"All download attempts failed for: {name}")
                return False
    
    return False

def fetch_onedrive_folder(folder_path: str = None, force_redownload: bool = False, recursive: bool = True):
    """
    Fetch all files from a specific OneDrive folder with robust error handling.
    
    Args:
        folder_path: OneDrive folder path to process
        force_redownload: If True, re-download all files regardless of modification time
        recursive: If True, recursively download from subfolders
    """
    if folder_path is None:
        folder_path = ONEDRIVE_FOLDER_PATH or "/"
    
    _ensure_dir(DOCS_DIR)
    
    try:
        print(f"Processing folder: {folder_path}")
        if force_redownload:
            print("Force redownload mode enabled")
        if recursive:
            print("Recursive mode enabled - will process subfolders")
        
        items = list_folder_items(folder_path, recursive=recursive)
        
        download_stats = {
            'total': 0,
            'downloaded': 0,
            'skipped': 0,
            'failed': 0,
            'redownloaded': 0,
            'folders_processed': set()
        }
        
        for item in items:
            # Skip folders (they're already processed for file listing)
            if item.get("folder"):
                continue
                
            name = _safe_name(item["name"])
            relative_path = item.get("_relative_path", item["name"])
            
            # Skip special OneDrive items that can't be downloaded
            if name.lower() in ["personal vault", "vault"]:
                print(f"Skipping protected item: {name}")
                continue
            
            download_stats['total'] += 1
            
            # Create destination path preserving folder structure
            if recursive and "/" in relative_path:
                # Create subdirectories in local docs folder
                rel_dir = os.path.dirname(relative_path)
                local_subdir = os.path.join(DOCS_DIR, _safe_name(rel_dir))
                _ensure_dir(local_subdir)
                dest_path = os.path.join(local_subdir, name)
                
                # Track processed folders for stats
                download_stats['folders_processed'].add(rel_dir)
            else:
                dest_path = os.path.join(DOCS_DIR, name)
            
            should_download = force_redownload
            
            if not force_redownload and os.path.exists(dest_path):
                # Check if file needs updating
                local_mtime = os.path.getmtime(dest_path)
                remote_mtime_str = item.get("lastModifiedDateTime", "")
                
                if remote_mtime_str:
                    remote_mtime = datetime.fromisoformat(remote_mtime_str.replace("Z", "+00:00")).timestamp()
                    if local_mtime >= remote_mtime:
                        # File is up to date, but check integrity
                        if _test_file_integrity(dest_path):
                            print(f"⏭️  Skipping (up to date): {relative_path}")
                            download_stats['skipped'] += 1
                            continue
                        else:
                            print(f"🔧 File exists but appears corrupted, re-downloading: {relative_path}")
                            should_download = True
                            download_stats['redownloaded'] += 1
                    else:
                        should_download = True
                else:
                    should_download = True
            
            if should_download or not os.path.exists(dest_path):
                print(f"⬇Downloading: {relative_path}")
                
                # Remove existing file if it exists (for clean redownload)
                if os.path.exists(dest_path):
                    os.remove(dest_path)
                
                if _download_with_retry(item, dest_path):
                    download_stats['downloaded'] += 1
                else:
                    download_stats['failed'] += 1
                
    except Exception as e:
        print(f"Error processing folder {folder_path}: {e}")
        return
    
    # Print summary
    print("\n" + "="*60)
    print("OneDrive Ingestion Summary:")
    print(f"Total files found: {download_stats['total']}")
    if recursive and download_stats['folders_processed']:
        print(f"Subfolders processed: {len(download_stats['folders_processed'])}")
        for folder in sorted(download_stats['folders_processed']):
            print(f"   - {folder}")
    print(f"Downloaded: {download_stats['downloaded']}")
    print(f"Re-downloaded (corrupted): {download_stats['redownloaded']}")
    print(f"Skipped (up to date): {download_stats['skipped']}")
    print(f"Failed: {download_stats['failed']}")
    
    if download_stats['failed'] > 0:
        print(f"\nTip: Run with --force-redownload to retry failed files")
    
    print("OneDrive ingestion complete.")

def force_redownload_corrupted():
    """Force re-download files that are known to be problematic."""
    print("Scanning for corrupted files and forcing re-download...")
    
    corrupted_files: Set[str] = set()
    
    # Scan existing files for corruption
    if os.path.exists(DOCS_DIR):
        for filename in os.listdir(DOCS_DIR):
            file_path = os.path.join(DOCS_DIR, filename)
            if os.path.isfile(file_path) and not _test_file_integrity(file_path):
                corrupted_files.add(filename)
                print(f"Found corrupted file: {filename}")
    
    if corrupted_files:
        print(f"\nRemoving {len(corrupted_files)} corrupted files...")
        for filename in corrupted_files:
            file_path = os.path.join(DOCS_DIR, filename)
            try:
                os.remove(file_path)
                print(f"Removed: {filename}")
            except Exception as e:
                print(f"Failed to remove {filename}: {e}")
        
        print(f"\nRe-downloading corrupted files...")
        fetch_onedrive_folder(force_redownload=False)  # Will download missing files
    else:
        print("No corrupted files found!")

def cleanup_temp_files():
    """Clean up any temporary or duplicate files."""
    print("Cleaning up temporary files...")
    
    cleanup_patterns = [
        ".tmp",
        ".temp", 
        "~$",  # Office temp files
        ".crdownload",  # Chrome download temp files
    ]
    
    cleaned = 0
    if os.path.exists(DOCS_DIR):
        for filename in os.listdir(DOCS_DIR):
            file_path = os.path.join(DOCS_DIR, filename)
            if os.path.isfile(file_path):
                for pattern in cleanup_patterns:
                    if pattern in filename.lower():
                        try:
                            os.remove(file_path)
                            print(f"Removed temp file: {filename}")
                            cleaned += 1
                            break
                        except Exception as e:
                            print(f"Failed to remove {filename}: {e}")
    
    if cleaned > 0:
        print(f"Cleaned up {cleaned} temporary files")
    else:
        print("No temporary files found")

if __name__ == "__main__":
    if not MICROSOFT_CLIENT_ID:
        print("Set MICROSOFT_CLIENT_ID in .env file")
        sys.exit(1)
    
    import argparse
    parser = argparse.ArgumentParser(description="OneDrive Document Ingestion with Robust Error Handling")
    parser.add_argument("--force-redownload", action="store_true", 
                       help="Force re-download all files regardless of modification time")
    parser.add_argument("--fix-corrupted", action="store_true",
                       help="Scan for and fix corrupted files")
    parser.add_argument("--cleanup", action="store_true",
                       help="Clean up temporary files")
    parser.add_argument("--folder", type=str, default=None,
                       help="Specific OneDrive folder path to process")
    
    args = parser.parse_args()
    
    folder_path = args.folder or ONEDRIVE_FOLDER_PATH or "/"
    
    print("OneDrive Document Ingestion Tool")
    print("=" * 50)
    
    if args.cleanup:
        cleanup_temp_files()
        print()
    
    if args.fix_corrupted:
        force_redownload_corrupted()
        print()
    
    print(f"Processing OneDrive folder: {folder_path}")
    fetch_onedrive_folder(folder_path, force_redownload=args.force_redownload)