class StreamFrameCodec:
    def __init__(self):
        self.buffer = bytearray()

    def encode_frame(self, payload: bytes) -> bytes:
        length = len(payload)
        return length.to_bytes(4, 'big') + payload

    def feed_chunk(self, chunk: bytes) -> list[bytes]:
        self.buffer.extend(chunk)
        frames = []
        
        while len(self.buffer) >= 4:
            frame_len = int.from_bytes(self.buffer[:4], 'big')
            total_needed = 4 + frame_len
            if len(self.buffer) < total_needed:
                break
            # Extract payload
            payload = bytes(self.buffer[4:total_needed])
            frames.append(payload)
            # Remove consumed bytes from buffer
            del self.buffer[:total_needed]
            
        return frames
