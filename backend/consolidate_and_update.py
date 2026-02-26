import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from backend.consolidate import consolidate_documents
from backend.onedrive_client import upload_file
from backend.config import ONEDRIVE_FOLDER_PATH

def consolidate_and_upload(output_filename: str = "consolidated_documents.txt", 
                           upload_folder: str = None):
    """
    Consolidate all processed documents and upload to OneDrive.
    
    Args:
        output_filename: Name of the consolidated file
        upload_folder: OneDrive folder path (defaults to ONEDRIVE_FOLDER_PATH from config)
    """
    print("=" * 60)
    print("CONSOLIDATE AND UPLOAD TO ONEDRIVE")
    print("=" * 60)
    
    # Step 1: Consolidate documents
    print("\nStep 1: Consolidating documents...")
    consolidated_path = consolidate_documents(output_filename)
    
    if not consolidated_path or not os.path.exists(consolidated_path):
        print(" Consolidation failed. Cannot proceed with upload.")
        return False
    
    print(f" Consolidation complete: {consolidated_path}")
    
    # Step 2: Upload to OneDrive
    print("\nStep 2: Uploading to OneDrive...")
    
    if upload_folder is None:
        upload_folder = ONEDRIVE_FOLDER_PATH or "/"
    
    try:
        result = upload_file(
            local_file_path=consolidated_path,
            onedrive_folder_path=upload_folder,
            filename=output_filename
        )
        
        if result:
            print("\n" + "=" * 60)
            print(" SUCCESS: Document consolidated and uploaded to OneDrive")
            print("=" * 60)
            print(f"Local file: {consolidated_path}")
            print(f"OneDrive location: {upload_folder}/{output_filename}")
            if result.get('webUrl'):
                print(f"Web URL: {result['webUrl']}")
            return True
        else:
            print("\n Upload failed")
            return False
            
    except Exception as e:
        print(f"\n Upload error: {e}")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Consolidate processed documents and upload to OneDrive"
    )
    parser.add_argument(
        "--output", "-o", 
        type=str, 
        default="consolidated_documents.txt",
        help="Output filename (default: consolidated_documents.txt)"
    )
    parser.add_argument(
        "--folder", "-f",
        type=str,
        default=None,
        help="OneDrive folder path (default: from .env ONEDRIVE_FOLDER_PATH)"
    )
    
    args = parser.parse_args()
    
    success = consolidate_and_upload(args.output, args.folder)
    
    if success:
        print("\nProcess completed successfully")
        sys.exit(0)
    else:
        print("\n Process failed")
        sys.exit(1)