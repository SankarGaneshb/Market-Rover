
import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
import sys
import pandas as pd
import numpy as np
from datetime import date

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Tier 1 Imports (SafeUtils)
from scripts import validate_issue_assignees
from scripts import check_models
from scripts import sanitize_file

class TestValidateIssueAssignees(unittest.TestCase):
    def test_valid_github_username(self):
        self.assertTrue(validate_issue_assignees.valid_github_username("octocat"))
        self.assertTrue(validate_issue_assignees.valid_github_username("octocat-1"))
        self.assertFalse(validate_issue_assignees.valid_github_username("-invalid"))
        self.assertFalse(validate_issue_assignees.valid_github_username("invalid-"))
        self.assertFalse(validate_issue_assignees.valid_github_username("inv@lid"))

    def test_valid_label(self):
        self.assertTrue(validate_issue_assignees.valid_label("bug"))
        self.assertTrue(validate_issue_assignees.valid_label("enhancement"))
        self.assertTrue(validate_issue_assignees.valid_label("good-first-issue"))
        self.assertFalse(validate_issue_assignees.valid_label(""))

class TestCheckModels(unittest.TestCase):
    @patch("scripts.check_models.genai")
    @patch("scripts.check_models.os.getenv")
    def test_check_models_found(self, mock_getenv, mock_genai):
        mock_getenv.return_value = "fake-key"
        m1 = MagicMock()
        m1.name = "models/gemini-pro"
        m1.supported_generation_methods = ["generateContent"]
        m2 = MagicMock()
        m2.name = "models/gemini-vision"
        m2.supported_generation_methods = ["generateContent"]
        mock_genai.list_models.return_value = [m1, m2]
        
        with patch('builtins.print') as mock_print:
            check_models.main()
            mock_genai.configure.assert_called_with(api_key="fake-key")
            mock_genai.list_models.assert_called_once()
            call_args = str(mock_print.call_args_list)
            self.assertIn("Success", call_args)

class TestSanitizeFile(unittest.TestCase):
    def test_aggressive_clean(self):
        dirty_content = b"Hello\x00World"
        m_open = mock_open(read_data=dirty_content)
        # Fix: open is a builtin, so we must patch builtins.open, NOT scripts.sanitize_file.open
        with patch("builtins.open", m_open):
            with patch("os.path.exists", return_value=True):
                with patch("builtins.print"):
                    sanitize_file.aggressive_clean()
        
        # Verify write called with cleaned content
        # Note: aggressive_clean opens file twice (read, then write).
        # m_open() returns the file handle.
        # We need to verify that write was called on one of the handles.
        m_open().write.assert_called_with(b"HelloWorld")

class TestFastSeasonality(unittest.TestCase):
    def test_analyze_seasonality_profile(self):
        # Local import to avoid global dependency issues
        from scripts import fast_seasonality
        
        dates = pd.date_range("2023-01-01", "2023-02-28", freq="D")
        close = np.linspace(100, 110, len(dates))
        df = pd.DataFrame({"Close": close}, index=dates)
        
        res = fast_seasonality.analyze_seasonality_profile(df)
        self.assertIn("Day", res.columns)
        self.assertAlmostEqual(res[res['Day'] == 1].iloc[0]['Avg_Rel_Price'], 1.0, places=2)

class TestExtractInfyTable(unittest.TestCase):
    def test_adjust_date(self):
        from scripts import extract_infy_table
        
        d_sun = date(2026, 1, 4)
        res = extract_infy_table.adjust_date(4, 1, 2026, 'buy')
        self.assertIn("05 (Mon)", res)
        
        res_hol = extract_infy_table.adjust_date(26, 1, 2026, 'buy')
        self.assertNotEqual(res_hol, "26 (Mon)")

class TestTrainBrain(unittest.TestCase):
    
    def test_train_brain_flow(self):
        # We Mock crew_engine BEFORE importing train_brain to prevent real import
        with patch.dict(sys.modules, {'crew_engine': MagicMock()}):
            from scripts import train_brain
            
            with patch("scripts.train_brain.shutil") as mock_shutil:
                with patch("scripts.train_brain.create_crew") as mock_create_crew:
                    with patch("scripts.train_brain.TRAINING_SOURCE") as mock_source:
                        with patch("scripts.train_brain.LIVE_PORTFOLIO") as mock_live:
                            with patch("scripts.train_brain.BACKUP_PORTFOLIO") as mock_backup:
                                with patch("scripts.train_brain.logger"):
                                    with patch("scripts.train_brain.os.remove"):
                                        with patch('builtins.print'):
                                            
                                            # Setup
                                            mock_source.exists.return_value = True
                                            mock_live.exists.return_value = True
                                            mock_backup.exists.return_value = True # Ensure cleanup logic runs
                                            mock_crew = MagicMock()
                                            mock_create_crew.return_value = mock_crew

                                            train_brain.main()
                                            
                                            # Verification
                                            self.assertTrue(mock_shutil.copy2.called)
                                            mock_create_crew.assert_called_with(max_parallel_stocks=10)
                                            mock_crew.run.assert_called_once()
                                            self.assertTrue(mock_shutil.move.called)

if __name__ == '__main__':
    unittest.main()
