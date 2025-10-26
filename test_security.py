#!/usr/bin/env python3
"""Quick security test suite"""

import os
import tempfile
from pathlib import Path

def test_gitignore():
    """Test that .gitignore exists and covers critical patterns"""
    print("Testing .gitignore...")

    gitignore = Path(".gitignore")
    if not gitignore.exists():
        print("  ❌ .gitignore not found!")
        return False

    content = gitignore.read_text()

    required_patterns = [
        "*.key", "*.token", ".env", "*.db",
        "__pycache__", "*.log", ".yolo_tokens.json"
    ]

    missing = []
    for pattern in required_patterns:
        if pattern not in content:
            missing.append(pattern)

    if missing:
        print(f"  ⚠️  Missing patterns: {', '.join(missing)}")
        return False

    print("  ✅ .gitignore looks good")
    return True


def test_yolo_guard():
    """Test YOLO guard is present and functional"""
    print("\nTesting YOLO guard...")

    try:
        from yolo_guard import YOLOGuard

        # Test token generation
        os.environ["YOLO_MODE"] = "1"
        token = YOLOGuard.generate_approval_token(ttl_seconds=60)

        # Test validation
        is_valid = YOLOGuard.validate_approval_token(token)

        if not is_valid:
            print("  ❌ Token validation failed")
            return False

        # Test reuse prevention
        is_valid_again = YOLOGuard.validate_approval_token(token)

        if is_valid_again:
            print("  ❌ Token can be reused (should fail)")
            return False

        print("  ✅ YOLO guard works correctly")
        return True

    except ImportError:
        print("  ❌ yolo_guard.py not found")
        return False
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def test_rate_limiter():
    """Test rate limiter is present and functional"""
    print("\nTesting rate limiter...")

    try:
        from rate_limiter import RateLimiter

        limiter = RateLimiter(requests_per_minute=3)

        # Test normal operation
        for i in range(3):
            allowed, msg = limiter.check_rate_limit("test")
            if not allowed:
                print(f"  ❌ Request {i+1} blocked unexpectedly")
                return False

        # Test limit enforcement
        allowed, msg = limiter.check_rate_limit("test")
        if allowed:
            print("  ❌ Rate limit not enforced")
            return False

        print("  ✅ Rate limiter works correctly")
        return True

    except ImportError:
        print("  ❌ rate_limiter.py not found")
        return False
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def test_integration():
    """Test that components are integrated into main code"""
    print("\nTesting integration...")

    try:
        from claude_bridge_secure import SecureBridge, RATE_LIMITER_AVAILABLE

        if not RATE_LIMITER_AVAILABLE:
            print("  ❌ Rate limiter not integrated into SecureBridge")
            return False

        # Create temp bridge and verify rate limiter exists
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            bridge = SecureBridge(db_path)

            if not hasattr(bridge, 'rate_limiter') or bridge.rate_limiter is None:
                print("  ❌ Rate limiter not initialized in SecureBridge")
                return False

        print("  ✅ Integration looks good")
        return True

    except ImportError as e:
        print(f"  ❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def main():
    print("="*60)
    print("Security Components Test Suite")
    print("="*60)

    results = {
        "gitignore": test_gitignore(),
        "yolo_guard": test_yolo_guard(),
        "rate_limiter": test_rate_limiter(),
        "integration": test_integration()
    }

    print("\n" + "="*60)
    print("Results:")
    print("="*60)

    passed = sum(results.values())
    total = len(results)

    for component, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{component:15s} {status}")

    print(f"\nTotal: {passed}/{total} passed")

    if passed == total:
        print("\n🎉 All security components ready!")
        return 0
    else:
        print("\n⚠️  Some components need attention")
        return 1


if __name__ == "__main__":
    exit(main())
