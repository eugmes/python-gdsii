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
    GDSII structure interface
    ~~~~~~~~~~~~~~~~~~~~~~~~~
"""
from __future__ import absolute_import
from . import tags, elements, record, _records

_STRNAME = _records.StringRecord('name', tags.STRNAME, 'Structure name (bytes).')
_BGNSTR = _records.TimestampsRecord('mod_time', 'acc_time', tags.BGNSTR,
    'Last modification time (datetime).', 'Last access time (datetime).')
_STRCLASS = _records.SimpleOptionalRecord('strclass', tags.STRCLASS,
    'Structure class (int, optional).')

@_records.stream_class
class Structure(object):
    """GDSII structure class."""
    _gds_objs = (_BGNSTR, _STRNAME, _STRCLASS)

    def __init__(self, recs):
        self._elements = []

        for obj in self._gds_objs:
            obj.read(self, recs)

        # read elements till ENDSTR
        while recs.current.tag != tags.ENDSTR:
            self._elements.append(elements._Base.load(recs))

    def save(self, stream):
        for obj in self._gds_objs:
            obj.save(self, stream)
        for elem in self._elements:
            elem.save(stream)
        record.Record(tags.ENDSTR).save(stream)

    @property
    def elements(self):
        """
        List of elements in the structure.
        See :mod:`pygdsii.elements` for possible elements.
        """
        return self._elements

    def __str__(self):
        return '<Structure: %s>' % self.name.decode()
