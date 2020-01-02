from threading import Event
from typing import Optional
from disruptor.sequence import Sequence

class Publisher():
    def __init__(self, id, barrier: Event):
        self.id = id
        self.sequence: Optional[Sequence] = None
        self.barrier = barrier

    def _release_barrier(self):
        try:
            self.barrier.set()
        except Exception:
            pass
        self.barrier.clear()

    def get_sequence(self):
        return self.sequence

    def update_sequence(self, sequence: Sequence) -> Sequence:
        # needs to be atomic to stop skipping
        self.sequence = sequence
        self._release_barrier() # release any producers waiting on previous barrier
        return sequence