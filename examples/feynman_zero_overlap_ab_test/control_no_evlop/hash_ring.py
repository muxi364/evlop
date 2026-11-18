import hashlib
import bisect

class ConsistentHashRing:
    def __init__(self, virtual_nodes: int = 50):
        self.virtual_nodes = virtual_nodes
        self.ring: list[int] = [] # Sorted list of hashes
        self.ring_map: dict[int, str] = {} # hash -> physical node name
        self.nodes: set[str] = set()

    def _hash(self, key: str) -> int:
        # Use MD5 to generate a 128-bit hash, convert to int
        hasher = hashlib.md5(key.encode('utf-8'))
        return int(hasher.hexdigest(), 16)

    def add_node(self, node: str) -> None:
        if node in self.nodes:
            return
        self.nodes.add(node)
        for i in range(self.virtual_nodes):
            vnode_key = f"{node}#v{i}"
            h = self._hash(vnode_key)
            bisect.insort(self.ring, h)
            self.ring_map[h] = node

    def remove_node(self, node: str) -> None:
        if node not in self.nodes:
            return
        self.nodes.remove(node)
        # Remove its virtual nodes from ring and ring_map
        new_ring = []
        for h in self.ring:
            if self.ring_map[h] == node:
                del self.ring_map[h]
            else:
                new_ring.append(h)
        self.ring = new_ring

    def get_replicas(self, key: str, count: int) -> list[str]:
        if not self.nodes or not self.ring:
            return []

        h = self._hash(key)
        idx = bisect.bisect_right(self.ring, h)
        if idx == len(self.ring):
            idx = 0

        replicas = []
        seen_nodes = set()
        ring_len = len(self.ring)

        # Walk the ring clockwise
        current_idx = idx
        for _ in range(ring_len):
            node = self.ring_map[self.ring[current_idx]]
            if node not in seen_nodes:
                seen_nodes.add(node)
                replicas.append(node)
                if len(replicas) == count:
                    break
            current_idx = (current_idx + 1) % ring_len

        return replicas
