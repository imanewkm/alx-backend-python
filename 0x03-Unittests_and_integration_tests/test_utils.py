#!/usr/bin/env python3

"""
Test suite for utils.py
"""

import unittest
from unittest.mock import patch
from parameterized import parameterized
from utils import (
    access_nested_map,
    memoize,
    get_json
    )


class TestAccessNestedMap(unittest.TestCase):
    """
    Test class for the utils..access_nested_map funtion
    """
    @parameterized.expand([
        ({"a": 1}, ("a",), 1),
        ({"a": {"b": 2}}, ("a",), {'b': 2}),
        ({"a": {"b": 2}}, ("a", "b"), 2),
    ])
    def test_access_nested_map(self, nested_map, path, output):
        """
        Test method
        """
        self.assertEqual(access_nested_map(nested_map, path), output)

    @parameterized.expand([
        ({}, ("a",)),
        ({"a": 1}, ("a", "b")),
    ])
    def test_access_nested_map_exception(self, nested_map, path):
        """
        Test for an exception
        """
        with self.assertRaises(KeyError) as cm:
            access_nested_map(nested_map, path)
            self.assertEqual(str(cm.exception), f"'{path[-1]}'")


class TestGetJson(unittest.TestCase):
    """
    Test class for the utils.get_json function
    """
    @parameterized.expand([
        ("http://example.com", {"payload": True}),
        ("http://holberton.io", {"payload": False}),
    ])
    @patch('requests.get')
    def test_get_json(self, test_url, test_payload, mock_get):
        """
        Mocks http calls
        """
        mock_get.return_value.json.return_value = test_payload
        output = get_json(test_url)
        mock_get.assert_called_once_with(test_url)
        self.assertDictEqual(test_payload, output)


class TestMemoize(unittest.TestCase):
    """
    Test class for the utils.memoized function
    """
    def test_memoize(self):
        """
        Test for memoization
        """
        class TestClass:
            """
            Class to pacth
            """
            def a_method(self):
                """
                Method return an integer 42
                """
                return 42

            @memoize
            def a_property(self):
                """
                Memoized method return result of a_method
                """
                return self.a_method()

        instance = TestClass()

        with patch.object(instance, 'a_method') as mck_fn:
            mck_fn.return_value = 42
            result1 = instance.a_property
            result2 = instance.a_property
            self.assertEqual(result1, 42)
            self.assertEqual(result2, 42)
            mck_fn.assert_called_once()
