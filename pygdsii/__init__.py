# -*- coding: utf-8 -*-
"""
    pygdsii - GDSII manipulation library
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module contains basic functions and data structures for reading and
    writing of GDSII files.

    :copyright: © 2010 by Eugeniy Meshcheryakov

    .. seealso::

        :class:`pygdsii.library.Library` for object-oriented interface to GDSII library.
"""
import struct
import math
from datetime import datetime

class FormatError(Exception):
    """Base class for all GDSII exceptions."""

class EndOfFileError(FormatError):
    """Raised on unexpected end of file."""

class IncorrectDataSize(FormatError):
    """Raised if data size is incorrect."""

class UnsupportedTagType(FormatError):
    """Raised on unsupported tag type."""

class MissingRecord(FormatError):
    """Raised when required record is not found."""

class DataSizeError(FormatError):
    """Raised when data size is incorrect for a given record."""

class GDSII:
    """Type containing GDSII record tags."""
    HEADER = 0x0002
    BGNLIB = 0x0102
    LIBNAME = 0x0206
    UNITS = 0x0305
    ENDLIB = 0x0400
    BGNSTR = 0x0502
    STRNAME = 0x0606
    ENDSTR = 0x0700
    BOUNDARY = 0x0800
    PATH = 0x0900
    SREF = 0x0A00
    AREF = 0x0B00
    TEXT = 0x0C00
    LAYER = 0x0D02
    DATATYPE = 0x0E02
    WIDTH = 0x0F03
    XY = 0x1003
    ENDEL = 0x1100
    SNAME = 0x1206
    COLROW = 0x1302
    TEXTNODE = 0x1400 #
    NODE = 0x1500
    TEXTTYPE = 0x1602
    PRESENTATION = 0x1701
    # SPACING = 0x18??
    STRING = 0x1906
    STRANS = 0x1A01
    MAG = 0x1B05
    ANGLE = 0x1C05
    # UINTEGER = 0x1D??
    # USTRING = 0x1E??
    REFLIBS = 0x1F06
    FONTS = 0x2006
    PATHTYPE = 0x2102
    GENERATIONS = 0x2202
    ATTRTABLE = 0x2306
    STYPTABLE = 0x2406
    STRTYPE = 0x2502
    ELFLAGS = 0x2601
    ELKEY = 0x2703
    # LINKTYPE = 0x28??
    # LINKKEYS = 0x29??
    NODETYPE = 0x2A02
    PROPATTR = 0x2B02
    PROPVALUE = 0x2C06
    BOX = 0x2D00
    BOXTYPE = 0x2E02
    PLEX = 0x2F03
    BGNEXTN = 0x3003
    ENDEXTN = 0x3103
    TAPENUM = 0x3202
    TAPECODE = 0x3302
    STRCLASS = 0x3401
    # RESERVED = 0x3503
    FORMAT = 0x3602
    MASK = 0x3706
    ENDMASKS = 0x3800
    LIBDIRSIZE = 0x3902
    SRFNAME = 0x3A06
    LIBSECUR = 0x3B02
    # Types used only with Custom Plus
    BORDER = 0x3C00
    SOFTFENCE = 0x3D00
    HARDFENCE = 0x3E00
    SOFTWIRE = 0x3F00
    HARDWIRE = 0x4000
    PATHPORT = 0x4100
    NODEPORT = 0x4200
    USERCONSTRAINT = 0x4300
    SPACERERROR = 0x4400
    CONTACT = 0x4500

# lambda because otherwise k and v are module variables
# PYTHON3: can be simplified
_TAG_TO_NAME_MAP = (lambda:
    dict([(GDSII.__dict__[key], key) for key in dir(GDSII) if key[0] != '_'])
)()

class GDSIIType:
    """GDSII data types."""
    NODATA = 0
    BITARRAY = 1
    INT2 = 2
    INT4 = 3
    REAL4 = 4 # not used
    REAL8 = 5
    ASCII = 6

_TYPE_TO_NAME_MAP = (lambda:
    dict((GDSIIType.__dict__[key], key) for key in dir(GDSIIType) if key[0] != '_')
)()

def type_of_tag(tag):
    """
    Returns type of a tag.

    :param tag: tag ID
    :type tag: int
    :rtype: int

    Examples:

        >>> type_of_tag(GDSII.HEADER)
        2
        >>> type_of_tag(GDSII.MASK)
        6

    """
    return tag & 0xff

_RECORD_HEADER_FMT = struct.Struct('>HH')

def _read_record(stream):
    """
    Reads GDSII element. Return tuple ``(tag, data)``.
    Data is returned as string.
    Raises :exc:`EndOfFileError` if end of file is reached.
    """
    header = stream.read(4)
    if not header or len(header) != 4:
        raise EndOfFileError
    data_size, tag = _RECORD_HEADER_FMT.unpack(header)
    if data_size < 4:
        raise IncorrectDataSize('data size is too small')
    if data_size % 2:
        raise IncorrectDataSize('data size is odd')

    data_size -= 4 # substract header size

    data = stream.read(data_size)
    if len(data) != data_size:
        raise EndOfFileError

    return (tag, data)

def _parse_nodata(data):
    """
    Parse :const:`NODATA` data type.

        >>> _parse_nodata(b'')
        >>> _parse_nodata(b'something')
        Traceback (most recent call last):
            ...
        IncorrectDataSize: NODATA
    """
    if len(data):
        raise IncorrectDataSize('NODATA')

def _parse_bitarray(data):
    """
    Parse :const:`BITARRAY` data type.

        >>> _parse_bitarray(b'ab') # ok, 2 bytes
        24930
        >>> _parse_bitarray(b'abcd') # too long
        Traceback (most recent call last):
            ...
        IncorrectDataSize: BITARRAY
        >>> _parse_bitarray('') # zero bytes
        Traceback (most recent call last):
            ...
        IncorrectDataSize: BITARRAY
    """
    if len(data) != 2:
        raise IncorrectDataSize('BITARRAY')
    (val,) = struct.unpack('>H', data)
    return val

def _parse_int2(data):
    """
    Parse INT2 data type.

        >>> _parse_int2(b'abcd') # ok, even number of bytes
        (24930, 25444)
        >>> _parse_int2(b'abcde') # odd number of bytes
        Traceback (most recent call last):
            ...
        IncorrectDataSize: INT2
        >>> _parse_int2(b'') # zero bytes
        Traceback (most recent call last):
            ...
        IncorrectDataSize: INT2
    """
    if not len(data) or (len(data) % 2):
        raise IncorrectDataSize('INT2')
    return struct.unpack('>%dh' % (len(data)/2), data)

def _parse_int4(data):
    """
    Parse INT4 data type.

        >>> _parse_int4(b'abcd')
        (1633837924,)
        >>> _parse_int4(b'abcdef') # not divisible by 4
        Traceback (most recent call last):
            ...
        IncorrectDataSize: INT4
        >>> _parse_int4(b'') # zero bytes
        Traceback (most recent call last):
            ...
        IncorrectDataSize: INT4
    """
    if not len(data) or (len(data) % 4):
        raise IncorrectDataSize('INT4')
    return struct.unpack('>%dl' % (len(data)/4), data)

def _int_to_real(num):
    """
    Convert REAL8 from internal integer representation to Python reals.

    Zeroes:
        >>> print(_int_to_real(0x0))
        0.0
        >>> print(_int_to_real(0x8000000000000000)) # negative
        0.0
        >>> print(_int_to_real(0xff00000000000000)) # denormalized
        0.0

    Others:
        >>> print(_int_to_real(0x4110000000000000))
        1.0
        >>> print(_int_to_real(0xC120000000000000))
        -2.0
    """
    sgn = -1 if 0x8000000000000000 & num else 1
    mant = num & 0x00ffffffffffffff
    exp = (num >> 56) & 0x7f
    return math.ldexp(sgn * mant, 4 * (exp - 64) - 56)

def _parse_real8(data):
    """
    Parse REAL8 data type.

        >>> _parse_real8(struct.pack('>3Q', 0x0, 0x4110000000000000, 0xC120000000000000))
        (0.0, 1.0, -2.0)
        >>> _parse_real8(b'') # zero bytes
        Traceback (most recent call last):
            ...
        IncorrectDataSize: REAL8
        >>> _parse_real8(b'abcd') # not divisible by 8
        Traceback (most recent call last):
            ...
        IncorrectDataSize: REAL8
    """
    if not len(data) or (len(data) % 8):
        raise IncorrectDataSize('REAL8')
    ints = struct.unpack('>%dQ' % (len(data)/8), data)
    return tuple(_int_to_real(n) for n in ints)

def _parse_ascii(data):
    r"""
    Parse ASCII data type.

        >>> _parse_ascii(b'') # zero bytes
        Traceback (most recent call last):
            ...
        IncorrectDataSize: ASCII
        >>> _parse_ascii(b'abcde') == b'abcde'
        True
        >>> _parse_ascii(b'abcde\0') == b'abcde' # strips trailing NUL
        True
    """
    if not len(data):
        raise IncorrectDataSize('ASCII')
    # XXX cross-version compatibility
    if data[-1:] == b'\0':
        return data[:-1]
    return data

_PARSE_FUNCS = {
    GDSIIType.NODATA: _parse_nodata,
    GDSIIType.BITARRAY: _parse_bitarray,
    GDSIIType.INT2: _parse_int2,
    GDSIIType.INT4: _parse_int4,
    GDSIIType.REAL8: _parse_real8,
    GDSIIType.ASCII: _parse_ascii
}

def _pack_nodata(data):
    """
    Pack NODATA tag data. Should always return empty string::

       >>> packed = _pack_nodata([])
       >>> packed == b''
       True
       >>> len(packed)
       0
    """
    return b''

def _pack_bitarray(data):
    """
    Pack BITARRAY tag data.

        >>> packed = _pack_bitarray(123)
        >>> packed == struct.pack('>H', 123)
        True
        >>> len(packed)
        2
    """
    return struct.pack('>H', data)

def _pack_int2(data):
    """
    Pack INT2 tag data.

        >>> _pack_int2([1, 2, -3]) == struct.pack('>3h', 1, 2, -3)
        True
        >>> packed = _pack_int2((1, 2, 3))
        >>> packed == struct.pack('>3h', 1, 2, 3)
        True
        >>> len(packed)
        6
    """
    size = len(data)
    return struct.pack('>{0}h'.format(size), *data)

def _pack_int4(data):
    """
    Pack INT4 tag data.

        >>> _pack_int4([1, 2, -3]) == struct.pack('>3l', 1, 2, -3)
        True
        >>> packed = _pack_int4((1, 2, 3))
        >>> packed == struct.pack('>3l', 1, 2, 3)
        True
        >>> len(packed)
        12
    """
    size = len(data)
    return struct.pack('>{0}l'.format(size), *data)

def _real_to_int(fnum):
    """
    Convert REAL8 from Python real to internal integer representation.

        >>> '0x%016x' % _real_to_int(0.0)
        '0x0000000000000000'
        >>> print(_int_to_real(_real_to_int(1.0)))
        1.0
        >>> print(_int_to_real(_real_to_int(-2.0)))
        -2.0
        >>> print(_int_to_real(_real_to_int(1e-9)))
        1e-09
    """
    # first convert number to IEEE double and split it in parts
    (ieee,) = struct.unpack('=Q', struct.pack('=d', fnum))
    sign = ieee & 0x8000000000000000
    ieee_exp = (ieee >> 52) & 0x7ff
    ieee_mant = ieee & 0xfffffffffffff

    if ieee_exp == 0:
        # zero or denormals
        # TODO maybe handle denormals
        return 0

    # substract exponent bias
    unb_ieee_exp = ieee_exp - 1023
    # add leading one and move to GDSII position
    ieee_mant_full = (ieee_mant + 0x10000000000000) << 3

    # convert exponent to 16-based, +1 for differences in presentation
    # of mantissa (1.xxxx in EEEE and 0.1xxxxx in GDSII
    exp16, rest = divmod(unb_ieee_exp + 1, 4)
    # compensate exponent converion
    if rest:
        rest = 4 - rest
        exp16 += 1
    ieee_mant_comp = ieee_mant_full >> rest

    # add GDSII exponent bias
    exp16_biased = exp16 + 64

    # try to fit everything
    if exp16_biased < -14:
        return 0 # number is too small. FIXME is it possible?
    elif exp16_biased < 0:
        ieee_mant_comp = ieee_mant_comp >> (exp16_biased * 4)
        exp16_biased = 0
    elif exp16_biased > 0x7f:
        raise FormatError('number is to big for REAL8')

    return sign | (exp16_biased << 56) | ieee_mant_comp

def _pack_real8(data):
    """
    Pack REAL8 tag data.

        >>> packed = _pack_real8([0, 1, -1, 0.5, 1e-9])
        >>> len(packed)
        40
        >>> list(map(str, _parse_real8(packed)))
        ['0.0', '1.0', '-1.0', '0.5', '1e-09']
    """
    size = len(data)
    return struct.pack('>{0}Q'.format(size), *[_real_to_int(num) for num in data])

def _pack_ascii(data):
    r"""
    Pack ASCII tag data.

        >>> _pack_ascii(b'abcd') == b'abcd'
        True
        >>> _pack_ascii(b'abc') == b'abc\0'
        True
    """
    size = len(data)
    if size % 2:
        return data + b'\0'
    return data

_PACK_FUNCS = {
    GDSIIType.NODATA: _pack_nodata,
    GDSIIType.BITARRAY: _pack_bitarray,
    GDSIIType.INT2: _pack_int2,
    GDSIIType.INT4: _pack_int4,
    GDSIIType.REAL8: _pack_real8,
    GDSIIType.ASCII: _pack_ascii
}
# TODO implement lazy parsing, maybe
class RecordData(object):
    """
    Class for representing a GDSII record with attached data.
    Example::

        >>> r = RecordData(GDSII.STRNAME, 'my_structure')
        >>> '%04x' % r.tag
        '0606'
        >>> r.tag_name
        'STRNAME'
        >>> r.tag_type
        6
        >>> r.tag_type_name
        'ASCII'
        >>> r.data
        'my_structure'

        >>> r = RecordData(0xffff, 'xxx') # Unknown tag type
        >>> r.tag_name
        '0xffff'
        >>> r.tag_type_name
        '0xff'
    """
    __slots__ = ['_tag', '_data']

    def __init__(self, tag, data):
        """Initialize with tag and parsed data."""
        self._tag = tag
        self._data = data

    def check_tag(self, tag):
        """
        Checks if current record has the same tag as the given one.
        Raises :exc:`MissingRecord` exception otherwise. For example::

            >>> rec = RecordData(GDSII.STRNAME, 'struct')
            >>> rec.check_tag(GDSII.STRNAME)
            >>> rec.check_tag(GDSII.DATATYPE)
            Traceback (most recent call last):
                ...
            MissingRecord: 1542
        """
        if self._tag != tag:
            raise MissingRecord(self._tag)

    def check_size(self, size):
        """
        Checks if data size equals to the given size.
        Raises :exc:`DataSizeError` otherwise. For example::

            >>> rec = RecordData(GDSII.DATATYPE, (0,))
            >>> rec.check_size(1)
            >>> rec.check_size(5)
            Traceback (most recent call last):
                ...
            DataSizeError: 3586
        """
        if len(self._data) != size:
            raise DataSizeError(self._tag)

    @classmethod
    def read(cls, stream):
        """
        Read a GDSII record from file.

        :param stream: GDS file opened for reading in binary mode
        :returns: a new :class:`RecordData` instance
        :raises: :exc:`UnsupportedTagType` if data cannot be parsed
        :raises: :exc:`EndOfFileError` if end of file is reached
        """
        tag, data = _read_record(stream)
        typ = type_of_tag(tag)
        try:
            parse_func = _PARSE_FUNCS[typ]
        except KeyError:
            raise UnsupportedTagType(typ)
        return cls(tag, parse_func(data))

    def save(self, stream):
        """
        Save record to a GDS file.

        :param stream: file opened for writing in binary mode
        :raises: :exc:`UnsupportedTagType` if tag type is not supported
        :raises: :exc:`FormatError` on incorrect data sizes, etc
        :raises: whatever :func:`struct.pack` can raise
        """
        tag_type = self.tag_type
        try:
            pack_func = _PACK_FUNCS[tag_type]
        except KeyError:
            raise UnsupportedTagType(tag_type)
        packed_data = pack_func(self._data)
        record_size = len(packed_data) + 4
        if record_size > 0xFFFF:
            raise FormatError('data size is too big')
        header = struct.pack('>HH', record_size, self._tag)
        stream.write(header)
        stream.write(packed_data)

    @property
    def tag(self):
        """Tag ID."""
        return self._tag

    @property
    def tag_name(self):
        """Tag name, if known, otherwise tag ID formatted as hex number."""
        if self._tag in _TAG_TO_NAME_MAP:
            return _TAG_TO_NAME_MAP[self._tag]
        return '0x%04x' % self._tag

    @property
    def tag_type(self):
        """Tag data type ID."""
        return type_of_tag(self._tag)

    @property
    def tag_type_name(self):
        """Tag data type name, if known, and formatted number otherwise."""
        typ = type_of_tag(self._tag)
        if typ in _TYPE_TO_NAME_MAP:
            return _TYPE_TO_NAME_MAP[typ]
        return '0x%02x' % typ

    @property
    def data(self):
        """Parsed data."""
        return self._data

    @property
    def points(self):
        """
        Convert data to list of points. Useful for :const:`XY` record.
        Raises :exc:`DataSizeError` if data size is incorrect.
        For example::

            >>> r = RecordData(GDSII.XY, [0, 1, 2, 3])
            >>> r.points
            [(0, 1), (2, 3)]
            >>> r = RecordData(GDSII.XY, []) # not allowed
            >>> r.points
            Traceback (most recent call last):
                ...
            DataSizeError: 4099
            >>> r = RecordData(GDSII.XY, [1, 2, 3]) # odd number of coordinates
            >>> r.points
            Traceback (most recent call last):
                ...
            DataSizeError: 4099
        """
        data_size = len(self._data)
        if not data_size or (data_size % 2):
            raise DataSizeError(self._tag)
        return [(self._data[i], self._data[i+1]) for i in range(0, data_size, 2)]

    @property
    def times(self):
        """
        Convert data to tuple ``(modification time, access time)``.
        Useful for :const:`BGNLIB` and :const:`BGNSTR`.

            >>> r = RecordData(GDSII.BGNLIB, [100, 1, 1, 1, 2, 3, 110, 8, 14, 21, 10, 35])
            >>> print(r.times[0].isoformat())
            2000-01-01T01:02:03
            >>> print(r.times[1].isoformat())
            2010-08-14T21:10:35
            >>> r = RecordData(GDSII.BGNLIB, [100, 1, 1, 1, 2, 3]) # wrong data length
            >>> r.times
            Traceback (most recent call last):
                ...
            DataSizeError: 258
        """
        if len(self._data) != 12:
            raise DataSizeError(self._tag)
        return (datetime(self._data[0]+1900, *self._data[1:6]),
                datetime(self._data[6]+1900, *self._data[7:12]))

def all_records(stream):
    """
    Generator function for iterating over all records in a GDSII file.
    Yields :class:`RecordData` objects.

    :param stream: GDS file opened for reading in binary mode
    """
    last = False
    while not last:
        rec = RecordData.read(stream)
        if rec.tag == GDSII.ENDLIB:
            last = True
        yield rec

def _ignore_record(recs, lastrec, tag):
    """
    Returns next record is ``lastrec`` has given tag,
    otherwise returns ``lastrec``.

    :param recs: :class:`RecordData` generator
    :type recs: iterable
    :param lastrec: last read record
    :type lastrec: :class:`RecordData`
    """
    if lastrec.tag != tag:
        return lastrec
    return next(recs)

if __name__ == '__main__':
    import doctest
    doctest.testmod()
