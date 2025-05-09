from src.data.data_feed import DataFeed
import unittest

class TestDataFeed(unittest.TestCase):

    def setUp(self):
        self.data_feed = DataFeed()

    def test_initialization(self):
        self.assertIsNotNone(self.data_feed)

    def test_fetch_data(self):
        data = self.data_feed.fetch_data('EURUSD')
        self.assertIsInstance(data, dict)
        self.assertIn('price', data)
        self.assertIn('timestamp', data)

    def test_fetch_data_invalid_symbol(self):
        with self.assertRaises(ValueError):
            self.data_feed.fetch_data('INVALID_SYMBOL')

    def test_data_source_integration(self):
        self.data_feed.add_data_source('Polygon', 'YOUR_API_KEY')
        self.assertIn('Polygon', self.data_feed.data_sources)

    def test_remove_data_source(self):
        self.data_feed.add_data_source('Polygon', 'YOUR_API_KEY')
        self.data_feed.remove_data_source('Polygon')
        self.assertNotIn('Polygon', self.data_feed.data_sources)

if __name__ == '__main__':
    unittest.main()