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
from . import GDSII, FormatError, _ignore_record

class ElementBase(object):
    """Base class for all GDSII elements."""
    __slots__ = ['_properties']

    def __init__(self, properties):
        """
        Initialize an element.
        Accepts list of attributes as keyword arguments.
        """
        self._properties = properties

    @classmethod
    def load(cls, recs, lastrec):
        """
        Load an element from file using given generator `recs`.

        :param recs: :class:`pygdsii.RecordData` generator
        :param lastrec: first record of an element
        :type lastrec: :class:`pygdsii.RecordData`
        :returns: new element of class defined by `recs`
        """
        element_class = cls._tag_to_class_map[lastrec.tag]
        if not element_class:
            raise FormatError('unexpected element tag')
        # do not call __init__() during reading from file
        # __init__() should require some arguments
        new_element = cls.__new__(element_class)
        new_element._read_element(recs)
        return new_element

    def _read_start(self, recs):
        """Ignores common optional records and returns next one."""
        self._properties = []
        # ignore ELFLAGS, PLEX
        rec = _ignore_record(recs, next(recs), GDSII.ELFLAGS)
        rec = _ignore_record(recs, rec, GDSII.PLEX)
        return rec

    def _read_rest(self, recs):
        """Reads properties and :const:`ENDEL`."""
        while True:
            rec = next(recs)
            if rec.tag == GDSII.PROPATTR:
                rec.check_size(1)
                propattr = rec.data[0]
                rec = next(rec)
                rec.check_tag(GDSII.PROPVALUE)
                self._properties[propattr] = rec.data
            elif rec.tag == GDSII.ENDEL:
                break
            else:
                raise FormatError('unexpected tag where PROPATTR or ENDEL are expected')
    
    def _read_element(self, recs):
        """Read element using `recs` generator."""
        raise NotImplementedError

    # TODO delete
    @property
    def properties(self):
        """
        Dictionary containing properties of an element.
        Keys should be integers. Values are byte strings.
        """
        return self._properties

class ElementWithLayer(ElementBase):
    """Abstract base class for all elements containing :const:`LAYER`."""
    __slots__ = ['_layer']

    def __init__(self, layer, properties):
        ElementBase.__init__(self, properties)
        self._layer = layer

    def _read_start(self, recs):
        """Reads layer definition and returns :const:`None`."""
        rec = ElementBase._read_start(self, recs)
        rec.check_tag(GDSII.LAYER)
        rec.check_size(1)
        self._layer = rec.data[0]

    @property
    def layer(self):
        """Layer (integer)."""
        return self._layer

class ElementWithLayerAndDataType(ElementWithLayer):
    """Abstract base class for all elements with :const:`LAYER` and :const:`DATATYPE`."""
    __slots__ = ['_data_type']

    def __init__(self, layer, data_type, properties):
        ElementWithLayer.__init__(self, layer, properties)
        self._data_type = data_type

    def _read_start(self, recs):
        ElementWithLayer._read_start(self, recs)
        rec = next(recs)
        rec.check_tag(GDSII.DATATYPE)
        rec.check_size(1)
        self._data_type = rec.data[0]

    @property
    def data_type(self):
        """Data type (integer)."""
        return self._data_type

class ReferenceElement(ElementBase):
    """Abstract base class for reference elements, :const:`SREF` and :const:`AREF`."""
    __slots__ = ['_struct_name', '_strans', '_mag', '_angle', '_point']

    def _read_start(self, recs):
        rec = ElementBase._read_start(self, recs)
        rec.check_tag(GDSII.SNAME)
        self._struct_name = rec.data
        self._strans = None
        self._mag = None
        self._angle = None
        rec = next(recs)
        if rec.tag == GDSII.STRANS:
            self._strans = rec.data
            rec = next(recs)
            if rec.tag == GDSII.MAG:
                rec.check_size(1)
                self._mag = rec.data[0]
                rec = next(recs)
            if rec.tag == GDSII.ANGLE:
                rec.check_size(1)
                self._angle = rec.data[0]
                rec = next(recs)
        return rec

    def __init__(self, struct_name, point, strans, mag, angle, properties):
        ElementBase.__init__(self, properties)
        self._struct_name = struct_name
        self._point = point
        self._strans = strans
        self._mag = mag
        self._angle = angle

    @property
    def struct_name(self):
        """Name of a referenced structure (byte array)."""
        return self._struct_name

    @property
    def strans(self):
        return self._strans

    @property
    def mag(self):
        """Magnification (real, optional)."""
        return self._mag

    @property
    def angle(self):
        """Rotation angle (real, optional)."""
        return self._angle

    @property
    def point(self):
        return self._point


class BoundaryElement(ElementWithLayerAndDataType):
    """Class for :const:`BOUNDARY` GDSII element."""
    __slots__ = ['_points']

    def __init__(self, layer, data_type, points, properties=[]):
        ElementWithLayerAndDataType.__init__(self, layer, data_type, properties)
        self._points = points
        # TODO check if passed points are valid

    def _read_element(self, recs):
        self._read_start(recs)
        rec = next(recs)
        rec.check_tag(GDSII.XY)
        points = rec.points
        if len(points) < 4:
            raise FormatError('less then 4 points in BOUNDARY')
        if points[0] != points[-1]:
            raise FormatError('BOUNDARY should be closed')
        self._points = points[:-1]
        self._read_rest(recs)

    @property
    def points(self):
        """
        List of points.
        At least 3 are required for a valid element.
        """
        return self._points

class PathElement(ElementWithLayerAndDataType):
    """Class for :const:`PATH` GDSII element."""
    __slots__ = ['_path_type', '_width', '_bgn_extn', '_end_extn', '_points']

    def __init__(self, layer, data_type, points,
            path_type = None, width=None, bgn_extn=None, end_extn=None, properties=[]):
        ElementWithLayerAndDataType.__init__(self, layer, data_type, properties)
        self._points = points
        # TODO Check if points are valid
        self._path_type = path_type
        self._width = width
        self._bgn_extn = bgn_extn
        self._end_extn = end_extn

    def _read_element(self, recs):
        self._read_start(recs)
        self._path_type = None
        self._width = None
        self._bgn_extn = None
        self._end_extn = None
        rec = next(recs)
        if rec.tag == GDSII.PATHTYPE:
            rec.check_size(1)
            self._path_type = rec.data[0]
            rec = next(recs)
        if rec.tag == GDSII.WIDTH:
            rec.check_size(1)
            self._width = rec.data[0]
            rec = next(recs)
        if rec.tag == GDSII.BGNEXTN:
            rec.check_size(1)
            self._bgn_extn = rec.data[0]
            rec = next(recs)
        if rec.tag == GDSII.ENDEXTN:
            rec.check_size(1)
            self._end_extn = rec.data[0]
            rec = next(recs)
        rec.check_tag(GDSII.XY)
        self._points = rec.points
        if len(self._points) < 2:
            raise FormatError('less then 2 points in PATH')
        self._read_rest(recs)

    @property
    def path_type(self):
        """
        Path type (integer, optional). Meaning:

        * 0 - square ends, flush with endpoints
        * 1 - round ends, centered at endpoints
        * 2 - square ends, centered at endpoints
        * 4 - square ends, extended by :attr:`bgn_extn` and :attr:`end_extn`
        """
        return self._path_type

    @property
    def width(self):
        """
        Width of the path (integer, optional).
        Absoute if negative.
        """
        return self._width

    @property
    def bgn_extn(self):
        """Beginning extension for path type 4 (integer, optional)."""
        return self._bgn_extn

    @property
    def end_extn(self):
        """End extension for path type 4 (integer, optional)."""
        return self._end_extn

    @property
    def points(self):
        """
        List of points.
        At least 2 are required for a valid element.
        """
        return self._points

class SRefElement(ReferenceElement):
    """Class for :const:`SREF` GDSII element."""

    def __init__(self, struct_name, point, strans=None, mag=None, angle=None, properties=[]):
        ReferenceElement.__init__(self, struct_name, point, strans, mag, angle, properties)

    def _read_element(self, recs):
        rec = self._read_start(recs)
        rec.check_tag(GDSII.XY)
        points = rec.points
        if len(points) != 1:
            raise FormatError('SREF should contain 1 point')
        self._point = points[0]
        self._read_rest(recs)

class ARefElement(ReferenceElement):
    """Class for :const:`AREF` GDSII element."""
    __slots__ = ['_cols', '_rows', '_col_off', '_row_off']

    def __init__(self, struct_name, point, cols, rows, col_off, row_off,
            strans=None, mag=None, angle=None, properties=[]):
        ReferenceElement.__init__(self, struct_name, point, strans, mag, angle, properties)
        self._cols = cols
        self._rows = rows
        self._col_off = col_off
        self._row_off = row_off

    def _read_element(self, recs):
        rec = self._read_start(recs)
        rec.check_tag(GDSII.COLROW)
        rec.check_size(2)
        self._cols, self._rows = rec.data
        
        rec = next(recs)
        rec.check_tag(GDSII.XY)
        points = rec.points
        if len(points) != 3:
            raise FormatError('AREF should contain 3 points')
        self._point, self._col_off, self._row_off = points
        self._read_rest(recs)

    @property
    def cols(self):
        """Number of columns (integer)."""
        return self._cols

    @property
    def rows(self):
        """Number of rows (integer)."""
        return self._rows

    @property
    def col_off(self):
        return self._col_off

    @property
    def row_off(self):
        return self._row_off

class TextElement(ElementWithLayer):
    """Class for :const:`TEXT` GDSII element."""
    __slots__ = ['_text_type', '_presentation', '_path_type', '_width', '_strans', '_mag', '_angle', '_point', '_string']
    def __init__(self, layer, text_type, point, string,
            presentation=None, path_type=None, width=None, strans=None, mag=None, angle=None, properties=[]):
        ElementWithLayer.__init__(self, layer, properties)
        self._text_type = text_type
        self._presentation = presentation
        self._path_type = path_type
        self._width = width
        self._strans = strans
        self._mag = mag
        self._angle = angle
        self._point = point
        # TODO check points
        self._string = string
        # TODO check string

    def _read_element(self, recs):
        self._read_start(recs)
        rec = next(recs)
        rec.check_tag(GDSII.TEXTTYPE)
        rec.check_size(1)
        self._text_type = rec.data[0]

        self._presentation = None
        self._path_type = None
        self._width = None
        self._strans = None
        self._mag = None
        self._angle = None

        rec = next(recs)
        if rec.tag == GDSII.PRESENTATION:
            self._presentation = rec.data
            rec = next(recs)

        if rec.tag == GDSII.PATHTYPE:
            rec.check_size(1)
            self._path_type = rec.data[0]
            rec = next(recs)

        if rec.tag == GDSII.WIDTH:
            rec.check_size(1)
            self._width = rec.data[0]
            rec = next(recs)

        if rec.tag == GDSII.STRANS:
            self._strans = rec.data
            
            rec = next(recs)
            if rec.tag == GDSII.MAG:
                rec.check_size(1)
                self._mag = rec.data[0]
                rec = next(recs)
            if rec.tag == GDSII.ANGLE:
                rec.check_size(1)
                self._angle = rec.data[0]
                rec = next(recs)

        rec.check_tag(GDSII.XY)
        points = rec.points
        if len(points) != 1:
            raise FormatError('TEXT should contain 1 point')
        self._point = points[0]

        rec = next(recs)
        rec.check_tag(GDSII.STRING)
        self._string = rec.data

        self._read_rest(recs)


    @property
    def text_type(self):
        """Text type (integer)."""
        return self._text_type

    @property
    def presentation(self):
        """
        Bit array that specifies how the text is presented (optional).
        Meaning of bits:

        * Bits 10 and 11 specify font number (0-3).
        * Bits 12 and 13 specify vertical justification (0 - top, 1 - middle, 2 - bottom).
        * Bits 14 and 15 specify horizontal justification (0 - left, 1 - center, 2 - rigth).
        """
        return self._presentation

    @property
    def width(self):
        """
        Width of the path (integer, optional).
        Absoulte if negative.
        """
        return self._width

    @property
    def path_type(self):
        return self._path_type

    @property
    def strans(self):
        """
        Bit array that specifies transformation (optional).
        Bit 0 specifies reflection.
        """
        return self._strans

    @property
    def mag(self):
        """Magnification (real, optional)."""
        return self._mag

    @property
    def angle(self):
        """Rotation angle (real, optional)."""
        return self._angle

    @property
    def point(self):
        return self._point

    @property
    def string(self):
        """A string as bytes array."""
        return self._string

class NodeElement(ElementWithLayer):
    """Class for :const:`NODE` GDSII element."""
    __slots__ = ['_node_type', '_points']

    def __init__(self, layer, node_type, points, properties=[]):
        ElementWithLayer.__init__(self, layer, properties)
        self._node_type = node_type
        self._points = points
        # TODO check points

    def _read_element(self, recs):
        self._read_start(recs)

        rec = next(recs)
        rec.check_tag(GDSII.NODETYPE)
        rec.check_size(1)
        self._node_type = rec.data[0]

        rec = next(recs)
        rec.check_tag(GDSII.XY)
        self._points = rec.points
        if len(self._points) < 1:
            raise FormatError('NODE should contain at least 1 point')

        self._read_rest(recs)
    
    @property
    def node_type(self):
        """Node type (integer)."""
        return self._node_type

    @property
    def points(self):
        return self._points

class BoxElement(ElementWithLayer):
    """Class for :const:`BOX` GDSII element."""
    __slots__ = ['_box_type', '_points']

    def __init__(self, layer, box_type, points, properties=[]):
        ElementWithLayer.__init__(self, layer, properties)
        self._box_type = box_type
        self._points = points
        # TODO check points

    def _read_element(self, recs):
        self._read_start(recs)

        rec = next(recs)
        rec.check_tag(GDSII.BOXTYPE)
        rec.check_size(1)
        self._box_type = rec.data[0]

        rec = next(recs)
        rec.check_tag(GDSII.XY)
        points = rec.points
        if len(points) != 5:
            raise FormatError('BOX should contain 5 points')
        if points[0] != points[-1]:
            raise FormatError('BOX should be closed')
        self._points = points[:-1]

        self._read_rest(recs)
    
    @property
    def box_type(self):
        """Box type (integer)."""
        return self._box_type

    @property
    def points(self):
        return self._points

ElementBase._tag_to_class_map = {
    GDSII.BOUNDARY: BoundaryElement,
    GDSII.PATH: PathElement,
    GDSII.SREF: SRefElement,
    GDSII.AREF: ARefElement,
    GDSII.TEXT: TextElement,
    GDSII.NODE: NodeElement,
    GDSII.BOX: BoxElement
}
