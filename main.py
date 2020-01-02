import time

from multiprocessing import RawArray, RawValue, Process #type: ignore
from threading import Thread

from disruptor.disruptor import Disruptor
from disruptor.sequence import Sequence
from disruptor.factory import EventFactory

import numpy as np #type: ignore


class Event(EventFactory):
    def __init__(self, ctype, size):
        self.count = RawValue('i')
        self.value = RawArray(ctype, size)

    def get(self):
        return self.count.value, np.frombuffer(
            self.value, dtype=np.uint8).copy()

    def set(self, data):
        (count, value) = data
        self.count.value = count
        np.copyto(np.frombuffer(self.value, dtype=np.uint8), value)

class ThreadEvent(EventFactory):
    def __init__(self):
        self.count = None
        self.value = None

    def get(self):
        return self.count, self.value

    def set(self, data):
        (count, value) = data
        self.count = count
        self.value = value



np_size = 1


def writer(ring_buffer:Disruptor):
    #ones = np.ones(np_size, dtype=np.uint8)
    for i in range(1000000):
        # this should block if the trailing listener still has a lock on the
        # sequence element
        # ring_buffer.publish_event(lambda event, sequence: 
        # event.set((i, ones.copy())))
        ring_buffer.publish_event(lambda event, sequence: 
        event.set((i, i)))


def listener(identifier: int, ring_buffer: Disruptor):
    subscriber = ring_buffer.registerSubscriber()
    latest: Sequence = Sequence(0)
    print('listener start...')
    try:
        while True:
            seq = ring_buffer.waitFor(latest, 2)
            subscriber.update_sequence(latest)
            #print(identifier, "listener", latest, ring_buffer.get(seq).get()[0])
            latest = Sequence(seq + 1)
    except TimeoutError:
        pass
    
    print('listener finishing')
    ring_buffer.removeSubscriber(subscriber)


BENCH_TIME = 5

def main():
    #ring_buffer = Disruptor(256, lambda: Event('B', np_size))
    ring_buffer = Disruptor(256, lambda: ThreadEvent(), multiproc=False)

    proc_writer = Thread(target=writer, args=(ring_buffer, ))
    time.sleep(0.1)
    listeners = [Thread(target=listener, args=(i, ring_buffer,)) for i in range(10)]
    proc_writer.start()
    for l in listeners:
        l.start()

    time.sleep(5)
    #proc_writer.terminate()
    print('PROFILE', (ring_buffer.next()-1)/BENCH_TIME, "ops/sec" )


if __name__ == '__main__':
    main()
