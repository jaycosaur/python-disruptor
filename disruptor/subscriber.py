from threading import Event, Lock
from typing import Optional, Dict
from disruptor.sequence import Sequence


class Subscriber:
    def __init__(self, id: str, barrier_factory: Event, lock: Lock):
        self.id = id
        self.sequence: Optional[Sequence] = 0
        self.barrier_factory = barrier_factory
        self.barrier: Dict[Sequence, Event] = {0: self.barrier_factory()}
        self._lock = lock
        self.disruptor_closed = False

    def _release_barrier(self, next_seq: Sequence):
        self.barrier[next_seq] = self.barrier_factory()
        self.sequence = next_seq
        barrier = self.barrier.pop(next_seq - 1)
        barrier.set()

    def get_sequence(self):
        return self.sequence

    def update_sequence(self, sequence: Sequence) -> Sequence:
        next_seq = sequence + 1
        self._release_barrier(next_seq)
        return sequence

    def wait_until_processed(self, sequence: Sequence):  # should have a timeout here
        current_seq = self.sequence
        if current_seq and current_seq > sequence:
            return
        try:
            barrier = self.barrier[sequence]
            barrier.wait()
        except KeyError:
            print("barrier doesnt exist", current_seq, sequence)
