import unittest

from spotifyify.utils import coalesce_items, coalesce_csv


class TestCoalesceItems(unittest.TestCase):
    def test_basic_strings(self):
        result = coalesce_items(["a", "b", "c"])
        self.assertEqual(result, ["a", "b", "c"])

    def test_strips_whitespace(self):
        result = coalesce_items(["  a  ", " b", "c "])
        self.assertEqual(result, ["a", "b", "c"])

    def test_filters_empty_strings(self):
        result = coalesce_items(["a", "", "  ", "b"])
        self.assertEqual(result, ["a", "b"])

    def test_empty_iterable(self):
        self.assertEqual(coalesce_items([]), [])

    def test_generator_input(self):
        result = coalesce_items(x for x in ["a", "b"])
        self.assertEqual(result, ["a", "b"])


class TestCoalesceCsv(unittest.TestCase):
    def test_joins_with_commas(self):
        self.assertEqual(coalesce_csv(["a", "b", "c"]), "a,b,c")

    def test_strips_and_filters(self):
        self.assertEqual(coalesce_csv(["a", " ", "b"]), "a,b")

    def test_empty(self):
        self.assertEqual(coalesce_csv([]), "")

    def test_single_item(self):
        self.assertEqual(coalesce_csv(["abc"]), "abc")
