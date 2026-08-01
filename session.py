"""
BlueWhisper - Day 4: shared chat session loop.

Used by chat.py whether you're hosting or connecting - one implementation
of the interactive loop instead of duplicating it. Adds two things on top
of Day 3's raw send/receive:

  - Timestamps on every message
  - A local log file per conversation (logs/, git-ignored) so you can
    scroll back through a chat later - only ever written to your own
    device, never sent anywhere

Requirements:
    pip install cryptography
"""

import datetime
import os
import threading

from cryptography.exceptions import InvalidTag

from crypto_utils import recv_encrypted, send_encrypted

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")


def _timestamp() -> str:
    return datetime.datetime.now().strftime("%H:%M:%S")


def _log_path(peer_label: str) -> str:
    os.makedirs(LOG_DIR, exist_ok=True)
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    safe_label = "".join(c if c.isalnum() else "_" for c in peer_label)
    return os.path.join(LOG_DIR, f"{date_str}_{safe_label}.log")


def _append_log(log_file: str, line: str):
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def _listen_for_messages(sock, key, log_file: str):
    while True:
        try:
            plaintext = recv_encrypted(sock, key)
        except ConnectionError:
            print("\n[Connection closed by peer]")
            break
        except InvalidTag:
            print("\n[Received a message that failed verification - discarded]")
            continue
        line = f"[{_timestamp()}] Peer: {plaintext}"
        print(f"\r{line}\nYou: ", end="", flush=True)
        _append_log(log_file, line)


def run_chat_session(sock, key, peer_label: str):
    """
    Run the interactive encrypted chat loop until the user types /quit, /exit,
    or the connection closes.

    peer_label names the log file - pass a saved contact's name if you have
    one, otherwise their MAC address.
    """
    log_file = _log_path(peer_label)
    print(f"Chatting with {peer_label}. Messages are logged to {log_file}")
    print("Type a message and press Enter to send. Type /quit to exit.\n")

    listener = threading.Thread(
        target=_listen_for_messages, args=(sock, key, log_file), daemon=True
    )
    listener.start()

    try:
        while True:
            message = input("You: ")
            if message.strip().lower() in ("/quit", "/exit"):
                break
            if message:
                send_encrypted(sock, key, message)
                _append_log(log_file, f"[{_timestamp()}] You: {message}")
    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        print("\nClosing connection...")
        sock.close()
