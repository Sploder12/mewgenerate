import threading
from typing import Any, Callable, Generic, TypeVar

T = TypeVar('T')

# external logic is needed for determining producer/consumer
class ResourceSync(Generic[T]):
    cv: threading.Condition
    done: bool

    onProduce: Callable[..., T]
    onWait: None | Callable[..., Any]
    onWaitEnd: None | Callable[..., Any]

    def __init__(self, produce: Callable[..., T], onWait: None | Callable[..., Any] = None, onWaitEnd: None | Callable[..., Any] = None):
        self.cv = threading.Condition()
        self.done = False
        self.onProduce = produce
        self.onWait = onWait
        self.onWaitEnd = onWaitEnd

    def produce(self, *args, **kwargs) -> T:
        with self.cv:
            out = self.onProduce(*args, **kwargs)
            self.done = True
            self.cv.notify_all()
            return out
    
    def consume(self, *args, **kwargs):
        waited = False
        with self.cv:
            if (not self.done):
                waited = True
                if (self.onWait != None):
                    self.onWait(*args, **kwargs)

                while not self.done:
                    self.cv.wait()
            
        if (waited and self.onWaitEnd != None):
            self.onWaitEnd(*args, **kwargs)

class MapSync(Generic[T]):
    class Entry:
        sync: ResourceSync[Any]
        value: Any

        # python generics are certainly something...
        def __init__(self, sync: ResourceSync[T]):
            self.sync = sync
            self.value = None
            
    onProduce: Callable[..., T]
    onWait: None | Callable[..., Any]
    onWaitEnd: None | Callable[..., Any]

    mapLock: threading.Lock
    data: dict[str, Entry]

    def __init__(self, produce: Callable[..., T], onWait: None | Callable[..., Any] = None, onWaitEnd: None | Callable[..., Any] = None):
        self.onProduce = produce
        self.onWait = onWait
        self.onWaitEnd = onWaitEnd
        self.mapLock = threading.Lock()
        self.data = {}

    def get(self, id: str, *args, **kwargs) -> T:
        producing = False
        with self.mapLock:
            if (id in self.data):
                entry = self.data[id]
            else:
                producing = True
                sync = ResourceSync(self.onProduce, self.onWait, self.onWaitEnd)
                entry = MapSync.Entry(sync)
                self.data[id] = entry

        if (not producing):
            entry.sync.consume(*args, **kwargs)
            return entry.value
        else:
            entry.value = entry.sync.produce(*args, **kwargs)
            return entry.value


class ValueSync(Generic[T]):
    # demented code reuse, don't try at home
    sync: MapSync[T]

    def __init__(self, produce: Callable[..., T], onWait: None | Callable[..., Any] = None, onWaitEnd: None | Callable[..., Any] = None):
        self.sync = MapSync[T](produce, onWait, onWaitEnd)

    def get(self, *args, **kwargs) -> T:
        return self.sync.get("", *args, **kwargs)