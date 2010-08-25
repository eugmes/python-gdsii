"""
    GDSII library object-oriented interface
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""
from . import GDSII, FormatError, _ignore_record
from .structure import Structure
from ._utils import BufferedGenerator

class Library(object):
    """GDSII library class."""
    __slots__ = ['_version', '_mod_time', '_acc_time', '_name', '_logical_unit', '_physical_unit', '_structures']

    def __init__(self, unbuf_recs):
        recs = BufferedGenerator(unbuf_recs)
        self._structures = []

        rec = next(recs)
        # HEADER
        rec.check_tag(GDSII.HEADER)
        rec.check_size(1)
        self._version = rec.data[0]

        # BGNLIB
        rec = next(recs)
        rec.check_tag(GDSII.BGNLIB)
        self._mod_time, self._acc_time = rec.times

        # ignore posssible LIBDIRSIZE, SRFNAME, LIBSECUR
        rec = _ignore_record(recs, next(recs), GDSII.LIBDIRSIZE)
        rec = _ignore_record(recs, rec, GDSII.SRFNAME)
        rec = _ignore_record(recs, rec, GDSII.LIBSECUR)

        # LIBNAME
        rec.check_tag(GDSII.LIBNAME)
        self._name = rec.data

        # ignore posssible REFLIBS, FONTS, ATTRTABLE, GENERATIONS
        rec = _ignore_record(recs, next(recs), GDSII.REFLIBS)
        rec = _ignore_record(recs, rec, GDSII.FONTS)
        rec = _ignore_record(recs, rec, GDSII.ATTRTABLE)
        rec = _ignore_record(recs, rec, GDSII.GENERATIONS)

        # ignore FORMAT and following MASK+ ENDMASKS
        if rec.tag == GDSII.FORMAT:
            rec = next(recs)
            if rec.tag == GDSII.MASK:
                while True:
                    rec = next(recs)
                    if rec.tag == GDSII.ENDMASKS:
                        rec = next(recs)
                        break
                    rec.check_tag(GDSII.MASK)

        # UNITS
        rec.check_tag(GDSII.UNITS)
        rec.check_size(2)
        self._logical_unit, self._physical_unit = rec.data

        # read structures starting with BGNSTR or ENDLIB
        while True:
            rec = next(recs)
            if rec.tag == GDSII.BGNSTR:
                self._structures.append(Structure(recs))
            elif rec.tag == GDSII.ENDLIB:
                break
            else:
                raise FormatError('unexpected tag where BGNSTR or ENDLIB are expected')

    @property
    def version(self):
        """GDSII file verion.

        Integer number as found in a GDSII file. For example value is 5 for GDSII v5
        and 0x600 for GDSII v6.
        """
        return self._version

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
        """Name of the library (bytes)."""
        return self._name

    @property
    def logical_unit(self):
        return self._logical_unit

    @property
    def physical_unit(self):
        return self._physical_unit

    # TODO remove
    @property
    def structures(self):
        """List of structures in this library (:class:`pygdsii.structure.Structure`)."""
        return self._structures

    def __str__(self):
        return '<Library: %s>' % self.name.decode()
