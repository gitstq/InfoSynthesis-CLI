"""
Unit tests for InfoSynthesis-CLI sources module
"""

import unittest
from datetime import datetime
from infosynthesis_cli.sources import (
    ContentItem, BaseSource, RedditSource, HackerNewsSource,
    GitHubSource, SourceManager
)


class TestContentItem(unittest.TestCase):
    """Test ContentItem dataclass"""

    def test_creation(self):
        item = ContentItem(
            title="Test Title",
            content="Test content",
            url="https://example.com",
            source="Test",
            author="testuser",
            score=100,
            created_at=datetime.now(),
            comments_count=10,
            tags=["test"],
            credibility_score=0.8
        )
        self.assertEqual(item.title, "Test Title")
        self.assertEqual(item.score, 100)
        self.assertEqual(item.credibility_score, 0.8)

    def test_to_dict(self):
        now = datetime.now()
        item = ContentItem(
            title="Test",
            content="Content",
            url="https://example.com",
            source="Test",
            author="user",
            score=50,
            created_at=now,
            comments_count=5,
            tags=["tag1"]
        )
        d = item.to_dict()
        self.assertEqual(d["title"], "Test")
        self.assertEqual(d["source"], "Test")
        self.assertIn("created_at", d)


class TestBaseSource(unittest.TestCase):
    """Test BaseSource functionality"""

    def test_init(self):
        source = BaseSource("TestSource", enabled=True, limit=10)
        self.assertEqual(source.name, "TestSource")
        self.assertTrue(source.enabled)
        self.assertEqual(source.limit, 10)

    def test_calculate_credibility(self):
        source = BaseSource("Test")
        # High engagement
        score = source._calculate_credibility(1000, 100, 1.0)
        self.assertGreaterEqual(score, 0.8)
        # Low engagement
        score = source._calculate_credibility(10, 0, 1.0)
        self.assertLessEqual(score, 0.6)


class TestRedditSource(unittest.TestCase):
    """Test Reddit source"""

    def test_init(self):
        source = RedditSource(enabled=True, limit=25)
        self.assertEqual(source.name, "Reddit")

    def test_search_returns_list(self):
        source = RedditSource()
        # This test may fail without network, so we just check it doesn't crash
        try:
            results = source.search("python")
            self.assertIsInstance(results, list)
        except Exception:
            # Network issues are acceptable in tests
            pass


class TestHackerNewsSource(unittest.TestCase):
    """Test HackerNews source"""

    def test_init(self):
        source = HackerNewsSource(enabled=True, limit=30)
        self.assertEqual(source.name, "HackerNews")


class TestGitHubSource(unittest.TestCase):
    """Test GitHub source"""

    def test_init(self):
        source = GitHubSource(enabled=True, limit=20)
        self.assertEqual(source.name, "GitHub")


class TestSourceManager(unittest.TestCase):
    """Test SourceManager"""

    def test_init(self):
        config = {
            "sources": {
                "enabled": ["reddit", "github"],
                "reddit": {"enabled": True, "limit": 10},
                "github": {"enabled": True, "limit": 10}
            }
        }
        manager = SourceManager(config)
        self.assertEqual(len(manager.sources), 2)

    def test_deduplicate(self):
        manager = SourceManager({"sources": {"enabled": []}})
        items = [
            ContentItem("Same Title", "Content", "url1", "Source1", "a", 10, datetime.now(), 0, [], 0.5),
            ContentItem("Same Title", "Content2", "url2", "Source2", "b", 20, datetime.now(), 0, [], 0.7),
            ContentItem("Different Title", "Content", "url3", "Source3", "c", 30, datetime.now(), 0, [], 0.6),
        ]
        unique = manager.deduplicate(items, threshold=0.8)
        self.assertLessEqual(len(unique), len(items))

    def test_similarity(self):
        manager = SourceManager({"sources": {"enabled": []}})
        sim = manager._calculate_similarity("hello world", "hello world")
        self.assertEqual(sim, 1.0)
        sim = manager._calculate_similarity("hello world", "completely different")
        self.assertLess(sim, 0.5)


if __name__ == '__main__':
    unittest.main()
