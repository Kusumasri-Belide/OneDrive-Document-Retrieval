# OneDrive Authentication Setup

## What Changed

Your authentication workflow has been updated to use:
1. **Device Code Flow** - Perfect for VMs and headless environments (no browser popup)
2. **Persistent Token Caching** - Authenticate once, token saved for future use

## Key Changes

1. **Device Code Authentication**: Shows a code in terminal instead of opening browser
2. **Persistent Token Cache**: Tokens saved to `token.json` file
3. **Automatic Token Refresh**: MSAL automatically refreshes expired tokens
4. **Silent Authentication**: Subsequent runs use cached tokens without prompting

## How It Works

### First Run (Authentication Required)
```bash
python backend/ingest_onedrive.py
```

You'll see output like:
```
No valid cached token found. Authenticating with Microsoft Graph...
============================================================
To sign in, use a web browser to open the page https://microsoft.com/devicelogin
and enter the code ABC123XYZ to authenticate.
============================================================
```

**Steps:**
1. Copy the URL and code shown in terminal
2. Open the URL in any browser (can be on different machine)
3. Enter the code
4. Sign in with your Microsoft account
5. Token is saved to `token.json`

### Subsequent Runs (No Authentication)
```bash
python backend/ingest_onedrive.py
```
- Loads token from `token.json`
- No authentication prompt
- Directly downloads files

## Why Device Code Flow?

Perfect for:
- Virtual Machines (VMs)
- Remote servers via SSH
- Headless environments
- Docker containers
- Any scenario where you can't open a browser directly

## Testing Authentication

Test the authentication separately:
```bash
# Test authentication (will use cache if available)
python scripts/test_auth.py

# Clear cache and force re-authentication
python scripts/test_auth.py --clear-cache
```

## Token Cache Location

- **File**: `token.json` (in project root)
- **Format**: MSAL serialized token cache
- **Security**: Added to `.gitignore` (not committed to git)

## Troubleshooting

### If authentication keeps prompting:

1. Check if `token.json` exists after first authentication
2. Verify file permissions (should be readable/writable)
3. Clear cache and re-authenticate:
   ```bash
   python scripts/test_auth.py --clear-cache
   python scripts/test_auth.py
   ```

### If token expires:

MSAL automatically handles token refresh. If refresh fails, you'll be prompted to re-authenticate (this is normal for security).

### Manual cache clearing:

```bash
# Delete the token file
del token.json  # Windows
rm token.json   # Linux/Mac

# Or use the script
python scripts/test_auth.py --clear-cache
```

## Security Notes

- `token.json` contains sensitive authentication data
- File is excluded from git via `.gitignore`
- Keep this file secure and don't share it
- Tokens expire automatically for security

## Files Modified

1. `backend/auth.py` - Added persistent token caching
2. `.gitignore` - Added token.json exclusion
3. `scripts/test_auth.py` - New test script (created)
4. `AUTH_SETUP.md` - This documentation (created)
