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
from . import tags, _ignore_record, RecordData
from .elements import ElementBase

class Structure(object):
    """GDSII structure class."""

    __slots__ = ['_mod_time', '_acc_time', '_name', '_elements']

    def __init__(self, recs):
        self._elements = []

        self._mod_time, self._acc_time = recs.current.times

        # STRNAME
        rec = next(recs)
        rec.check_tag(tags.STRNAME)
        self._name = rec.data

        # ignore STRCLASS
        rec = _ignore_record(recs, next(recs), tags.STRCLASS)

        # read elements till ENDSTR
        while recs.current.tag != tags.ENDSTR:
            self._elements.append(ElementBase.load(recs))

    def save(self, stream):
        RecordData(tags.BGNSTR, times=(self._mod_time, self._acc_time)).save(stream)
        RecordData(tags.STRNAME, self._name).save(stream)
        # ignore STRCLASS
        for elem in self._elements:
            elem.save(stream)
        RecordData(tags.ENDSTR).save(stream)

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
