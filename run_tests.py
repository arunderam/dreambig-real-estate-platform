#!/usr/bin/env python3
"""
Test runner script for DreamBig Real Estate Platform
"""
import os
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(command, description):
    """Run a command and handle errors."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {command}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR: {description} failed!")
        print(f"Exit code: {e.returncode}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Run tests for DreamBig Real Estate Platform")
    parser.add_argument("--type", choices=["unit", "integration", "performance", "security", "all"], 
                       default="all", help="Type of tests to run")
    parser.add_argument("--coverage", action="store_true", help="Run with coverage report")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--parallel", "-n", type=int, help="Number of parallel workers")
    parser.add_argument("--markers", "-m", help="Run tests with specific markers")
    parser.add_argument("--file", "-f", help="Run specific test file")
    parser.add_argument("--function", "-k", help="Run tests matching pattern")
    
    args = parser.parse_args()
    
    # Change to project directory
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    # Base pytest command
    pytest_cmd = ["python", "-m", "pytest"]
    
    # Add verbose flag
    if args.verbose:
        pytest_cmd.append("-v")
    
    # Add parallel execution
    if args.parallel:
        pytest_cmd.extend(["-n", str(args.parallel)])
    
    # Add coverage
    if args.coverage:
        pytest_cmd.extend([
            "--cov=app",
            "--cov-report=html:htmlcov",
            "--cov-report=term-missing",
            "--cov-report=xml"
        ])
    
    # Add markers
    if args.markers:
        pytest_cmd.extend(["-m", args.markers])
    
    # Add function pattern
    if args.function:
        pytest_cmd.extend(["-k", args.function])
    
    # Determine test files to run
    test_files = []
    
    if args.file:
        test_files.append(f"app/tests/{args.file}")
    elif args.type == "unit":
        test_files.extend([
            "app/tests/test_models.py",
            "app/tests/test_crud.py",
            "app/tests/test_business_rules.py"
        ])
    elif args.type == "integration":
        test_files.extend([
            "app/tests/test_api_auth.py",
            "app/tests/test_api_properties.py"
        ])
    elif args.type == "performance":
        test_files.append("app/tests/test_performance.py")
    elif args.type == "security":
        test_files.append("app/tests/test_security.py")
    elif args.type == "all":
        test_files.extend([
            "app/tests/test_models.py",
            "app/tests/test_crud.py",
            "app/tests/test_business_rules.py",
            "app/tests/test_api_auth.py",
            "app/tests/test_api_properties.py",
            "app/tests/test_performance.py",
            "app/tests/test_security.py"
        ])
    
    # Add test files to command
    pytest_cmd.extend(test_files)
    
    # Convert to string command
    command = " ".join(pytest_cmd)
    
    print("DreamBig Real Estate Platform - Test Runner")
    print(f"Test Type: {args.type}")
    print(f"Coverage: {'Enabled' if args.coverage else 'Disabled'}")
    print(f"Parallel Workers: {args.parallel if args.parallel else 'Auto'}")
    
    # Run the tests
    success = run_command(command, f"{args.type.title()} Tests")
    
    if success:
        print(f"\n✅ {args.type.title()} tests completed successfully!")
        
        if args.coverage:
            print("\n📊 Coverage report generated:")
            print("  - HTML report: htmlcov/index.html")
            print("  - XML report: coverage.xml")
            
            # Try to open coverage report
            try:
                import webbrowser
                coverage_path = project_root / "htmlcov" / "index.html"
                if coverage_path.exists():
                    print(f"  - Opening coverage report in browser...")
                    webbrowser.open(f"file://{coverage_path.absolute()}")
            except Exception:
                pass
    else:
        print(f"\n❌ {args.type.title()} tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
