# Architecture

This document lays out the design for the whole project before the later days implement it, so every day's code fits into one coherent system.

## 1. Transport layer — Bluetooth Classic RFCOMM

- Uses the **Serial Port Profile (SPP)** over **RFCOMM**, via the `bluetooth` socket API (provided by the `pybluez2` package).
- One device advertises an RFCOMM service on a known UUID and listens (**server**); the other looks up that UUID on a paired device and connects (**client**).
- Bluetooth Classic is chosen over BLE because desktop OS support for acting as a BLE peripheral/server is inconsistent (Windows and macOS mainly support BLE *central* mode well), while RFCOMM server sockets work the same way on Linux, Windows, and macOS.
- Range is roughly 10 m for typical Class 2 Bluetooth radios, more with Class 1.

## 2. Security layer — end-to-end encryption

Encryption happens in the application layer, on top of the raw Bluetooth socket, so the message content is unreadable even if the transport itself were intercepted.

| Step | Primitive | Purpose |
|------|-----------|---------|
| Key exchange | X25519 (ECDH) | Both devices generate an ephemeral key pair and exchange public keys over the socket to agree on a shared secret, without ever transmitting a private key |
| Key derivation | HKDF-SHA256 | Turns the raw shared secret into a fixed-length symmetric key suitable for AES |
| Message encryption | AES-256-GCM | Authenticated encryption — every message gets its own random 96-bit nonce, and GCM's tag detects any tampering |

**Threat model:** this protects the *content and integrity* of messages while in transit over the Bluetooth link. It does not (on its own) verify that the paired device belongs to a specific trusted person beyond standard Bluetooth pairing — that's a possible Day 5+ extension (e.g. showing a short key-fingerprint on both screens for manual verification, similar to Signal's safety numbers).

## 3. Message framing

Every encrypted message is sent as:

```
[4 bytes: length of ciphertext, big-endian] [12 bytes: nonce] [ciphertext + 16-byte GCM tag]
```

The 4-byte length prefix lets the receiver know exactly how many bytes to read off the socket before attempting to decrypt — necessary because TCP-like streams (which RFCOMM behaves like) don't preserve message boundaries on their own.

## 4. Session flow

1. **Discovery** (Day 1): find nearby discoverable devices and their MAC addresses.
2. **Connect** (Day 2): one side listens on an RFCOMM channel, the other connects to it by MAC address + UUID.
3. **Handshake** (Day 3): both sides generate an X25519 key pair, send their public key, derive the shared AES key via HKDF.
4. **Chat** (Day 4): messages are typed, encrypted, length-prefixed, and sent; incoming bytes are read, decrypted, and printed.
5. **Hardening** (Day 5): handle disconnects/reconnects, malformed frames, failed decryption (tampered/corrupted data), and general polish.

## 5. Why not BLE / a mesh network?

A true multi-hop Bluetooth mesh (like Bridgefy or Serval) — where messages can relay through other nearby phones to reach someone out of direct range — is a much larger undertaking (routing, flood control, duplicate suppression, mesh topology management) and isn't realistic to build and test properly in 5 days. This project scopes to **direct, paired, device-to-device** messaging, which is still a complete and demonstrable offline E2E-encrypted chat system.
