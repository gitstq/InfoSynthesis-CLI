"""
Output formatting and export engine
Supports Markdown, HTML, JSON, and PDF formats
"""

import json
import html as html_module
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path

from .llm import SummaryResult


class OutputFormatter:
    """Format and export synthesis results"""

    def __init__(self, language: str = "zh"):
        self.language = language
        self.translations = self._get_translations()

    def _get_translations(self) -> Dict[str, Dict[str, str]]:
        """Get translations for different languages"""
        return {
            "zh": {
                "title": "🔍 信息聚合与智能摘要报告",
                "query": "📌 研究主题",
                "generated_at": "⏰ 生成时间",
                "executive_summary": "📋 执行摘要",
                "key_points": "💡 关键要点",
                "sentiment": "😊 情感分析",
                "timeline": "📅 时间线",
                "sources": "📊 数据来源分析",
                "source_items": "📑 原始数据",
                "confidence": "🎯 置信度",
                "total_items": "信息总数",
                "top_sources": "主要来源",
                "reliability": "可信度",
                "mentions": "提及次数",
                "positive": "积极",
                "negative": "消极",
                "neutral": "中性",
                "mixed": "混合",
            },
            "zh_tw": {
                "title": "🔍 資訊聚合與智慧摘要報告",
                "query": "📌 研究主題",
                "generated_at": "⏰ 生成時間",
                "executive_summary": "📋 執行摘要",
                "key_points": "💡 關鍵要點",
                "sentiment": "😊 情感分析",
                "timeline": "📅 時間線",
                "sources": "📊 資料來源分析",
                "source_items": "📑 原始資料",
                "confidence": "🎯 置信度",
                "total_items": "資訊總數",
                "top_sources": "主要來源",
                "reliability": "可信度",
                "mentions": "提及次數",
                "positive": "積極",
                "negative": "消極",
                "neutral": "中性",
                "mixed": "混合",
            },
            "en": {
                "title": "🔍 Information Synthesis & Intelligent Summary Report",
                "query": "📌 Research Topic",
                "generated_at": "⏰ Generated At",
                "executive_summary": "📋 Executive Summary",
                "key_points": "💡 Key Points",
                "sentiment": "😊 Sentiment Analysis",
                "timeline": "📅 Timeline",
                "sources": "📊 Source Analysis",
                "source_items": "📑 Source Items",
                "confidence": "🎯 Confidence",
                "total_items": "Total Items",
                "top_sources": "Top Sources",
                "reliability": "Reliability",
                "mentions": "Mentions",
                "positive": "Positive",
                "negative": "Negative",
                "neutral": "Neutral",
                "mixed": "Mixed",
            },
            "ja": {
                "title": "🔍 情報集約とインテリジェント要約レポート",
                "query": "📌 研究テーマ",
                "generated_at": "⏰ 生成時間",
                "executive_summary": "📋 エグゼクティブサマリー",
                "key_points": "💡 重要ポイント",
                "sentiment": "😊 感情分析",
                "timeline": "📅 タイムライン",
                "sources": "📊 情報源分析",
                "source_items": "📑 ソースデータ",
                "confidence": "🎯 信頼度",
                "total_items": "総項目数",
                "top_sources": "主要ソース",
                "reliability": "信頼性",
                "mentions": "言及回数",
                "positive": "ポジティブ",
                "negative": "ネガティブ",
                "neutral": "中立",
                "mixed": "混合",
            },
            "ko": {
                "title": "🔍 정보 집약 및 지능형 요약 보고서",
                "query": "📌 연구 주제",
                "generated_at": "⏰ 생성 시간",
                "executive_summary": "📋 요약",
                "key_points": "💡 핵심 포인트",
                "sentiment": "😊 감정 분석",
                "timeline": "📅 타임라인",
                "sources": "📊 출처 분석",
                "source_items": "📑 원본 데이터",
                "confidence": "🎯 신뢰도",
                "total_items": "총 항목",
                "top_sources": "주요 출처",
                "reliability": "신뢰성",
                "mentions": "언급 횟수",
                "positive": "긍정적",
                "negative": "부정적",
                "neutral": "중립",
                "mixed": "혼합",
            },
            "es": {
                "title": "🔍 Informe de Síntesis de Información y Resumen Inteligente",
                "query": "📌 Tema de Investigación",
                "generated_at": "⏰ Generado En",
                "executive_summary": "📋 Resumen Ejecutivo",
                "key_points": "💡 Puntos Clave",
                "sentiment": "😊 Análisis de Sentimiento",
                "timeline": "📅 Cronología",
                "sources": "📊 Análisis de Fuentes",
                "source_items": "📑 Elementos de Fuente",
                "confidence": "🎯 Confianza",
                "total_items": "Total de Elementos",
                "top_sources": "Principales Fuentes",
                "reliability": "Fiabilidad",
                "mentions": "Menciones",
                "positive": "Positivo",
                "negative": "Negativo",
                "neutral": "Neutral",
                "mixed": "Mixto",
            }
        }

    def _t(self, key: str) -> str:
        """Get translation"""
        translations = self.translations.get(self.language, self.translations["en"])
        return translations.get(key, key)

    def format_markdown(self, result: SummaryResult, query: str, items: List[Dict[str, Any]]) -> str:
        """Format as Markdown"""
        t = self._t
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        md = f"""# {t('title')}

> **{t('query')}**: {query}
>
> **{t('generated_at')}**: {now}

---

## {t('executive_summary')}

{result.summary}

---

## {t('key_points')}

"""
        for i, point in enumerate(result.key_points, 1):
            md += f"{i}. {point}\n"

        md += f"""
---

## {t('sentiment')}

**{result.sentiment}**

---

## {t('sources')}

| {t('top_sources')} | {t('mentions')} | {t('reliability')} |
|---|---|---|
"""
        for src in result.sources_analysis:
            md += f"| {src['source']} | {src['mentions']} | {src['reliability']} |\n"

        if result.timeline:
            md += f"""
---

## {t('timeline')}

"""
            for event in result.timeline[:15]:
                md += f"- **{event['date']}**: {event['event'][:150]}\n"

        md += f"""
---

## {t('source_items')}

> {t('total_items')}: {len(items)}

"""
        for i, item in enumerate(items[:50], 1):
            title = item.get('title', 'Untitled')[:120]
            source = item.get('source', 'Unknown')
            url = item.get('url', '')
            score = item.get('score', 0)
            credibility = item.get('credibility_score', 0)

            md += f"{i}. **[{source}]** [{title}]({url}) - ⭐ {score} | 🔒 {credibility:.2f}\n"

        md += f"""
---

*Generated by InfoSynthesis-CLI v1.0.0*
"""
        return md

    def format_html(self, result: SummaryResult, query: str, items: List[Dict[str, Any]]) -> str:
        """Format as HTML"""
        t = self._t
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Convert markdown summary to HTML (basic)
        summary_html = result.summary.replace('\n\n', '</p><p>').replace('\n', '<br>')
        summary_html = f"<p>{summary_html}</p>"

        html_content = f"""<!DOCTYPE html>
<html lang="{self.language}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html_module.escape(t('title'))}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; line-height: 1.6; color: #333; }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 30px; border-left: 4px solid #3498db; padding-left: 15px; }}
        blockquote {{ background: #f8f9fa; border-left: 4px solid #3498db; padding: 15px; margin: 0; }}
        table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
        th {{ background: #3498db; color: white; }}
        tr:nth-child(even) {{ background: #f8f9fa; }}
        .item {{ padding: 8px; border-bottom: 1px solid #eee; }}
        .item a {{ color: #3498db; text-decoration: none; }}
        .item a:hover {{ text-decoration: underline; }}
        .sentiment {{ font-size: 1.2em; font-weight: bold; padding: 10px; border-radius: 5px; display: inline-block; }}
        .sentiment-positive {{ background: #d4edda; color: #155724; }}
        .sentiment-negative {{ background: #f8d7da; color: #721c24; }}
        .sentiment-neutral {{ background: #e2e3e5; color: #383d41; }}
        .sentiment-mixed {{ background: #fff3cd; color: #856404; }}
        .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; color: #666; font-size: 0.9em; text-align: center; }}
    </style>
</head>
<body>
    <h1>🔍 {html_module.escape(t('title'))}</h1>

    <blockquote>
        <strong>{html_module.escape(t('query'))}:</strong> {html_module.escape(query)}<br>
        <strong>{html_module.escape(t('generated_at'))}:</strong> {now}
    </blockquote>

    <h2>📋 {html_module.escape(t('executive_summary'))}</h2>
    {summary_html}

    <h2>💡 {html_module.escape(t('key_points'))}</h2>
    <ol>
"""
        for point in result.key_points:
            html_content += f"        <li>{html_module.escape(point)}</li>\n"

        sentiment_class = f"sentiment-{result.sentiment.lower()}"
        html_content += f"""    </ol>

    <h2>😊 {html_module.escape(t('sentiment'))}</h2>
    <span class="sentiment {sentiment_class}">{html_module.escape(result.sentiment)}</span>

    <h2>📊 {html_module.escape(t('sources'))}</h2>
    <table>
        <tr><th>{html_module.escape(t('top_sources'))}</th><th>{html_module.escape(t('mentions'))}</th><th>{html_module.escape(t('reliability'))}</th></tr>
"""
        for src in result.sources_analysis:
            html_content += f"        <tr><td>{html_module.escape(src['source'])}</td><td>{src['mentions']}</td><td>{html_module.escape(src['reliability'])}</td></tr>\n"

        html_content += """    </table>

    <h2>📑 Source Items</h2>
"""
        for i, item in enumerate(items[:50], 1):
            title = html_module.escape(item.get('title', 'Untitled')[:120])
            source = html_module.escape(item.get('source', 'Unknown'))
            url = html_module.escape(item.get('url', ''))
            score = item.get('score', 0)
            credibility = item.get('credibility_score', 0)

            html_content += f"""    <div class="item">
        {i}. <strong>[{source}]</strong> <a href="{url}" target="_blank">{title}</a>
        - ⭐ {score} | 🔒 {credibility:.2f}
    </div>
"""

        html_content += f"""
    <div class="footer">
        Generated by InfoSynthesis-CLI v1.0.0 | {html_module.escape(t('total_items'))}: {len(items)}
    </div>
</body>
</html>"""
        return html_content

    def format_json(self, result: SummaryResult, query: str, items: List[Dict[str, Any]]) -> str:
        """Format as JSON"""
        data = {
            "meta": {
                "query": query,
                "generated_at": datetime.now().isoformat(),
                "language": self.language,
                "version": "1.0.0"
            },
            "summary": {
                "text": result.summary,
                "key_points": result.key_points,
                "sentiment": result.sentiment,
                "confidence": result.confidence
            },
            "timeline": result.timeline,
            "sources_analysis": result.sources_analysis,
            "items": items
        }
        return json.dumps(data, indent=2, ensure_ascii=False)

    def save(self, result: SummaryResult, query: str, items: List[Dict[str, Any]],
             output_path: str, format_type: str = "markdown") -> str:
        """Save output to file"""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        if format_type == "markdown":
            content = self.format_markdown(result, query, items)
            if not path.suffix:
                path = path.with_suffix('.md')
        elif format_type == "html":
            content = self.format_html(result, query, items)
            if not path.suffix:
                path = path.with_suffix('.html')
        elif format_type == "json":
            content = self.format_json(result, query, items)
            if not path.suffix:
                path = path.with_suffix('.json')
        else:
            content = self.format_markdown(result, query, items)

        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)

        return str(path)
