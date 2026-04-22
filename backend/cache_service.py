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
        
        # Initial load from DB
        self._load_from_db()

    def _load_from_db(self):
        """Load stats from database on startup"""
        try:
            from backend.supabase_service import get_processing_stats
            db_stats = get_processing_stats()
            if db_stats:
                self.hits = db_stats.get("cache_hits", 0)
                self.misses = db_stats.get("cache_misses", 0)
                self.tokens_saved = db_stats.get("estimated_tokens_saved", 0)
                self.regex_only_count = db_stats.get("regex_only", 0)
                self.regex_plus_ai_count = db_stats.get("regex_plus_ai", 0)
                self.ai_only_count = db_stats.get("ai_only", 0)
                logger.info("Successfully loaded processing stats from database.")
        except Exception as e:
            logger.warning(f"Could not load stats from database: {e}")

    def _save_to_db(self):
        """Save current stats to database"""
        try:
            from backend.supabase_service import update_processing_stats
            stats = self.get_stats()
            # Remove total_processed as it's computed
            if "total_processed" in stats:
                del stats["total_processed"]
            update_processing_stats(stats)
        except Exception as e:
            logger.warning(f"Could not save stats to database: {e}")

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
            self._save_to_db() # Persist hit
            return self.cache[file_hash]
        
        self.misses += 1
        # No save here, we'll save after extraction is done and cached
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
        
        # Persist stats update
        self._save_to_db()
        
        if len(self.cache) > self.max_size:
            # Remove the oldest item (first item in OrderedDict)
            self.cache.popitem(last=False)
            logger.info("Cache full, removed oldest entry.")

    def add_tokens_saved(self, count: int):
        """Update tokens saved and persist to DB"""
        self.tokens_saved += count
        self._save_to_db()

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
