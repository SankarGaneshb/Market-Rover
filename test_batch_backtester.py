import sys
import unittest
from unittest.mock import patch
import rover_tools.batch_backtester as bb
import json
import os

class TestBatchBacktester(unittest.TestCase):
    @patch('rover_tools.batch_backtester.get_common_tickers')
    def test_run_batch_backtest(self, mock_tickers):
        # Only process a couple of tickers to save time
        mock_tickers.return_value = ["ABB.NS - ABB India Limited", "TCS.NS - Tata Consultancy Services"]
        
        # Run it
        bb.run_batch_backtest()
        
        # Verify JSON
        self.assertTrue(os.path.exists(bb.OUTPUT_FILE))
        with open(bb.OUTPUT_FILE, 'r') as f:
            data = json.load(f)
            self.assertIn('ABB.NS', data['results'])
            self.assertIsInstance(data['results']['ABB.NS']['median_error'], float)

        # Verify Markdown
        self.assertTrue(os.path.exists(bb.SUMMARY_FILE))
        with open(bb.SUMMARY_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
            # Ensure it says something like "3y" instead of "[2025, 2024, 2023]y"
            self.assertNotIn("[", content)
            self.assertIn("y |", content)

if __name__ == '__main__':
    unittest.main()
