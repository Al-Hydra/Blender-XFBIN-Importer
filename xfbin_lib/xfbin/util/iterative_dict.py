from typing import Iterable


class IterativeDict(dict):
    __index: int

    def __init__(self):
        super().__init__()
        self.__index = 0

    def get_or_next(self, key):
        result = super().get(key)

        if result is None:
            result = self[key] = self.__index
            self.__index += 1

        return result

    def update_or_next(self, other: Iterable):
        for k in other:
            self.get_or_next(k)

    def clear(self):
        super().clear()
        self.__index = 0
