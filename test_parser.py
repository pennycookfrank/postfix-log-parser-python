#!/usr/bin/env python3
"""
Test script for postfix log parser
"""

import json
from postfix_log_parser import PostfixLogParser, PostfixLogProcessor


def test_single_line_parsing():
    """Test parsing a single log line"""
    parser = PostfixLogParser()
    
    # Test line from the original Go project
    test_line = "Oct 10 04:02:08 mail.example.com postfix/smtp[22928]: DFBEFDBF00C5: to=<test@example-to.com>, relay=mail.example-to.com[192.168.0.10]:25, delay=5.3, delays=0.26/0/0.31/4.7, dsn=2.0.0, status=sent (250 2.0.0 Ok: queued as C598F1B0002D)"
    
    result = parser.parse_line(test_line)
    
    print("Single line parsing test:")
    print(f"Time: {result.time}")
    print(f"Hostname: {result.hostname}")
    print(f"Process: {result.process}")
    print(f"Queue ID: {result.queue_id}")
    print(f"To: {result.to_addr}")
    print(f"Status: {result.status}")
    print(f"Messages: {result.messages}")
    print()


def test_log_processing():
    """Test processing multiple related log lines"""
    processor = PostfixLogProcessor()
    
    # Sample log lines that form a complete email transaction
    test_lines = [
        "Oct 10 15:59:29 mail postfix/smtpd[1827]: 3D74ADB7400B: client=example.com[127.0.0.1]",
        "Oct 10 15:59:29 mail postfix/cleanup[1695]: 3D74ADB7400B: message-id=<f93388828093534f92d85ffe21b2a719@example.info>",
        "Oct 10 15:59:29 mail postfix/qmgr[18719]: 3D74ADB7400B: from=<test2@example.info>, size=2140, nrcpt=1 (queue active)",
        "Oct 10 15:59:30 mail postfix/smtp[1827]: 3D74ADB7400B: to=<test@example.to>, relay=example.to[192.168.0.20]:25, delay=1.7, delays=0.02/0/1.7/0.06, dsn=2.0.0, status=sent (250 [Sniper] OK 1539154772 snipe-queue 10549)",
        "Oct 10 15:59:30 mail postfix/smtp[1827]: 3D74ADB7400B: to=<test2@example.to>, relay=example.to[192.168.0.20]:25, delay=1.7, delays=0.02/0/1.7/0.06, dsn=2.0.0, status=sent (250 [Sniper] OK 1539154772 snipe-queue 10549)",
        "Oct 10 15:59:30 mail postfix/qmgr[18719]: 3D74ADB7400B: removed"
    ]
    
    print("Log processing test:")
    
    completed_entries = list(processor.process_lines(test_lines))
    
    for entry in completed_entries:
        # Convert to dict for JSON serialization
        from dataclasses import asdict
        entry_dict = asdict(entry)
        # Convert from_addr to from for compatibility
        if 'from_addr' in entry_dict:
            entry_dict['from'] = entry_dict.pop('from_addr')
        
        json_output = json.dumps(entry_dict, default=str, indent=2, ensure_ascii=False)
        print(json_output)


def test_iso8601_parsing():
    """Test ISO8601 timestamp parsing"""
    parser = PostfixLogParser()
    
    # Test ISO8601 format
    test_line = "2023-10-10T15:59:29.123456+09:00 mail postfix/smtpd[1827]: 3D74ADB7400B: client=example.com[127.0.0.1]"
    
    result = parser.parse_line(test_line)
    
    print("ISO8601 parsing test:")
    print(f"Time: {result.time}")
    print(f"Hostname: {result.hostname}")
    print(f"Queue ID: {result.queue_id}")
    print()


if __name__ == "__main__":
    test_single_line_parsing()
    test_log_processing()
    test_iso8601_parsing()
