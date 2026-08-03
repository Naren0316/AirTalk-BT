"""
Tests for crypto_utils.py.

socket.socketpair() gives two connected sockets with the same send()/recv()
interface a bluetooth.BluetoothSocket has, so these tests exercise the exact
handshake and encrypt/send/recv/decrypt code path server.py, client.py, and
chat.py all use - without needing real Bluetooth hardware.
"""

import socket
import struct
import threading

import pytest
from cryptography.exceptions import InvalidTag

from crypto_utils import (
    decrypt_message,
    encrypt_message,
    perform_handshake,
    recv_encrypted,
    send_encrypted,
)


@pytest.fixture
def connected_pair():
    sock_a, sock_b = socket.socketpair()
    yield sock_a, sock_b
    sock_a.close()
    sock_b.close()


def _handshake_both_sides(sock_a, sock_b):
    """Run perform_handshake() on both ends at once (it's a blocking two-way exchange)."""
    results = {}

    def run(sock, result_key):
        results[result_key] = perform_handshake(sock)

    t_a = threading.Thread(target=run, args=(sock_a, "key_a"))
    t_b = threading.Thread(target=run, args=(sock_b, "key_b"))
    t_a.start()
    t_b.start()
    t_a.join(timeout=5)
    t_b.join(timeout=5)
    return results["key_a"], results["key_b"]


def test_handshake_derives_matching_keys(connected_pair):
    sock_a, sock_b = connected_pair
    key_a, key_b = _handshake_both_sides(sock_a, sock_b)
    assert key_a == key_b
    assert len(key_a) == 32  # AES-256 needs a 32-byte key


def test_handshake_keys_differ_across_sessions(connected_pair):
    """Every session should get its own fresh key - not reused."""
    sock_a, sock_b = connected_pair
    key_a, _ = _handshake_both_sides(sock_a, sock_b)

    sock_c, sock_d = socket.socketpair()
    try:
        key_c, _ = _handshake_both_sides(sock_c, sock_d)
    finally:
        sock_c.close()
        sock_d.close()

    assert key_a != key_c


def test_message_round_trip(connected_pair):
    sock_a, sock_b = connected_pair
    key_a, key_b = _handshake_both_sides(sock_a, sock_b)

    send_encrypted(sock_a, key_a, "hello from A")
    assert recv_encrypted(sock_b, key_b) == "hello from A"

    send_encrypted(sock_b, key_b, "hello from B")
    assert recv_encrypted(sock_a, key_a) == "hello from B"


def test_empty_message_round_trip(connected_pair):
    sock_a, sock_b = connected_pair
    key_a, key_b = _handshake_both_sides(sock_a, sock_b)

    send_encrypted(sock_a, key_a, "")
    assert recv_encrypted(sock_b, key_b) == ""


def test_unicode_message_round_trip(connected_pair):
    sock_a, sock_b = connected_pair
    key_a, key_b = _handshake_both_sides(sock_a, sock_b)

    message = "caf\u00e9 \U0001F600 \u0928\u092e\u0938\u094d\u0924\u0947"
    send_encrypted(sock_a, key_a, message)
    assert recv_encrypted(sock_b, key_b) == message


def test_tampered_ciphertext_is_rejected():
    key = b"0" * 32
    payload = bytearray(encrypt_message(key, "original message"))
    payload[-1] ^= 0xFF  # corrupt the last byte of the GCM auth tag

    with pytest.raises(InvalidTag):
        decrypt_message(key, bytes(payload))


def test_wrong_key_cannot_decrypt():
    key_a = b"0" * 32
    key_b = b"1" * 32
    payload = encrypt_message(key_a, "secret")

    with pytest.raises(InvalidTag):
        decrypt_message(key_b, payload)


def test_recv_encrypted_raises_on_disconnect(connected_pair):
    sock_a, sock_b = connected_pair
    key_a, key_b = _handshake_both_sides(sock_a, sock_b)

    sock_a.close()
    with pytest.raises(ConnectionError):
        recv_encrypted(sock_b, key_b)


def test_recv_encrypted_rejects_oversized_frame(connected_pair):
    """A corrupted or malicious length header shouldn't trigger a huge read/allocation."""
    sock_a, sock_b = connected_pair
    sock_a.send(struct.pack(">I", 50_000_000))
    with pytest.raises(ValueError):
        recv_encrypted(sock_b, b"0" * 32)


def test_handshake_rejects_wrong_length_public_key(connected_pair):
    """A malformed handshake message should fail cleanly, not crash deep in the crypto library."""
    sock_a, sock_b = connected_pair
    bogus_key = b"x" * 10  # a real X25519 public key is always 32 bytes
    sock_a.send(struct.pack(">I", len(bogus_key)) + bogus_key)

    with pytest.raises(ValueError):
        perform_handshake(sock_b)
