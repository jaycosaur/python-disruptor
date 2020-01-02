from abc import ABCMeta, abstractmethod
from typing import Generic, TypeVar

T = TypeVar('T')


class EventFactory(Generic[T], metaclass=ABCMeta):
    @abstractmethod
    def set(self, value: T) -> None:
        pass

    @abstractmethod
    def get(self, ) -> T:
        pass
