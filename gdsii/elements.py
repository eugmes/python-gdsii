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
    GDSII element classes
    ~~~~~~~~~~~~~~~~~~~~~

    This module contains definitions for classes representing
    various GDSII elements. Mapping between GDSII elements and
    classes is given in the following table:

        +-------------------+--------------------------+
        | :const:`AREF`     | :class:`ARefElement`     |
        +-------------------+--------------------------+
        | :const:`BOUNDARY` | :class:`BoundaryElement` |
        +-------------------+--------------------------+
        | :const:`BOX`      | :class:`BoxElement`      |
        +-------------------+--------------------------+
        | :const:`NODE`     | :class:`NodeElement`     |
        +-------------------+--------------------------+
        | :const:`PATH`     | :class:`PathElement`     |
        +-------------------+--------------------------+
        | :const:`SREF`     | :class:`SRefElement`     |
        +-------------------+--------------------------+
        | :const:`TEXT`     | :class:`TextElement`     |
        +-------------------+--------------------------+
"""
from __future__ import absolute_import
from . import GDSII, FormatError, RecordData
from ._records import (elflags, plex, layer, data_type, path_type, width, bgn_extn,
        end_extn, xy, struct_name, strans, colrow, text_type, presentation, string,
        node_type, box_type, properties)

__all__ = (
    'BoundaryElement',
    'PathElement',
    'SRefElement',
    'ARefElement',
    'TextElement',
    'NodeElement',
    'BoxElement'
)

class ElementBase(object):
    """Base class for all GDSII elements."""

    @classmethod
    def load(cls, recs):
        """
        Load an element from file using given generator `recs`.

        :param recs: :class:`pygdsii.RecordData` generator
        :returns: new element of class defined by `recs`
        """
        element_class = cls._tag_to_class_map[recs.current.tag]
        if not element_class:
            raise FormatError('unexpected element tag')
        # do not call __init__() during reading from file
        # __init__() should require some arguments
        new_element = element_class._read_element(recs)
        return new_element

    @classmethod
    def _read_element(cls, recs):
        """Read element using `recs` generator."""
        self = cls.__new__(cls)
        next(recs)
        for obj in self._gds_objs:
            obj.read(self, recs)
        recs.current.check_tag(GDSII.ENDEL)
        next(recs)
        return self

    def save(self, stream):
        RecordData(self._gds_tag).save(stream)
        for obj in self._gds_objs:
            obj.save(self, stream)
        RecordData(GDSII.ENDEL).save(stream)

def element_decorator(cls):
    slots = []
    for obj in cls._gds_objs:
        for (propname, prop) in obj.props().items():
            setattr(cls, propname, prop)
            slots.append('_'+propname)
    cls.__slots__ = slots # FIXME
    return cls

@element_decorator
class BoundaryElement(ElementBase):
    """Class for :const:`BOUNDARY` GDSII element."""
    _gds_tag = GDSII.BOUNDARY
    _gds_objs = (elflags, plex, layer, data_type, xy, properties)

@element_decorator
class PathElement(ElementBase):
    """Class for :const:`PATH` GDSII element."""
    _gds_tag = GDSII.PATH
    _gds_objs = (elflags, plex, layer, data_type, path_type, width, bgn_extn, end_extn, xy, properties)

@element_decorator
class SRefElement(ElementBase):
    """Class for :const:`SREF` GDSII element."""
    _gds_tag = GDSII.SREF
    _gds_objs = (elflags, plex, struct_name, strans, xy, properties)

@element_decorator
class ARefElement(ElementBase):
    """Class for :const:`AREF` GDSII element."""
    _gds_tag = GDSII.AREF
    _gds_objs = (elflags, plex, struct_name, strans, colrow, xy, properties)

@element_decorator
class TextElement(ElementBase):
    """Class for :const:`TEXT` GDSII element."""
    _gds_tag = GDSII.TEXT
    _gds_objs = (elflags, plex, layer, text_type, presentation, path_type, width, strans, xy, string, properties)

@element_decorator
class NodeElement(ElementBase):
    """Class for :const:`NODE` GDSII element."""
    _gds_tag = GDSII.NODE
    _gds_objs = (elflags, plex, layer, node_type, xy)

@element_decorator
class BoxElement(ElementBase):
    """Class for :const:`BOX` GDSII element."""
    _gds_tag = GDSII.BOX
    _gds_objs = (elflags, plex, layer, box_type, xy, properties)

_all_elements = (BoundaryElement, PathElement, SRefElement, ARefElement, TextElement, NodeElement, BoxElement)

ElementBase._tag_to_class_map = (lambda: dict(((cls._gds_tag, cls) for cls in _all_elements)))()
