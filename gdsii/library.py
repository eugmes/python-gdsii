# -*- coding: utf-8 -*-
#
#   Copyright © 2010 Eugeniy Meshcheryakov <eugen@debian.org>
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Lesser General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU Lesser General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
    GDSII library object-oriented interface
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""
from __future__ import absolute_import
from . import tags, FormatError, _ignore_record, RecordData
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
        rec.check_tag(tags.HEADER)
        rec.check_size(1)
        self._version = rec.data[0]

        # BGNLIB
        rec = next(recs)
        rec.check_tag(tags.BGNLIB)
        self._mod_time, self._acc_time = rec.times

        # ignore posssible LIBDIRSIZE, SRFNAME, LIBSECUR
        rec = _ignore_record(recs, next(recs), tags.LIBDIRSIZE)
        rec = _ignore_record(recs, rec, tags.SRFNAME)
        rec = _ignore_record(recs, rec, tags.LIBSECUR)

        # LIBNAME
        rec.check_tag(tags.LIBNAME)
        self._name = rec.data

        # ignore posssible REFLIBS, FONTS, ATTRTABLE, GENERATIONS
        rec = _ignore_record(recs, next(recs), tags.REFLIBS)
        rec = _ignore_record(recs, rec, tags.FONTS)
        rec = _ignore_record(recs, rec, tags.ATTRTABLE)
        rec = _ignore_record(recs, rec, tags.GENERATIONS)

        # ignore FORMAT and following MASK+ ENDMASKS
        if rec.tag == tags.FORMAT:
            rec = next(recs)
            if rec.tag == tags.MASK:
                while True:
                    rec = next(recs)
                    if rec.tag == tags.ENDMASKS:
                        rec = next(recs)
                        break
                    rec.check_tag(tags.MASK)

        # UNITS
        rec.check_tag(tags.UNITS)
        rec.check_size(2)
        self._logical_unit, self._physical_unit = rec.data

        # read structures starting with BGNSTR or ENDLIB
        while True:
            rec = next(recs)
            if rec.tag == tags.BGNSTR:
                self._structures.append(Structure(recs))
            elif rec.tag == tags.ENDLIB:
                break
            else:
                raise FormatError('unexpected tag where BGNSTR or ENDLIB are expected')

    def save(self, stream):
        RecordData(tags.HEADER, (self._version,)).save(stream)
        RecordData(tags.BGNLIB, times=(self._mod_time, self._acc_time)).save(stream)
        # ignore tags.LIBDIRSIZE
        # ignore tags.SRFNAME
        # ignore tags.LIBSECUR
        RecordData(tags.LIBNAME, self._name).save(stream)
        # ignore tags.REFLIBS
        # ignore tags.FONTS
        # ignore tags.ATTRTABLE
        # ignore tags.GENERATIONS
        # FORMAT and following MASK+ ENDMASKS
        RecordData(tags.UNITS, (self._logical_unit, self._physical_unit)).save(stream)
        for struc in self._structures:
            struc.save(stream)
        RecordData(tags.ENDLIB).save(stream)

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
