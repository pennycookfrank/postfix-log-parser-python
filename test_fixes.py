#!/usr/bin/env python3
"""
Test the specific fixes for the problematic log format
"""

import subprocess
import json
import sys


def test_problematic_log_parsing():
    """Test parsing of the problematic log format"""
    print("=== Testing Problematic Log Format Fixes ===")

    # Test cases that were failing before
    test_cases = [
        {
            "name": "Empty message-id",
            "line": "Jul  3 00:00:02 mailhost.example.com postfix/cleanup[4120776]: D15612055068: message-id=<>",
            "expected_fields": ["queue_id"],
            "expected_empty_fields": [
                "message_id"
            ],  # message_id should be empty string
        },
        {
            "name": "Long process ID (7 digits)",
            "line": "Jul  3 00:00:02 mailhost.example.com postfix/cleanup[4120776]: D15612055068: message-id=<>",
            "expected_fields": ["process", "queue_id"],
        },
        {
            "name": "Relay/smtp process",
            "line": "Jul  3 00:00:05 mailhost.example.com postfix/relay/smtp[4120778]: D15612055068: to=<user1@example.com>, relay=relay.example.com[198.51.100.1]:25, delay=2.5, delays=0.04/0.03/1.7/0.72, dsn=2.0.0, status=sent (250 2.0.0 Ok: queued as E6E7310002B10)",
            "expected_fields": ["process", "to", "status"],
        },
        {
            "name": "Double space in timestamp",
            "line": "Jul  3 00:00:02 mailhost.example.com postfix/qmgr[1282252]: D15612055068: from=<user2@example.com>, size=1237, nrcpt=2 (queue active)",
            "expected_fields": ["time", "hostname", "from"],
        },
    ]

    success_count = 0

    for test_case in test_cases:
        print(f"\nTesting: {test_case['name']}")
        print(f"Line: {test_case['line'][:80]}...")

        # Test with line mode
        result = subprocess.run(
            ["python", "postfix_log_parser.py", "--line-mode"],
            input=test_case["line"],
            text=True,
            capture_output=True,
        )

        if result.returncode == 0 and result.stdout.strip():
            try:
                parsed = json.loads(result.stdout.strip())

                # Check expected fields
                all_fields_present = True
                for field in test_case["expected_fields"]:
                    if field not in parsed or not parsed[field]:
                        print(f"  ✗ Missing or empty field: {field}")
                        all_fields_present = False
                    else:
                        print(f"  ✓ Field {field}: {parsed[field]}")

                # Check expected empty fields (should be present but empty)
                if "expected_empty_fields" in test_case:
                    for field in test_case["expected_empty_fields"]:
                        if field not in parsed:
                            print(f"  ✗ Missing field: {field}")
                            all_fields_present = False
                        elif parsed[field] == "":
                            print(f"  ✓ Empty field {field}: (correctly empty)")
                        else:
                            print(
                                f"  ✗ Field {field} should be empty but got: {parsed[field]}"
                            )
                            all_fields_present = False

                if all_fields_present:
                    print(f"  ✓ {test_case['name']} - All expected fields present")
                    success_count += 1
                else:
                    print(f"  ✗ {test_case['name']} - Some fields missing")

            except json.JSONDecodeError:
                print(f"  ✗ {test_case['name']} - Invalid JSON output")
        else:
            print(f"  ✗ {test_case['name']} - No output or error")
            if result.stderr:
                print(f"    Error: {result.stderr}")

    print(f"\nResults: {success_count}/{len(test_cases)} test cases passed")
    return success_count == len(test_cases)


def test_full_transaction():
    """Test the full problematic transaction"""
    print("\n=== Testing Full Problematic Transaction ===")

    log_lines = [
        "Jul  3 00:00:02 mailhost.example.com postfix/cleanup[4120776]: D15612055068: message-id=<>",
        "Jul  3 00:00:02 mailhost.example.com postfix/qmgr[1282252]: D15612055068: from=<user2@example.com>, size=1237, nrcpt=2 (queue active)",
        "Jul  3 00:00:04 mailhost.example.com postfix/smtpd[4115659]: disconnect from unknown[192.0.2.1] ehlo=1 mail=1 rcpt=2 data=1 commands=5",
        "Jul  3 00:00:05 mailhost.example.com postfix/relay/smtp[4120778]: D15612055068: to=<user1@example.com>, relay=relay.example.com[198.51.100.1]:25, delay=2.5, delays=0.04/0.03/1.7/0.72, dsn=2.0.0, status=sent (250 2.0.0 Ok: queued as E6E7310002B10)",
        "Jul  3 00:00:05 mailhost.example.com postfix/relay/smtp[4120778]: D15612055068: to=<user3@example.com>, relay=relay.example.com[198.51.100.1]:25, delay=2.5, delays=0.04/0.03/1.7/0.72, dsn=2.0.0, status=sent (250 2.0.0 Ok: queued as E6E7310002B10)",
        "Jul  3 00:00:05 mailhost.example.com postfix/qmgr[1282252]: D15612055068: removed",
    ]

    input_text = "\n".join(log_lines)

    # Test transaction mode
    result = subprocess.run(
        ["python", "postfix_log_parser.py"],
        input=input_text,
        text=True,
        capture_output=True,
    )

    if result.returncode == 0 and result.stdout.strip():
        try:
            parsed = json.loads(result.stdout.strip())

            print("✓ Transaction parsed successfully")
            print(f"  Queue ID: {parsed.get('queue_id', 'N/A')}")
            print(f"  From: {parsed.get('from', 'N/A')}")
            print(f"  Messages: {len(parsed.get('messages', []))} delivery attempts")

            # Check specific fields
            expected_values = {"queue_id": "D15612055068", "from": "user2@example.com"}

            all_correct = True
            for field, expected in expected_values.items():
                actual = parsed.get(field)
                if actual == expected:
                    print(f"  ✓ {field}: {actual}")
                else:
                    print(f"  ✗ {field}: expected {expected}, got {actual}")
                    all_correct = False

            # Check message count
            messages = parsed.get("messages", [])
            if len(messages) == 2:
                print(f"  ✓ Message count: {len(messages)}")

                # Check recipients
                recipients = [msg.get("to") for msg in messages]
                expected_recipients = ["user1@example.com", "user3@example.com"]
                if set(recipients) == set(expected_recipients):
                    print(f"  ✓ Recipients: {recipients}")
                else:
                    print(
                        f"  ✗ Recipients: expected {expected_recipients}, got {recipients}"
                    )
                    all_correct = False
            else:
                print(f"  ✗ Message count: expected 2, got {len(messages)}")
                all_correct = False

            return all_correct

        except json.JSONDecodeError:
            print("✗ Invalid JSON output")
            return False
    else:
        print("✗ Transaction parsing failed")
        if result.stderr:
            print(f"Error: {result.stderr}")
        return False


def main():
    """Run all fix tests"""
    print("Testing fixes for problematic log format...\n")

    test1_passed = test_problematic_log_parsing()
    test2_passed = test_full_transaction()

    print(f"\n{'=' * 50}")
    if test1_passed and test2_passed:
        print("🎉 All fix tests passed!")
        return 0
    else:
        print("❌ Some fix tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
