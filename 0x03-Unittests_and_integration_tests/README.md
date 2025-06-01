# 0x03. Unittests and Integration Tests

## Description

This project focuses on understanding and implementing unit tests and integration tests in Python. You'll learn the difference between these testing approaches and common testing patterns such as mocking, parametrizations, and fixtures.

**Unit Testing**: Tests individual functions with expected results for different inputs, including edge cases. External calls should be mocked to isolate the function's logic.

**Integration Testing**: Tests complete code paths end-to-end, with minimal mocking of only low-level external calls (HTTP, file I/O, database I/O).

## Learning Objectives

- Understand the difference between unit and integration tests
- Implement common testing patterns: mocking, parametrizations, and fixtures
- Write comprehensive test suites for Python applications

## Requirements

- Ubuntu 18.04 LTS with Python 3.7
- All files must end with a new line
- First line: `#!/usr/bin/env python3`
- Code style: pycodestyle (version 2.5)
- All files must be executable
- All modules, classes, and functions must have documentation
- All functions must be type-annotated

## Usage

Execute tests with:
```bash
$ python -m unittest path/to/test_file.py
```

## Resources

- [unittest — Unit testing framework](https://docs.python.org/3/library/unittest.html)
- [unittest.mock — mock object library](https://docs.python.org/3/library/unittest.
