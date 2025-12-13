"""
Unit tests for help module (Session 8)
"""

import unittest
from package.help import (
    get_help_topic,
    get_help_overview,
    get_unknown_topic_message,
    get_welcome_message,
    get_security_wizard_section,
    get_csv_wizard_section,
    get_category_wizard_section,
    get_completion_wizard_section,
    HELP_TOPICS,
    SUGGESTED_CATEGORIES
)


class TestHelpTopics(unittest.TestCase):
    """Test help topic retrieval"""

    def test_get_help_overview_with_none(self):
        """Test getting overview when topic is None"""
        result = get_help_topic(None)

        self.assertIn("F.U.C.K. HELP SYSTEM", result)
        self.assertIn("Available help topics:", result)
        self.assertIn("setup", result)
        self.assertIn("categories", result)
        self.assertIn("csv-format", result)
        self.assertIn("security", result)

    def test_get_help_topic_setup(self):
        """Test getting setup help topic"""
        result = get_help_topic("setup")

        self.assertIn("FIRST-TIME SETUP GUIDE", result)
        self.assertIn("PREPARE YOUR DATA", result)
        self.assertIn("SECURITY SETUP", result)
        self.assertIn("FUCK_GLOBAL_SALT", result)
        self.assertIn("FUCK_ENCRYPTION_KEY", result)

    def test_get_help_topic_categories(self):
        """Test getting categories help topic"""
        result = get_help_topic("categories")

        self.assertIn("CATEGORY MANAGEMENT GUIDE", result)
        self.assertIn("BUILT-IN CATEGORIES", result)
        self.assertIn("Groceries/Food", result)
        self.assertIn("bulk-edit", result)

    def test_get_help_topic_csv_format(self):
        """Test getting csv-format help topic"""
        result = get_help_topic("csv-format")

        self.assertIn("CSV FORMAT GUIDE", result)
        self.assertIn("REQUIRED COLUMNS", result)
        self.assertIn("Date", result)
        self.assertIn("Amount", result)
        self.assertIn("COMMON BANK FORMATS", result)

    def test_get_help_topic_security(self):
        """Test getting security help topic"""
        result = get_help_topic("security")

        self.assertIn("SECURITY GUIDE", result)
        self.assertIn("ENCRYPTION", result)
        self.assertIn("Fernet", result)
        self.assertIn("KEYS AND SALT", result)
        self.assertIn("BEST PRACTICES", result)

    def test_get_help_topic_case_insensitive(self):
        """Test that topic lookup is case-insensitive"""
        result_lower = get_help_topic("setup")
        result_upper = get_help_topic("SETUP")
        result_mixed = get_help_topic("Setup")

        self.assertEqual(result_lower, result_upper)
        self.assertEqual(result_lower, result_mixed)

    def test_get_unknown_topic(self):
        """Test getting unknown help topic"""
        result = get_help_topic("nonexistent")

        self.assertIn("UNKNOWN HELP TOPIC: nonexistent", result)
        self.assertIn("Available topics:", result)
        self.assertIn("setup", result)

    def test_all_topics_exist(self):
        """Test that all defined topics can be retrieved"""
        for topic_name in HELP_TOPICS.keys():
            result = get_help_topic(topic_name)
            self.assertIsNotNone(result)
            self.assertTrue(len(result) > 0)


class TestWizardSections(unittest.TestCase):
    """Test setup wizard section messages"""

    def test_welcome_message(self):
        """Test welcome message"""
        result = get_welcome_message()

        self.assertIn("F.U.C.K. INTERACTIVE SETUP WIZARD", result)
        self.assertIn("Welcome to F.U.C.K.", result)
        self.assertIn("This wizard will help you", result)
        self.assertIn("Press Enter to continue", result)

    def test_security_wizard_section(self):
        """Test security wizard section"""
        result = get_security_wizard_section()

        self.assertIn("STEP 1: SECURITY SETUP", result)
        self.assertIn("FUCK_GLOBAL_SALT", result)
        self.assertIn("FUCK_ENCRYPTION_KEY", result)
        self.assertIn("Do you already have encryption keys", result)

    def test_csv_wizard_section(self):
        """Test CSV wizard section"""
        result = get_csv_wizard_section()

        self.assertIn("STEP 2: CSV FILE PREPARATION", result)
        self.assertIn("Required columns:", result)
        self.assertIn("Date", result)
        self.assertIn("Amount", result)
        self.assertIn("Press Enter when you have", result)

    def test_category_wizard_section(self):
        """Test category wizard section"""
        result = get_category_wizard_section()

        self.assertIn("STEP 3: CATEGORY STRUCTURE", result)
        self.assertIn("Recommended category structure", result)
        self.assertIn("Groceries/Food", result)
        self.assertIn("Dining Out", result)

    def test_completion_wizard_section(self):
        """Test completion wizard section"""
        result = get_completion_wizard_section()

        self.assertIn("SETUP COMPLETE!", result)
        self.assertIn("PROCESS YOUR FIRST CSV", result)
        self.assertIn("VIEW YOUR DATA", result)
        self.assertIn("GENERATE REPORTS", result)
        self.assertIn("Happy budgeting", result)


class TestSuggestedCategories(unittest.TestCase):
    """Test suggested categories list"""

    def test_suggested_categories_not_empty(self):
        """Test that suggested categories list is not empty"""
        self.assertTrue(len(SUGGESTED_CATEGORIES) > 0)

    def test_suggested_categories_common_ones(self):
        """Test that common categories are in the list"""
        self.assertIn("Groceries/Food", SUGGESTED_CATEGORIES)
        self.assertIn("Utilities/Bills", SUGGESTED_CATEGORIES)
        self.assertIn("Entertainment", SUGGESTED_CATEGORIES)
        self.assertIn("Transportation", SUGGESTED_CATEGORIES)

    def test_suggested_categories_all_strings(self):
        """Test that all suggested categories are strings"""
        for category in SUGGESTED_CATEGORIES:
            self.assertIsInstance(category, str)
            self.assertTrue(len(category) > 0)


class TestHelpTopicsCompleteness(unittest.TestCase):
    """Test that help topics are comprehensive"""

    def test_all_topics_have_content(self):
        """Test that all topics have substantial content"""
        for topic_name, content in HELP_TOPICS.items():
            self.assertTrue(len(content) > 100, f"Topic '{topic_name}' seems too short")
            self.assertIn("="*80, content, f"Topic '{topic_name}' missing formatting")

    def test_setup_topic_has_all_sections(self):
        """Test that setup topic covers all necessary sections"""
        content = HELP_TOPICS["setup"]

        self.assertIn("PREPARE YOUR DATA", content)
        self.assertIn("SECURITY SETUP", content)
        self.assertIn("PROCESS YOUR FIRST CSV", content)
        self.assertIn("VIEW YOUR DATA", content)

    def test_security_topic_has_all_sections(self):
        """Test that security topic covers all necessary sections"""
        content = HELP_TOPICS["security"]

        self.assertIn("ENCRYPTION", content)
        self.assertIn("KEYS AND SALT", content)
        self.assertIn("BEST PRACTICES", content)
        self.assertIn("THREAT MODEL", content)

    def test_csv_format_topic_has_examples(self):
        """Test that CSV format topic includes bank examples"""
        content = HELP_TOPICS["csv-format"]

        self.assertIn("Chase", content)
        self.assertIn("Bank of America", content)
        self.assertIn("Wells Fargo", content)
        self.assertIn("EXAMPLE CSV", content)


if __name__ == '__main__':
    unittest.main()
