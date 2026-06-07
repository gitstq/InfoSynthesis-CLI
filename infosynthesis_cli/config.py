"""
Configuration management for InfoSynthesis-CLI
"""

import os
import json
from pathlib import Path


DEFAULT_CONFIG = {
    "llm": {
        "provider": "glm-5.1",
        "api_key": "",
        "api_base": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        "model": "glm-5.1",
        "temperature": 0.7,
        "max_tokens": 4096,
        "timeout": 60
    },
    "sources": {
        "enabled": ["reddit", "hackernews", "github", "zhihu", "bilibili", "juejin"],
        "reddit": {"enabled": True, "limit": 25},
        "hackernews": {"enabled": True, "limit": 30},
        "github": {"enabled": True, "limit": 20},
        "zhihu": {"enabled": True, "limit": 20},
        "bilibili": {"enabled": True, "limit": 15},
        "juejin": {"enabled": True, "limit": 20},
        "weibo": {"enabled": False, "limit": 15},
        "youtube": {"enabled": False, "limit": 10}
    },
    "output": {
        "format": "markdown",
        "language": "zh",
        "max_summary_length": 2000,
        "include_sources": True,
        "include_timeline": True,
        "include_sentiment": True
    },
    "search": {
        "time_range": "7d",
        "min_score": 5,
        "deduplicate": True,
        "similarity_threshold": 0.75
    },
    "cache": {
        "enabled": True,
        "ttl": 3600,
        "max_size": 100
    }
}


class Config:
    """Configuration manager"""

    def __init__(self):
        self.config_dir = Path.home() / ".infosynthesis"
        self.config_file = self.config_dir / "config.json"
        self.cache_dir = self.config_dir / "cache"
        self.data = self._load()

    def _load(self):
        """Load configuration from file or create default"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    merged = self._deep_merge(DEFAULT_CONFIG.copy(), data)
                    return merged
            except (json.JSONDecodeError, IOError):
                pass
        return DEFAULT_CONFIG.copy()

    def _deep_merge(self, base, override):
        """Deep merge two dictionaries"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                base[key] = self._deep_merge(base[key].copy(), value)
            else:
                base[key] = value
        return base

    def save(self):
        """Save configuration to file"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    def get(self, *keys, default=None):
        """Get nested config value"""
        value = self.data
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

    def set(self, *keys, value):
        """Set nested config value"""
        target = self.data
        for key in keys[:-1]:
            if key not in target:
                target[key] = {}
            target = target[key]
        target[keys[-1]] = value
        self.save()

    def get_api_key(self):
        """Get API key from config or environment"""
        api_key = self.get("llm", "api_key", default="")
        if not api_key:
            # Try environment variables
            env_vars = [
                "GLM_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY",
                "DEEPSEEK_API_KEY", "DASHSCOPE_API_KEY"
            ]
            for env_var in env_vars:
                api_key = os.environ.get(env_var, "")
                if api_key:
                    break
        return api_key

    def get_cache_dir(self):
        """Get cache directory"""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        return self.cache_dir
