"""Socketを開かず、framingの境界と実観測原票を検算する。"""
import hashlib
import json
import unittest
from pathlib import Path

from framing import Decoder, MAX_PAYLOAD, encode, one_recv_one_frame

ROOT = Path(__file__).resolve().parent


def require(condition, label):
    if not condition:
        raise ValueError(label)


def verify(document):
    require(document["status"] == "pass", "actual observation status")
    require(document["environment"]["host"] == "127.0.0.1", "loopback only")
    require(document["environment"]["attempts"] == 1 and document["environment"]["retries"] == 0,
            "attempt/retry binding")
    expected = [value.encode("ascii") for value in document["input"]["payloads_ascii"]]
    stream = b"".join(encode(value) for value in expected)
    require(stream.hex() == document["input"]["stream_hex"], "input bytes")
    require([run["receive_cap"] for run in document["runs"]] == [3, 64], "actual two variants")
    for run in document["runs"]:
        require(run["endpoint"][0] == "127.0.0.1" and 0 < run["endpoint"][1] < 65536, "endpoint")
        sends = [event for event in run["events"] if event["operation"] == "sendall"]
        recvs = [event for event in run["events"] if event["operation"] == "recv"]
        require([bytes.fromhex(event["hex"]) for event in sends] == [encode(value) for value in expected], "send API bytes")
        require([event["length"] for event in sends] == [6, 7], "send lengths")
        require(len(recvs) == len(run["chunks"]) + 1 and recvs[-1]["returned"] == 0
                and recvs[-1]["hex"] == "", "observed EOF")
        require(len(recvs) <= document["input"]["max_recv_calls_per_connection"], "bounded calls")
        require(max(event["monotonic_ns"] for event in sends) < min(event["monotonic_ns"] for event in recvs), "sender barrier")
        decoder, received, bad_messages = Decoder(), bytearray(), []
        for event, chunk in zip(recvs, run["chunks"]):
            raw = bytes.fromhex(event["hex"])
            require(chunk["hex"] == event["hex"] and chunk["call"] == event["call"], "raw event binding")
            require(event["requested"] == run["receive_cap"] == chunk["requested"], "requested cap")
            require(event["returned"] == chunk["returned"] == len(raw) and 0 < len(raw) <= run["receive_cap"], "actual returned length")
            emitted = [value.decode("ascii") for value in decoder.feed(raw)]
            require(chunk["emitted"] == emitted and chunk["buffer_hex"] == bytes(decoder.buffer).hex(), "incremental parser result")
            received.extend(raw)
            try:
                value = one_recv_one_frame(raw)
                bad_messages.append(value)
                require(chunk["naive"] == {"status": "accepted", "payload": value.decode("ascii")}, "naive acceptance")
            except ValueError as error:
                require(chunk["naive"] == {"status": "refused", "reason": str(error)}, "naive refusal")
        decoder.finish()
        require(bytes(received) == stream and decoder.messages == expected, "full stream reconstruction")
        oracle = run["oracle"]
        require(oracle["bytes_match"] and oracle["length_framing"] == [value.decode("ascii") for value in expected], "success oracle")
        require(oracle["recv_lengths"] == [chunk["returned"] for chunk in run["chunks"]], "recv oracle")
        require(oracle["naive_messages"] == [value.decode("ascii") for value in bad_messages]
                and oracle["naive_matches"] == (bad_messages == expected), "failure oracle")
        require(run["cleanup"] == {"owned_socket_count": 3, "open_owned_sockets": 0, "sender_thread_alive": False}, "cleanup")
    for name, digest in document["source_digests"].items():
        require(name in {"framing.py", "observe_tcp.py"}, "source name")
        require(digest == "sha256:" + hashlib.sha256((ROOT / name).read_bytes()).hexdigest(), "source digest")


class LessonTests(unittest.TestCase):
    def test_every_partition_restores_two_messages(self):
        stream = encode(b"PING") + encode(b"HELLO")
        # All 4096 compositions of these 13 bytes: headers/bodies split and coalesced.
        for mask in range(1 << (len(stream) - 1)):
            decoder, start = Decoder(), 0
            for end in range(1, len(stream)):
                if mask & (1 << (end - 1)):
                    decoder.feed(stream[start:end])
                    start = end
            decoder.feed(stream[start:])
            decoder.finish()
            self.assertEqual(decoder.messages, [b"PING", b"HELLO"])

    def test_boundary_dependent_parser(self):
        self.assertEqual(one_recv_one_frame(encode(b"PING")), b"PING")
        with self.assertRaises(ValueError):
            one_recv_one_frame(encode(b"PING")[:3])
        with self.assertRaises(ValueError):
            one_recv_one_frame(encode(b"PING") + encode(b"HELLO"))

    def test_partial_eof_and_invalid_lengths(self):
        for raw in [b"\x00", encode(b"PING")[:-1], encode(b"PING") + encode(b"HELLO")[:-1]]:
            decoder = Decoder()
            decoder.feed(raw)
            with self.assertRaises(ValueError):
                decoder.finish()
        for raw in [b"\x00\x00", (MAX_PAYLOAD + 1).to_bytes(2, "big")]:
            with self.assertRaises(ValueError):
                Decoder().feed(raw)
        self.assertEqual(Decoder().feed(encode(b"A" * MAX_PAYLOAD)), [b"A" * MAX_PAYLOAD])

    def test_actual_record_and_digests(self):
        data = (ROOT / "observation-data.js").read_text()
        document = json.loads(data.removeprefix("window.TCP_OBSERVATION = ").removesuffix(";\n"))
        observation = document["observation"]
        verify(observation)
        directory = ROOT / document["artifact_directory"]
        command = json.loads((directory / "command.json").read_text())
        self.assertEqual(command["exit_code"], 0)
        self.assertEqual(command["stderr"], "")
        self.assertEqual(command["stdout_digest"], "sha256:" + hashlib.sha256(command["stdout"].encode()).hexdigest())
        self.assertEqual(json.loads(command["stdout"]), {key: value for key, value in observation.items() if key != "execution_id"})
        for artifact in document["manifest"]["artifacts"]:
            self.assertEqual(artifact["digest"], "sha256:" + hashlib.sha256((directory / artifact["path"]).read_bytes()).hexdigest())
        self.assertEqual(json.loads((directory / "observation.json").read_text()), observation)
        for label, mutation in [
            ("fake success", lambda item: item["runs"][0]["chunks"][0].update(emitted=["PING"])),
            ("raw mismatch", lambda item: item["runs"][0]["events"][-2].update(hex="ff")),
            ("cleanup incomplete", lambda item: item["runs"][0]["cleanup"].update(open_owned_sockets=1)),
            ("missing variant", lambda item: item["runs"].pop()),
            ("changed digest", lambda item: item["source_digests"].update({"framing.py": "sha256:invalid"})),
        ]:
            changed = json.loads(json.dumps(observation))
            mutation(changed)
            with self.subTest(label=label), self.assertRaises(ValueError):
                verify(changed)


if __name__ == "__main__":
    unittest.main(verbosity=2)
