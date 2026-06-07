"""
Command-line interface for InfoSynthesis-CLI
"""

import sys
import argparse
import time
from pathlib import Path
from typing import Optional

from . import __version__
from .config import Config
from .sources import SourceManager
from .llm import LLMManager
from .output import OutputFormatter


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser"""
    parser = argparse.ArgumentParser(
        prog='infosynthesis',
        description='🔍 InfoSynthesis-CLI - Lightweight Multi-Source Information Aggregation & Intelligent Summary Engine',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s search "AI agents"                    # Search and synthesize
  %(prog)s search "AI agents" -o report.md       # Save to file
  %(prog)s search "AI agents" -f html            # Export as HTML
  %(prog)s search "AI agents" --lang en          # English output
  %(prog)s config --set-key YOUR_API_KEY         # Set API key
  %(prog)s config --show                         # Show configuration

Supported sources: Reddit, HackerNews, GitHub, Zhihu, Bilibili, Juejin
Supported LLM providers: GLM-5.1, OpenAI, Claude, DeepSeek
        """
    )

    parser.add_argument('-v', '--version', action='version', version=f'%(prog)s {__version__}')

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Search command
    search_parser = subparsers.add_parser('search', help='Search and synthesize information')
    search_parser.add_argument('query', help='Search query or research topic')
    search_parser.add_argument('-o', '--output', help='Output file path')
    search_parser.add_argument('-f', '--format', choices=['markdown', 'html', 'json'],
                               default='markdown', help='Output format (default: markdown)')
    search_parser.add_argument('-l', '--lang', choices=['zh', 'zh_tw', 'en', 'ja', 'ko', 'es'],
                               default='zh', help='Output language (default: zh)')
    search_parser.add_argument('--no-dedup', action='store_true',
                               help='Disable deduplication')
    search_parser.add_argument('--sources', help='Comma-separated list of sources to use')
    search_parser.add_argument('--max-items', type=int, default=100,
                               help='Maximum number of items to process (default: 100)')

    # Config command
    config_parser = subparsers.add_parser('config', help='Manage configuration')
    config_parser.add_argument('--show', action='store_true', help='Show current configuration')
    config_parser.add_argument('--set-key', help='Set LLM API key')
    config_parser.add_argument('--set-provider', choices=['glm-5.1', 'openai', 'claude', 'deepseek'],
                               help='Set LLM provider')
    config_parser.add_argument('--enable-source', help='Enable a source')
    config_parser.add_argument('--disable-source', help='Disable a source')

    # Interactive mode
    interactive_parser = subparsers.add_parser('interactive', help='Interactive TUI mode')
    interactive_parser.add_argument('-l', '--lang', choices=['zh', 'zh_tw', 'en', 'ja', 'ko', 'es'],
                                    default='zh', help='Output language')

    return parser


def print_banner():
    """Print application banner"""
    banner = """
╔══════════════════════════════════════════════════════════════════╗
║  🔍 InfoSynthesis-CLI v1.0.0                                     ║
║  Lightweight Multi-Source Information Aggregation Engine         ║
║  轻量级多源信息聚合与智能摘要引擎                                   ║
╚══════════════════════════════════════════════════════════════════╝
    """
    print(banner)


def print_progress(message: str, done: bool = False):
    """Print progress message"""
    icon = "✅" if done else "⏳"
    print(f"  {icon} {message}")


def handle_search(args) -> int:
    """Handle search command"""
    print_banner()

    query = args.query
    output_path = args.output
    format_type = args.format
    language = args.lang
    deduplicate = not args.no_dedup
    max_items = args.max_items

    print(f"\n🔎 Query: {query}")
    print(f"🌐 Language: {language}")
    print(f"📄 Format: {format_type}")
    print(f"🔢 Max items: {max_items}")
    print()

    # Load configuration
    print_progress("Loading configuration...")
    config = Config()

    # Override sources if specified
    if args.sources:
        enabled = [s.strip().lower() for s in args.sources.split(',')]
        config.set("sources", "enabled", enabled)

    print_progress("Configuration loaded", done=True)

    # Initialize source manager
    print_progress("Initializing sources...")
    source_manager = SourceManager(config.data)
    print_progress(f"Initialized {len(source_manager.sources)} sources", done=True)

    # Search all sources
    start_time = time.time()
    items = source_manager.search_all(query)
    search_time = time.time() - start_time

    print(f"\n📊 Found {len(items)} items in {search_time:.1f}s")

    if not items:
        print("\n⚠️  No results found. Try a different query or check your network connection.")
        return 1

    # Deduplicate
    if deduplicate:
        print_progress("Deduplicating results...")
        original_count = len(items)
        items = source_manager.deduplicate(items)
        removed = original_count - len(items)
        print_progress(f"Removed {removed} duplicates, {len(items)} unique items remaining", done=True)

    # Limit items
    items = items[:max_items]

    # Convert to dicts
    item_dicts = [item.to_dict() for item in items]

    # Generate summary
    print_progress("Generating intelligent summary...")
    llm_manager = LLMManager(config)
    result = llm_manager.summarize(item_dicts, query, language)
    print_progress("Summary generated", done=True)

    # Format output
    print_progress("Formatting output...")
    formatter = OutputFormatter(language)

    if output_path:
        saved_path = formatter.save(result, query, item_dicts, output_path, format_type)
        print_progress(f"Report saved to: {saved_path}", done=True)
    else:
        # Print to stdout
        if format_type == "json":
            output = formatter.format_json(result, query, item_dicts)
        elif format_type == "html":
            output = formatter.format_html(result, query, item_dicts)
        else:
            output = formatter.format_markdown(result, query, item_dicts)
        print("\n" + "=" * 60)
        print(output)
        print("=" * 60)

    # Print summary stats
    print(f"""
📈 Summary Statistics:
   • Total items collected: {len(items)}
   • Sources used: {len(set(item.source for item in items))}
   • Confidence score: {result.confidence:.0%}
   • Sentiment: {result.sentiment}
   • Key points extracted: {len(result.key_points)}
""")

    return 0


def handle_config(args) -> int:
    """Handle config command"""
    config = Config()

    if args.show:
        print("\n📋 Current Configuration:")
        print("-" * 40)
        import json
        print(json.dumps(config.data, indent=2, ensure_ascii=False))
        print("-" * 40)
        return 0

    if args.set_key:
        config.set("llm", "api_key", args.set_key)
        print("✅ API key saved successfully")
        return 0

    if args.set_provider:
        config.set("llm", "provider", args.set_provider)
        print(f"✅ LLM provider set to: {args.set_provider}")
        return 0

    if args.enable_source:
        enabled = config.get("sources", "enabled", default=[])
        if args.enable_source not in enabled:
            enabled.append(args.enable_source)
            config.set("sources", "enabled", enabled)
            config.set("sources", args.enable_source, {"enabled": True, "limit": 25})
        print(f"✅ Source enabled: {args.enable_source}")
        return 0

    if args.disable_source:
        enabled = config.get("sources", "enabled", default=[])
        if args.disable_source in enabled:
            enabled.remove(args.disable_source)
            config.set("sources", "enabled", enabled)
        print(f"✅ Source disabled: {args.disable_source}")
        return 0

    print("ℹ️  Use --show to view configuration or --help for more options")
    return 0


def handle_interactive(args) -> int:
    """Handle interactive mode"""
    print_banner()
    print("\n🎯 Interactive Mode")
    print("Type your research query (or 'quit' to exit):\n")

    config = Config()
    formatter = OutputFormatter(args.lang)

    while True:
        try:
            query = input("🔍 Query > ").strip()
            if query.lower() in ('quit', 'exit', 'q'):
                print("👋 Goodbye!")
                break
            if not query:
                continue

            # Create mock args for search
            class MockArgs:
                query = query
                output = None
                format = 'markdown'
                lang = args.lang
                no_dedup = False
                sources = None
                max_items = 50

            handle_search(MockArgs())
            print("\n" + "-" * 60 + "\n")

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")

    return 0


def main(argv: Optional[list] = None) -> int:
    """Main entry point"""
    parser = create_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 1

    try:
        if args.command == 'search':
            return handle_search(args)
        elif args.command == 'config':
            return handle_config(args)
        elif args.command == 'interactive':
            return handle_interactive(args)
        else:
            parser.print_help()
            return 1
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        return 130
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
