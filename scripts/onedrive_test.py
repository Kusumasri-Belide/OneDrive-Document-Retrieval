#!/usr/bin/env python3
"""
Simple script to test OneDrive integration
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from backend.ingest_onedrive import fetch_onedrive_folder

if __name__ == "__main__":
    print("Testing OneDrive integration...")
    try:
        fetch_onedrive_folder()
        print("OneDrive test completed successfully!")
    except Exception as e:
        print(f"OneDrive test failed: {e}")
        sys.exit(1)