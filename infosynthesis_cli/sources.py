"""
Multi-source information aggregation engine
Supports Reddit, HackerNews, GitHub, Zhihu, Bilibili, Juejin, and more
"""

import urllib.request
import urllib.parse
import urllib.error
import json
import re
import html
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ContentItem:
    """Represents a single content item from any source"""
    title: str
    content: str
    url: str
    source: str
    author: str
    score: int
    created_at: datetime
    comments_count: int
    tags: List[str]
    credibility_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "content": self.content[:500] if self.content else "",
            "url": self.url,
            "source": self.source,
            "author": self.author,
            "score": self.score,
            "created_at": self.created_at.isoformat(),
            "comments_count": self.comments_count,
            "tags": self.tags,
            "credibility_score": self.credibility_score
        }


class BaseSource:
    """Base class for all information sources"""

    def __init__(self, name: str, enabled: bool = True, limit: int = 25):
        self.name = name
        self.enabled = enabled
        self.limit = limit
        self.timeout = 15

    def _fetch(self, url: str, headers: Optional[Dict[str, str]] = None) -> Optional[str]:
        """Fetch URL content with error handling"""
        default_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.0'
        }
        if headers:
            default_headers.update(headers)

        try:
            req = urllib.request.Request(url, headers=default_headers)
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                return response.read().decode('utf-8', errors='ignore')
        except Exception as e:
            print(f"  ⚠️  {self.name} fetch error: {str(e)[:80]}")
            return None

    def search(self, query: str) -> List[ContentItem]:
        """Search for content - to be implemented by subclasses"""
        raise NotImplementedError

    def _calculate_credibility(self, score: int, comments: int, source_weight: float = 1.0) -> float:
        """Calculate credibility score based on engagement metrics"""
        engagement = score + comments * 2
        if engagement > 1000:
            base = 0.9
        elif engagement > 500:
            base = 0.8
        elif engagement > 100:
            base = 0.7
        elif engagement > 50:
            base = 0.6
        else:
            base = 0.5
        return min(base * source_weight, 1.0)


class RedditSource(BaseSource):
    """Reddit search via Pushshift API"""

    def __init__(self, enabled: bool = True, limit: int = 25):
        super().__init__("Reddit", enabled, limit)

    def search(self, query: str) -> List[ContentItem]:
        """Search Reddit posts"""
        items = []
        try:
            # Use Reddit's JSON API via search
            encoded_query = urllib.parse.quote(query)
            url = f"https://www.reddit.com/search.json?q={encoded_query}&sort=relevance&limit={self.limit}"

            data = self._fetch(url)
            if not data:
                return items

            json_data = json.loads(data)
            posts = json_data.get("data", {}).get("children", [])

            for post in posts[:self.limit]:
                pdata = post.get("data", {})
                title = html.unescape(pdata.get("title", ""))
                content = html.unescape(pdata.get("selftext", "") or "")
                url_post = f"https://reddit.com{pdata.get('permalink', '')}"
                author = pdata.get("author", "unknown")
                score = pdata.get("score", 0)
                created_utc = pdata.get("created_utc", 0)
                comments = pdata.get("num_comments", 0)
                subreddit = pdata.get("subreddit", "")

                created_at = datetime.fromtimestamp(created_utc) if created_utc else datetime.now()

                item = ContentItem(
                    title=title,
                    content=content,
                    url=url_post,
                    source="Reddit",
                    author=author,
                    score=score,
                    created_at=created_at,
                    comments_count=comments,
                    tags=[subreddit],
                    credibility_score=self._calculate_credibility(score, comments, 0.85)
                )
                items.append(item)

        except Exception as e:
            print(f"  ⚠️  Reddit error: {str(e)[:80]}")

        return items


class HackerNewsSource(BaseSource):
    """HackerNews search via Algolia API"""

    def __init__(self, enabled: bool = True, limit: int = 30):
        super().__init__("HackerNews", enabled, limit)

    def search(self, query: str) -> List[ContentItem]:
        """Search HackerNews"""
        items = []
        try:
            encoded_query = urllib.parse.quote(query)
            url = f"https://hn.algolia.com/api/v1/search?query={encoded_query}&hitsPerPage={self.limit}&tags=story"

            data = self._fetch(url)
            if not data:
                return items

            json_data = json.loads(data)
            hits = json_data.get("hits", [])

            for hit in hits[:self.limit]:
                title = html.unescape(hit.get("title", "") or hit.get("story_title", ""))
                content = html.unescape(hit.get("text", "") or "")
                url_post = hit.get("url", f"https://news.ycombinator.com/item?id={hit.get('objectID', '')}")
                author = hit.get("author", "unknown")
                points = hit.get("points", 0)
                created_at = hit.get("created_at", "")
                comments = hit.get("num_comments", 0)
                tags = hit.get("_tags", [])

                try:
                    created_dt = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%S.%fZ") if created_at else datetime.now()
                except ValueError:
                    try:
                        created_dt = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ") if created_at else datetime.now()
                    except ValueError:
                        created_dt = datetime.now()

                item = ContentItem(
                    title=title,
                    content=content,
                    url=url_post,
                    source="HackerNews",
                    author=author,
                    score=points,
                    created_at=created_dt,
                    comments_count=comments,
                    tags=[t for t in tags if isinstance(t, str)][:5],
                    credibility_score=self._calculate_credibility(points, comments, 0.9)
                )
                items.append(item)

        except Exception as e:
            print(f"  ⚠️  HackerNews error: {str(e)[:80]}")

        return items


class GitHubSource(BaseSource):
    """GitHub search via public API"""

    def __init__(self, enabled: bool = True, limit: int = 20):
        super().__init__("GitHub", enabled, limit)

    def search(self, query: str) -> List[ContentItem]:
        """Search GitHub repositories and issues"""
        items = []
        try:
            encoded_query = urllib.parse.quote(query)
            url = f"https://api.github.com/search/repositories?q={encoded_query}&sort=stars&order=desc&per_page={self.limit}"

            data = self._fetch(url, headers={
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'InfoSynthesis-CLI/1.0'
            })
            if not data:
                return items

            json_data = json.loads(data)
            repos = json_data.get("items", [])

            for repo in repos[:self.limit]:
                title = repo.get("full_name", "")
                content = repo.get("description", "") or ""
                url_repo = repo.get("html_url", "")
                author = repo.get("owner", {}).get("login", "unknown")
                stars = repo.get("stargazers_count", 0)
                forks = repo.get("forks_count", 0)
                issues = repo.get("open_issues_count", 0)
                language = repo.get("language", "")
                created_at = repo.get("created_at", "")
                updated_at = repo.get("updated_at", "")

                try:
                    created_dt = datetime.strptime(updated_at or created_at, "%Y-%m-%dT%H:%M:%SZ") if (updated_at or created_at) else datetime.now()
                except ValueError:
                    created_dt = datetime.now()

                score = stars + forks * 2

                item = ContentItem(
                    title=title,
                    content=content,
                    url=url_repo,
                    source="GitHub",
                    author=author,
                    score=score,
                    created_at=created_dt,
                    comments_count=issues,
                    tags=[language] if language else [],
                    credibility_score=self._calculate_credibility(stars, forks, 0.95)
                )
                items.append(item)

        except Exception as e:
            print(f"  ⚠️  GitHub error: {str(e)[:80]}")

        return items


class ZhihuSource(BaseSource):
    """Zhihu search"""

    def __init__(self, enabled: bool = True, limit: int = 20):
        super().__init__("Zhihu", enabled, limit)

    def search(self, query: str) -> List[ContentItem]:
        """Search Zhihu"""
        items = []
        try:
            encoded_query = urllib.parse.quote(query)
            url = f"https://www.zhihu.com/api/v4/search_v3?gk_version=gz-gaokao&q={encoded_query}&t=general"

            data = self._fetch(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://www.zhihu.com/search'
            })
            if not data:
                return items

            json_data = json.loads(data)
            results = json_data.get("data", [])

            for result in results[:self.limit]:
                obj = result.get("object", {})
                title = html.unescape(obj.get("title", "").replace('<em>', '').replace('</em>', ''))
                content = html.unescape(obj.get("excerpt", "").replace('<em>', '').replace('</em>', ''))
                url_post = obj.get("url", "")
                author = obj.get("author", {}).get("name", "unknown")
                voteup = obj.get("voteup_count", 0)
                comments = obj.get("comment_count", 0)

                item = ContentItem(
                    title=title,
                    content=content,
                    url=url_post,
                    source="Zhihu",
                    author=author,
                    score=voteup,
                    created_at=datetime.now(),
                    comments_count=comments,
                    tags=["zhihu"],
                    credibility_score=self._calculate_credibility(voteup, comments, 0.8)
                )
                items.append(item)

        except Exception as e:
            print(f"  ⚠️  Zhihu error: {str(e)[:80]}")

        return items


class BilibiliSource(BaseSource):
    """Bilibili search"""

    def __init__(self, enabled: bool = True, limit: int = 15):
        super().__init__("Bilibili", enabled, limit)

    def search(self, query: str) -> List[ContentItem]:
        """Search Bilibili"""
        items = []
        try:
            encoded_query = urllib.parse.quote(query)
            url = f"https://api.bilibili.com/x/web-interface/search/type?keyword={encoded_query}&search_type=video&page=1&pagesize={self.limit}"

            data = self._fetch(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://search.bilibili.com'
            })
            if not data:
                return items

            json_data = json.loads(data)
            results = json_data.get("data", {}).get("result", [])

            for result in results[:self.limit]:
                title = html.unescape(result.get("title", "").replace('<em class="keyword">', '').replace('</em>', ''))
                content = html.unescape(result.get("description", ""))
                bvid = result.get("bvid", "")
                url_video = f"https://bilibili.com/video/{bvid}" if bvid else ""
                author = result.get("author", "unknown")
                play = result.get("play", 0)
                if isinstance(play, str):
                    play = int(play) if play.isdigit() else 0
                danmaku = result.get("danmaku", 0)
                if isinstance(danmaku, str):
                    danmaku = int(danmaku) if danmaku.isdigit() else 0

                item = ContentItem(
                    title=title,
                    content=content,
                    url=url_video,
                    source="Bilibili",
                    author=author,
                    score=play,
                    created_at=datetime.now(),
                    comments_count=danmaku,
                    tags=[result.get("typename", "")],
                    credibility_score=self._calculate_credibility(play, danmaku, 0.75)
                )
                items.append(item)

        except Exception as e:
            print(f"  ⚠️  Bilibili error: {str(e)[:80]}")

        return items


class JuejinSource(BaseSource):
    """Juejin (掘金) search"""

    def __init__(self, enabled: bool = True, limit: int = 20):
        super().__init__("Juejin", enabled, limit)

    def search(self, query: str) -> List[ContentItem]:
        """Search Juejin articles"""
        items = []
        try:
            encoded_query = urllib.parse.quote(query)
            url = f"https://api.juejin.cn/search_api/v1/search?query={encoded_query}&page=0&page_size={self.limit}"

            data = self._fetch(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://juejin.cn/search'
            })
            if not data:
                return items

            json_data = json.loads(data)
            results = json_data.get("data", [])

            for result in results[:self.limit]:
                doc = result.get("result_model", {}).get("article_info", {})
                title = html.unescape(doc.get("title", ""))
                content = html.unescape(doc.get("brief_content", ""))
                article_id = doc.get("article_id", "")
                url_article = f"https://juejin.cn/post/{article_id}" if article_id else ""
                author_info = result.get("result_model", {}).get("user_info", {})
                author = author_info.get("user_name", "unknown")
                digg = doc.get("digg_count", 0)
                comments = doc.get("comment_count", 0)
                tags_info = result.get("result_model", {}).get("tags", [])
                tags = [t.get("tag_name", "") for t in tags_info]

                item = ContentItem(
                    title=title,
                    content=content,
                    url=url_article,
                    source="Juejin",
                    author=author,
                    score=digg,
                    created_at=datetime.now(),
                    comments_count=comments,
                    tags=tags,
                    credibility_score=self._calculate_credibility(digg, comments, 0.82)
                )
                items.append(item)

        except Exception as e:
            print(f"  ⚠️  Juejin error: {str(e)[:80]}")

        return items


class SourceManager:
    """Manages all information sources"""

    SOURCE_MAP = {
        "reddit": RedditSource,
        "hackernews": HackerNewsSource,
        "github": GitHubSource,
        "zhihu": ZhihuSource,
        "bilibili": BilibiliSource,
        "juejin": JuejinSource,
    }

    def __init__(self, config: Dict[str, Any]):
        self.sources: Dict[str, BaseSource] = {}
        self.config = config
        self._init_sources()

    def _init_sources(self):
        """Initialize enabled sources"""
        sources_config = self.config.get("sources", {})
        enabled_sources = sources_config.get("enabled", [])

        for source_name, source_class in self.SOURCE_MAP.items():
            source_cfg = sources_config.get(source_name, {})
            is_enabled = source_name in enabled_sources and source_cfg.get("enabled", True)
            limit = source_cfg.get("limit", 25)

            if is_enabled:
                self.sources[source_name] = source_class(enabled=True, limit=limit)

    def search_all(self, query: str) -> List[ContentItem]:
        """Search all enabled sources"""
        all_items = []
        total_sources = len(self.sources)

        print(f"\n🔍 Searching across {total_sources} sources...")

        for i, (name, source) in enumerate(self.sources.items(), 1):
            print(f"  [{i}/{total_sources}] Searching {name}...", end=" ")
            try:
                items = source.search(query)
                print(f"✓ Found {len(items)} items")
                all_items.extend(items)
            except Exception as e:
                print(f"✗ Error: {str(e)[:60]}")

        # Sort by credibility score descending
        all_items.sort(key=lambda x: x.credibility_score, reverse=True)
        return all_items

    def deduplicate(self, items: List[ContentItem], threshold: float = 0.75) -> List[ContentItem]:
        """Remove duplicate/similar items using simple similarity"""
        if not items:
            return items

        unique_items = [items[0]]

        for item in items[1:]:
            is_duplicate = False
            for existing in unique_items:
                similarity = self._calculate_similarity(item.title, existing.title)
                if similarity >= threshold:
                    is_duplicate = True
                    # Keep the one with higher credibility
                    if item.credibility_score > existing.credibility_score:
                        existing.title = item.title
                        existing.content = item.content
                        existing.credibility_score = item.credibility_score
                        existing.score = max(existing.score, item.score)
                    break

            if not is_duplicate:
                unique_items.append(item)

        return unique_items

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity using Jaccard similarity on words"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union) if union else 0.0
