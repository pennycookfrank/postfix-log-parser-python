#!/usr/bin/env python3
"""
Example usage of the postfix log parser library
"""

from postfix_log_parser import PostfixLogParser, PostfixLogProcessor
import json


def example_single_line():
    """Example of parsing a single log line"""
    print("=== Single Line Parsing Example ===")
    
    parser = PostfixLogParser()
    
    log_line = "Oct 10 04:02:08 mail.example.com postfix/smtp[22928]: DFBEFDBF00C5: to=<test@example-to.com>, relay=mail.example-to.com[192.168.0.10]:25, delay=5.3, delays=0.26/0/0.31/4.7, dsn=2.0.0, status=sent (250 2.0.0 Ok: queued as C598F1B0002D)"
    
    result = parser.parse_line(log_line)
    
    if result:
        print(f"Parsed successfully:")
        print(f"  Time: {result.time}")
        print(f"  Hostname: {result.hostname}")
        print(f"  Process: {result.process}")
        print(f"  Queue ID: {result.queue_id}")
        print(f"  To: {result.to_addr}")
        print(f"  Status: {result.status}")
    else:
        print("Failed to parse log line")
    
    print()


def example_multiple_lines():
    """Example of processing multiple related log lines"""
    print("=== Multiple Lines Processing Example ===")
    
    processor = PostfixLogProcessor()
    
    # Sample log lines that form a complete email transaction
    log_lines = [
        "Oct 10 15:59:29 mail postfix/smtpd[1827]: 3D74ADB7400B: client=example.com[127.0.0.1]",
        "Oct 10 15:59:29 mail postfix/cleanup[1695]: 3D74ADB7400B: message-id=<f93388828093534f92d85ffe21b2a719@example.info>",
        "Oct 10 15:59:29 mail postfix/qmgr[18719]: 3D74ADB7400B: from=<test2@example.info>, size=2140, nrcpt=1 (queue active)",
        "Oct 10 15:59:30 mail postfix/smtp[1827]: 3D74ADB7400B: to=<test@example.to>, relay=example.to[192.168.0.20]:25, delay=1.7, delays=0.02/0/1.7/0.06, dsn=2.0.0, status=sent (250 [Sniper] OK 1539154772 snipe-queue 10549)",
        "Oct 10 15:59:30 mail postfix/qmgr[18719]: 3D74ADB7400B: removed"
    ]
    
    completed_entries = list(processor.process_lines(log_lines))
    
    print(f"Processed {len(completed_entries)} completed email transactions:")
    
    for i, entry in enumerate(completed_entries, 1):
        print(f"\nTransaction {i}:")
        print(f"  Queue ID: {entry.queue_id}")
        print(f"  From: {entry.from_addr}")
        print(f"  Client: {entry.client_hostname} [{entry.client_ip}]")
        print(f"  Message ID: {entry.message_id}")
        print(f"  Messages: {len(entry.messages)} delivery attempts")
        
        for j, msg in enumerate(entry.messages, 1):
            print(f"    {j}. To: {msg.to}, Status: {msg.status}")


def example_json_output():
    """Example of JSON output format"""
    print("=== JSON Output Example ===")
    
    processor = PostfixLogProcessor()
    
    log_lines = [
        "Oct 10 15:59:29 mail postfix/smtpd[1827]: ABC123: client=example.com[127.0.0.1]",
        "Oct 10 15:59:29 mail postfix/cleanup[1695]: ABC123: message-id=<test@example.com>",
        "Oct 10 15:59:29 mail postfix/qmgr[18719]: ABC123: from=<sender@example.com>, size=1024, nrcpt=1 (queue active)",
        "Oct 10 15:59:30 mail postfix/smtp[1827]: ABC123: to=<recipient@example.org>, relay=example.org[192.168.1.10]:25, delay=0.5, delays=0.01/0/0.02/0.47, dsn=2.0.0, status=sent (250 OK)",
        "Oct 10 15:59:30 mail postfix/qmgr[18719]: ABC123: removed"
    ]
    
    completed_entries = list(processor.process_lines(log_lines))
    
    for entry in completed_entries:
        # Convert to dict for JSON serialization
        from dataclasses import asdict
        entry_dict = asdict(entry)
        # Convert from_addr to from for compatibility
        if 'from_addr' in entry_dict:
            entry_dict['from'] = entry_dict.pop('from_addr')
        
        json_output = json.dumps(entry_dict, default=str, indent=2, ensure_ascii=False)
        print(json_output)


if __name__ == "__main__":
    example_single_line()
    example_multiple_lines()
    example_json_output()
