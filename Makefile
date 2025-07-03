.PHONY: test install clean example help

# Default target
help:
	@echo "Available targets:"
	@echo "  test          - Run test script"
	@echo "  test-modes    - Run comprehensive mode tests"
	@echo "  test-fixes    - Run fix tests for problematic log formats"
	@echo "  test-encoding - Test encoding handling"
	@echo "  test-incomplete - Test incomplete log handling"
	@echo "  test-all      - Run all tests"
	@echo "  example       - Run example script"
	@echo "  test-data     - Test with original test data (transaction mode)"
	@echo "  test-line-mode - Test line mode functionality"
	@echo "  install       - Install the package"
	@echo "  clean         - Clean up generated files"
	@echo "  help          - Show this help message"

# Run tests
test:
	python test_parser.py

# Run comprehensive mode tests
test-modes:
	python test_modes.py

# Run fix tests for problematic log formats
test-fixes:
	python test_fixes.py

# Test encoding handling
test-encoding:
	python test_encoding.py

# Test incomplete log handling
test-incomplete:
	python test_incomplete_logs.py

# Run all tests
test-all:
	@echo "Running all tests..."
	@echo "1. Basic tests:"
	python test_parser.py
	@echo ""
	@echo "2. Mode tests:"
	python test_modes.py
	@echo ""
	@echo "3. Fix tests:"
	python test_fixes.py
	@echo ""
	@echo "4. Encoding tests:"
	python test_encoding.py
	@echo ""
	@echo "5. Incomplete log tests:"
	python test_incomplete_logs.py
	@echo ""
	@echo "All tests completed!"

# Run example
example:
	python example.py

# Test with original test data
test-data:
	@echo "Testing with original syslog format (transaction mode):"
	head -20 test/test.log | python postfix_log_parser.py
	@echo ""
	@echo "Testing with ISO8601 format (transaction mode):"
	head -20 test/test-iso8601.log | python postfix_log_parser.py

# Test line mode
test-line-mode:
	@echo "Testing line mode with individual log entries:"
	head -10 test/test.log | python postfix_log_parser.py --line-mode
	@echo ""
	@echo "Testing single line:"
	echo "Oct 10 04:02:08 mail postfix/smtp[123]: ABC: to=<test@example.com>, status=sent" | python postfix_log_parser.py --line-mode

# Install package
install:
	pip install -e .

# Clean up
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -delete

# Compare output with original Go implementation (if available)
compare:
	@echo "Python implementation output:"
	head -20 test/test.log | python postfix_log_parser.py | jq .
	@echo ""
	@echo "Note: Install original Go implementation to compare outputs"
