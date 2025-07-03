#!/usr/bin/env python3
"""
Test incomplete log scenarios where client information is missing
"""

import subprocess
import json
import tempfile
import os

def test_incomplete_log_scenarios():
    """Test various incomplete log scenarios"""
    
    print("=== Testing Incomplete Log Scenarios ===")
    
    # Scenario 1: Deferred mail already in queue (no client info)
    deferred_only_log = [
        "Jul  3 00:00:05 mail postfix/qmgr[1234]: ABC123: from=<sender@example.com>, size=1024, nrcpt=1 (queue active)",
        "Jul  3 00:00:10 mail postfix/smtp[5678]: ABC123: to=<recipient@example.org>, relay=example.org[192.168.1.10]:25, delay=300.5, delays=300/0/0.02/0.47, dsn=2.0.0, status=sent (250 OK)",
        "Jul  3 00:00:10 mail postfix/qmgr[1234]: ABC123: removed"
    ]
    
    # Scenario 2: Log starts from cleanup (message already received)
    cleanup_start_log = [
        "Jul  3 00:00:02 mail postfix/cleanup[4567]: DEF456: message-id=<test@example.com>",
        "Jul  3 00:00:02 mail postfix/qmgr[1234]: DEF456: from=<sender@example.com>, size=2048, nrcpt=2 (queue active)",
        "Jul  3 00:00:05 mail postfix/smtp[5678]: DEF456: to=<user1@example.org>, relay=example.org[192.168.1.10]:25, delay=3.2, delays=0.1/0/0.1/3.0, dsn=2.0.0, status=sent (250 OK)",
        "Jul  3 00:00:05 mail postfix/smtp[5678]: DEF456: to=<user2@example.org>, relay=example.org[192.168.1.10]:25, delay=3.3, delays=0.1/0/0.1/3.1, dsn=2.0.0, status=sent (250 OK)",
        "Jul  3 00:00:05 mail postfix/qmgr[1234]: DEF456: removed"
    ]
    
    # Scenario 3: Bounce/error processing (no original client)
    bounce_log = [
        "Jul  3 00:00:15 mail postfix/bounce[9999]: GHI789: sender non-delivery notification: JKL012",
        "Jul  3 00:00:15 mail postfix/qmgr[1234]: JKL012: from=<>, size=3456, nrcpt=1 (queue active)",
        "Jul  3 00:00:16 mail postfix/smtp[5678]: JKL012: to=<sender@example.com>, relay=example.com[192.168.1.20]:25, delay=1.1, delays=0.05/0/0.05/1.0, dsn=2.0.0, status=sent (250 OK)",
        "Jul  3 00:00:16 mail postfix/qmgr[1234]: JKL012: removed"
    ]
    
    scenarios = [
        ("Deferred mail (no client info)", deferred_only_log),
        ("Log starts from cleanup", cleanup_start_log),
        ("Bounce processing", bounce_log)
    ]
    
    for scenario_name, log_lines in scenarios:
        print(f"\n--- {scenario_name} ---")
        
        # Test default behavior (should have null time)
        print("Default behavior (no fallback):")
        input_text = '\n'.join(log_lines)
        result = subprocess.run(
            ['python', 'postfix_log_parser.py'],
            input=input_text,
            text=True,
            capture_output=True
        )
        
        if result.returncode == 0 and result.stdout.strip():
            try:
                parsed = json.loads(result.stdout.strip())
                
                print(f"  Queue ID: {parsed.get('queue_id', 'N/A')}")
                print(f"  Time: {parsed.get('time', 'N/A')}")
                print(f"  From: {parsed.get('from', 'N/A')}")
                print(f"  Messages: {len(parsed.get('messages', []))}")
                
                # Check default behavior
                if parsed.get('time') is None:
                    print(f"  ✓ Default behavior: TIME IS NULL (as expected)")
                else:
                    print(f"  ✗ Unexpected: Time should be null but got: {parsed.get('time')}")
                    
            except json.JSONDecodeError:
                print("  ✗ Failed to parse JSON")
        else:
            print("  ✗ No output or error")
        
        # Test with fallback enabled
        print("With --use-fallback-time:")
        result = subprocess.run(
            ['python', 'postfix_log_parser.py', '--use-fallback-time'],
            input=input_text,
            text=True,
            capture_output=True
        )
        
        if result.returncode == 0 and result.stdout.strip():
            try:
                parsed = json.loads(result.stdout.strip())
                
                print(f"  Queue ID: {parsed.get('queue_id', 'N/A')}")
                print(f"  Time: {parsed.get('time', 'N/A')}")
                print(f"  From: {parsed.get('from', 'N/A')}")
                print(f"  Messages: {len(parsed.get('messages', []))}")
                
                # Check fallback behavior
                if parsed.get('time') is not None:
                    print(f"  ✓ Fallback behavior: Time available: {parsed.get('time')}")
                else:
                    print(f"  ✗ Fallback failed: Time is still null")
                    
            except json.JSONDecodeError:
                print("  ✗ Failed to parse JSON")

def test_line_mode_incomplete():
    """Test line mode with incomplete logs"""
    
    print(f"\n=== Line Mode with Incomplete Logs ===")
    
    incomplete_lines = [
        "Jul  3 00:00:05 mail postfix/qmgr[1234]: ABC123: from=<sender@example.com>, size=1024, nrcpt=1 (queue active)",
        "Jul  3 00:00:10 mail postfix/smtp[5678]: ABC123: to=<recipient@example.org>, relay=example.org[192.168.1.10]:25, delay=300.5, delays=300/0/0.02/0.47, dsn=2.0.0, status=sent (250 OK)"
    ]
    
    for line in incomplete_lines:
        print(f"\nTesting line: {line[:60]}...")
        
        result = subprocess.run(
            ['python', 'postfix_log_parser.py', '--line-mode'],
            input=line,
            text=True,
            capture_output=True
        )
        
        if result.returncode == 0 and result.stdout.strip():
            try:
                parsed = json.loads(result.stdout.strip())
                print(f"  Time: {parsed.get('time', 'N/A')}")
                print(f"  Queue ID: {parsed.get('queue_id', 'N/A')}")
                print(f"  From: {parsed.get('from', 'N/A')}")
                print(f"  To: {parsed.get('to', 'N/A')}")
            except json.JSONDecodeError:
                print("  ✗ Failed to parse JSON")

if __name__ == "__main__":
    test_incomplete_log_scenarios()
    test_line_mode_incomplete()
