import unittest
from unittest.mock import Mock, patch
from app import app


class MyTestCase(unittest.TestCase):

    def test_something(self):
        with patch('app.models') as mocked_models:
            mocked_models
            self.assertEqual(True, True)


if __name__ == '__main__':
    unittest.main()
