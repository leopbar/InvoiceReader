import hashlib
import logging
from collections import OrderedDict

logger = logging.getLogger(__name__)

class InvoiceCache:
    def __init__(self, max_size=100):
        self.cache = OrderedDict()
        self.max_size = max_size
        self.hits = 0
        self.misses = 0
        self.tokens_saved = 0
        
        # Detailed stats
        self.regex_only_count = 0
        self.regex_plus_ai_count = 0
        self.ai_only_count = 0

    def hash_file(self, file_bytes: bytes) -> str:
        """Generate SHA256 hash of file"""
        return hashlib.sha256(file_bytes).hexdigest()

    def get_cached(self, file_hash: str) -> dict or None:
        """Return cached result if exists, move to end (LRU)"""
        if file_hash in self.cache:
            self.hits += 1
            # Move to end to mark as recently used
            self.cache.move_to_end(file_hash)
            logger.info(f"Cache hit for hash: {file_hash[:10]}...")
            return self.cache[file_hash]
        
        self.misses += 1
        return None

    def set_cache(self, file_hash: str, data: dict):
        """Store result in cache, remove oldest if full"""
        if file_hash in self.cache:
            self.cache.move_to_end(file_hash)
        
        self.cache[file_hash] = data
        
        # Track method stats from the data (if it's a miss, gemini_service calls this)
        inner_data = data.get("data", {})
        method = inner_data.get("extraction_method")
        if method == "regex_only":
            self.regex_only_count += 1
        elif method == "regex_plus_ai":
            self.regex_plus_ai_count += 1
        elif method == "ai_only":
            self.ai_only_count += 1
        
        if len(self.cache) > self.max_size:
            # Remove the oldest item (first item in OrderedDict)
            self.cache.popitem(last=False)
            logger.info("Cache full, removed oldest entry.")

    def get_stats(self):
        return {
            "total_processed": self.hits + self.misses,
            "cache_hits": self.hits,
            "cache_misses": self.misses,
            "regex_only": self.regex_only_count,
            "regex_plus_ai": self.regex_plus_ai_count,
            "ai_only": self.ai_only_count,
            "estimated_tokens_saved": self.tokens_saved
        }

# Singleton instance
cache_service = InvoiceCache()
