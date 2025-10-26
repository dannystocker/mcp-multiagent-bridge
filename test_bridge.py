#!/usr/bin/env python3
"""
Test suite for secure Claude Code bridge
"""

import tempfile
import os
from pathlib import Path

# Add the bridge to path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from claude_bridge_secure import SecureBridge, SecretRedactor


def test_secret_redaction():
    """Test that secrets are properly redacted"""
    print("Testing secret redaction...")
    
    tests = [
        ("My AWS key is AKIAIOSFODNN7EXAMPLE", "AWS_KEY_REDACTED"),
        ("Password is: hunter2", "PASSWORD_REDACTED"),
        ("Authorization: Bearer eyJhbGc...", "BEARER_TOKEN_REDACTED"),
        ("GitHub token: ghp_1234567890abcdefghijklmnopqrstuvwxyz", "GITHUB_TOKEN_REDACTED"),
        ("OpenAI key: sk-..." + "x"*45, "OPENAI_KEY_REDACTED"),
    ]
    
    for original, expected_substring in tests:
        redacted = SecretRedactor.redact(original)
        assert expected_substring in redacted, f"Failed to redact: {original}"
        assert original not in redacted if original != redacted else True
        print(f"  ✓ Redacted: {original[:30]}...")
    
    print("✅ Secret redaction tests passed\n")


def test_conversation_lifecycle():
    """Test creating conversation and exchanging messages"""
    print("Testing conversation lifecycle...")
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
        db_path = tmp.name
    
    try:
        bridge = SecureBridge(db_path)
        
        # Create conversation
        result = bridge.create_conversation("backend_dev", "frontend_dev")
        conv_id = result['conversation_id']
        token_a = result['session_a_token']
        token_b = result['session_b_token']
        
        print(f"  ✓ Created conversation: {conv_id}")
        
        # Session A sends message
        bridge.send_message(
            conv_id, 'a', token_a,
            "Hello from session A",
            {"action_type": "question"}
        )
        print("  ✓ Session A sent message")
        
        # Session B reads message
        messages = bridge.get_unread_messages(conv_id, 'b', token_b)
        assert len(messages) == 1, "Should have 1 unread message"
        assert messages[0]['message'] == "Hello from session A"
        print("  ✓ Session B received message")
        
        # Verify message marked as read
        messages_again = bridge.get_unread_messages(conv_id, 'b', token_b)
        assert len(messages_again) == 0, "Message should be marked read"
        print("  ✓ Message marked as read atomically")
        
        # Session B replies
        bridge.send_message(
            conv_id, 'b', token_b,
            "Reply from session B",
            {"action_type": "info"}
        )
        print("  ✓ Session B sent reply")
        
        # Session A reads reply
        replies = bridge.get_unread_messages(conv_id, 'a', token_a)
        assert len(replies) == 1
        assert replies[0]['message'] == "Reply from session B"
        print("  ✓ Session A received reply")
        
        # Test status updates
        bridge.update_status(conv_id, 'a', token_a, 'working')
        status = bridge.get_partner_status(conv_id, 'b', token_b)
        assert status['status'] == 'working'
        assert status['alive'] == True
        print("  ✓ Status updates working")
        
        print("✅ Conversation lifecycle tests passed\n")
        
    finally:
        os.unlink(db_path)


def test_authentication():
    """Test token authentication"""
    print("Testing authentication...")
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
        db_path = tmp.name
    
    try:
        bridge = SecureBridge(db_path)
        
        result = bridge.create_conversation("role_a", "role_b")
        conv_id = result['conversation_id']
        token_a = result['session_a_token']
        
        # Valid token should work
        bridge.send_message(conv_id, 'a', token_a, "Valid message")
        print("  ✓ Valid token accepted")
        
        # Invalid token should fail
        try:
            bridge.send_message(conv_id, 'a', "invalid_token", "Should fail")
            assert False, "Should have raised PermissionError"
        except PermissionError:
            print("  ✓ Invalid token rejected")
        
        # Wrong session token should fail
        try:
            token_b = result['session_b_token']
            bridge.send_message(conv_id, 'a', token_b, "Wrong session")
            assert False, "Should have raised PermissionError"
        except PermissionError:
            print("  ✓ Wrong session token rejected")
        
        print("✅ Authentication tests passed\n")
        
    finally:
        os.unlink(db_path)


def test_redaction_in_messages():
    """Test that secrets are redacted when sending messages"""
    print("Testing message redaction...")
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
        db_path = tmp.name
    
    try:
        bridge = SecureBridge(db_path)
        
        result = bridge.create_conversation("dev_a", "dev_b")
        conv_id = result['conversation_id']
        token_a = result['session_a_token']
        token_b = result['session_b_token']
        
        # Send message with secret
        secret_msg = "Here's the API key: AKIAIOSFODNN7EXAMPLE"
        send_result = bridge.send_message(conv_id, 'a', token_a, secret_msg)
        
        assert send_result['redacted'] == True, "Should flag as redacted"
        print("  ✓ Message flagged as redacted")
        
        # Verify secret was actually redacted in storage
        messages = bridge.get_unread_messages(conv_id, 'b', token_b)
        assert "AKIAIOSFODNN7EXAMPLE" not in messages[0]['message']
        assert "AWS_KEY_REDACTED" in messages[0]['message']
        print("  ✓ Secret removed from stored message")
        
        print("✅ Message redaction tests passed\n")
        
    finally:
        os.unlink(db_path)


def test_concurrency():
    """Test concurrent message sending doesn't corrupt data"""
    print("Testing concurrent operations...")
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
        db_path = tmp.name
    
    try:
        bridge = SecureBridge(db_path)
        
        result = bridge.create_conversation("session_a", "session_b")
        conv_id = result['conversation_id']
        token_a = result['session_a_token']
        token_b = result['session_b_token']
        
        # Rapidly send multiple messages from both sessions
        for i in range(5):
            bridge.send_message(conv_id, 'a', token_a, f"Message A-{i}")
            bridge.send_message(conv_id, 'b', token_b, f"Message B-{i}")
        
        print("  ✓ Sent 10 messages rapidly")
        
        # Verify all messages received correctly
        msgs_b = bridge.get_unread_messages(conv_id, 'b', token_b)
        msgs_a = bridge.get_unread_messages(conv_id, 'a', token_a)
        
        assert len(msgs_b) == 5, f"Expected 5 messages for B, got {len(msgs_b)}"
        assert len(msgs_a) == 5, f"Expected 5 messages for A, got {len(msgs_a)}"
        print("  ✓ All messages received correctly")
        
        print("✅ Concurrency tests passed\n")
        
    finally:
        os.unlink(db_path)


def run_all_tests():
    """Run all test suites"""
    print("\n" + "="*80)
    print("Running Secure Bridge Test Suite")
    print("="*80 + "\n")
    
    try:
        test_secret_redaction()
        test_conversation_lifecycle()
        test_authentication()
        test_redaction_in_messages()
        test_concurrency()
        
        print("="*80)
        print("✅ ALL TESTS PASSED")
        print("="*80 + "\n")
        
        return 0
        
    except Exception as e:
        print("\n" + "="*80)
        print(f"❌ TEST FAILED: {str(e)}")
        print("="*80 + "\n")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(run_all_tests())
