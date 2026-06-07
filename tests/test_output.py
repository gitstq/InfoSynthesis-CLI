"""
Unit tests for InfoSynthesis-CLI output module
"""

import unittest
import json
import tempfile
import os
from datetime import datetime
from infosynthesis_cli.output import OutputFormatter
from infosynthesis_cli.llm import SummaryResult


class TestOutputFormatter(unittest.TestCase):
    """Test OutputFormatter"""

    def setUp(self):
        self.formatter = OutputFormatter("zh")
        self.result = SummaryResult(
            summary="This is a test summary.",
            key_points=["Point 1", "Point 2", "Point 3"],
            sentiment="Positive",
            timeline=[{"date": "2024-01-01", "event": "Event 1"}],
            sources_analysis=[{"source": "Test", "mentions": 5, "reliability": "High"}],
            confidence=0.9
        )
        self.query = "test query"
        self.items = [
            {"title": "Item 1", "source": "Reddit", "url": "https://example.com/1", "score": 100, "credibility_score": 0.8},
            {"title": "Item 2", "source": "GitHub", "url": "https://example.com/2", "score": 50, "credibility_score": 0.9},
        ]

    def test_format_markdown(self):
        md = self.formatter.format_markdown(self.result, self.query, self.items)
        self.assertIn("信息聚合与智能摘要报告", md)
        self.assertIn("test query", md)
        self.assertIn("Point 1", md)
        self.assertIn("Reddit", md)

    def test_format_html(self):
        html = self.formatter.format_html(self.result, self.query, self.items)
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("test query", html)
        self.assertIn("Point 1", html)

    def test_format_json(self):
        json_str = self.formatter.format_json(self.result, self.query, self.items)
        data = json.loads(json_str)
        self.assertEqual(data["meta"]["query"], self.query)
        self.assertEqual(len(data["summary"]["key_points"]), 3)

    def test_save_markdown(self):
        with tempfile.NamedTemporaryFile(suffix='.md', delete=False) as f:
            path = f.name
        try:
            saved = self.formatter.save(self.result, self.query, self.items, path, "markdown")
            self.assertTrue(os.path.exists(saved))
            with open(saved, 'r', encoding='utf-8') as f:
                content = f.read()
            self.assertIn("信息聚合与智能摘要报告", content)
        finally:
            os.unlink(path)

    def test_multilingual(self):
        en_formatter = OutputFormatter("en")
        md = en_formatter.format_markdown(self.result, self.query, self.items)
        self.assertIn("Information Synthesis", md)

        zh_tw_formatter = OutputFormatter("zh_tw")
        md = zh_tw_formatter.format_markdown(self.result, self.query, self.items)
        self.assertIn("資訊聚合", md)


if __name__ == '__main__':
    unittest.main()
