"""
Multi-LLM backend support for intelligent summarization
Supports GLM-5.1, OpenAI, Claude, DeepSeek, and more
"""

import urllib.request
import urllib.error
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from .config import Config


@dataclass
class SummaryResult:
    """Result from LLM summarization"""
    summary: str
    key_points: List[str]
    sentiment: str
    timeline: List[Dict[str, str]]
    sources_analysis: List[Dict[str, Any]]
    confidence: float


class LLMBackend:
    """Base LLM backend"""

    def __init__(self, config: Config):
        self.config = config
        self.api_key = config.get_api_key()
        self.timeout = config.get("llm", "timeout", default=60)

    def summarize(self, contents: List[Dict[str, Any]], query: str, language: str = "zh") -> SummaryResult:
        """Generate summary from contents"""
        raise NotImplementedError

    def _call_api(self, url: str, headers: Dict[str, str], data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Make API call"""
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode('utf-8'),
                headers={**headers, 'Content-Type': 'application/json'},
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                return json.loads(response.read().decode('utf-8'))
        except Exception as e:
            print(f"  ⚠️  LLM API error: {str(e)[:100]}")
            return None

    def _build_prompt(self, contents: List[Dict[str, Any]], query: str, language: str) -> str:
        """Build prompt for summarization"""
        lang_instruction = {
            "zh": "请用中文回答",
            "en": "Please answer in English",
            "ja": "日本語で答えてください",
            "ko": "한국어로 답변해 주세요"
        }.get(language, "Please answer in English")

        # Prepare content summary
        content_text = ""
        for i, item in enumerate(contents[:30], 1):  # Limit to top 30 items
            content_text += f"\n[{i}] Source: {item['source']}\n"
            content_text += f"Title: {item['title']}\n"
            content_text += f"Content: {item['content'][:300]}...\n"
            content_text += f"Score: {item['score']}, Credibility: {item['credibility_score']:.2f}\n"
            content_text += f"URL: {item['url']}\n"

        prompt = f"""You are an expert information synthesis analyst. Your task is to analyze multiple information sources and generate a comprehensive, structured summary.

{lang_instruction}

## Research Query
{query}

## Source Data
{content_text}

## Instructions
Please analyze the above information and provide:

1. **Executive Summary** (2-3 paragraphs): A comprehensive overview of the key findings
2. **Key Points** (5-8 bullet points): The most important insights and facts
3. **Sentiment Analysis**: Overall sentiment (Positive/Negative/Neutral/Mixed) with brief explanation
4. **Timeline**: Key events or developments in chronological order
5. **Source Credibility Assessment**: Brief analysis of source reliability

Format your response in Markdown. Be objective, factual, and comprehensive."""

        return prompt

    def _parse_response(self, text: str) -> SummaryResult:
        """Parse LLM response into structured result"""
        # Extract key points
        key_points = []
        lines = text.split('\n')
        in_key_points = False

        for line in lines:
            stripped = line.strip()
            if 'key point' in stripped.lower() or '要点' in stripped or '关键' in stripped:
                in_key_points = True
                continue
            if in_key_points:
                if stripped.startswith('- ') or stripped.startswith('* ') or stripped.startswith('• '):
                    point = stripped[2:].strip()
                    if point and len(point) > 10:
                        key_points.append(point)
                elif stripped and not stripped.startswith('#') and len(stripped) > 10 and len(key_points) < 8:
                    # Fallback for non-bullet points
                    pass
                elif stripped.startswith('#') and len(key_points) > 0:
                    in_key_points = False

        # Limit key points
        key_points = key_points[:8]

        # Determine sentiment
        sentiment = "Neutral"
        text_lower = text.lower()
        positive_words = ['positive', 'optimistic', 'bullish', 'good', 'great', 'excellent', '积极', '乐观', '正面']
        negative_words = ['negative', 'pessimistic', 'bearish', 'bad', 'poor', 'concerning', '消极', '悲观', '负面']

        pos_count = sum(1 for w in positive_words if w in text_lower)
        neg_count = sum(1 for w in negative_words if w in text_lower)

        if pos_count > neg_count + 2:
            sentiment = "Positive"
        elif neg_count > pos_count + 2:
            sentiment = "Negative"
        elif pos_count > 0 and neg_count > 0:
            sentiment = "Mixed"

        # Extract timeline (simplified)
        timeline = []
        import re
        date_pattern = r'(\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]\d{4})'
        for line in lines:
            dates = re.findall(date_pattern, line)
            if dates and len(line) > 20:
                timeline.append({
                    "date": dates[0],
                    "event": line.strip()[:200]
                })
                if len(timeline) >= 10:
                    break

        # Source analysis
        sources_analysis = []
        source_counts = {}
        for line in lines:
            for source in ['Reddit', 'HackerNews', 'GitHub', 'Zhihu', 'Bilibili', 'Juejin']:
                if source in line:
                    source_counts[source] = source_counts.get(source, 0) + 1

        for source, count in source_counts.items():
            sources_analysis.append({
                "source": source,
                "mentions": count,
                "reliability": "High" if source in ['GitHub', 'HackerNews'] else "Medium"
            })

        return SummaryResult(
            summary=text,
            key_points=key_points if key_points else ["No key points extracted"],
            sentiment=sentiment,
            timeline=timeline,
            sources_analysis=sources_analysis,
            confidence=0.85
        )


class GLM51Backend(LLMBackend):
    """GLM-5.1 backend (Zhipu AI)"""

    def summarize(self, contents: List[Dict[str, Any]], query: str, language: str = "zh") -> SummaryResult:
        """Generate summary using GLM-5.1"""
        if not self.api_key:
            return self._fallback_summary(contents, query, language)

        prompt = self._build_prompt(contents, query, language)

        api_base = self.config.get("llm", "api_base", default="https://open.bigmodel.cn/api/paas/v4/chat/completions")

        data = {
            "model": "glm-5.1",
            "messages": [
                {"role": "system", "content": "You are an expert information synthesis analyst."},
                {"role": "user", "content": prompt}
            ],
            "temperature": self.config.get("llm", "temperature", default=0.7),
            "max_tokens": self.config.get("llm", "max_tokens", default=4096)
        }

        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        response = self._call_api(api_base, headers, data)

        if response and 'choices' in response:
            text = response['choices'][0]['message']['content']
            return self._parse_response(text)

        return self._fallback_summary(contents, query, language)

    def _fallback_summary(self, contents: List[Dict[str, Any]], query: str, language: str) -> SummaryResult:
        """Generate fallback summary without LLM"""
        translations = {
            "zh": {
                "summary": f"## {query} - 信息聚合摘要\n\n",
                "key_points_label": "### 关键要点",
                "sources_label": "### 数据来源分析",
                "sentiment_label": "### 情感分析",
                "timeline_label": "### 时间线",
                "no_api": "> ⚠️ 未配置API密钥，使用本地摘要生成。",
                "total_items": "共收集到",
                "items": "条信息",
                "top_sources": "主要来源",
                "sentiment_neutral": "整体情感倾向：中性"
            },
            "en": {
                "summary": f"## {query} - Information Synthesis Summary\n\n",
                "key_points_label": "### Key Points",
                "sources_label": "### Source Analysis",
                "sentiment_label": "### Sentiment Analysis",
                "timeline_label": "### Timeline",
                "no_api": "> ⚠️ No API key configured. Using local summary generation.",
                "total_items": "Collected",
                "items": "items",
                "top_sources": "Top Sources",
                "sentiment_neutral": "Overall sentiment: Neutral"
            }
        }
        lang = translations.get(language, translations["en"])

        summary_text = lang["summary"]
        summary_text += f"{lang['no_api']}\n\n"
        summary_text += f"{lang['total_items']} **{len(contents)}** {lang['items']}.\n\n"

        # Source distribution
        source_counts = {}
        for item in contents:
            source = item.get('source', 'Unknown')
            source_counts[source] = source_counts.get(source, 0) + 1

        summary_text += f"{lang['sources_label']}\n"
        for source, count in sorted(source_counts.items(), key=lambda x: -x[1]):
            summary_text += f"- **{source}**: {count} items\n"

        summary_text += f"\n{lang['key_points_label']}\n"
        for i, item in enumerate(contents[:10], 1):
            title = item.get('title', '')[:100]
            if title:
                summary_text += f"{i}. [{item.get('source', '?')}] {title}\n"

        summary_text += f"\n{lang['sentiment_label']}\n"
        summary_text += f"{lang['sentiment_neutral']}\n"

        return SummaryResult(
            summary=summary_text,
            key_points=[item.get('title', '') for item in contents[:8] if item.get('title')],
            sentiment="Neutral",
            timeline=[],
            sources_analysis=[{"source": s, "mentions": c, "reliability": "Medium"} for s, c in source_counts.items()],
            confidence=0.6
        )


class OpenAIBackend(LLMBackend):
    """OpenAI-compatible backend"""

    def summarize(self, contents: List[Dict[str, Any]], query: str, language: str = "zh") -> SummaryResult:
        """Generate summary using OpenAI-compatible API"""
        if not self.api_key:
            return self._fallback_summary(contents, query, language)

        prompt = self._build_prompt(contents, query, language)

        api_base = self.config.get("llm", "api_base", default="https://api.openai.com/v1/chat/completions")

        data = {
            "model": self.config.get("llm", "model", default="gpt-3.5-turbo"),
            "messages": [
                {"role": "system", "content": "You are an expert information synthesis analyst."},
                {"role": "user", "content": prompt}
            ],
            "temperature": self.config.get("llm", "temperature", default=0.7),
            "max_tokens": self.config.get("llm", "max_tokens", default=4096)
        }

        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        response = self._call_api(api_base, headers, data)

        if response and 'choices' in response:
            text = response['choices'][0]['message']['content']
            return self._parse_response(text)

        return self._fallback_summary(contents, query, language)

    def _fallback_summary(self, contents, query, language):
        # Same fallback as GLM
        return GLM51Backend(self.config)._fallback_summary(contents, query, language)


class LLMManager:
    """Manages LLM backends"""

    def __init__(self, config: Config):
        self.config = config
        self.provider = config.get("llm", "provider", default="glm-5.1")

    def get_backend(self) -> LLMBackend:
        """Get appropriate LLM backend"""
        if self.provider in ["glm-5.1", "glm", "zhipu"]:
            return GLM51Backend(self.config)
        else:
            return OpenAIBackend(self.config)

    def summarize(self, contents: List[Dict[str, Any]], query: str, language: str = "zh") -> SummaryResult:
        """Generate summary"""
        backend = self.get_backend()
        return backend.summarize(contents, query, language)
