#!/usr/bin/env python3
"""
Test runner script for langgraph-test project.
Provides convenient ways to run different test suites.
"""

import sys
import subprocess
import argparse


def run_command(cmd, description=""):
    """Run a command and handle the output."""
    if description:
        print(f"\n{'=' * 50}")
        print(f"🧪 {description}")
        print(f"{'=' * 50}")
    
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=False)
    
    if result.returncode != 0:
        print(f"❌ Command failed with exit code {result.returncode}")
        return False
    else:
        print(f"✅ {description or 'Command'} completed successfully")
        return True


def main():
    parser = argparse.ArgumentParser(description="Run tests for langgraph-test project")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--api", action="store_true", help="Run API tests only")
    parser.add_argument("--performance", action="store_true", help="Run performance tests only")
    parser.add_argument("--smoke", action="store_true", help="Run smoke tests only")
    parser.add_argument("--fast", action="store_true", help="Run fast tests only (exclude slow)")
    parser.add_argument("--coverage", action="store_true", help="Run with coverage report")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--parallel", "-n", type=int, help="Run tests in parallel (number of workers)")
    
    args = parser.parse_args()
    
    # Base pytest command
    cmd = ["python", "-m", "pytest"]
    
    # Add verbosity
    if args.verbose:
        cmd.append("-v")
    else:
        cmd.extend(["-q", "--tb=short"])
    
    # Add parallel execution
    if args.parallel:
        cmd.extend(["-n", str(args.parallel)])
    
    # Add coverage
    if args.coverage:
        cmd.extend(["--cov=src", "--cov-report=html", "--cov-report=term-missing"])
    
    # Determine which tests to run
    if args.unit:
        cmd.extend(["-m", "unit", "tests/unit/"])
        description = "Unit Tests"
    elif args.integration:
        cmd.extend(["-m", "integration", "tests/integration/"])
        description = "Integration Tests"
    elif args.api:
        cmd.extend(["-m", "api", "tests/api/"])
        description = "API Tests"
    elif args.performance:
        cmd.extend(["-m", "performance", "tests/performance/"])
        description = "Performance Tests"
    elif args.smoke:
        cmd.extend(["-m", "smoke"])
        description = "Smoke Tests"
    elif args.fast:
        cmd.extend(["-m", "not slow"])
        description = "Fast Tests (excluding slow tests)"
    elif args.all:
        cmd.append("tests/")
        description = "All Tests"
    else:
        # Default: run fast tests
        cmd.extend(["-m", "not slow and not performance", "tests/"])
        description = "Default Test Suite (fast tests)"
    
    # Run the tests
    success = run_command(cmd, description)
    
    if not success:
        sys.exit(1)
    
    print(f"\n🎉 {description} completed successfully!")


if __name__ == "__main__":
    main() 