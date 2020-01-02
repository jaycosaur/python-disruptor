# Python Disruptor

Python implementation of a disruptor: *a multi-subscriber, multi-producer, blocking ring buffer*.

Inspired by LMAX Disruptor for Java without support for blocking subscribers and pipelines. Also as python has no support for atomic operations usage of locks is required, particularly for multi-producer disruptors.

Examples can be found in the example directory.

__Note this is a work in progress and the API format will change.__

### TODO

- [ ] Add multi-producer capability
- [ ] Add multiprocess tests
- [ ] Add sample program examples
- [ ] Provide benchmarking
- [ ] Add introduction to docs


## Introduction

TODO

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

seq = disruptor.waitFor(0) # wait for the event at sequence value 0 to be available

val = disruptor.get(seq).get() # retrieve the event from the ring buffer

print(f'I got a value: {val}')

subscriber.update_sequence(seq) # mark sequence as processed for subscriber
```

Accessing an element that is not yet created will block.

```python
seq = disruptor.waitFor(1) # will block
```

But you can timeout the wait to stop faulty producers from blocking the system
```python
seq = disruptor.waitFor(1, timeout=5) # wait for at most 5 seconds
```

For more examples please refer to the [examples](https://github.com/jaycosaur/python-disruptor/tree/master/examples).

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

[MIT](https://choosealicense.com/licenses/mit/)