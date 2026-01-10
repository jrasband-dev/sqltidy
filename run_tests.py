"""
Test runner script for SQLTidy.

Usage:
    python run_tests.py              # Run all tests
    python run_tests.py unit         # Run only unit tests
    python run_tests.py integration  # Run only integration tests
    python run_tests.py dialects     # Run only dialect tests
    python run_tests.py -v           # Verbose output
    python run_tests.py -k keyword   # Run tests matching keyword
"""

import sys
import subprocess


def run_tests(args=None):
    """Run pytest with the given arguments."""
    cmd = [sys.executable, "-m", "pytest"]

    if args:
        # Parse custom arguments
        if "unit" in args:
            cmd.append("tests/unit")
            args.remove("unit")
        elif "integration" in args:
            cmd.append("tests/integration")
            args.remove("integration")
        elif "dialects" in args:
            cmd.append("tests/dialects")
            args.remove("dialects")

        # Add remaining args
        cmd.extend(args)
    else:
        # Run all tests
        cmd.append("tests/")

    print(f"Running: {' '.join(cmd)}")
    print("=" * 80)

    result = subprocess.run(cmd)
    return result.returncode


if __name__ == "__main__":
    args = sys.argv[1:] if len(sys.argv) > 1 else None
    exit_code = run_tests(args)
    sys.exit(exit_code)
