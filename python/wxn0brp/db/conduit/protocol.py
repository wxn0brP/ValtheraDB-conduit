import json
import struct
from dataclasses import dataclass
from typing import Any, BinaryIO

HEADER = struct.Struct("<III")


@dataclass
class Frame:
    frame_type: int
    db_name: str
    payload: dict[str, Any]


def encode_frame(frame_type: int, db_name: str, payload: dict[str, Any] | None = None) -> bytes:
    db_name_body = db_name.encode("utf-8")
    body = json.dumps(payload or {}, separators=(",", ":")).encode("utf-8")
    return HEADER.pack(frame_type, len(db_name_body), len(body)) + db_name_body + body


def read_frame(stream: BinaryIO) -> Frame:
    header = _read_exact(stream, HEADER.size)
    frame_type, db_name_length, payload_length = HEADER.unpack(header)
    db_name = _read_exact(stream, db_name_length).decode("utf-8") if db_name_length else ""
    payload_raw = _read_exact(stream, payload_length)
    payload = json.loads(payload_raw.decode("utf-8")) if payload_raw else {}
    return Frame(frame_type, db_name, payload)


def _read_exact(stream: BinaryIO, size: int) -> bytes:
    chunks = bytearray()
    while len(chunks) < size:
        chunk = stream.read(size - len(chunks))
        if not chunk:
            raise EOFError("ValtheraDB Conduit closed the stream")
        chunks.extend(chunk)
    return bytes(chunks)
