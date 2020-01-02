
import threading
import multiprocessing as mp

from disruptor.factory import EventFactory
from disruptor.sequence import Sequence
from disruptor.subscriber import Subscriber

from typing import Callable, Dict, List, Optional
from typing_extensions import Protocol
import uuid

class DisruptorClosed(Exception):
    pass

class PublisherAlreadyRegistered(Exception):
    pass

class OutdatedSequence(Exception):
    pass


class SequenceNotFound(Exception):
    pass


class Empty(Exception):
    pass

"""
Tree of handlers
Once Top handler 'finishes' sequence, notification sent to children etc etc.
Top handler cannot overwrite lowest leaf node in tree at any point in time!

When trying to access a sequence that is unavailable the handler registers a Barrier on that sequence,
Once the sequence has been written to via the Publisher the barrier is released

Single publisher implementation only!
"""


class PublishEventCallback(Protocol):
    def __call__(self, event: EventFactory, sequence: Sequence) -> None: ...

class PublishEventCallable(Protocol):
    def __call__(self, cb: PublishEventCallback, *, timeout: Optional[int] = None) -> None: ...

class Disruptor:
    def __init__(self, length: int, factory, *, multiproc=False):
        if length % 2:
            raise ValueError("length must be a power of 2")
        assert callable(factory)
        self.ring_size = length  # fixed so no need for ctype
        self._ring = [factory() for x in range(length)]
        # instead of two separate hash tables embed these into the ring
        self.__read_barriers: Dict[Sequence, threading.Event] = {} # how can I use locks not barriers
        # this will have an subscriber identifier and the current value they
        # are up to
        self.subscribers: List[Subscriber] = []
        self.publisher_count = 0 # if > 0 then must use locks on sequence incrementation
        # need to track the subscribers and see what the lowest read is at
        # on a subscriber get it writes to this subscriber dict that sequence value
        # on the next subscriber read it updates this value
        self.manager = mp.Manager() if multiproc else None
        self.mu = self.manager.Lock() if self.manager else threading.Lock()
        self.__next_sequence: Sequence = Sequence(0)
        self._closed = False
        self._publishers: Optional[int] = None

    def registerPublisher(self) -> PublishEventCallable:
        if self.is_closed():
            raise DisruptorClosed()
        elif self._publishers is not None:
            raise PublisherAlreadyRegistered()
        else:
            # will be publishers class with id, lock and publish event method etc
            self._publishers = 1
            return self.publish_event
        


    def registerSubscriber(self) -> Subscriber:
        if self.is_closed():
            raise DisruptorClosed()
        with self.mu:
            subscriber = Subscriber(uuid.uuid4(), self.manager.Event() if self.manager else threading.Event())
            self.subscribers.append(subscriber)
            return subscriber

    def removeSubscriber(self, subscriber: Subscriber) -> None:
        with self.mu:
            for index, sub in enumerate(self.subscribers):
                if sub.id == subscriber.id:
                    self.subscribers.pop(index)
                    return
            raise Exception('subscriber not found')
            
    # @throttle_timer
    def next(self, timeout: Optional[int]=None):
        if self.is_closed():
            raise DisruptorClosed()

        next_value = self.__next_sequence
        # will remove this if subscribers are embeded in the ring
        for subscriber in self.subscribers:
            seq = subscriber.sequence
            if seq is not None and abs(seq-next_value) % self.ring_size == 0:
                is_ok = subscriber.barrier.wait(timeout)
                if not is_ok:
                    raise TimeoutError()
        return next_value

    def _increment_next(self) -> Sequence:
        # needs lock if multi producer
        next_value = Sequence(self.__next_sequence + 1)
        self.__next_sequence = next_value
        return next_value

    def get(self, sequence: int):
        next_sequence = self.__next_sequence
        if sequence < next_sequence - self.ring_size:
            raise OutdatedSequence()
        elif sequence > next_sequence:
            raise SequenceNotFound()

        return self._ring[sequence % self.ring_size]

    def publish(self, sequence: Sequence):
        self._increment_next()
        try:
            barrier = self.__read_barriers.pop(sequence)
            barrier.set()
        except KeyError:
            pass

    def publish_event(self, cb: PublishEventCallback, *, timeout: Optional[int] = None) -> None:
        if self.is_closed():
            raise DisruptorClosed()
        sequence = self.next(timeout)
        event = self.get(sequence)
        cb(event, sequence)
        self.publish(sequence)

    def waitFor(self, sequence: Sequence, timeout=None) -> Sequence:
        with self.mu:
            if self.is_closed():
                raise DisruptorClosed()
            next_value = self.__next_sequence
            if sequence < next_value:
                # sequence already happened
                return sequence

            barrier = self.__read_barriers.get(sequence)

            if not barrier:
                barrier = self.manager.Event() if self.manager else threading.Event()
                barrier = self.__read_barriers.setdefault(sequence, barrier)

        # this should not be called by the main distruptor thread
        # need a RLock check here to ensure caller is not disruptor
        ok = barrier.wait(timeout)
        if ok:
            return sequence
        raise TimeoutError()

    def getCursor(self) -> Sequence:
        """Get the current cursor value that can be read.

        Returns:
            Sequence -- value of the cursor for entries that have been published.
        """
        upto = Sequence(self.__next_sequence - 1)
        if upto < 0:
            raise Empty()
        else:
            return upto

    def is_closed(self) -> bool:
        return self._closed

    def close(self) -> None:
        # should only be callable from producers
        self._closed = True
        for sub in self.subscribers:
            sub.disruptor_closed = True