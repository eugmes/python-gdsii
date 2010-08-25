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
from . import GDSII, FormatError
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
        return self

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
    _gds_objs = (elflags, plex, layer, data_type, xy, properties)

@element_decorator
class PathElement(ElementBase):
    """Class for :const:`PATH` GDSII element."""
    _gds_objs = (elflags, plex, layer, data_type, path_type, width, bgn_extn, end_extn, xy, properties)

@element_decorator
class SRefElement(ElementBase):
    """Class for :const:`SREF` GDSII element."""
    _gds_objs = (elflags, plex, struct_name, strans, xy, properties)

@element_decorator
class ARefElement(ElementBase):
    """Class for :const:`AREF` GDSII element."""
    _gds_objs = (elflags, plex, struct_name, strans, colrow, xy, properties)

@element_decorator
class TextElement(ElementBase):
    """Class for :const:`TEXT` GDSII element."""
    _gds_objs = (elflags, plex, layer, text_type, presentation, path_type, width, strans, xy, string, properties)

@element_decorator
class NodeElement(ElementBase):
    """Class for :const:`NODE` GDSII element."""
    _gds_objs = (elflags, plex, layer, node_type, xy)

@element_decorator
class BoxElement(ElementBase):
    """Class for :const:`BOX` GDSII element."""
    _gds_objs = (elflags, plex, layer, xy, properties)

ElementBase._tag_to_class_map = {
    GDSII.BOUNDARY: BoundaryElement,
    GDSII.PATH: PathElement,
    GDSII.SREF: SRefElement,
    GDSII.AREF: ARefElement,
    GDSII.TEXT: TextElement,
    GDSII.NODE: NodeElement,
    GDSII.BOX: BoxElement
}
