#!/usr/bin/env python3
"""
Test encoding handling
"""

import subprocess
import tempfile
import os

def create_test_file_with_bad_encoding():
    """Create a test file with mixed encoding"""
    
    # Create a temporary file with mixed content
    with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
        # Write some valid UTF-8 content
        f.write(b'Jul  3 00:00:02 emporium2 postfix/cleanup[4120776]: D15612055068: message-id=<test@example.com>\n')
        
        # Write some problematic bytes (like 0xb4 which caused the original error)
        f.write(b'Jul  3 00:00:03 emporium2 postfix/qmgr[1282252]: ABC123: from=<user\xb4@example.com>, size=1237\n')
        
        # Write more valid content
        f.write(b'Jul  3 00:00:04 emporium2 postfix/qmgr[1282252]: ABC123: removed\n')
        
        temp_filename = f.name
    
    return temp_filename

def test_encoding_handling():
    """Test the encoding handling"""
    
    print("=== Testing Encoding Handling ===")
    
    temp_file = create_test_file_with_bad_encoding()
    
    try:
        # Test with default settings (should handle gracefully)
        print("\n1. Testing with default encoding handling:")
        result = subprocess.run(
            ['python', 'postfix_log_parser.py', '--line-mode'],
            stdin=open(temp_file, 'rb'),
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✓ Default encoding handling worked")
            lines = result.stdout.strip().split('\n')
            print(f"  Parsed {len(lines)} lines")
        else:
            print("✗ Default encoding handling failed")
            print(f"  Error: {result.stderr}")
        
        # Test with ignore errors
        print("\n2. Testing with --encoding-errors=ignore:")
        result = subprocess.run(
            ['python', 'postfix_log_parser.py', '--line-mode', '--encoding-errors=ignore'],
            stdin=open(temp_file, 'rb'),
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✓ Ignore errors worked")
            lines = result.stdout.strip().split('\n')
            print(f"  Parsed {len(lines)} lines")
        else:
            print("✗ Ignore errors failed")
            print(f"  Error: {result.stderr}")
        
        # Test with latin-1 encoding
        print("\n3. Testing with --encoding=latin-1:")
        result = subprocess.run(
            ['python', 'postfix_log_parser.py', '--line-mode', '--encoding=latin-1'],
            stdin=open(temp_file, 'rb'),
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✓ Latin-1 encoding worked")
            lines = result.stdout.strip().split('\n')
            print(f"  Parsed {len(lines)} lines")
        else:
            print("✗ Latin-1 encoding failed")
            print(f"  Error: {result.stderr}")
        
        # Test with auto encoding
        print("\n4. Testing with --encoding=auto:")
        result = subprocess.run(
            ['python', 'postfix_log_parser.py', '--line-mode', '--encoding=auto'],
            stdin=open(temp_file, 'rb'),
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✓ Auto encoding worked")
            lines = result.stdout.strip().split('\n')
            print(f"  Parsed {len(lines)} lines")
        else:
            print("✗ Auto encoding failed")
            print(f"  Error: {result.stderr}")
    
    finally:
        # Clean up
        os.unlink(temp_file)

if __name__ == "__main__":
    test_encoding_handling()
