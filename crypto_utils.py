"""
BlueWhisper - Day 3: end-to-end encryption.

Provides everything server.py and client.py need to turn the plain RFCOMM
socket from Day 2 into an encrypted channel:

  - X25519 key pair generation and a handshake that exchanges public keys
    over the socket and derives a shared key (ECDH)
  - HKDF-SHA256 to turn that shared secret into a 32-byte AES-256 key
  - AES-256-GCM authenticated encryption/decryption (confidentiality +
    tamper detection) with a fresh random nonce per message
  - send_encrypted() / recv_encrypted() helpers that handle the framing
    (length prefix + nonce + ciphertext) so the rest of the code just
    passes plaintext strings in and out

See docs/ARCHITECTURE.md for why each piece was chosen.

Requirements:
    pip install cryptography
"""

import os
import struct

from cryptography.hazmat.primitives.asymmetric.x25519 import (
    X25519PrivateKey,
    X25519PublicKey,
)
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

NONCE_SIZE = 12  # bytes - standard nonce size for AES-GCM
LENGTH_PREFIX_SIZE = 4  # bytes - big-endian unsigned int


def generate_keypair():
    """Generate a fresh X25519 key pair for this session (not reused across sessions)."""
    private_key = X25519PrivateKey.generate()
    return private_key, private_key.public_key()


def serialize_public_key(public_key: X25519PublicKey) -> bytes:
    """Turn a public key into raw bytes so it can be sent over the socket."""
    return public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )


def deserialize_public_key(data: bytes) -> X25519PublicKey:
    """Rebuild a public key object from raw bytes received over the socket."""
    return X25519PublicKey.from_public_bytes(data)


def derive_shared_key(private_key: X25519PrivateKey, peer_public_key: X25519PublicKey) -> bytes:
    """
    Run the ECDH exchange and derive a 32-byte AES-256 key from the result.

    Both sides call this with their own private key and the other side's
    public key. ECDH guarantees they land on the same shared secret without
    either private key ever going over the wire.
    """
    shared_secret = private_key.exchange(peer_public_key)
    return HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b"bluewhisper-handshake",
    ).derive(shared_secret)


def perform_handshake(sock) -> bytes:
    """
    Exchange X25519 public keys over an already-connected socket and return
    the derived shared AES-256 key.

    Identical on both ends - each side just sends its own public key, then
    reads the other side's.
    """
    private_key, public_key = generate_keypair()
    own_key_bytes = serialize_public_key(public_key)

    sock.send(struct.pack(">I", len(own_key_bytes)) + own_key_bytes)

    peer_key_len = struct.unpack(">I", _recv_exact(sock, LENGTH_PREFIX_SIZE))[0]
    peer_key_bytes = _recv_exact(sock, peer_key_len)
    peer_public_key = deserialize_public_key(peer_key_bytes)

    return derive_shared_key(private_key, peer_public_key)


def encrypt_message(key: bytes, plaintext: str) -> bytes:
    """Encrypt a plaintext string. Returns nonce + ciphertext + auth tag."""
    nonce = os.urandom(NONCE_SIZE)
    ciphertext = AESGCM(key).encrypt(nonce, plaintext.encode("utf-8"), None)
    return nonce + ciphertext


def decrypt_message(key: bytes, data: bytes) -> str:
    """
    Reverse of encrypt_message.

    Raises cryptography.exceptions.InvalidTag if the data was tampered with
    or corrupted - callers should treat that as "discard this message",
    not crash the whole chat session.
    """
    nonce, ciphertext = data[:NONCE_SIZE], data[NONCE_SIZE:]
    plaintext = AESGCM(key).decrypt(nonce, ciphertext, None)
    return plaintext.decode("utf-8")


def send_encrypted(sock, key: bytes, plaintext: str):
    """Encrypt a message and send it length-prefixed over the socket."""
    payload = encrypt_message(key, plaintext)
    sock.send(struct.pack(">I", len(payload)) + payload)


def recv_encrypted(sock, key: bytes) -> str:
    """
    Block until one full encrypted message has arrived, then decrypt it.

    Raises:
        ConnectionError - the peer closed the connection.
        cryptography.exceptions.InvalidTag - the message failed integrity
            verification (corrupted or tampered with).
    """
    length = struct.unpack(">I", _recv_exact(sock, LENGTH_PREFIX_SIZE))[0]
    payload = _recv_exact(sock, length)
    return decrypt_message(key, payload)


def _recv_exact(sock, num_bytes: int) -> bytes:
    """
    Read exactly num_bytes from the socket.

    RFCOMM behaves like a TCP stream - a single recv() call isn't guaranteed
    to return a whole message, so this loops until enough bytes have arrived.
    """
    buf = b""
    while len(buf) < num_bytes:
        chunk = sock.recv(num_bytes - len(buf))
        if not chunk:
            raise ConnectionError("Connection closed while reading a message")
        buf += chunk
    return buf
