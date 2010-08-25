class BufferedGenerator(object):
    __slots__ = ['_generator', '_current']
    def __init__(self, generator):
        self._generator = generator

    @property
    def current(self):
        if not hasattr(self, '_current'):
            return self.next()
        return self._current

    def next(self):
        self._current = next(self._generator)
        return self._current

    __next__ = next
