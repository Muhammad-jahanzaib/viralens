"""
Circuit Breaker Pattern
Prevents cascading failures and repeated calls to failing APIs
"""

from enum import Enum
from datetime import datetime, timedelta
from typing import Callable, Any, Optional
from threading import Lock
import logging

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failures detected, blocking calls
    HALF_OPEN = "half_open"  # Testing if service recovered

class CircuitBreaker:
    """
    Circuit breaker to prevent repeated calls to failing services

    States:
    - CLOSED: Normal operation, calls go through
    - OPEN: Too many failures, calls blocked immediately
    - HALF_OPEN: Testing recovery, limited calls allowed
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 3,
        timeout_seconds: int = 60,
        recovery_timeout: int = 30
    ):
        """
        Initialize circuit breaker

        Args:
            name: Circuit breaker name (for logging)
            failure_threshold: Number of failures before opening circuit
            timeout_seconds: How long to keep circuit open
            recovery_timeout: Time to wait before testing recovery
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.recovery_timeout = recovery_timeout

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.opened_at = None

        self.lock = Lock()

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function through circuit breaker

        Args:
            func: Function to execute
            *args, **kwargs: Function arguments

        Returns:
            Function result

        Raises:
            CircuitBreakerError: If circuit is open
        """

        with self.lock:
            # Check current state
            self._update_state()

            if self.state == CircuitState.OPEN:
                raise CircuitBreakerError(
                    f"{self.name} circuit is OPEN (too many failures). "
                    f"Will retry in {self._time_until_half_open():.0f}s"
                )

        # Execute function
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result

        except Exception as e:
            self._on_failure()
            raise

    def _update_state(self):
        """Update circuit state based on time and failures"""

        if self.state == CircuitState.OPEN:
            # Check if timeout passed
            if self.opened_at and datetime.now() - self.opened_at > timedelta(seconds=self.timeout_seconds):
                logger.info(f"🔄 {self.name} circuit moving to HALF_OPEN (testing recovery)")
                self.state = CircuitState.HALF_OPEN
                self.failure_count = 0

    def _on_success(self):
        """Handle successful call"""

        with self.lock:
            if self.state == CircuitState.HALF_OPEN:
                logger.info(f"✅ {self.name} circuit CLOSED (service recovered)")
                self.state = CircuitState.CLOSED

            self.failure_count = 0
            self.last_failure_time = None

    def _on_failure(self):
        """Handle failed call"""

        with self.lock:
            self.failure_count += 1
            self.last_failure_time = datetime.now()

            if self.state == CircuitState.HALF_OPEN:
                # Failed during recovery test
                logger.warning(f"❌ {self.name} circuit OPEN again (recovery failed)")
                self.state = CircuitState.OPEN
                self.opened_at = datetime.now()

            elif self.failure_count >= self.failure_threshold:
                # Too many failures
                logger.error(
                    f"❌ {self.name} circuit OPEN "
                    f"({self.failure_count} failures, threshold: {self.failure_threshold})"
                )
                self.state = CircuitState.OPEN
                self.opened_at = datetime.now()

    def _time_until_half_open(self) -> float:
        """Calculate seconds until HALF_OPEN state"""

        if not self.opened_at:
            return 0

        elapsed = (datetime.now() - self.opened_at).total_seconds()
        remaining = self.timeout_seconds - elapsed

        return max(0, remaining)

    def reset(self):
        """Manually reset circuit breaker"""

        with self.lock:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.last_failure_time = None
            self.opened_at = None
            logger.info(f"♻️  {self.name} circuit breaker reset")

    def get_state(self) -> dict:
        """Get current circuit state"""

        return {
            'name': self.name,
            'state': self.state.value,
            'failure_count': self.failure_count,
            'is_open': self.state == CircuitState.OPEN,
            'time_until_retry': self._time_until_half_open() if self.state == CircuitState.OPEN else 0
        }


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open"""
    pass


class CircuitBreakerRegistry:
    """Global registry of circuit breakers"""

    _breakers = {}
    _lock = Lock()

    @classmethod
    def get(cls, name: str, failure_threshold: int = 3, timeout_seconds: int = 60) -> CircuitBreaker:
        """Get or create circuit breaker"""

        with cls._lock:
            if name not in cls._breakers:
                cls._breakers[name] = CircuitBreaker(name, failure_threshold, timeout_seconds)

            return cls._breakers[name]

    @classmethod
    def reset_all(cls):
        """Reset all circuit breakers"""

        with cls._lock:
            for breaker in cls._breakers.values():
                breaker.reset()

    @classmethod
    def get_all_states(cls) -> list:
        """Get states of all circuit breakers"""

        with cls._lock:
            return [breaker.get_state() for breaker in cls._breakers.values()]


# Pre-configured circuit breakers for each collector
GOOGLE_TRENDS_BREAKER = CircuitBreakerRegistry.get('GoogleTrends', failure_threshold=2, timeout_seconds=300)
TWITTER_BREAKER = CircuitBreakerRegistry.get('Twitter', failure_threshold=3, timeout_seconds=180)
YOUTUBE_BREAKER = CircuitBreakerRegistry.get('YouTube', failure_threshold=2, timeout_seconds=900)
REDDIT_BREAKER = CircuitBreakerRegistry.get('Reddit', failure_threshold=3, timeout_seconds=120)
NEWS_BREAKER = CircuitBreakerRegistry.get('News', failure_threshold=3, timeout_seconds=180)


# Example usage
if __name__ == "__main__":
    import time

    breaker = CircuitBreaker('TestAPI', failure_threshold=3, timeout_seconds=10)

    def failing_api():
        raise Exception("API Error")

    # Simulate failures
    for i in range(5):
        try:
            breaker.call(failing_api)
        except CircuitBreakerError as e:
            print(f"Circuit breaker blocked call: {e}")
        except Exception as e:
            print(f"API failed: {e}")

        time.sleep(1)

    print(f"\nCircuit state: {breaker.get_state()}")
