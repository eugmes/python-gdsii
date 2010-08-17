"""
    GDSII structure interface
    ~~~~~~~~~~~~~~~~~~~~~~~~~
"""
from . import GDSII, _ignore_record
from .elements import ElementBase

class Structure(object):
    """GDSII structure class."""

    __slots__ = ['_mod_time', '_acc_time', '_name', '_elements']

    def __init__(self, recs, lastrec):
        self._elements = []

        self._mod_time, self._acc_time = lastrec.times

        # STRNAME
        rec = next(recs)
        rec.check_tag(GDSII.STRNAME)
        self._name = rec.data

        # ignore STRCLASS
        rec = _ignore_record(recs, next(recs), GDSII.STRCLASS)

        # read elements till ENDSTR
        while rec.tag != GDSII.ENDSTR:
            self._elements.append(ElementBase.load(recs, rec))
            rec = next(recs)
    
    @property
    def mod_time(self):
        """Last modification time (datetime)."""
        return self._mod_time

    @property
    def acc_time(self):
        """Last access time (datetime)."""
        return self._acc_time

    @property
    def name(self):
        """Structure name (bytes)."""
        return self._name

    # TODO remove
    @property
    def elements(self):
        """
        List of elements in the structure.
        See :mod:`pygdsii.elements` for possible elements.
        """
        return self._elements

    def __str__(self):
        return '<Structure: %s>' % self.name.decode()
