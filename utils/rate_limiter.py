"""
Universal Rate Limiter
Prevents 429 errors across all APIs
"""

import time
from datetime import datetime, timedelta
from typing import Dict, Optional
from threading import Lock
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    """Thread-safe rate limiter for API calls"""

    def __init__(self, max_requests: int, window_seconds: int, name: str = "API"):
        """
        Initialize rate limiter

        Args:
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds
            name: Name for logging
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.name = name

        self.requests = []
        self.lock = Lock()
        self.rate_limited_until = None

    def acquire(self, cost: int = 1) -> bool:
        """
        Attempt to acquire permission for API call

        Args:
            cost: Cost in requests (e.g., YouTube search = 100)

        Returns:
            bool: True if allowed, False if rate limited
        """
        with self.lock:
            now = datetime.now()

            # Check if we're in rate limit cooldown
            if self.rate_limited_until and now < self.rate_limited_until:
                wait_time = (self.rate_limited_until - now).seconds
                logger.warning(f"⏳ {self.name} rate limited, {wait_time}s remaining")
                return False

            # Remove old requests outside window
            cutoff = now - timedelta(seconds=self.window_seconds)
            self.requests = [req for req in self.requests if req > cutoff]

            # Check if we can make request
            total_cost = sum(1 for _ in self.requests) + cost

            if total_cost > self.max_requests:
                # Rate limit triggered
                self.rate_limited_until = now + timedelta(seconds=self.window_seconds)
                logger.warning(f"❌ {self.name} rate limit reached ({total_cost}/{self.max_requests})")
                return False

            # Record request
            for _ in range(cost):
                self.requests.append(now)

            remaining = self.max_requests - len(self.requests)
            logger.debug(f"✅ {self.name} request allowed ({remaining} remaining)")
            return True

    def wait_if_needed(self, cost: int = 1, max_wait: int = 60) -> bool:
        """
        Wait until request can be made

        Args:
            cost: Request cost
            max_wait: Maximum seconds to wait

        Returns:
            bool: True if acquired, False if timeout
        """
        start = time.time()

        while not self.acquire(cost):
            if time.time() - start > max_wait:
                logger.error(f"❌ {self.name} timeout after {max_wait}s")
                return False

            time.sleep(1)

        return True

    def reset(self):
        """Reset rate limiter (e.g., after API key change)"""
        with self.lock:
            self.requests = []
            self.rate_limited_until = None
            logger.info(f"♻️  {self.name} rate limiter reset")


class RateLimiterRegistry:
    """Global registry of rate limiters"""

    _limiters: Dict[str, RateLimiter] = {}
    _lock = Lock()

    @classmethod
    def get(cls, name: str, max_requests: int, window_seconds: int) -> RateLimiter:
        """Get or create rate limiter"""

        with cls._lock:
            if name not in cls._limiters:
                cls._limiters[name] = RateLimiter(max_requests, window_seconds, name)

            return cls._limiters[name]

    @classmethod
    def reset_all(cls):
        """Reset all rate limiters"""
        with cls._lock:
            for limiter in cls._limiters.values():
                limiter.reset()


# Pre-configured rate limiters
GOOGLE_TRENDS_LIMITER = RateLimiterRegistry.get('GoogleTrends', max_requests=10, window_seconds=60)
TWITTER_LIMITER = RateLimiterRegistry.get('Twitter', max_requests=450, window_seconds=900)  # 450/15min
YOUTUBE_LIMITER = RateLimiterRegistry.get('YouTube', max_requests=10000, window_seconds=86400)  # Daily
NEWSAPI_LIMITER = RateLimiterRegistry.get('NewsAPI', max_requests=100, window_seconds=86400)  # Daily


# Example usage
if __name__ == "__main__":
    limiter = RateLimiter(max_requests=5, window_seconds=10, name="Test")

    # Make 5 requests
    for i in range(7):
        if limiter.acquire():
            print(f"✅ Request {i+1} allowed")
        else:
            print(f"❌ Request {i+1} rate limited")
        time.sleep(1)
