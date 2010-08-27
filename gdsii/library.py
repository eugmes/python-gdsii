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
from . import exceptions, record, structure, tags, _records, _utils

_HEADER = _records.SimpleRecord('version', tags.HEADER,
""" GDSII file verion.

    Integer number as found in a GDSII file. For example value is 5 for GDSII v5
    and 0x600 for GDSII v6.
""")
_BGNLIB = _records.TimestampsRecord('mod_time', 'acc_time', tags.BGNLIB,
    'Last modification time (datetime).', 'Last access time (datetime).')
_LIBDIRSIZE = _records.SimpleOptionalRecord('libdirsize', tags.LIBDIRSIZE, None)
_SRFNAME = _records.OptionalWholeRecord('srfname', tags.SRFNAME, 'Name of spacing rules file (bytes, optional).')
_LIBSECUR = _records.ACLRecord('acls', tags.LIBSECUR, 'ACL data, list of tuples (GID, UID, ACCESS).')
_LIBNAME = _records.StringRecord('name', tags.LIBNAME, 'Library name (bytes).')
_REFLIBS = _records.OptionalWholeRecord('reflibs', tags.REFLIBS, None)
_FONTS = _records.OptionalWholeRecord('fonts', tags.FONTS, None)
_ATTRTABLE = _records.OptionalWholeRecord('attrtable', tags.ATTRTABLE, None)
_GENERATIONS = _records.SimpleOptionalRecord('generations', tags.GENERATIONS, None)
_FORMAT = _records.FormatRecord('format', 'masks', tags.FORMAT, None, None)
_UNITS = _records.UnitsRecord('logical_unit', 'physical_unit', tags.UNITS, None, None)

@_records.stream_class
class Library(object):
    """GDSII library class.

    GDS Syntax:

          HEADER BGNLIB [LIBDIRSIZE] [SRFNAME] [LIBSECUR] LIBNAME [REFLIBS]
          [FONTS] [ATTRTABLE] [GENERATIONS] [<format>] UNITS {<structure>}* ENDLIB
    """
    _gds_objs = (_HEADER, _BGNLIB, _LIBDIRSIZE, _SRFNAME, _LIBSECUR, _LIBNAME, _REFLIBS,
            _FONTS, _ATTRTABLE, _GENERATIONS, _FORMAT, _UNITS)

    def __init__(self, unbuf_recs):
        recs = _utils.BufferedIterator(unbuf_recs)
        self._structures = []

        next(recs)
        for obj in self._gds_objs:
            obj.read(self, recs)

        # read structures starting with BGNSTR or ENDLIB
        rec = recs.current
        while True:
            if rec.tag == tags.BGNSTR:
                self._structures.append(structure.Structure(recs))
                rec = next(recs)
            elif rec.tag == tags.ENDLIB:
                break
            else:
                raise exceptions.FormatError('unexpected tag where BGNSTR or ENDLIB are expected: %d', rec.tag)

    def save(self, stream):
        for obj in self._gds_objs:
            obj.save(self, stream)
        for struc in self._structures:
            struc.save(stream)
        record.Record(tags.ENDLIB).save(stream)

    @property
    def structures(self):
        """List of structures in this library (:class:`pygdsii.structure.Structure`)."""
        return self._structures

    def __str__(self):
        return '<Library: %s>' % self.name.decode()
