"""Run one offline unittest directory; stdout avoids PowerShell stderr wrapping."""
import sys
import unittest

if len(sys.argv) != 2 or sys.argv[1] not in {"task1", "task2", "task3"}:
    raise SystemExit("Usage: python -B run_python_tests.py task1|task2|task3")
suite = unittest.defaultTestLoader.discover(sys.argv[1])
result = unittest.TextTestRunner(stream=sys.stdout, verbosity=2).run(suite)
raise SystemExit(0 if result.wasSuccessful() else 1)
