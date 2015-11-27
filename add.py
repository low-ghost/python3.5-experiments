from typing import Iterable, List, Callable, Any, TypeVar, Union
import sys
import functools

T1 = TypeVar('T1')
T2 = TypeVar('T2')
T3 = TypeVar('T3')

def safe_cast(to_type: Callable[[T1], T2], val: T1, default: T3=None) -> Union[T2, T3]:
    try:
        return to_type(val)
    except ValueError:
        return default

def compose(*funcs):
    return lambda v: functools.reduce(lambda accum, f: f(accum), funcs[::-1], v)

def add(x: int, y: int) -> int:
    return x + y if y is not None else x;

to_int = functools.partial(safe_cast, int)

# not_none = compose(list, partial(filter, None.__ne__))

def add_iterable(I: Iterable[Any]) -> int:
    return functools.reduce(add, map(to_int, I), 0)

print(add_iterable(sys.argv))
