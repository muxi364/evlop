"""
Unit tests for FrameCodec covering all Feynman counter-examples.
"""

import unittest
from frame_codec import FrameCodec


class TestFrameCodec(unittest.TestCase):
    """Test suite for FrameCodec."""

    def test_counter_example_one_byte_at_a_time(self) -> None:
        """Test feeding a frame 1 byte at a time."""
        codec = FrameCodec()
        raw = b"Hello Feynman World!"
        encoded = FrameCodec.encode(raw)

        extracted = []
        for i, b in enumerate(encoded):
            res = codec.feed_chunk(bytes([b]))
            if i < len(encoded) - 1:
                self.assertEqual(res, [])
            else:
                self.assertEqual(res, [raw])

    def test_counter_example_three_concatenated_frames(self) -> None:
        """Test feeding 3 concatenated frames in a single chunk."""
        codec = FrameCodec()
        p1 = b"Frame One"
        p2 = b"Frame Two Payload"
        p3 = b"F3"
        chunk = FrameCodec.encode(p1) + FrameCodec.encode(p2) + FrameCodec.encode(p3)

        frames = codec.feed_chunk(chunk)
        self.assertEqual(frames, [p1, p2, p3])

    def test_counter_example_binary_payload_roundtrip(self) -> None:
        """Test empty and arbitrary binary payloads containing delimiter bytes."""
        codec = FrameCodec()
        empty_payload = b""
        binary_payload = bytes(range(256))

        encoded = FrameCodec.encode(empty_payload) + FrameCodec.encode(binary_payload)
        frames = codec.feed_chunk(encoded)

        self.assertEqual(frames, [empty_payload, binary_payload])


if __name__ == "__main__":
    unittest.main()
