# Handling Encoding Issues in Production Logs

If you encounter Unicode/encoding errors like:
```
UnicodeDecodeError: 'utf-8' codec can't decode byte 0xb4 in position 6319: invalid start byte
```

This means your log files contain characters that aren't valid UTF-8. Here are several solutions:

## Quick Solutions

### 1. Use Error Replacement (Recommended)
Replace problematic characters with placeholder characters:
```bash
cat /var/log/maillog | python postfix_log_parser.py --encoding-errors=replace
```

### 2. Ignore Problematic Characters
Skip problematic characters entirely:
```bash
cat /var/log/maillog | python postfix_log_parser.py --encoding-errors=ignore
```

### 3. Try Latin-1 Encoding
Many legacy systems use Latin-1 encoding:
```bash
cat /var/log/maillog | python postfix_log_parser.py --encoding=latin-1
```

### 4. Auto-detect Encoding
Let the parser try to detect the encoding automatically:
```bash
cat /var/log/maillog | python postfix_log_parser.py --encoding=auto
```

## For Production Use

### Option 1: Pre-process with iconv
Clean the log file before parsing:
```bash
iconv -f latin-1 -t utf-8 /var/log/maillog | python postfix_log_parser.py
```

### Option 2: Use sed to remove problematic characters
```bash
sed 's/[^\x00-\x7F]//g' /var/log/maillog | python postfix_log_parser.py
```

### Option 3: Combine with error handling
```bash
cat /var/log/maillog | python postfix_log_parser.py --encoding-errors=replace --line-mode
```

## Examples

### Handle mixed encoding log with line-by-line output:
```bash
tail -f /var/log/maillog | python postfix_log_parser.py --line-mode --encoding-errors=replace
```

### Process historical logs with automatic encoding detection:
```bash
cat /var/log/maillog.1 | python postfix_log_parser.py --encoding=auto --flush-remaining
```

### Safe processing with error replacement:
```bash
zcat /var/log/maillog.*.gz | python postfix_log_parser.py --encoding-errors=replace
```

## Encoding Options Explained

- `--encoding=utf-8` (default): Expect UTF-8 encoding
- `--encoding=latin-1`: Use Latin-1/ISO-8859-1 encoding (common in older systems)
- `--encoding=cp1252`: Use Windows-1252 encoding
- `--encoding=auto`: Try to auto-detect the encoding

- `--encoding-errors=strict` (default for most): Fail on encoding errors
- `--encoding-errors=replace`: Replace problematic characters with �
- `--encoding-errors=ignore`: Skip problematic characters entirely

## Recommended Production Command

For most production environments with mixed encoding issues:
```bash
cat /var/log/maillog | python postfix_log_parser.py --encoding-errors=replace --line-mode
```

This will:
- Handle encoding errors gracefully by replacing bad characters
- Output each log line immediately (good for real-time processing)
- Continue processing even if some characters are corrupted
