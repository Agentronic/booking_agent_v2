#!/usr/bin/env python
"""
Unit test runner for the booking agent project.
Runs all tests in the test directory.
"""

import os
import sys
import unittest
import logging
import argparse
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("unit_tests.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def run_tests(verbose=False, individual=False):
    """
    Run all unit tests in the test directory.
    
    Args:
        verbose: If True, show more detailed test output
        individual: If True, run each test file individually
    """
    start_time = time.time()
    logger.info("Starting unit tests for booking agent")
    
    # Add the project root to the path
    bin_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(bin_dir)
    sys.path.append(project_root)
    
    # Get all test files
    test_dir = os.path.join(project_root, 'test')
    test_files = [f for f in os.listdir(test_dir) 
                 if f.startswith('test_') and f.endswith('.py')]
    
    if individual:
        # Run each test file individually
        total_tests = 0
        failures = 0
        errors = 0
        
        for test_file in test_files:
            test_module = f"test.{test_file[:-3]}"  # Remove .py extension
            logger.info(f"Running tests from {test_module}")
            
            # Create a test suite for this module
            suite = unittest.defaultTestLoader.loadTestsFromName(test_module)
            runner = unittest.TextTestRunner(verbosity=2 if verbose else 1)
            result = runner.run(suite)
            
            total_tests += result.testsRun
            failures += len(result.failures)
            errors += len(result.errors)
            
            print("-" * 70)
        
        # Print summary
        logger.info(f"Ran {total_tests} tests with {failures} failures and {errors} errors")
        success = failures == 0 and errors == 0
    else:
        # Run all tests together
        suite = unittest.defaultTestLoader.discover(test_dir)
        runner = unittest.TextTestRunner(verbosity=2 if verbose else 1)
        result = runner.run(suite)
        success = result.wasSuccessful()
    
    end_time = time.time()
    duration = end_time - start_time
    
    if success:
        logger.info(f"All tests passed successfully in {duration:.2f} seconds")
        return 0
    else:
        logger.error(f"Tests completed with failures in {duration:.2f} seconds")
        return 1

def main():
    """Parse command line arguments and run tests."""
    parser = argparse.ArgumentParser(description='Run unit tests for booking agent')
    parser.add_argument('-v', '--verbose', action='store_true', 
                        help='Show more detailed test output')
    parser.add_argument('-i', '--individual', action='store_true',
                        help='Run each test file individually')
    parser.add_argument('-d', '--dependencies', action='store_true',
                        help='Run dependency tests first')
    
    args = parser.parse_args()
    
    # Run dependency tests first if requested
    if args.dependencies:
        logger.info("Running dependency tests")
        bin_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(bin_dir)
        dependency_test = os.path.join(project_root, 'test', 'test_dependencies.py')
        os.system(f"python {dependency_test}")
        print("\n" + "=" * 70 + "\n")
    
    # Run all unit tests
    return run_tests(args.verbose, args.individual)

if __name__ == "__main__":
    sys.exit(main())
