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

        +-------------------+-------------------+
        | :const:`AREF`     | :class:`ARef`     |
        +-------------------+-------------------+
        | :const:`BOUNDARY` | :class:`Boundary` |
        +-------------------+-------------------+
        | :const:`BOX`      | :class:`Box`      |
        +-------------------+-------------------+
        | :const:`NODE`     | :class:`Node`     |
        +-------------------+-------------------+
        | :const:`PATH`     | :class:`Path`     |
        +-------------------+-------------------+
        | :const:`SREF`     | :class:`SRef`     |
        +-------------------+-------------------+
        | :const:`TEXT`     | :class:`Text`     |
        +-------------------+-------------------+
"""
from __future__ import absolute_import
from . import tags, FormatError, RecordData
from ._records import (SimpleRecord, SimpleOptionalRecord, OptionalFlagsRecord,
        PropertiesRecord, XYRecord, StringRecord, ColRowRecord, STransRecord)

__all__ = (
    'Boundary',
    'Path',
    'SRef',
    'ARef',
    'Text',
    'Node',
    'Box'
)

elflags = OptionalFlagsRecord('elflags', tags.ELFLAGS, 'Element flags (bitfield).')
plex = SimpleOptionalRecord('plex', tags.PLEX, 'Plex (integer).')
layer = SimpleRecord('layer', tags.LAYER, 'Layer (integer).')
data_type = SimpleRecord('data_type', tags.DATATYPE, 'Data type (integer).')
path_type = SimpleOptionalRecord('path_type', tags.PATHTYPE, 'Path type (integer).')
width = SimpleOptionalRecord('width', tags.WIDTH, 'Width of the path (integer).')
bgn_extn = SimpleOptionalRecord('bgn_extn', tags.BGNEXTN, 'Beginning extension for path type 4 (integer, optional).')
end_extn = SimpleOptionalRecord('end_extn', tags.ENDEXTN, 'End extension for path type 4 (integer, optional).')
xy = XYRecord('xy', tags.XY, 'Points.')
struct_name = StringRecord('struct_name', tags.SNAME, 'Name of a referenced structure (byte array).')
strans = STransRecord('strans', tags.STRANS, 'Transformation flags.')
colrow = ColRowRecord('cols', 'rows', 'Number of columns (integer).', 'Number of rows (integer).')
text_type = SimpleRecord('text_type', tags.TEXTTYPE, 'Text type (integer).')
presentation = OptionalFlagsRecord('presentation', tags.PRESENTATION,
""" Bit array that specifies how the text is presented (optional).
    Meaning of bits:

    * Bits 10 and 11 specify font number (0-3).
    * Bits 12 and 13 specify vertical justification (0 - top, 1 - middle, 2 - bottom).
    * Bits 14 and 15 specify horizontal justification (0 - left, 1 - center, 2 - rigth).
""")
string = StringRecord('string', tags.STRING, 'A string as bytes array.')
node_type = SimpleRecord('node_type', tags.NODETYPE, 'Node type (integer).')
box_type = SimpleRecord('box_type', tags.BOXTYPE, 'Box type (integer).')
properties = PropertiesRecord('properties',
""" List containing properties of an element.
    Properties are represented as tuples (propattr, propvalue).
    Type of propattr is int, propvalue is bytes.
""")

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
        recs.current.check_tag(tags.ENDEL)
        next(recs)
        return self

    def save(self, stream):
        RecordData(self._gds_tag).save(stream)
        for obj in self._gds_objs:
            obj.save(self, stream)
        RecordData(tags.ENDEL).save(stream)

def element_decorator(cls):
    slots = []
    for obj in cls._gds_objs:
        for (propname, prop) in obj.props().items():
            setattr(cls, propname, prop)
            slots.append('_'+propname)
    cls.__slots__ = slots # FIXME
    return cls

@element_decorator
class Boundary(ElementBase):
    """Class for :const:`BOUNDARY` GDSII element."""
    _gds_tag = tags.BOUNDARY
    _gds_objs = (elflags, plex, layer, data_type, xy, properties)

@element_decorator
class Path(ElementBase):
    """Class for :const:`PATH` GDSII element."""
    _gds_tag = tags.PATH
    _gds_objs = (elflags, plex, layer, data_type, path_type, width, bgn_extn, end_extn, xy, properties)

@element_decorator
class SRef(ElementBase):
    """Class for :const:`SREF` GDSII element."""
    _gds_tag = tags.SREF
    _gds_objs = (elflags, plex, struct_name, strans, xy, properties)

@element_decorator
class ARef(ElementBase):
    """Class for :const:`AREF` GDSII element."""
    _gds_tag = tags.AREF
    _gds_objs = (elflags, plex, struct_name, strans, colrow, xy, properties)

@element_decorator
class Text(ElementBase):
    """Class for :const:`TEXT` GDSII element."""
    _gds_tag = tags.TEXT
    _gds_objs = (elflags, plex, layer, text_type, presentation, path_type, width, strans, xy, string, properties)

@element_decorator
class Node(ElementBase):
    """Class for :const:`NODE` GDSII element."""
    _gds_tag = tags.NODE
    _gds_objs = (elflags, plex, layer, node_type, xy)

@element_decorator
class Box(ElementBase):
    """Class for :const:`BOX` GDSII element."""
    _gds_tag = tags.BOX
    _gds_objs = (elflags, plex, layer, box_type, xy, properties)

_all_elements = (Boundary, Path, SRef, ARef, Text, Node, Box)

ElementBase._tag_to_class_map = (lambda: dict(((cls._gds_tag, cls) for cls in _all_elements)))()
