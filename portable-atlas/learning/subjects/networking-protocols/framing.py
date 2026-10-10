"""教材用の2-byte big-endian length framing。TCP観測とは独立したparser。"""
import struct

MAX_PAYLOAD = 1024


def encode(payload):
    if not 0 < len(payload) <= MAX_PAYLOAD:
        raise ValueError("payload length outside 1..1024")
    return struct.pack("!H", len(payload)) + payload


class Decoder:
    def __init__(self):
        self.buffer = bytearray()
        self.messages = []

    def feed(self, chunk):
        self.buffer.extend(chunk)
        emitted = []
        while len(self.buffer) >= 2:
            length = struct.unpack("!H", self.buffer[:2])[0]
            if not 0 < length <= MAX_PAYLOAD:
                raise ValueError("invalid length prefix")
            if len(self.buffer) < 2 + length:
                break
            payload = bytes(self.buffer[2:2 + length])
            del self.buffer[:2 + length]
            self.messages.append(payload)
            emitted.append(payload)
        return emitted

    def finish(self):
        if self.buffer:
            raise ValueError("EOF with incomplete frame")


def one_recv_one_frame(chunk):
    """意図した異常実装: 各recvが必ず1 frameであると仮定する。"""
    if len(chunk) < 2:
        raise ValueError("header incomplete")
    length = struct.unpack("!H", chunk[:2])[0]
    if not 0 < length <= MAX_PAYLOAD:
        raise ValueError("invalid length prefix")
    if len(chunk) != 2 + length:
        raise ValueError("recv boundary is not a frame boundary")
    return chunk[2:]
