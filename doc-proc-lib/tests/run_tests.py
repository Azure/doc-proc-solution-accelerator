#!/usr/bin/env python3
"""
Test runner script for doc-proc-lib.

This script provides various options for running tests with different configurations.
"""

import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description=""):
    """Run a command and handle errors."""
    if description:
        print(f"\n{description}")
        print("=" * len(description))
    
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.stdout:
        print(result.stdout)
    
    if result.stderr:
        print(f"STDERR: {result.stderr}", file=sys.stderr)
    
    if result.returncode != 0:
        print(f"Command failed with return code {result.returncode}")
        sys.exit(1)
    
    return result


def main():
    parser = argparse.ArgumentParser(description="Run tests for doc-proc-lib")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--coverage", action="store_true", help="Run tests with coverage report")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--pattern", "-k", help="Run tests matching pattern")
    parser.add_argument("--file", "-f", help="Run tests in specific file")
    parser.add_argument("--install-deps", action="store_true", help="Install test dependencies")
    parser.add_argument("--component", choices=["step", "service", "pipeline", "utils"], 
                       help="Run tests for specific component")
    
    args = parser.parse_args()
    
    # Install dependencies if requested
    if args.install_deps:
        run_command(
            [sys.executable, "-m", "pip", "install", "-r", "requirements-test.txt"],
            "Installing test dependencies"
        )
    
    # Build pytest command
    cmd = [sys.executable, "-m", "pytest"]
    
    # Add coverage if requested
    if args.coverage:
        cmd.extend(["--cov=doc", "--cov-report=html", "--cov-report=term"])
    
    # Add verbosity
    if args.verbose:
        cmd.append("-v")
    
    # Add specific test markers
    if args.unit:
        cmd.extend(["-m", "unit"])
    elif args.integration:
        cmd.extend(["-m", "integration"])
    
    # Add pattern matching
    if args.pattern:
        cmd.extend(["-k", args.pattern])
    
    # Add specific component
    if args.component:
        cmd.append(f"./{args.component}/")
    
    # Add specific file
    if args.file:
        cmd.append(args.file)
    
    # If no specific tests specified, run all tests
    if not any([args.unit, args.integration, args.file, args.component]):
        cmd.append("./")
    
    # Run the tests
    run_command(cmd, "Running tests")


if __name__ == "__main__":
    main()
