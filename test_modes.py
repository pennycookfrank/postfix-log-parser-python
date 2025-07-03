#!/usr/bin/env python3
"""
Test both transaction mode and line mode functionality
"""

import subprocess
import json
import sys


def test_line_mode():
    """Test line mode functionality"""
    print("=== Testing Line Mode ===")
    
    # Test single line
    test_line = "Oct 10 04:02:08 mail.example.com postfix/smtp[22928]: DFBEFDBF00C5: to=<test@example-to.com>, relay=mail.example-to.com[192.168.0.10]:25, delay=5.3, delays=0.26/0/0.31/4.7, dsn=2.0.0, status=sent (250 2.0.0 Ok: queued as C598F1B0002D)"
    
    result = subprocess.run(
        ['python', 'postfix_log_parser.py', '--line-mode'],
        input=test_line,
        text=True,
        capture_output=True
    )
    
    if result.returncode == 0 and result.stdout.strip():
        try:
            parsed = json.loads(result.stdout.strip())
            print(f"✓ Single line parsed successfully")
            print(f"  Queue ID: {parsed.get('queue_id', 'N/A')}")
            print(f"  To: {parsed.get('to', 'N/A')}")
            print(f"  Status: {parsed.get('status', 'N/A')}")
        except json.JSONDecodeError:
            print("✗ Invalid JSON output")
            return False
    else:
        print("✗ Line mode failed")
        print(f"Error: {result.stderr}")
        return False
    
    print()
    return True


def test_transaction_mode():
    """Test transaction mode functionality"""
    print("=== Testing Transaction Mode ===")
    
    # Test with sample transaction
    test_lines = [
        "Oct 10 15:59:29 mail postfix/smtpd[1827]: 3D74ADB7400B: client=example.com[127.0.0.1]",
        "Oct 10 15:59:29 mail postfix/cleanup[1695]: 3D74ADB7400B: message-id=<test@example.info>",
        "Oct 10 15:59:29 mail postfix/qmgr[18719]: 3D74ADB7400B: from=<sender@example.info>, size=2140, nrcpt=1 (queue active)",
        "Oct 10 15:59:30 mail postfix/smtp[1827]: 3D74ADB7400B: to=<recipient@example.to>, relay=example.to[192.168.0.20]:25, delay=1.7, delays=0.02/0/1.7/0.06, dsn=2.0.0, status=sent (250 OK)",
        "Oct 10 15:59:30 mail postfix/qmgr[18719]: 3D74ADB7400B: removed"
    ]
    
    input_text = '\n'.join(test_lines)
    
    result = subprocess.run(
        ['python', 'postfix_log_parser.py'],
        input=input_text,
        text=True,
        capture_output=True
    )
    
    if result.returncode == 0 and result.stdout.strip():
        try:
            parsed = json.loads(result.stdout.strip())
            print(f"✓ Transaction parsed successfully")
            print(f"  Queue ID: {parsed.get('queue_id', 'N/A')}")
            print(f"  From: {parsed.get('from', 'N/A')}")
            print(f"  Client: {parsed.get('client_hostname', 'N/A')} [{parsed.get('client_ip', 'N/A')}]")
            print(f"  Messages: {len(parsed.get('messages', []))} delivery attempts")
            
            if parsed.get('messages'):
                for i, msg in enumerate(parsed['messages'], 1):
                    print(f"    {i}. To: {msg.get('to', 'N/A')}, Status: {msg.get('status', 'N/A')}")
        except json.JSONDecodeError:
            print("✗ Invalid JSON output")
            return False
    else:
        print("✗ Transaction mode failed")
        print(f"Error: {result.stderr}")
        return False
    
    print()
    return True


def test_help():
    """Test help functionality"""
    print("=== Testing Help ===")
    
    result = subprocess.run(
        ['python', 'postfix_log_parser.py', '--help'],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0 and 'usage:' in result.stdout:
        print("✓ Help message displayed correctly")
        return True
    else:
        print("✗ Help failed")
        return False


def main():
    """Run all tests"""
    print("Running comprehensive mode tests...\n")
    
    tests = [
        test_line_mode,
        test_transaction_mode,
        test_help
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
