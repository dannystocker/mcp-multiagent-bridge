#!/usr/bin/env python3
"""
YOLO Mode Guard - Multi-stage confirmation system

Prevents accidental/unauthorized command execution by requiring:
1. Environment variable flag (YOLO_MODE=1)
2. Typed confirmation phrase
3. One-time random code
4. Time-limited approval token for actual execution

Author: Danny Stocker
License: MIT
"""

import os
import sys
import secrets
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional

class YOLOGuard:
    """Multi-stage confirmation system for dangerous operations"""

    TOKEN_FILE = Path.home() / ".yolo_tokens.json"
    AUDIT_LOG = Path.home() / "yolo_audit.log"

    @classmethod
    def require_confirmation(cls) -> bool:
        """
        Stage 1: Manual confirmation with typed phrases

        Returns:
            True if user completes confirmation flow
        """
        # Check environment variable
        if os.getenv("YOLO_MODE") != "1":
            print("❌ YOLO mode is disabled.")
            print("   Set YOLO_MODE=1 to enable.")
            return False

        # Display warning
        print("\n" + "="*70)
        print("⚠️  WARNING: YOLO MODE ENABLES COMMAND EXECUTION")
        print("="*70)
        print("\nThis allows AI agents to run commands on your system.")
        print("Commands will have access to your files and permissions.")
        print("\nOnly proceed if:")
        print("  • You understand the security implications")
        print("  • You are in an isolated/sandboxed environment")
        print("  • You have backups of important data")
        print("  • You will supervise all operations")
        print()

        # Require exact confirmation phrase
        required_phrase = "I UNDERSTAND THE RISKS"
        confirmation = input(f"Type '{required_phrase}' to continue: ").strip()

        if confirmation != required_phrase:
            print("❌ Confirmation phrase incorrect. Aborting.")
            cls._log_audit("CONFIRMATION_FAILED", {
                "reason": "incorrect_phrase",
                "provided": confirmation[:20] + "..."
            })
            return False

        # Generate and require one-time code
        code = secrets.token_hex(3)  # 6-character hex string
        print(f"\nOne-time code: {code}")
        user_code = input("Retype the code above: ").strip()

        if user_code != code:
            print("❌ Code mismatch. Aborting.")
            cls._log_audit("CONFIRMATION_FAILED", {
                "reason": "code_mismatch"
            })
            return False

        # Success
        cls._log_audit("YOLO_ENABLED", {
            "method": "interactive_confirmation",
            "timestamp": datetime.now().isoformat()
        })
        print("\n✅ YOLO mode enabled for this session")
        print("   Use --generate-token to create execution tokens\n")

        return True

    @classmethod
    def generate_approval_token(cls, ttl_seconds: int = 300) -> str:
        """
        Stage 2: Generate time-limited execution token

        Args:
            ttl_seconds: Token lifetime in seconds (default: 5 minutes)

        Returns:
            URL-safe token string
        """
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(seconds=ttl_seconds)

        # Load existing tokens
        tokens = cls._load_tokens()

        # Store new token
        tokens[token] = {
            "created_at": datetime.now().isoformat(),
            "expires_at": expires_at.isoformat(),
            "ttl_seconds": ttl_seconds,
            "used": False
        }

        cls._save_tokens(tokens)
        cls._log_audit("TOKEN_GENERATED", {
            "token_preview": token[:10] + "...",
            "ttl_seconds": ttl_seconds,
            "expires_at": expires_at.isoformat()
        })

        print(f"\n✅ Approval token generated")
        print(f"   Token: {token}")
        print(f"   Valid for: {ttl_seconds} seconds ({ttl_seconds//60} minutes)")
        print(f"   Expires at: {expires_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"\nUse with:")
        print(f"   --execute --approval-token {token}")
        print()

        return token

    @classmethod
    def validate_approval_token(cls, token: str) -> bool:
        """
        Stage 3: Validate and consume approval token

        Args:
            token: Token to validate

        Returns:
            True if token is valid, False otherwise
        """
        tokens = cls._load_tokens()

        # Check if token exists
        if token not in tokens:
            cls._log_audit("TOKEN_INVALID", {
                "token_preview": token[:10] + "...",
                "reason": "not_found"
            })
            return False

        token_data = tokens[token]

        # Check if already used
        if token_data["used"]:
            cls._log_audit("TOKEN_INVALID", {
                "token_preview": token[:10] + "...",
                "reason": "already_used",
                "used_at": token_data.get("used_at", "unknown")
            })
            return False

        # Check expiration
        expires_at = datetime.fromisoformat(token_data["expires_at"])
        if datetime.now() > expires_at:
            cls._log_audit("TOKEN_INVALID", {
                "token_preview": token[:10] + "...",
                "reason": "expired",
                "expired_at": token_data["expires_at"]
            })
            return False

        # Mark as used
        tokens[token]["used"] = True
        tokens[token]["used_at"] = datetime.now().isoformat()
        cls._save_tokens(tokens)

        cls._log_audit("TOKEN_VALIDATED", {
            "token_preview": token[:10] + "...",
            "created_at": token_data["created_at"],
            "used_at": tokens[token]["used_at"]
        })

        return True

    @classmethod
    def _load_tokens(cls) -> Dict:
        """Load tokens from file"""
        if not cls.TOKEN_FILE.exists():
            return {}

        try:
            return json.loads(cls.TOKEN_FILE.read_text())
        except json.JSONDecodeError:
            # Corrupted file, start fresh
            return {}

    @classmethod
    def _save_tokens(cls, tokens: Dict):
        """Save tokens to file with restricted permissions"""
        cls.TOKEN_FILE.write_text(json.dumps(tokens, indent=2))
        cls.TOKEN_FILE.chmod(0o600)  # Owner read/write only

    @classmethod
    def _log_audit(cls, action: str, details: Dict):
        """Append audit entry to log file"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "details": details
        }

        # Ensure log directory exists
        cls.AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)

        # Append as JSON lines
        with open(cls.AUDIT_LOG, "a") as f:
            f.write(json.dumps(entry) + "\n")

    @classmethod
    def cleanup_expired_tokens(cls) -> int:
        """Remove expired tokens from storage"""
        tokens = cls._load_tokens()
        now = datetime.now()

        expired = []
        for token, data in tokens.items():
            expires_at = datetime.fromisoformat(data["expires_at"])
            if now > expires_at:
                expired.append(token)

        for token in expired:
            del tokens[token]

        if expired:
            cls._save_tokens(tokens)
            cls._log_audit("TOKENS_CLEANED", {
                "count": len(expired)
            })

        return len(expired)

    @classmethod
    def list_active_tokens(cls) -> list:
        """List all valid (non-expired, unused) tokens"""
        tokens = cls._load_tokens()
        now = datetime.now()

        active = []
        for token, data in tokens.items():
            expires_at = datetime.fromisoformat(data["expires_at"])
            if not data["used"] and now <= expires_at:
                active.append({
                    "token_preview": token[:10] + "...",
                    "created_at": data["created_at"],
                    "expires_at": data["expires_at"],
                    "ttl_seconds": data["ttl_seconds"]
                })

        return active


def main():
    """CLI interface for YOLO guard"""
    import argparse

    parser = argparse.ArgumentParser(
        description="YOLO Mode Guard - Safe command execution gating",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Enable YOLO mode (requires confirmation)
  export YOLO_MODE=1
  python yolo_guard.py --enable-yolo

  # Generate 5-minute token
  python yolo_guard.py --generate-token --ttl 300

  # List active tokens
  python yolo_guard.py --list-tokens

  # Clean up expired tokens
  python yolo_guard.py --cleanup
        """
    )

    parser.add_argument(
        "--enable-yolo",
        action="store_true",
        help="Enable YOLO mode with interactive confirmation"
    )

    parser.add_argument(
        "--generate-token",
        action="store_true",
        help="Generate time-limited approval token"
    )

    parser.add_argument(
        "--ttl",
        type=int,
        default=300,
        help="Token TTL in seconds (default: 300 = 5 minutes)"
    )

    parser.add_argument(
        "--list-tokens",
        action="store_true",
        help="List active (valid) tokens"
    )

    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Remove expired tokens"
    )

    args = parser.parse_args()

    # Enable YOLO mode
    if args.enable_yolo:
        success = YOLOGuard.require_confirmation()
        sys.exit(0 if success else 1)

    # Generate token
    if args.generate_token:
        if os.getenv("YOLO_MODE") != "1":
            print("❌ YOLO_MODE not enabled. Set YOLO_MODE=1 first.")
            sys.exit(1)

        YOLOGuard.generate_approval_token(args.ttl)
        sys.exit(0)

    # List active tokens
    if args.list_tokens:
        tokens = YOLOGuard.list_active_tokens()

        if not tokens:
            print("No active tokens.")
        else:
            print(f"\nActive tokens: {len(tokens)}")
            for token in tokens:
                print(f"\n  Token: {token['token_preview']}")
                print(f"  Created: {token['created_at']}")
                print(f"  Expires: {token['expires_at']}")
                print(f"  TTL: {token['ttl_seconds']}s")

        sys.exit(0)

    # Cleanup expired
    if args.cleanup:
        count = YOLOGuard.cleanup_expired_tokens()
        print(f"✅ Removed {count} expired token(s)")
        sys.exit(0)

    # No arguments - show help
    parser.print_help()


if __name__ == "__main__":
    main()
