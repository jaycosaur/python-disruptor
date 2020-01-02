from multiprocessing import RawArray, Array #type: ignore
import threading
import unittest
import ctypes

from disruptor.factory import EventFactory
from disruptor.disruptor import Disruptor, DisruptorClosed, PublisherAlreadyRegistered
from disruptor.sequence import Sequence
from time import sleep

import numpy as np #type: ignore


class SimpleFactory(EventFactory[int]):
    def __init__(self, value):
        self.value = value
    def get(self):
        return self.value

    def set(self, value):
        self.value = value


class ComplexFactory(EventFactory[RawArray]):
    def __init__(self, value):
        self.value = value
    def get(self):
        return self.value.copy()

    def set(self, value):
        np.copyto(self.value, value)


class TestDisruptor(unittest.TestCase):
    def test_simple_factory(self):
        event = SimpleFactory(3)
        self.assertEqual(event.get(), 3)

    def test_complex_factory(self):
        complex_factory = ComplexFactory(np.frombuffer(
            RawArray('B', 4), dtype=np.uint8))
        complex_factory.set(np.ones(4, dtype=np.uint8))
        self.assertTrue(
            np.array_equal(
                complex_factory.get(),
                np.ones(
                    4,
                    dtype=np.uint8)))

    def test_invalid_length(self):
        with self.assertRaises(ValueError):
            disruptor = Disruptor(5, lambda: SimpleFactory(0))
    
    def test_invalid_factory(self):
        with self.assertRaises(AssertionError):
            disruptor = Disruptor(4, ())


    def test_threaded_disrupter(self):
        disruptor = Disruptor(4, lambda: SimpleFactory(0))

        def publisher(disruptor: Disruptor):
            for i in range(10):
                disruptor.publish_event(lambda event, seq: event.set(i))
                sleep(0.1) # simulate slowness


        def subscriber(disruptor: Disruptor):
            count = 0
            subscriber = disruptor.registerSubscriber()
            sum_values = 0
            while count < 10:
                seq = disruptor.waitFor(Sequence(count))
                sum_values += disruptor.get(seq).get()
                subscriber.update_sequence(seq)
                count += 1

            self.assertEqual(sum_values, sum(range(10)))

        threads = [
            threading.Thread(target=publisher, args=(disruptor,)),
            threading.Thread(target=subscriber, args=(disruptor,))
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()
    
    def test_disruptor_timeout_on_slow_publisher(self):
        disruptor = Disruptor(4, lambda: SimpleFactory(0))
        disruptor.publish_event(lambda event, seq: event.set(0))
        subscriber = disruptor.registerSubscriber()
        seq = disruptor.waitFor(0, 0)
        subscriber.update_sequence(seq)
        with self.assertRaises(TimeoutError):
            disruptor.waitFor(1, 0)

    def test_publish_timeout_on_blocking_subscriber(self):
        disruptor = Disruptor(2, lambda: SimpleFactory(0))
        disruptor.publish_event(lambda event, seq: event.set(0))
        disruptor.publish_event(lambda event, seq: event.set(0))
        subscriber = disruptor.registerSubscriber()
        seq = disruptor.waitFor(0, 1)
        subscriber.update_sequence(seq)
        with self.assertRaises(TimeoutError):
            disruptor.publish_event(lambda event, seq: event.set(0), timeout=0)

    def test_cannot_publish_on_closed_disruptor(self):
        disruptor = Disruptor(2, lambda: SimpleFactory(0))
        disruptor.close()
        with self.assertRaises(DisruptorClosed):
            disruptor.publish_event(lambda event, seq: event.set(0))

    
    def test_subscriber_cannot_wait_on_closed_disruptor(self):
        disruptor = Disruptor(2, lambda: SimpleFactory(0))
        disruptor.publish_event(lambda event, seq: event.set(0))
        disruptor.close()
        with self.assertRaises(DisruptorClosed):
            _ = disruptor.waitFor(0, 1)

    def test_cannot_register_publisher_on_closed_disruptor(self):
        disruptor = Disruptor(2, lambda: SimpleFactory(0))
        disruptor.close()
        with self.assertRaises(DisruptorClosed):
            disruptor.registerPublisher()

    def test_cannot_register_subscriber_on_closed_disruptor(self):
        disruptor = Disruptor(2, lambda: SimpleFactory(0))
        disruptor.close()
        with self.assertRaises(DisruptorClosed):
            disruptor.registerSubscriber()
    
    def test_cannot_register_multiple_publishers(self):
        """Temporary test before multi publisher support added
        """
        disruptor = Disruptor(2, lambda: SimpleFactory(0))
        disruptor.registerPublisher()
        with self.assertRaises(PublisherAlreadyRegistered):
            disruptor.registerPublisher()
        




if __name__ == '__main__':
    unittest.main()
