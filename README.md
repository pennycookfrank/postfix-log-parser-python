# postfix-log-parser-python

Parse postfix log files and output structured JSON format. This is a Python equivalent of the original Go-based postfix-log-parser.

**Original Go project:** [https://github.com/youyo/postfix-log-parser](https://github.com/youyo/postfix-log-parser)

## Features

- Parse postfix log entries from stdin or files
- Extract structured data including timestamps, hostnames, queue IDs, client info, and message details
- Group related log entries by queue ID to track email processing lifecycle
- Support for both standard syslog and ISO8601 timestamp formats
- Output consolidated JSON format per email transaction
- Available as both library and command-line tool
- **Enhanced regex patterns** to handle various postfix log formats including:
  - Multiple spaces in timestamps (e.g., `Jul  3` with double space)
  - Complex process names (e.g., `postfix/relay/smtp[1234567]`)
  - Long process IDs (7+ digits)
  - Empty message IDs (`message-id=<>`)
  - Various postfix service types
- **Robust encoding handling** for production logs with mixed character sets
- **Flexible time assignment**:
  - **Default**: Time from client connection only (null for incomplete logs)
  - **Optional fallback**: Intelligent time assignment for incomplete logs (message-id, from, or delivery time)

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Command Line

The parser supports two modes:

#### Transaction Mode (Default)
Groups related log entries by queue ID and outputs complete email transactions:

```console
# cat /var/log/maillog | python postfix_log_parser.py
{
  "time": "2023-10-10T15:59:29+09:00",
  "hostname": "mail",
  "process": "postfix/smtpd[1827]",
  "queue_id": "3D74ADB7400B",
  "client_hostname": "example.com",
  "client_ip": "127.0.0.1",
  "message_id": "f93388828093534f92d85ffe21b2a719@example.info",
  "from": "test2@example.info",
  "messages": [
    {
      "time": "2023-10-10T15:59:30+09:00",
      "to": "test@example.to",
      "status": "sent",
      "message": "to=<test@example.to>, relay=example.to[192.168.0.20]:25, delay=1.7, delays=0.02/0/1.7/0.06, dsn=2.0.0, status=sent (250 [Sniper] OK 1539154772 snipe-queue 10549)"
    }
  ]
}
```

#### Line Mode
Outputs each parsed log line immediately as JSON:

```console
# echo "Oct 10 04:02:08 mail postfix/smtp[123]: ABC: to=<test@example.com>, status=sent" | python postfix_log_parser.py --line-mode
{
  "time": "2023-10-10T04:02:08",
  "hostname": "mail",
  "process": "postfix/smtp[123]",
  "queue_id": "ABC",
  "to": "test@example.com",
  "status": "sent",
  "messages": "to=<test@example.com>, status=sent"
}
```

#### Command Line Options

```console
# Show help
python postfix_log_parser.py --help

# Line mode - output each line immediately
python postfix_log_parser.py --line-mode

# Transaction mode with incomplete transaction flushing
python postfix_log_parser.py --flush-remaining

# Use fallback timestamps for incomplete logs
python postfix_log_parser.py --use-fallback-time

# Handle encoding issues (common in production logs)
python postfix_log_parser.py --encoding-errors=replace

# Use different encoding
python postfix_log_parser.py --encoding=latin-1

# Auto-detect encoding
python postfix_log_parser.py --encoding=auto
```

#### Time Assignment Behavior

**Default behavior**: Transaction time is set only from client connection information (`client=hostname[ip]`). If no client connection info is available, time will be `null`.

**With `--use-fallback-time`**: Uses intelligent fallback for incomplete logs:
1. **Primary**: Client connection time (most accurate)
2. **Fallback 1**: Message-ID time  
3. **Fallback 2**: From/sender time
4. **Fallback 3**: Delivery time

```console
# Default: null time for incomplete logs
cat /var/log/maillog | python postfix_log_parser.py

# Fallback: use available timestamps for incomplete logs  
cat /var/log/maillog | python postfix_log_parser.py --use-fallback-time
```

#### Handling Encoding Issues

If you encounter Unicode errors with production logs:
```bash
# Replace problematic characters (recommended)
cat /var/log/maillog | python postfix_log_parser.py --encoding-errors=replace

# Try Latin-1 encoding (common in legacy systems)
cat /var/log/maillog | python postfix_log_parser.py --encoding=latin-1

# Auto-detect encoding
cat /var/log/maillog | python postfix_log_parser.py --encoding=auto
```

See `ENCODING_GUIDE.md` for detailed encoding handling instructions.

### Library Usage

```python
from postfix_log_parser import PostfixLogParser

# Initialize parser
parser = PostfixLogParser()

# Parse a single log line
log_line = "Oct 10 04:02:08 mail.example.com postfix/smtp[22928]: DFBEFDBF00C5: to=<test@example-to.com>, relay=mail.example-to.com[192.168.0.10]:25, delay=5.3, delays=0.26/0/0.31/4.7, dsn=2.0.0, status=sent (250 2.0.0 Ok: queued as C598F1B0002D)"

log_format = parser.parse_line(log_line)
print(log_format)
```

## Output Format

The parser groups related log entries by queue ID and outputs a consolidated JSON object containing:

- `time`: Timestamp of the initial log entry
- `hostname`: Mail server hostname
- `process`: Postfix process information
- `queue_id`: Unique queue identifier
- `client_hostname`: Client hostname (if available)
- `client_ip`: Client IP address (if available)
- `message_id`: Email message ID (if available)
- `from`: Sender email address (if available)
- `messages`: Array of delivery attempts/results

## Requirements

- Python 3.6+
- No external dependencies for core functionality

## License

MIT License - see LICENSE file for details.
