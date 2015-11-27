from typing import Iterable, List, Callable, Any, TypeVar, Union
import sys
from operator import is_not
from itertools import islice
from functools import reduce, partial

T1 = TypeVar('T1')
T2 = TypeVar('T2')
T3 = TypeVar('T3')

def safe_cast(toType: Callable[[T1], T2], val: T1, default: T3=None) -> [T2, T3]:
    try:
        return toType(val)
    except ValueError:
        return default

def add(x: int, y: int) -> int:
    return x + y

toInt = partial(safe_cast, int)

def notNone(L: Iterable[Any]) -> List[Any]:
    return list(filter(None.__ne__, L))

def addIterable(I: Iterable[Any]) -> int:
    return reduce(add, notNone(map(toInt, I)), 0)

print(addIterable(sys.argv))
