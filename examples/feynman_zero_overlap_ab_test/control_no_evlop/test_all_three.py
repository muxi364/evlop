import unittest

from expr_eval import eval_expr
from hash_ring import ConsistentHashRing
from stream_codec import StreamFrameCodec

class TestExprEval(unittest.TestCase):
    def test_basic_arithmetic(self):
        self.assertEqual(eval_expr("2 + 3 * 4"), 14)
        self.assertEqual(eval_expr("(2 + 3) * 4"), 20)
        self.assertEqual(eval_expr("10 / 3"), 3)
        self.assertEqual(eval_expr("-10 / 3"), -4) # floor division of -10 / 3 = -3.333... -> floor is -4
        self.assertEqual(eval_expr("2 ^ 3"), 8)
        self.assertEqual(eval_expr("-5"), -5)

    def test_comparisons_and_booleans(self):
        self.assertTrue(eval_expr("5 == 5"))
        self.assertFalse(eval_expr("5 == 4"))
        self.assertTrue(eval_expr("3 < 5 and 5 > 4"))
        self.assertTrue(eval_expr("3 > 5 or 5 > 4"))
        self.assertFalse(eval_expr("3 > 5 and 5 > 4"))
        self.assertTrue(eval_expr("1 + 1 == 2 and (10 / 2) == 5"))

class TestHashRing(unittest.TestCase):
    def test_hash_ring_basic(self):
        ring = ConsistentHashRing(virtual_nodes=10)
        ring.add_node("nodeA")
        ring.add_node("nodeB")
        ring.add_node("nodeC")

        replicas = ring.get_replicas("my_key", 2)
        self.assertEqual(len(replicas), 2)
        self.assertEqual(len(set(replicas)), 2) # distinct physical nodes
        for r in replicas:
            self.assertIn(r, ["nodeA", "nodeB", "nodeC"])

        ring.remove_node("nodeA")
        replicas_after = ring.get_replicas("my_key", 2)
        self.assertEqual(len(replicas_after), 2)
        for r in replicas_after:
            self.assertIn(r, ["nodeB", "nodeC"])
            self.assertNotEqual(r, "nodeA")

    def test_hash_ring_edge_cases(self):
        ring = ConsistentHashRing()
        self.assertEqual(ring.get_replicas("key", 3), [])
        ring.add_node("node1")
        self.assertEqual(ring.get_replicas("key", 3), ["node1"]) # only 1 node available

class TestStreamCodec(unittest.TestCase):
    def test_codec_single_frame(self):
        codec = StreamFrameCodec()
        payload = b"hello world"
        encoded = codec.encode_frame(payload)
        
        frames = codec.feed_chunk(encoded)
        self.assertEqual(len(frames), 1)
        self.assertEqual(frames[0], payload)

    def test_codec_partial_and_multiple_frames(self):
        codec = StreamFrameCodec()
        p1 = b"frame1"
        p2 = b"frame2_longer"
        
        encoded1 = codec.encode_frame(p1)
        encoded2 = codec.encode_frame(p2)
        
        combined = encoded1 + encoded2
        # Feed byte by byte or in chunks
        chunk1 = combined[:5]
        chunk2 = combined[5:]
        
        frames1 = codec.feed_chunk(chunk1)
        self.assertEqual(frames1, [])
        
        frames2 = codec.feed_chunk(chunk2)
        self.assertEqual(len(frames2), 2)
        self.assertEqual(frames2[0], p1)
        self.assertEqual(frames2[1], p2)

if __name__ == "__main__":
    unittest.main()
