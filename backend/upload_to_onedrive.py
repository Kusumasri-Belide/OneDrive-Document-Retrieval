import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from backend.onedrive_client import upload_file
from backend.config import ONEDRIVE_FOLDER_PATH

def upload_to_onedrive(local_file_path: str, 
                       onedrive_folder: str = None,
                       filename: str = None):
    """
    Upload a file to OneDrive.
    
    Args:
        local_file_path: Path to the local file to upload
        onedrive_folder: OneDrive folder path (defaults to ONEDRIVE_FOLDER_PATH from config)
        filename: Optional custom filename (defaults to original filename)
    
    Returns:
        True if upload successful, False otherwise
    """
    print("=" * 60)
    print("UPLOAD FILE TO ONEDRIVE")
    print("=" * 60)
    
    # Validate local file exists
    if not os.path.exists(local_file_path):
        print(f"✗ Error: Local file not found: {local_file_path}")
        return False
    
    # Use default folder if not specified
    if onedrive_folder is None:
        onedrive_folder = ONEDRIVE_FOLDER_PATH or "/"
    
    # Use original filename if not specified
    if filename is None:
        filename = os.path.basename(local_file_path)
    
    print(f"\nLocal file: {local_file_path}")
    print(f"File size: {os.path.getsize(local_file_path):,} bytes")
    print(f"OneDrive destination: {onedrive_folder}/{filename}")
    print()
    
    try:
        result = upload_file(
            local_file_path=local_file_path,
            onedrive_folder_path=onedrive_folder,
            filename=filename
        )
        
        if result:
            print("\n" + "=" * 60)
            print("✓ SUCCESS: File uploaded to OneDrive")
            print("=" * 60)
            print(f"OneDrive location: {onedrive_folder}/{filename}")
            if result.get('webUrl'):
                print(f"Web URL: {result['webUrl']}")
            if result.get('id'):
                print(f"File ID: {result['id']}")
            return True
        else:
            print("\n✗ Upload failed")
            return False
            
    except Exception as e:
        print(f"\n✗ Upload error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Upload a file to OneDrive"
    )
    parser.add_argument(
        "file",
        type=str,
        help="Path to the local file to upload"
    )
    parser.add_argument(
        "--folder", "-f",
        type=str,
        default=None,
        help="OneDrive folder path (default: from .env ONEDRIVE_FOLDER_PATH)"
    )
    parser.add_argument(
        "--name", "-n",
        type=str,
        default=None,
        help="Custom filename for OneDrive (default: original filename)"
    )
    
    args = parser.parse_args()
    
    success = upload_to_onedrive(args.file, args.folder, args.name)
    
    if success:
        print("\n✓ Upload completed successfully")
        sys.exit(0)
    else:
        print("\n✗ Upload failed")
        sys.exit(1)
