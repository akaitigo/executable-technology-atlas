"""127.0.0.1のみ、2接続、各3秒timeout、13-byte合成入力のTCP API観測。"""
import hashlib
import json
import platform
import socket
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from framing import Decoder, encode, one_recv_one_frame

ROOT = Path(__file__).resolve().parent
PAYLOADS = [b"PING", b"HELLO"]


def now():
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def observe(cap):
    frames = [encode(payload) for payload in PAYLOADS]
    stream = b"".join(frames)
    events, sender_errors, owned_sockets = [], [], []
    sent = threading.Event()
    worker = None
    started = now()

    def event(actor, operation, **values):
        events.append({"actor": actor, "operation": operation, "at": now(),
                       "monotonic_ns": time.monotonic_ns(), **values})

    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    owned_sockets.append(listener)
    listener.settimeout(3)
    try:
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
        endpoint = listener.getsockname()
        event("receiver", "listen", address=list(endpoint))

        def send():
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            owned_sockets.append(client)
            client.settimeout(3)
            try:
                client.connect(endpoint)
                event("sender", "connect", local=list(client.getsockname()), peer=list(client.getpeername()))
                for index, frame in enumerate(frames):
                    client.sendall(frame)
                    event("sender", "sendall", call=index + 1, length=len(frame), hex=frame.hex())
                client.shutdown(socket.SHUT_WR)
                event("sender", "shutdown-write")
            except Exception as error:
                sender_errors.append(type(error).__name__ + ": " + str(error))
            finally:
                sent.set()
                client.close()

        worker = threading.Thread(target=send, name="learning-tcp-sender", daemon=True)
        worker.start()
        connection, peer = listener.accept()
        owned_sockets.append(connection)
        connection.settimeout(3)
        event("receiver", "accept", local=list(connection.getsockname()), peer=list(peer))
        # Application scheduling, not a TCP packet boundary or network-delay simulation.
        if not sent.wait(3):
            raise TimeoutError("sender completion barrier")
        if sender_errors:
            raise RuntimeError(sender_errors[0])
        decoder, received, bad_messages, chunks = Decoder(), bytearray(), [], []
        for call in range(1, 33):
            chunk = connection.recv(cap)
            event("receiver", "recv", call=call, requested=cap, returned=len(chunk), hex=chunk.hex())
            if not chunk:
                decoder.finish()
                break
            received.extend(chunk)
            good = decoder.feed(chunk)
            try:
                bad = one_recv_one_frame(chunk)
                bad_messages.append(bad)
                bad_result = {"status": "accepted", "payload": bad.decode("ascii")}
            except ValueError as error:
                bad_result = {"status": "refused", "reason": str(error)}
            chunks.append({"call": call, "requested": cap, "returned": len(chunk),
                           "hex": chunk.hex(), "emitted": [x.decode("ascii") for x in good],
                           "buffer_hex": bytes(decoder.buffer).hex(), "naive": bad_result})
        else:
            raise RuntimeError("bounded recv limit exceeded")
        if bytes(received) != stream or decoder.messages != PAYLOADS:
            raise RuntimeError("stream or incremental decoder oracle failed")
        result = {"id": "recv-cap-" + str(cap), "started_at": started, "completed_at": now(),
                  "receive_cap": cap, "endpoint": list(endpoint),
                  "sends": [{"length": len(frame), "hex": frame.hex()} for frame in frames],
                  "chunks": chunks, "received_hex": bytes(received).hex(), "events": events,
                  "oracle": {"bytes_match": True,
                             "length_framing": [x.decode("ascii") for x in decoder.messages],
                             "naive_messages": [x.decode("ascii") for x in bad_messages],
                             "naive_matches": bad_messages == PAYLOADS,
                             "send_lengths": [len(x) for x in frames],
                             "recv_lengths": [len(bytes.fromhex(x["hex"])) for x in chunks]}}
        if cap == 3 and result["oracle"]["naive_matches"]:
            raise RuntimeError("expected framing defect was not observed")
    finally:
        for owned in owned_sockets:
            owned.close()
        if worker is not None:
            worker.join(4)
    result["cleanup"] = {"owned_socket_count": len(owned_sockets),
                         "open_owned_sockets": sum(x.fileno() >= 0 for x in owned_sockets),
                         "sender_thread_alive": worker.is_alive()}
    if result["cleanup"]["open_owned_sockets"] or result["cleanup"]["sender_thread_alive"]:
        raise RuntimeError("owned runtime cleanup failed")
    return result


def main():
    started = now()
    runs = [observe(3), observe(64)]
    document = {"schema_version": 1, "subject_id": "networking-protocols",
                "lesson_id": "tcp-stream-framing", "status": "pass",
                "started_at": started, "completed_at": now(),
                "environment": {"python": platform.python_version(), "implementation": platform.python_implementation(),
                                "os": platform.system(), "os_release": platform.release(),
                                "machine": platform.machine(), "transport": "AF_INET/SOCK_STREAM/TCP",
                                "host": "127.0.0.1", "attempts": 1, "retries": 0},
                "input": {"payloads_ascii": [x.decode("ascii") for x in PAYLOADS],
                          "framing": "uint16 big-endian payload byte length",
                          "stream_hex": b"".join(encode(x) for x in PAYLOADS).hex(),
                          "recv_caps": [3, 64], "socket_timeout_seconds": 3,
                          "max_recv_calls_per_connection": 32,
                          "scheduling": "receiver waits until two sendall calls and SHUT_WR have completed"},
                "source_digests": {name: "sha256:" + hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                                   for name in ["observe_tcp.py", "framing.py"]},
                "runs": runs,
                "scope": {"kind": "current-real-stream-api", "synthetic_payloads": True,
                          "packet_capture": False, "retransmission_measured": False,
                          "congestion_measured": False, "subject_completion_credit": False}}
    print(json.dumps(document, ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(type(error).__name__ + ": " + str(error), file=sys.stderr)
        sys.exit(1)
