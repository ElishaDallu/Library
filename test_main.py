import unittest
import lib_main


class TestApp(unittest.TestCase):
    def test_import_book(self):
        # with app.Flask.app_context(self):
        title = "Liar's Poker"
        print(title)
        self.assertTrue(lib_main.import_book(title), title)


if __name__ == '__main__':
    unittest.main()
