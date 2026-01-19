"""
Parallel Data Collection Engine
Executes collectors in parallel with circuit breakers and timeouts
"""

import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
from typing import Dict, Callable, List, Any
import time
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import logger
from utils.circuit_breaker import CircuitBreakerError

class ParallelCollector:
    """Execute data collectors in parallel with fault tolerance"""

    def __init__(self, max_workers: int = 5, timeout_per_collector: int = 90):
        """
        Initialize parallel collector

        Args:
            max_workers: Maximum parallel threads
            timeout_per_collector: Timeout for each collector in seconds
        """
        self.max_workers = max_workers
        self.timeout = timeout_per_collector

    def collect_all(self, collectors: Dict[str, Callable]) -> Dict[str, Any]:
        """
        Execute all collectors in parallel

        Args:
            collectors: Dict of {name: collector_function}

        Returns:
            Dict of {name: result}
        """

        logger.info(f"📊 Starting parallel collection ({len(collectors)} sources)")
        logger.info("=" * 60)

        start_time = time.time()
        results = {}

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all collectors
            future_to_name = {}

            for name, collector_func in collectors.items():
                future = executor.submit(self._execute_collector, name, collector_func)
                future_to_name[future] = name

            # Collect results as they complete
            for future in as_completed(future_to_name, timeout=self.timeout + 10):
                name = future_to_name[future]

                try:
                    result = future.result(timeout=5)  # Quick timeout for result retrieval
                    results[name] = result

                    if result['success']:
                        duration = result['duration']
                        logger.info(f"✅ {name}: Success ({duration:.1f}s)")
                    else:
                        logger.warning(f"⚠️  {name}: Partial success - {result.get('error', 'Unknown issue')}")

                except TimeoutError:
                    logger.error(f"❌ {name}: Timeout after {self.timeout}s")
                    results[name] = self._error_result(name, "Timeout")

                except Exception as e:
                    logger.error(f"❌ {name}: {str(e)}")
                    results[name] = self._error_result(name, str(e))

        total_duration = time.time() - start_time

        # Summary
        successful = sum(1 for r in results.values() if r['success'])
        logger.info("=" * 60)
        logger.info(f"✅ Collection complete: {successful}/{len(collectors)} sources in {total_duration:.1f}s")

        return results

    def _execute_collector(self, name: str, collector_func: Callable) -> Dict:
        """
        Execute single collector with error handling

        Args:
            name: Collector name
            collector_func: Function to execute

        Returns:
            Dict with result and metadata
        """

        start_time = time.time()

        try:
            logger.info(f"🔄 Collecting {name} data...")

            # Execute collector
            data = collector_func()

            duration = time.time() - start_time

            # Check if data is valid
            if data is None:
                return {
                    'success': False,
                    'data': None,
                    'error': 'Collector returned None',
                    'duration': duration,
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                }

            return {
                'success': True,
                'data': data,
                'error': None,
                'duration': duration,
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }

        except CircuitBreakerError as e:
            duration = time.time() - start_time
            logger.warning(f"⚠️  {name} circuit breaker open: {e}")

            return {
                'success': False,
                'data': None,
                'error': f"Circuit breaker open: {str(e)}",
                'duration': duration,
                'circuit_open': True,
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"❌ {name} error: {e}")

            return {
                'success': False,
                'data': None,
                'error': str(e),
                'duration': duration,
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }

    def _error_result(self, name: str, error: str) -> Dict:
        """Create error result"""

        return {
            'success': False,
            'data': None,
            'error': error,
            'duration': 0,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }


# Example usage
if __name__ == "__main__":
    import time
    import random

    def slow_collector():
        """Simulate slow collector"""
        time.sleep(random.uniform(2, 5))
        return {'items': random.randint(10, 100)}

    def fast_collector():
        """Simulate fast collector"""
        time.sleep(random.uniform(0.5, 1))
        return {'items': random.randint(5, 20)}

    def failing_collector():
        """Simulate failing collector"""
        time.sleep(1)
        if random.random() < 0.5:
            raise Exception("Random failure")
        return {'items': 0}

    collectors = {
        'SlowSource': slow_collector,
        'FastSource': fast_collector,
        'UnreliableSource': failing_collector
    }

    parallel = ParallelCollector(max_workers=3)
    results = parallel.collect_all(collectors)

    print("\nResults:")
    for name, result in results.items():
        print(f"  {name}: {'✅' if result['success'] else '❌'} ({result['duration']:.1f}s)")
