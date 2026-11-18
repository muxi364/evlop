import unittest
from expr_eval import eval_expr
from hash_ring import ConsistentHashRing
from stream_codec import StreamFrameCodec

class TestAllThree(unittest.TestCase):

    def test_feynman_expr_eval_counter_examples(self):
        # 1. Exponentiation right-associativity: 2 ^ 3 ^ 2 -> 2 ^ (3 ^ 2) = 2 ^ 9 = 512 (not 64)
        self.assertEqual(eval_expr("2 ^ 3 ^ 2"), 512)

        # 2. Short-circuit boolean logic: True or (1 / 0) and False and (1 / 0)
        self.assertEqual(eval_expr("True or (1 / 0)"), True)
        self.assertEqual(eval_expr("False and (1 / 0)"), False)

        # 3. Unary minus precedence: -2 ^ 2 vs (-2) ^ 2
        # -2 ^ 2 parses as -(2 ^ 2) = -4, whereas (-2) ^ 2 = 4
        self.assertEqual(eval_expr("-2 ^ 2"), -4)
        self.assertEqual(eval_expr("(-2) ^ 2"), 4)

        # Additional expressions
        self.assertEqual(eval_expr("10 + 2 * 3"), 16)
        self.assertEqual(eval_expr("(10 + 2) * 3"), 36)
        self.assertEqual(eval_expr("10 / 3"), 3)
        self.assertEqual(eval_expr("5 == 5"), True)
        self.assertEqual(eval_expr("5 < 3"), False)

    def test_feynman_hash_ring_counter_examples(self):
        ring = ConsistentHashRing(virtual_nodes=10)
        ring.add_node("nodeA")
        ring.add_node("nodeB")

        # 1. Replicas must be distinct physical nodes
        replicas = ring.get_replicas("some_key", count=2)
        self.assertEqual(len(replicas), 2)
        self.assertEqual(len(set(replicas)), 2)

        # 2. Requesting more replicas than available nodes clamps to available distinct nodes
        replicas_many = ring.get_replicas("another_key", count=5)
        self.assertEqual(len(replicas_many), 2)
        self.assertEqual(set(replicas_many), {"nodeA", "nodeB"})

        # 3. Wrap around & node removal
        ring.remove_node("nodeA")
        replicas_single = ring.get_replicas("key", count=2)
        self.assertEqual(replicas_single, ["nodeB"])

    def test_feynman_stream_codec_counter_examples(self):
        codec = StreamFrameCodec()
        payload = b"Hello Feynman EVLOP!"
        encoded = codec.encode_frame(payload)

        # 1. Feed 1 byte at a time (fragmented chunk)
        extracted = []
        for b in encoded[:-1]:
            extracted.extend(codec.feed_chunk(bytes([b])))
        self.assertEqual(extracted, [])

        # Feed final byte
        extracted.extend(codec.feed_chunk(encoded[-1:]))
        self.assertEqual(extracted, [payload])

        # 2. Coalesced chunks (multiple frames in one feed)
        codec2 = StreamFrameCodec()
        f1 = codec2.encode_frame(b"frame1")
        f2 = codec2.encode_frame(b"frame2")
        f3 = codec2.encode_frame(b"frame3")
        
        frames = codec2.feed_chunk(f1 + f2 + f3)
        self.assertEqual(frames, [b"frame1", b"frame2", b"frame3"])

if __name__ == '__main__':
    unittest.main()
