from typing import Any

def pred(el: Any, thelist: list) -> Any:
    prev = None
    for item in thelist:
        if item == el:
            return prev
        prev = item
    return prev

def succ(el: Any, thelist: list) -> Any:
    for i, item in enumerate(thelist):
        if item == el:
            if i < len(thelist) - 1:
                return thelist[i + 1]
    return None