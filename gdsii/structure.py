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
from . import elements, record, tags, _records
from datetime import datetime

_STRNAME = _records.StringRecord('name', tags.STRNAME, 'Structure name (bytes).')
_BGNSTR = _records.TimestampsRecord('mod_time', 'acc_time', tags.BGNSTR,
    'Last modification time (datetime).', 'Last access time (datetime).')
_STRCLASS = _records.SimpleOptionalRecord('strclass', tags.STRCLASS,
    'Structure class (int, optional).')

class Structure(object):
    """GDSII structure class."""
    _gds_objs = (_BGNSTR, _STRNAME, _STRCLASS)

    def __init__(self, name, mod_time=None, acc_time=None, strclass=None):
        self.name = name
        self.mod_time = mod_time if mod_time is not None else datetime.utcnow()
        self.acc_time = acc_time if acc_time is not None else datetime.utcnow()
        self.strclass = strclass
        self.elements = []

    @classmethod
    def _load(cls, gen):
        self = cls.__new__(cls)
        self.elements = []

        for obj in self._gds_objs:
            obj.read(self, gen)

        # read elements till ENDSTR
        while gen.current.tag != tags.ENDSTR:
            self.elements.append(elements._Base._load(gen))
        return self

    def _save(self, stream):
        for obj in self._gds_objs:
            obj.save(self, stream)
        for elem in self.elements:
            elem._save(stream)
        record.Record(tags.ENDSTR).save(stream)

    def __repr__(self):
        return '<Structure: %s>' % self.name.decode()

    def __iter__(self):
        return iter(self.elements)
