"""
Rate Limiter - Token bucket implementation

Prevents abuse by limiting requests per session across multiple time windows.

Author: Danny Stocker
License: MIT
"""

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Tuple, Dict

class RateLimiter:
    """
    Token bucket rate limiter with multiple time windows.

    Tracks requests per session across minute, hour, and day windows.
    """

    def __init__(
        self,
        requests_per_minute: int = 10,
        requests_per_hour: int = 100,
        requests_per_day: int = 500
    ):
        """
        Initialize rate limiter with configurable limits.

        Args:
            requests_per_minute: Max requests in 1-minute window
            requests_per_hour: Max requests in 1-hour window
            requests_per_day: Max requests in 1-day window
        """
        self.rpm = requests_per_minute
        self.rph = requests_per_hour
        self.rpd = requests_per_day

        # Session buckets: session_id -> {minute: {...}, hour: {...}, day: {...}}
        self.buckets = defaultdict(lambda: {
            'minute': {'count': 0, 'reset_at': datetime.now()},
            'hour': {'count': 0, 'reset_at': datetime.now()},
            'day': {'count': 0, 'reset_at': datetime.now()}
        })

    def check_rate_limit(self, session_id: str) -> Tuple[bool, str]:
        """
        Check if request is within rate limits.

        Args:
            session_id: Unique identifier for session

        Returns:
            Tuple of (allowed: bool, reason: str)
            - If allowed: (True, "OK")
            - If blocked: (False, "Rate limit: X req/period exceeded")
        """
        now = datetime.now()
        bucket = self.buckets[session_id]

        # Check and reset minute bucket
        if now > bucket['minute']['reset_at']:
            bucket['minute'] = {
                'count': 0,
                'reset_at': now + timedelta(minutes=1)
            }

        # Check BEFORE incrementing
        if bucket['minute']['count'] >= self.rpm:
            reset_in = (bucket['minute']['reset_at'] - now).seconds
            return False, f"Rate limit: {self.rpm} req/min exceeded (resets in {reset_in}s)"

        # Check and reset hour bucket
        if now > bucket['hour']['reset_at']:
            bucket['hour'] = {
                'count': 0,
                'reset_at': now + timedelta(hours=1)
            }

        if bucket['hour']['count'] >= self.rph:
            reset_in = (bucket['hour']['reset_at'] - now).seconds // 60
            return False, f"Rate limit: {self.rph} req/hour exceeded (resets in {reset_in}m)"

        # Check and reset day bucket
        if now > bucket['day']['reset_at']:
            bucket['day'] = {
                'count': 0,
                'reset_at': now + timedelta(days=1)
            }

        if bucket['day']['count'] >= self.rpd:
            reset_in = (bucket['day']['reset_at'] - now).seconds // 3600
            return False, f"Rate limit: {self.rpd} req/day exceeded (resets in {reset_in}h)"

        # All checks passed - increment counters
        bucket['minute']['count'] += 1
        bucket['hour']['count'] += 1
        bucket['day']['count'] += 1

        return True, "OK"

    def get_usage(self, session_id: str) -> Dict:
        """
        Get current usage statistics for a session.

        Args:
            session_id: Session to check

        Returns:
            Dict with usage info for each time window:
            {
                'minute': {'used': X, 'limit': Y, 'reset_at': 'ISO-8601'},
                'hour': {...},
                'day': {...}
            }
        """
        bucket = self.buckets.get(session_id)

        if not bucket:
            # No requests yet
            now = datetime.now()
            return {
                'minute': {
                    'used': 0,
                    'limit': self.rpm,
                    'remaining': self.rpm,
                    'reset_at': (now + timedelta(minutes=1)).isoformat()
                },
                'hour': {
                    'used': 0,
                    'limit': self.rph,
                    'remaining': self.rph,
                    'reset_at': (now + timedelta(hours=1)).isoformat()
                },
                'day': {
                    'used': 0,
                    'limit': self.rpd,
                    'remaining': self.rpd,
                    'reset_at': (now + timedelta(days=1)).isoformat()
                }
            }

        return {
            'minute': {
                'used': bucket['minute']['count'],
                'limit': self.rpm,
                'remaining': max(0, self.rpm - bucket['minute']['count']),
                'reset_at': bucket['minute']['reset_at'].isoformat()
            },
            'hour': {
                'used': bucket['hour']['count'],
                'limit': self.rph,
                'remaining': max(0, self.rph - bucket['hour']['count']),
                'reset_at': bucket['hour']['reset_at'].isoformat()
            },
            'day': {
                'used': bucket['day']['count'],
                'limit': self.rpd,
                'remaining': max(0, self.rpd - bucket['day']['count']),
                'reset_at': bucket['day']['reset_at'].isoformat()
            }
        }

    def reset_session(self, session_id: str):
        """Reset rate limits for a session (admin use only)"""
        if session_id in self.buckets:
            del self.buckets[session_id]

    def get_all_sessions(self) -> list:
        """Get list of all tracked sessions"""
        return list(self.buckets.keys())


# Example usage
if __name__ == "__main__":
    # Create limiter with custom limits
    limiter = RateLimiter(
        requests_per_minute=3,
        requests_per_hour=10,
        requests_per_day=50
    )

    print("Testing rate limiter...")
    print(f"Limits: {limiter.rpm}/min, {limiter.rph}/hour, {limiter.rpd}/day\n")

    # Simulate requests
    for i in range(5):
        allowed, msg = limiter.check_rate_limit("test_session")

        if allowed:
            print(f"Request {i+1}: ✅ {msg}")
            usage = limiter.get_usage("test_session")
            print(f"  Minute: {usage['minute']['used']}/{usage['minute']['limit']}")
        else:
            print(f"Request {i+1}: ❌ {msg}")

    print("\nUsage summary:")
    usage = limiter.get_usage("test_session")
    for period in ['minute', 'hour', 'day']:
        info = usage[period]
        print(f"{period.capitalize()}: {info['used']}/{info['limit']} "
              f"({info['remaining']} remaining)")
