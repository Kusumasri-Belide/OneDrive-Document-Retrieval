import msal
import os
import json
import atexit
from .config import (
    MICROSOFT_CLIENT_ID,
    MICROSOFT_CLIENT_SECRET,
    MICROSOFT_TENANT_ID,
    GRAPH_SCOPE
)

# Token cache file path
TOKEN_CACHE_FILE = "token.json"

# Global token cache
_cached_token = None
_msal_app = None
_token_cache = None

def _load_token_cache():
    """Load token cache from disk."""
    cache = msal.SerializableTokenCache()
    if os.path.exists(TOKEN_CACHE_FILE):
        try:
            with open(TOKEN_CACHE_FILE, 'r') as f:
                cache.deserialize(f.read())
            print(f"Loaded token cache from {TOKEN_CACHE_FILE}")
        except Exception as e:
            print(f"Warning: Could not load token cache: {e}")
    return cache

def _save_token_cache():
    """Save token cache to disk."""
    global _token_cache
    if _token_cache and _token_cache.has_state_changed:
        try:
            with open(TOKEN_CACHE_FILE, 'w') as f:
                f.write(_token_cache.serialize())
            print(f"Token cache saved to {TOKEN_CACHE_FILE}")
        except Exception as e:
            print(f"Warning: Could not save token cache: {e}")

def _get_msal_app():
    """Get or create MSAL application instance with persistent token cache."""
    global _msal_app, _token_cache
    if _msal_app is None:
        _token_cache = _load_token_cache()
        _msal_app = msal.PublicClientApplication(
            client_id=MICROSOFT_CLIENT_ID,
            authority="https://login.microsoftonline.com/common",
            token_cache=_token_cache
        )
        # Register cleanup function to save cache on exit
        atexit.register(_save_token_cache)
    return _msal_app

def get_access_token() -> str:
    """Get access token with persistent caching to avoid repeated authentication."""
    global _cached_token
    
    app = _get_msal_app()
    
    # First, try to get token from cache (silent acquisition)
    accounts = app.get_accounts()
    if accounts:
        print(f"Found {len(accounts)} cached account(s), attempting silent token acquisition...")
        result = app.acquire_token_silent(GRAPH_SCOPE, account=accounts[0])
        if result and "access_token" in result:
            _cached_token = result["access_token"]
            print("✓ Using cached token (no authentication required)")
            _save_token_cache()  # Save any cache updates
            return _cached_token
        else:
            print(f"Silent token acquisition failed: {result.get('error_description', 'Unknown error')}")
    
    # Use device code flow for VM/headless environments
    print("No valid cached token found. Authenticating with Microsoft Graph...")
    print("(This should only happen once - token will be cached for future use)")
    print("\n" + "="*60)
    
<<<<<<< HEAD
    flow = app.initiate_device_flow(scopes=GRAPH_SCOPE)
    
    if "user_code" not in flow:
        raise RuntimeError(f"Failed to create device flow: {flow.get('error_description', flow)}")
    
    # Display instructions to user
    print(flow["message"])
    print("="*60 + "\n")
    
    # Wait for user to authenticate
    result = app.acquire_token_by_device_flow(flow)
=======
    # Only do interactive login if no cached token is available
    print("Authenticating with Microsoft Graph (this should only happen once)...")
    result = app.acquire_token_interactive(scopes=GRAPH_SCOPE)
>>>>>>> 8d5ee6e1c299e7ec4faba52e139b3a328050d9b4

    if "access_token" not in result:
        raise RuntimeError(f"Failed to acquire token: {result.get('error_description', result)}")

    _cached_token = result["access_token"]
<<<<<<< HEAD
    print("\n✓ Authentication successful - token cached for subsequent requests")
    _save_token_cache()  # Save the new token to disk
=======
    print("Authentication successful - token cached for subsequent requests")
>>>>>>> 8d5ee6e1c299e7ec4faba52e139b3a328050d9b4
    return _cached_token

def clear_token_cache():
    """Clear the cached token (useful for testing or when token expires)."""
    global _cached_token, _token_cache
    _cached_token = None
    
    # Clear the persistent cache file
    if os.path.exists(TOKEN_CACHE_FILE):
        try:
            os.remove(TOKEN_CACHE_FILE)
            print(f"Cleared token cache file: {TOKEN_CACHE_FILE}")
        except Exception as e:
            print(f"Warning: Could not remove token cache file: {e}")
    
    # Reset the in-memory cache
    if _token_cache:
        _token_cache = msal.SerializableTokenCache()