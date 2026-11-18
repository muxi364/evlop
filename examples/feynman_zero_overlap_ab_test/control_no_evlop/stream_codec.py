class StreamFrameCodec:
    def __init__(self):
        self.buffer = bytearray()

    def encode_frame(self, payload: bytes) -> bytes:
        if not isinstance(payload, bytes):
            raise TypeError("Payload must be bytes")
        length_prefix = len(payload).to_bytes(4, 'big')
        return length_prefix + payload

    def feed_chunk(self, chunk: bytes) -> list[bytes]:
        if not isinstance(chunk, bytes):
            raise TypeError("Chunk must be bytes")
        self.buffer.extend(chunk)
        frames = []
        
        while len(self.buffer) >= 4:
            # Read 4-byte big endian length
            frame_len = int.from_bytes(self.buffer[:4], 'big')
            total_needed = 4 + frame_len
            if len(self.buffer) < total_needed:
                # Incomplete frame, wait for more data
                break
            
            # Extract payload
            payload = bytes(self.buffer[4:total_needed])
            frames.append(payload)
            
            # Consume processed bytes from buffer
            del self.buffer[:total_needed]
            
        return frames
