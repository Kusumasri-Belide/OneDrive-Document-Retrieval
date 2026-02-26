import requests
from typing import List, Dict
from .config import GRAPH_BASE_URL
from .auth import get_access_token, clear_token_cache

# Cache the token to avoid repeated authentication
_cached_headers = None

def _get_headers():
    """Get authentication headers with token caching."""
    global _cached_headers
    if _cached_headers is None:
        token = get_access_token()
        _cached_headers = {"Authorization": f"Bearer {token}"}
    return _cached_headers

def _make_authenticated_request(url: str, method: str = "GET", data: bytes = None, extra_headers: dict = None):
    """Make an authenticated request with automatic token refresh on 401."""
    global _cached_headers
    
    headers = _get_headers().copy()
    if extra_headers:
        headers.update(extra_headers)
    
    if method.upper() == "GET":
        resp = requests.get(url, headers=headers)
    elif method.upper() == "PUT":
        resp = requests.put(url, headers=headers, data=data)
    elif method.upper() == "POST":
        resp = requests.post(url, headers=headers, data=data)
    else:
        raise ValueError(f"Unsupported HTTP method: {method}")
    
    # If we get 401 (Unauthorized), clear cache and retry once
    if resp.status_code == 401:
        print("Token expired, refreshing authentication...")
        _cached_headers = None  # Clear cached headers
        clear_token_cache()     # Clear token cache
        headers = _get_headers().copy()  # Get fresh token and headers
        if extra_headers:
            headers.update(extra_headers)
        
        if method.upper() == "GET":
            resp = requests.get(url, headers=headers)
        elif method.upper() == "PUT":
            resp = requests.put(url, headers=headers, data=data)
        elif method.upper() == "POST":
            resp = requests.post(url, headers=headers, data=data)
    
    return resp

def list_folder_items(folder_path: str, recursive: bool = False) -> List[Dict]:
    """
    List items in a OneDrive folder.
    
    Args:
        folder_path: Path to the OneDrive folder
        recursive: If True, recursively list items from all subfolders
    
    Returns:
        List of file and folder items
    """
    print(f"DEBUG: Using folder path: {folder_path} (recursive: {recursive})")
    
    # First, let's try to get drive info
    drive_url = f"{GRAPH_BASE_URL}/me/drive"
    print(f"DEBUG: Testing drive access: {drive_url}")
    
    resp = _make_authenticated_request(drive_url)
    print(f"DEBUG: Drive response status: {resp.status_code}")
    if resp.status_code != 200:
        print(f"DEBUG: Drive response content: {resp.text}")
        resp.raise_for_status()
    
    drive_info = resp.json()
    print(f"DEBUG: Drive info: {drive_info.get('name', 'Unknown')} - {drive_info.get('driveType', 'Unknown type')}")
    
    if recursive:
        return _list_folder_recursive(folder_path)
    else:
        return _list_folder_single(folder_path)


def _list_folder_single(folder_path: str) -> List[Dict]:
    """List items in a single folder (non-recursive)."""
    # If folder_path is empty or "/", list root
    if not folder_path or folder_path == "/":
        url = f"{GRAPH_BASE_URL}/me/drive/root/children"
    else:
        url = f"{GRAPH_BASE_URL}/me/drive/root:{folder_path}:/children"
    
    print(f"DEBUG: Full URL: {url}")
    items = []

    while url:
        resp = _make_authenticated_request(url)
        print(f"DEBUG: Response status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"DEBUG: Response content: {resp.text}")
        resp.raise_for_status()
        data = resp.json()
        items.extend(data.get("value", []))
        url = data.get("@odata.nextLink")

    return items


def _list_folder_recursive(folder_path: str, _current_path: str = "") -> List[Dict]:
    """Recursively list all items in folder and subfolders."""
    all_items = []
    
    # Get items in current folder
    current_folder_path = folder_path if not _current_path else f"{folder_path}/{_current_path}"
    items = _list_folder_single(current_folder_path)
    
    files = []
    folders = []
    
    # Separate files and folders
    for item in items:
        # Add relative path information to the item
        if _current_path:
            item["_relative_path"] = f"{_current_path}/{item['name']}"
        else:
            item["_relative_path"] = item["name"]
        
        if item.get("folder"):
            folders.append(item)
        else:
            files.append(item)
    
    # Add all files from current folder
    all_items.extend(files)
    
    # Recursively process subfolders
    for folder_item in folders:
        folder_name = folder_item["name"]
        subfolder_path = f"{_current_path}/{folder_name}" if _current_path else folder_name
        
        print(f"Recursively processing subfolder: {subfolder_path}")
        
        try:
            subfolder_items = _list_folder_recursive(folder_path, subfolder_path)
            all_items.extend(subfolder_items)
        except Exception as e:
            print(f"Failed to process subfolder {subfolder_path}: {e}")
            continue
    
    return all_items


def download_file(item: Dict) -> bytes:
    """Download file content as bytes to preserve binary files."""
    file_id = item["id"]
    content_url = f"{GRAPH_BASE_URL}/me/drive/items/{file_id}/content"
    
    print(f"DEBUG: Downloading file via Graph API: {content_url}")
    
    resp = _make_authenticated_request(content_url)
    resp.raise_for_status()
    return resp.content  # Use .content for binary data, not .text


def _ensure_folder_exists(folder_path: str) -> bool:
    """
    Ensure a folder exists in OneDrive, create if it doesn't.
    
    Args:
        folder_path: OneDrive folder path (e.g., "/Boeing" or "/Boeing/Subfolder")
    
    Returns:
        True if folder exists or was created successfully
    """
    if not folder_path or folder_path == "/":
        return True  # Root always exists
    
    # Check if folder exists
    folder = folder_path.strip("/")
    check_url = f"{GRAPH_BASE_URL}/me/drive/root:/{folder}"
    
    resp = _make_authenticated_request(check_url)
    
    if resp.status_code == 200:
        print(f"✓ Folder exists: {folder_path}")
        return True
    elif resp.status_code == 404:
        print(f"Folder not found: {folder_path}, creating...")
        
        # Create folder - need to handle nested paths
        path_parts = folder.split("/")
        current_path = ""
        
        for part in path_parts:
            parent_path = current_path if current_path else ""
            current_path = f"{current_path}/{part}" if current_path else part
            
            # Check if this level exists
            check_url = f"{GRAPH_BASE_URL}/me/drive/root:/{current_path}"
            resp = _make_authenticated_request(check_url)
            
            if resp.status_code == 404:
                # Create this folder level
                if parent_path:
                    create_url = f"{GRAPH_BASE_URL}/me/drive/root:/{parent_path}:/children"
                else:
                    create_url = f"{GRAPH_BASE_URL}/me/drive/root/children"
                
                folder_data = {
                    "name": part,
                    "folder": {},
                    "@microsoft.graph.conflictBehavior": "rename"
                }
                
                import json
                extra_headers = {"Content-Type": "application/json"}
                resp = _make_authenticated_request(
                    create_url, 
                    method="POST", 
                    data=json.dumps(folder_data).encode('utf-8'),
                    extra_headers=extra_headers
                )
                
                if resp.status_code in [200, 201]:
                    print(f"✓ Created folder: {current_path}")
                else:
                    print(f"✗ Failed to create folder {current_path}: {resp.status_code}")
                    print(f"  Response: {resp.text}")
                    return False
        
        return True
    else:
        print(f"✗ Error checking folder: {resp.status_code}")
        print(f"  Response: {resp.text}")
        return False


def upload_file(local_file_path: str, onedrive_folder_path: str, filename: str = None) -> Dict:
    """
    Upload a file to OneDrive.
    
    Args:
        local_file_path: Path to the local file to upload
        onedrive_folder_path: OneDrive folder path (e.g., "/Boeing" or "/")
        filename: Optional custom filename (defaults to local filename)
    
    Returns:
        Dict with upload result information
    """
    import os
    
    if not os.path.exists(local_file_path):
        raise FileNotFoundError(f"Local file not found: {local_file_path}")
    
    # Get filename
    if filename is None:
        filename = os.path.basename(local_file_path)
    
    # Read file content
    with open(local_file_path, 'rb') as f:
        file_content = f.read()
    
    file_size = len(file_content)
    print(f"Uploading {filename} ({file_size:,} bytes) to {onedrive_folder_path}")
    
    # Try multiple upload methods
    methods = [
        ("Path-based simple", _upload_via_path_simple),
        ("Path-based children", _upload_via_path_children),
        ("ID-based", _upload_via_folder_id),
    ]
    
    for method_name, upload_func in methods:
        try:
            print(f"Trying method: {method_name}")
            result = upload_func(onedrive_folder_path, filename, file_content)
            if result:
                print(f"✓ Upload successful using {method_name}: {filename}")
                print(f"  File ID: {result.get('id')}")
                print(f"  Web URL: {result.get('webUrl')}")
                return result
        except Exception as e:
            print(f"  Method {method_name} failed: {e}")
            continue
    
    raise Exception("All upload methods failed")


def _upload_via_path_simple(folder_path: str, filename: str, file_content: bytes) -> Dict:
    """Upload using simple path-based URL."""
    if not folder_path or folder_path == "/":
        upload_url = f"{GRAPH_BASE_URL}/me/drive/root/children/{filename}/content"
    else:
        folder = folder_path.strip("/")
        upload_url = f"{GRAPH_BASE_URL}/me/drive/root:/{folder}:/{filename}:/content"
    
    print(f"  URL: {upload_url}")
    extra_headers = {"Content-Type": "application/octet-stream"}
    resp = _make_authenticated_request(upload_url, method="PUT", data=file_content, extra_headers=extra_headers)
    
    if resp.status_code in [200, 201]:
        return resp.json()
    else:
        raise Exception(f"Status {resp.status_code}: {resp.text}")


def _upload_via_path_children(folder_path: str, filename: str, file_content: bytes) -> Dict:
    """Upload using children endpoint."""
    if not folder_path or folder_path == "/":
        upload_url = f"{GRAPH_BASE_URL}/me/drive/root/children"
    else:
        folder = folder_path.strip("/")
        upload_url = f"{GRAPH_BASE_URL}/me/drive/root:/{folder}:/children"
    
    # First create the file item
    import json
    file_metadata = {
        "name": filename,
        "file": {},
        "@microsoft.graph.conflictBehavior": "replace"
    }
    
    print(f"  Creating file item at: {upload_url}")
    extra_headers = {"Content-Type": "application/json"}
    resp = _make_authenticated_request(
        upload_url, 
        method="POST", 
        data=json.dumps(file_metadata).encode('utf-8'),
        extra_headers=extra_headers
    )
    
    if resp.status_code not in [200, 201]:
        raise Exception(f"Create failed - Status {resp.status_code}: {resp.text}")
    
    file_item = resp.json()
    file_id = file_item.get('id')
    
    # Now upload content to the created file
    content_url = f"{GRAPH_BASE_URL}/me/drive/items/{file_id}/content"
    print(f"  Uploading content to: {content_url}")
    
    extra_headers = {"Content-Type": "application/octet-stream"}
    resp = _make_authenticated_request(content_url, method="PUT", data=file_content, extra_headers=extra_headers)
    
    if resp.status_code in [200, 201]:
        return resp.json()
    else:
        raise Exception(f"Content upload failed - Status {resp.status_code}: {resp.text}")


def _upload_via_folder_id(folder_path: str, filename: str, file_content: bytes) -> Dict:
    """Upload using folder ID."""
    folder_id = _get_folder_id(folder_path)
    if not folder_id:
        raise Exception(f"Cannot get folder ID for: {folder_path}")
    
    upload_url = f"{GRAPH_BASE_URL}/me/drive/items/{folder_id}:/{filename}:/content"
    print(f"  URL: {upload_url}")
    
    extra_headers = {"Content-Type": "application/octet-stream"}
    resp = _make_authenticated_request(upload_url, method="PUT", data=file_content, extra_headers=extra_headers)
    
    if resp.status_code in [200, 201]:
        return resp.json()
    else:
        raise Exception(f"Status {resp.status_code}: {resp.text}")


def _get_folder_id(folder_path: str) -> str:
    """
    Get the folder ID for a given path.
    
    Args:
        folder_path: OneDrive folder path
    
    Returns:
        Folder ID or None if not found
    """
    if not folder_path or folder_path == "/":
        # Get root folder ID
        url = f"{GRAPH_BASE_URL}/me/drive/root"
        resp = _make_authenticated_request(url)
        if resp.status_code == 200:
            return resp.json().get('id')
        return None
    
    folder = folder_path.strip("/")
    url = f"{GRAPH_BASE_URL}/me/drive/root:/{folder}"
    
    resp = _make_authenticated_request(url)
    
    if resp.status_code == 200:
        folder_id = resp.json().get('id')
        print(f"✓ Found folder ID: {folder_id}")
        return folder_id
    else:
        print(f"✗ Folder not found: {folder_path}")
<<<<<<< HEAD
        return None
=======
        return None
>>>>>>> 8d5ee6e1c299e7ec4faba52e139b3a328050d9b4
