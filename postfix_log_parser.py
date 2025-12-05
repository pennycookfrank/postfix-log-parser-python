#!/usr/bin/env python3
"""
Postfix Log Parser - Python implementation

Parse postfix log entries and extract structured information.
This is a Python equivalent of the Go-based postfix-log-parser.
"""

import re
import json
import sys
import argparse
import io
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict


@dataclass
class LogFormat:
    """Represents a parsed postfix log entry"""
    time: Optional[datetime] = None
    hostname: str = ""
    process: str = ""
    queue_id: str = ""
    messages: str = ""
    client_hostname: str = ""
    client_ip: str = ""
    message_id: str = ""
    from_addr: str = ""
    to_addr: str = ""
    status: str = ""


@dataclass
class Message:
    """Represents a delivery message"""
    time: Optional[datetime] = None
    to: str = ""
    status: str = ""
    message: str = ""


@dataclass
class PostfixLogEntry:
    """Represents a consolidated postfix log entry"""
    time: Optional[datetime] = None
    hostname: str = ""
    process: str = ""
    queue_id: str = ""
    client_hostname: str = ""
    client_ip: str = ""
    message_id: str = ""
    from_addr: str = ""
    messages: List[Message] = None

    def __post_init__(self):
        if self.messages is None:
            self.messages = []


class PostfixLogParser:
    """Parser for postfix log entries"""
    
    # Time formats
    TIME_FORMAT_SYSLOG_PLUS_YEAR = "%Y %b %d %H:%M:%S"
    TIME_FORMAT_ISO8601 = "%Y-%m-%dT%H:%M:%S.%f%z"
    TIME_FORMAT_ISO8601_ALT = "%Y-%m-%dT%H:%M:%S%z"
    
    # Regex patterns
    TIME_REGEXP = r'([A-Za-z]{3}\s+[0-9]{1,2} [0-9]{2}:[0-9]{2}:[0-9]{2}|^\d{4}-[01]\d-[0-3]\dT[0-2]\d:[0-5]\d:[0-5]\d(?:\.\d+)?(?:[+-][0-2]\d:[0-5]\d|Z))'
    HOST_REGEXP = r'([0-9A-Za-z\.-]*)'
    PROCESS_REGEXP = r'(postfix(?:/[a-z]+)+\[[0-9]+\])?'
    QUEUE_ID_REGEXP = r'([0-9A-Z]*)'
    MESSAGE_DETAILS_REGEXP = r'((?:client=(.+)\[(.+)\])?(?:message-id=<([^>]*)>)?(?:from=<([^>]+@[^>]+)>)?(?:to=<([^>]+@[^>]+)>.*status=([a-z]+))?.*)'
    
    def __init__(self):
        # Compile the main regex pattern
        pattern = (
            f'{self.TIME_REGEXP} {self.HOST_REGEXP} {self.PROCESS_REGEXP}: '
            f'{self.QUEUE_ID_REGEXP}(?:: )?{self.MESSAGE_DETAILS_REGEXP}'
        )
        self.regex = re.compile(pattern)
    
    def _parse_time(self, time_str: str) -> Optional[datetime]:
        """Parse timestamp from log entry"""
        if not time_str:
            return None
            
        # Try ISO8601 format first
        for fmt in [self.TIME_FORMAT_ISO8601, self.TIME_FORMAT_ISO8601_ALT]:
            try:
                return datetime.strptime(time_str, fmt)
            except ValueError:
                continue
        
        # Try syslog format (first prepending year)
        try:
            current_year = datetime.now().year
            time_str = str(current_year) + ' ' + time_str
            return datetime.strptime(time_str, self.TIME_FORMAT_SYSLOG_PLUS_YEAR)
        except ValueError:
            return None
    
    def parse_line(self, line: str) -> Optional[LogFormat]:
        """Parse a single log line"""
        if isinstance(line, bytes):
            line = line.decode('utf-8', errors='ignore')
        
        line = line.strip()
        if not line:
            return None
            
        match = self.regex.match(line)
        if not match:
            return None
        
        groups = match.groups()
        
        # Parse timestamp
        time_obj = self._parse_time(groups[0]) if groups[0] else None
        
        log_format = LogFormat(
            time=time_obj,
            hostname=groups[1] or "",
            process=groups[2] or "",
            queue_id=groups[3] or "",
            messages=groups[4] or "",
            client_hostname=groups[5] or "",
            client_ip=groups[6] or "",
            message_id=groups[7] if groups[7] else "",  # Handle empty message-id
            from_addr=groups[8] or "",
            to_addr=groups[9] or "",
            status=groups[10] or ""
        )
        
        return log_format


class PostfixLogProcessor:
    """Process multiple log entries and group by queue ID"""
    
    def __init__(self, use_fallback_time=False):
        self.parser = PostfixLogParser()
        self.queue_map: Dict[str, PostfixLogEntry] = {}
        self.use_fallback_time = use_fallback_time
    
    def process_line(self, line: str) -> Optional[PostfixLogEntry]:
        """Process a single log line and return completed entry if available"""
        log_format = self.parser.parse_line(line)
        if not log_format or not log_format.queue_id:
            return None
        
        queue_id = log_format.queue_id
        
        # Initialize entry if new queue ID
        if queue_id not in self.queue_map:
            self.queue_map[queue_id] = PostfixLogEntry(queue_id=queue_id)
        
        entry = self.queue_map[queue_id]
        
        # Update entry with client information (preferred time source)
        if log_format.client_hostname:
            entry.time = log_format.time
            entry.hostname = log_format.hostname
            entry.process = log_format.process
            entry.client_hostname = log_format.client_hostname
            entry.client_ip = log_format.client_ip
        
        # Update with message ID
        if log_format.message_id:
            entry.message_id = log_format.message_id
            # If fallback time is enabled and no time set yet, use message-id time
            if self.use_fallback_time and entry.time is None:
                entry.time = log_format.time
                entry.hostname = log_format.hostname
                entry.process = log_format.process
        
        # Update with sender information
        if log_format.from_addr:
            entry.from_addr = log_format.from_addr
            # If fallback time is enabled and no time set yet, use from time
            if self.use_fallback_time and entry.time is None:
                entry.time = log_format.time
                entry.hostname = log_format.hostname
                entry.process = log_format.process
        
        # Add delivery message
        if log_format.to_addr:
            message = Message(
                time=log_format.time,
                to=log_format.to_addr,
                status=log_format.status,
                message=log_format.messages
            )
            entry.messages.append(message)
            # If fallback time is enabled and no time set yet, use delivery time
            if self.use_fallback_time and entry.time is None:
                entry.time = log_format.time
                entry.hostname = log_format.hostname
                entry.process = log_format.process
        
        # Check if this is the "removed" message (end of processing)
        if log_format.messages == "removed":
            # Return completed entry and remove from map
            completed_entry = self.queue_map.pop(queue_id)
            return completed_entry
        
        return None
    
    def process_lines(self, lines):
        """Process multiple lines and yield completed entries"""
        for line in lines:
            completed_entry = self.process_line(line)
            if completed_entry:
                yield completed_entry
    
    def get_remaining_entries(self):
        """Get any remaining entries that weren't completed"""
        return list(self.queue_map.values())


def get_robust_stdin_reader(encoding_errors='replace'):
    """
    Create a robust stdin reader that can handle various encodings
    """
    # Try common encodings in order of preference
    encodings_to_try = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
    
    # Read a small sample to detect encoding
    try:
        # Try to peek at the first few bytes
        sample = sys.stdin.buffer.peek(8192)[:1024]  # Read up to 1KB sample
    except (OSError, io.UnsupportedOperation):
        # If peek is not supported, fall back to utf-8 with error handling
        return io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8', errors=encoding_errors)
    
    # Try to decode the sample with different encodings
    for encoding in encodings_to_try:
        try:
            sample.decode(encoding)
            # If successful, use this encoding
            return io.TextIOWrapper(sys.stdin.buffer, encoding=encoding, errors=encoding_errors)
        except UnicodeDecodeError:
            continue
    
    # If all encodings fail, fall back to utf-8 with error handling
    return io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8', errors=encoding_errors)


def datetime_serializer(obj):
    """JSON serializer for datetime objects"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

def print_json_output(output_dict, indent=None):
    json_output = json.dumps(
        output_dict,
        default=datetime_serializer,
        ensure_ascii=False,
        indent=indent,
    )
    print(json_output)
    sys.stdout.flush()
    return None

def main():
    """Main CLI function"""
    import argparse
    import io
    
    parser = argparse.ArgumentParser(
        description='Parse postfix log entries and output JSON format',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Transaction mode (default) - groups related entries
  cat /var/log/maillog | python postfix_log_parser.py
  
  # Line mode - output each parsed line immediately
  cat /var/log/maillog | python postfix_log_parser.py --line-mode
  
  # Use fallback timestamps for incomplete logs
  cat /var/log/maillog | python postfix_log_parser.py --use-fallback-time
  
  # Handle encoding issues in production logs
  cat /var/log/maillog | python postfix_log_parser.py --encoding-errors=replace
  
  # Parse single line
  echo "Oct 10 04:02:08 mail postfix/smtp[123]: ABC: to=<test@example.com>, status=sent" | python postfix_log_parser.py --line-mode
        """
    )
    
    parser.add_argument(
        '--line-mode', '-l',
        action='store_true',
        help='Output each parsed line immediately instead of grouping by transaction'
    )
    
    parser.add_argument(
        '--flush-remaining', '-f',
        action='store_true',
        help='Output remaining incomplete transactions at end (transaction mode only)'
    )
    
    parser.add_argument(
        '--encoding', '-e',
        default='utf-8',
        help='Input encoding (default: utf-8). Use "auto" for automatic detection.'
    )
    
    parser.add_argument(
        '--encoding-errors',
        choices=['strict', 'ignore', 'replace'],
        default='replace',
        help='How to handle encoding errors (default: replace)'
    )
    
    parser.add_argument(
        '--use-fallback-time',
        action='store_true',
        help='Use fallback timestamps when client connection info is missing (message-id, from, or delivery time)'
    )

    parser.add_argument(
        '--indent', '-i',
        action='store_true',
        help='Produce indented output for easier reading.'
    )
    
    args = parser.parse_args()
    indent = 4 if args.indent else None
    
    # Set up stdin with proper encoding handling
    if args.encoding == 'auto':
        # Try to detect encoding or fall back to common encodings
        stdin_reader = get_robust_stdin_reader(args.encoding_errors)
    else:
        stdin_reader = io.TextIOWrapper(
            sys.stdin.buffer, 
            encoding=args.encoding, 
            errors=args.encoding_errors
        )
    
    if args.line_mode:
        # Line mode: output each parsed line immediately
        log_parser = PostfixLogParser()
        
        try:
            for line in stdin_reader:
                line = line.strip()
                if not line:
                    continue
                    
                log_format = log_parser.parse_line(line)
                if log_format:
                    # Convert to dict and handle datetime serialization
                    log_dict = asdict(log_format)
                    # Convert from_addr back to from for compatibility
                    if 'from_addr' in log_dict:
                        log_dict['from'] = log_dict.pop('from_addr')
                    # Rename to_addr to to for compatibility
                    if 'to_addr' in log_dict:
                        log_dict['to'] = log_dict.pop('to_addr')
                    
                    print_json_output(log_dict, indent)
        
        except KeyboardInterrupt:
            pass
        except BrokenPipeError:
            # Handle broken pipe gracefully
            pass
        except UnicodeDecodeError as e:
            print(f"Encoding error: {e}", file=sys.stderr)
            print("Try using --encoding-errors=ignore or --encoding=latin-1", file=sys.stderr)
            sys.exit(1)
    
    else:
        # Transaction mode: group entries and output complete transactions
        processor = PostfixLogProcessor(use_fallback_time=args.use_fallback_time)
        
        try:
            # Process stdin line by line
            for line in stdin_reader:
                completed_entry = processor.process_line(line.strip())
                if completed_entry:
                    # Convert to dict and handle datetime serialization
                    entry_dict = asdict(completed_entry)
                    # Convert from_addr back to from for compatibility
                    if 'from_addr' in entry_dict:
                        entry_dict['from'] = entry_dict.pop('from_addr')
                    
                    print_json_output(entry_dict, indent)
            
            # Optionally flush remaining incomplete transactions
            if args.flush_remaining:
                remaining_entries = processor.get_remaining_entries()
                for entry in remaining_entries:
                    entry_dict = asdict(entry)
                    if 'from_addr' in entry_dict:
                        entry_dict['from'] = entry_dict.pop('from_addr')
                    
                    print_json_output(entry_dict, indent)
        
        except KeyboardInterrupt:
            pass
        except BrokenPipeError:
            # Handle broken pipe gracefully
            pass
        except UnicodeDecodeError as e:
            print(f"Encoding error: {e}", file=sys.stderr)
            print("Try using --encoding-errors=ignore or --encoding=latin-1", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
