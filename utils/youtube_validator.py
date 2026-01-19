"""
YouTube Channel ID Validator
Utility functions to validate YouTube channel IDs
"""

import re

def validate_youtube_channel_id(channel_id):
    """
    Validate YouTube Channel ID format
    
    YouTube Channel IDs follow the pattern: UC + 22 alphanumeric/dash/underscore characters
    Total length: 24 characters
    
    Examples:
        Valid: UCsqjHFMB_JYTaEnf_vmTNqg (Doug DeMuro)
        Valid: UCl2mFZoRqjw_ELax4Yisf6w (Louis Rossman)
        Invalid: @DougDeMuro (this is a handle, not an ID)
        Invalid: UC123 (too short)
    
    Args:
        channel_id (str): The channel ID to validate
    
    Returns:
        tuple: (is_valid: bool, error_message: str or None)
    """
    if not channel_id:
        return False, "YouTube Channel ID is required"
    
    # Remove whitespace
    channel_id = channel_id.strip()
    
    # Check if it starts with @ (common mistake - user provided handle instead of ID)
    if channel_id.startswith('@'):
        return False, (
            "This appears to be a channel handle (@username), not a Channel ID. "
            "Channel IDs start with 'UC' followed by 22 characters. "
            "Example: UCsqjHFMB_JYTaEnf_vmTNqg"
        )
    
    # YouTube Channel ID pattern: UC + 22 characters (letters, numbers, dash, underscore)
    pattern = r'^UC[\w-]{22}$'
    
    if not re.match(pattern, channel_id):
        # Provide specific feedback
        if not channel_id.startswith('UC'):
            return False, (
                "Invalid Channel ID format. Channel IDs must start with 'UC'. "
                "Example: UCsqjHFMB_JYTaEnf_vmTNqg"
            )
        elif len(channel_id) != 24:
            return False, (
                f"Invalid Channel ID length. Expected 24 characters, got {len(channel_id)}. "
                "Format: UC + 22 characters"
            )
        else:
            return False, (
                "Invalid Channel ID format. Only letters, numbers, dash (-), and underscore (_) are allowed. "
                "Example: UCsqjHFMB_JYTaEnf_vmTNqg"
            )
    
    return True, None


def extract_channel_id_from_url(url):
    """
    Extract Channel ID from various YouTube URL formats
    
    Supported formats:
        - https://www.youtube.com/channel/UCsqjHFMB_JYTaEnf_vmTNqg
        - https://youtube.com/channel/UCsqjHFMB_JYTaEnf_vmTNqg
        - UCsqjHFMB_JYTaEnf_vmTNqg (just the ID)
    
    Args:
        url (str): YouTube URL or channel ID
    
    Returns:
        str or None: Extracted channel ID, or None if not found
    """
    if not url:
        return None
    
    url = url.strip()
    
    # If it's already a valid channel ID, return it
    is_valid, _ = validate_youtube_channel_id(url)
    if is_valid:
        return url
    
    # Try to extract from URL
    # Pattern: /channel/CHANNEL_ID
    match = re.search(r'/channel/(UC[\w-]{22})', url)
    if match:
        return match.group(1)
    
    return None


def get_channel_id_help_text():
    """
    Get user-friendly help text for finding YouTube Channel ID
    
    Returns:
        str: Help text with instructions
    """
    return """
How to find YouTube Channel ID:

Method 1: View Page Source
1. Go to the YouTube channel page
2. Right-click and select "View Page Source" (or press Ctrl+U / Cmd+Option+U)
3. Search for "channelId" (Ctrl+F / Cmd+F)
4. Copy the ID (starts with UC, 24 characters total)

Method 2: Use Online Tool
Visit: https://commentpicker.com/youtube-channel-id.php
Paste the channel URL and it will extract the ID.

Method 3: Check Channel URL
Some channels show the ID in the URL:
youtube.com/channel/UCsqjHFMB_JYTaEnf_vmTNqg
                     ^--- This is the Channel ID

Valid Format:
- Starts with 'UC'
- Followed by 22 characters (letters, numbers, dash, underscore)
- Total: 24 characters
- Example: UCsqjHFMB_JYTaEnf_vmTNqg
""".strip()


# Example usage and tests
if __name__ == '__main__':
    print("YouTube Channel ID Validator - Test Cases\n")
    print("=" * 60)
    
    test_cases = [
        ("UCsqjHFMB_JYTaEnf_vmTNqg", True, "Doug DeMuro - Valid ID"),
        ("UCl2mFZoRqjw_ELax4Yisf6w", True, "Louis Rossman - Valid ID"),
        ("@DougDeMuro", False, "Handle (starts with @)"),
        ("UC123", False, "Too short"),
        ("XCsqjHFMB_JYTaEnf_vmTNqg", False, "Doesn't start with UC"),
        ("UCsqjHFMB_JYTaEnf_vmTNqg123", False, "Too long"),
        ("", False, "Empty string"),
        ("  UCsqjHFMB_JYTaEnf_vmTNqg  ", True, "Valid with whitespace"),
    ]
    
    for channel_id, expected_valid, description in test_cases:
        is_valid, error_msg = validate_youtube_channel_id(channel_id)
        status = "✅ PASS" if is_valid == expected_valid else "❌ FAIL"
        
        print(f"\n{status} - {description}")
        print(f"  Input: '{channel_id}'")
        print(f"  Valid: {is_valid} (expected {expected_valid})")
        if error_msg:
            print(f"  Error: {error_msg}")
    
    print("\n" + "=" * 60)
    print("\nURL Extraction Tests:\n")
    
    url_tests = [
        ("https://www.youtube.com/channel/UCsqjHFMB_JYTaEnf_vmTNqg", "UCsqjHFMB_JYTaEnf_vmTNqg"),
        ("UCsqjHFMB_JYTaEnf_vmTNqg", "UCsqjHFMB_JYTaEnf_vmTNqg"),
        ("https://youtube.com/@DougDeMuro", None),
    ]
    
    for url, expected in url_tests:
        result = extract_channel_id_from_url(url)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        print(f"{status} - Input: {url}")
        print(f"  Result: {result} (expected {expected})\n")
