from threading import Event
from typing import Optional
from disruptor.sequence import Sequence

class Subscriber():
    def __init__(self, id, barrier: Event):
        self.id = id
        self.sequence: Optional[Sequence] = None
        self.barrier = barrier
        self.disruptor_closed = False

    def _release_barrier(self):
        try:
            self.barrier.set()
        except Exception:
            pass
        self.barrier.clear()

    def get_sequence(self):
        return self.sequence

    def update_sequence(self, sequence: Sequence) -> Sequence:
        self.sequence = sequence
        self._release_barrier()
        return sequence