#!/usr/bin/env python3
"""
Simple script to run the test suite.
"""

import sys
import unittest
import os

# Add the project directory to the path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import the test modules
from tests.test_server import TestRadarrSonarrMCPServer

if __name__ == "__main__":
    # Run all tests
    unittest.main(module=None, argv=['run_tests.py'])
