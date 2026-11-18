"""
Stateful TCP byte-stream frame codec with 4-byte big-endian length prefix
and arbitrary chunk reassembly.
"""

import struct
from typing import List


class FrameCodec:
    """Stateful stream codec for framing and deframing binary data."""

    def __init__(self) -> None:
        self._buffer = bytearray()

    @staticmethod
    def encode(payload: bytes) -> bytes:
        """Encode a payload with a 4-byte big-endian length prefix."""
        if not isinstance(payload, (bytes, bytearray)):
            raise TypeError("Payload must be bytes or bytearray")
        length = len(payload)
        return struct.pack(">I", length) + bytes(payload)

    def feed_chunk(self, chunk: bytes) -> List[bytes]:
        """Feed arbitrary stream bytes and return all fully assembled frames."""
        if chunk:
            self._buffer.extend(chunk)

        frames: List[bytes] = []
        while len(self._buffer) >= 4:
            # Read 4-byte big-endian length prefix
            (length,) = struct.unpack(">I", self._buffer[:4])
            total_frame_size = 4 + length

            if len(self._buffer) < total_frame_size:
                # Incomplete frame, wait for more data
                break

            # Extract payload
            payload = bytes(self._buffer[4:total_frame_size])
            frames.append(payload)

            # Consume processed bytes from buffer
            del self._buffer[:total_frame_size]

        return frames
