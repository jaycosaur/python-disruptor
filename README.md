# Python Disruptor

Python implementation of a disruptor: _a multi-subscriber, multi-producer, blocking ring buffer_.

Inspired by LMAX Disruptor for Java without support for blocking subscribers and pipelines. Also as python has no support for atomic operations usage of locks is required, particularly for multi-producer disruptors.

Examples can be found in the example directory.

**Note this is a work in progress and the API format will change.**

### TODO

- [ ] Add multi-producer capability
- [ ] Add multiprocess tests
- [ ] Add sample program examples
- [ ] Provide benchmarking
- [ ] Add introduction to docs

## Introduction

TODO

## Why do I need this?

When building systems that need ordered event processing such as a two stage system that when an event is received it saves to a log file, then sends a message to a client (perhaps connected via a websocket). The producer should not be blocked by an consumers, and each of the stages should not be blocked by the next stage, ie. saving the next event to a log file should not be waiting for the client to send the previous message. In other words subscribers can be lazy and slow, without affecting any subscribers higher in the food chain.

The above system is relativly straightforward and can indeed be implemented through a series of limitless queues between each processor stage. This works well for small message sizes and low message frequency. When either the size of the message, or the frequency of the messages goes up you begin to run into bottle necks when using the standard libraries queues and pipes.

## Notes on performance

Is this as quick as a queue? Should I use this instead of a queue?

This is a specialised piece of kit, it performs poorly in comparison to the threading queue for simple tasks.

As a comparison on my MacBook Pro with i5 I achieved for a simple integer test:

DISRUPTOR = 93230.7 events/s
QUEUE = 192721.2 events/s

Showing that the queue is about twice as fast in this simple case, though I am still working to improve this further.

For multiprocessing workloads however it 'can' perform much better than the `multiprocessing.Queue`. This is because you can 'skip' the pickle by using shared memory and preallocated arrays.

Performance metrics to come.

## Installation

Pending PyPi publication:

```
pip3 install disruptor
```

## Usage

Construct an event factory.

```python
from python_disruptor import EventFactory

class MyFactory(EventFactory):
    def __init__(self):
        self.value = None
    def get(self):
        return self.value
    def set(self, value):
        self.value = value
```

Create a disruptor with a capacity of 4 events in the ring and publish an event.

```python
from python_disruptor import Disruptor

disruptor = Disruptor(4, lambda: MyFactory())
```

Or if usage with multiprocessing is required:

```python
disruptor = Disruptor(4, lambda: MyFactory(), multiproc=True)
```

Publish an event to the disruptor.

```python
disruptor.publish_event(lambda event, _seq: event.set(0))
```

Register a subscriber and try and access the first element.

```python
subscriber = disruptor.registerSubscriber()

seq = disruptor.wait_for(0) # wait for the event at sequence value 0 to be available

val = disruptor.get(seq).get() # retrieve the event from the ring buffer

print(f'I got a value: {val}')

subscriber.update_sequence(seq) # mark sequence as processed for subscriber
```

Accessing an element that is not yet created will block.

```python
seq = disruptor.wait_for(1) # will block
```

But you can timeout the wait to stop faulty producers from blocking the system

```python
seq = disruptor.wait_for(1, timeout=5) # wait for at most 5 seconds
```

For more examples please refer to the [examples](https://github.com/jaycosaur/python-disruptor/tree/master/examples).

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

[MIT](https://choosealicense.com/licenses/mit/)
