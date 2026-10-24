import unittest


def add(a, b):
    return a + b


class TestBasics(unittest.TestCase):

    def test_addition(self):
        self.assertEqual(add(2, 3), 5)

    def test_numbers_equal(self):
        self.assertEqual(10, 10)

    def test_list_length(self):
        players = ["Jack", "Alex", "Sarah"]
        self.assertEqual(len(players), 3)


if __name__ == "__main__":
    unittest.main()