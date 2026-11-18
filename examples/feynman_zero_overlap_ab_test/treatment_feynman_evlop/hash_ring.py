import hashlib
import bisect

class ConsistentHashRing:
    def __init__(self, virtual_nodes: int = 50):
        self.virtual_nodes = virtual_nodes
        self.ring = []  # list of (hash_val, physical_node)
        self.physical_nodes = set()

    def _hash(self, key: str) -> int:
        return int(hashlib.md5(key.encode('utf-8')).hexdigest(), 16) & 0xFFFFFFFF

    def add_node(self, node: str):
        if node in self.physical_nodes:
            return
        self.physical_nodes.add(node)
        for i in range(self.virtual_nodes):
            v_key = f"{node}#vnode{i}"
            h = self._hash(v_key)
            bisect.insort(self.ring, (h, node))

    def remove_node(self, node: str):
        if node not in self.physical_nodes:
            return
        self.physical_nodes.remove(node)
        self.ring = [item for item in self.ring if item[1] != node]

    def get_replicas(self, key: str, count: int) -> list[str]:
        if not self.physical_nodes:
            return []
        
        max_distinct = len(self.physical_nodes)
        count = min(count, max_distinct)
        if count <= 0:
            return []

        h = self._hash(key)
        # Find insertion index
        keys_list = [item[0] for item in self.ring]
        idx = bisect.bisect_left(keys_list, h)
        if idx == len(self.ring):
            idx = 0

        result = []
        seen = set()
        n_ring = len(self.ring)
        
        curr = idx
        for _ in range(n_ring):
            _, node = self.ring[curr]
            if node not in seen:
                seen.add(node)
                result.append(node)
                if len(result) == count:
                    break
            curr = (curr + 1) % n_ring
            
        return result
