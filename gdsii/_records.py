from __future__ import absolute_import
from . import GDSII

class AbstractRecord(object):
    def __init__(self, variable, doc):
        self.variable = variable
        self.priv_variable = '_' + variable
        self.doc = doc

    def getter(self):
        def f(obj):
            return getattr(obj, self.priv_variable)
        return f

    def setter(self):
        def f(obj, value):
            setattr(obj, self.priv_variable)
        return f

    def props(self):
        return {
                self.variable: property(self.getter(), self.setter(), doc=self.doc)
        }
    
    def read(self, instance, gen):
        raise NotImplementedError

    def __repr__(self):
        return '<property: %s>'%self.variable

class SimpleRecord(AbstractRecord):
    def __init__(self, variable, gds_record, doc):
        AbstractRecord.__init__(self, variable, doc)
        self.gds_record = gds_record

    def read(self, instance, gen):
        rec = gen.current
        rec.check_tag(self.gds_record)
        rec.check_size(1)
        setattr(instance, self.priv_variable, rec.data[0])
        next(gen)

class SimpleOptionalRecord(SimpleRecord):
    def read(self, instance, gen):
        rec = gen.current
        if rec.tag == self.gds_record:
            rec.check_size(1)
            setattr(instance, self.priv_variable, rec.data[0])
            next(gen)

class OptionalFlagsRecord(SimpleRecord):
    def read(self, instance, gen):
        rec = gen.current
        if rec.tag == self.gds_record:
            setattr(instance, self.priv_variable, rec.data)
            next(gen)

class PropertiesRecord(AbstractRecord):
    def read(self, instance, gen):
        rec = gen.current
        props = dict()
        while rec.tag == GDSII.PROPATTR:
            rec.check_size(1)
            propattr = rec.data[0]
            rec = next(gen)
            rec.check_tag(self.gds_record)
            props[propattr] = rec.data
            rec = next(gen)
        setattr(instance, self.priv_variable, props)

class XYRecord(SimpleRecord):
    def read(self, instance, gen):
        rec = gen.current
        rec.check_tag(self.gds_record)
        setattr(instance, self.priv_variable, rec.points)
        next(gen)

class StringRecord(SimpleRecord):
    def read(self, instance, gen):
        rec = gen.current
        rec.check_tag(self.gds_record)
        setattr(instance, self.priv_variable, rec.data)
        next(gen)

class ColRowRecord(AbstractRecord):
    def __init__(self, variable1, variable2, doc1, doc2):
        AbstractRecord.__init__(self, variable1, doc1)
        self.variable2 = variable2
        self.priv_variable2 = '_' + variable2
        self.doc2 = doc2

    def getter2(self):
        def f(obj):
            return getattr(obj, self.priv_variable2)
        return f

    def setter2(self):
        def f(obj, value):
            setattr(obj, self.priv_variable2)
        return f

    def props(self):
        res = AbstractRecord.props(self)
        res[self.variable2] =  property(self.getter2(), self.setter2(), doc=self.doc2)
        return res

    def read(self, instance, gen):
        rec = gen.current
        rec.check_tag(GDSII.COLROW)
        rec.check_size(2)
        cols, rows = rec.data
        setattr(instance, self.priv_variable, cols)
        setattr(instance, self.priv_variable2, rows)
        next(gen)

class STransPrroperty(OptionalFlagsRecord):
    mag = SimpleOptionalRecord('mag', GDSII.MAG, 'Magnification (real, optional).')
    angle = SimpleOptionalRecord('angle', GDSII.ANGLE, 'Rotation angle (real, optional).')

    def props(self):
        res = dict(list(self.mag.props().items()) +
                list(self.angle.props().items()) +
                list(OptionalFlagsRecord.props(self).items()))
        return res

    def read(self, instance, gen):
        rec = gen.current
        if rec.tag == self.gds_record:
            setattr(instance, self.priv_variable, rec.data)
            next(gen)
            self.mag.read(instance, gen)
            self.angle.read(instance, gen)

elflags = OptionalFlagsRecord('elflags', GDSII.ELFLAGS, 'Element flags (bitfield).')
plex = SimpleOptionalRecord('plex', GDSII.PLEX, 'Plex (integer).')
layer = SimpleRecord('layer', GDSII.LAYER, 'Layer (integer).')
data_type = SimpleRecord('data_type', GDSII.DATATYPE, 'Data type (integer).')
path_type = SimpleOptionalRecord('path_type', GDSII.PATHTYPE, 'Path type (integer).')
width = SimpleOptionalRecord('width', GDSII.WIDTH, 'Width of the path (integer).')
bgn_extn = SimpleOptionalRecord('bgn_extn', GDSII.BGNEXTN, 'Beginning extension for path type 4 (integer, optional).')
end_extn = SimpleOptionalRecord('end_extn', GDSII.ENDEXTN, 'End extension for path type 4 (integer, optional).')
xy = XYRecord('xy', GDSII.XY, 'Points.')
struct_name = StringRecord('struct_name', GDSII.SNAME, 'Name of a referenced structure (byte array).')
strans = STransPrroperty('strans', GDSII.STRANS, 'Transformation flags.')
colrow = ColRowRecord('cols', 'rows', 'Number of columns (integer).', 'Number of rows (integer).')
text_type = SimpleRecord('text_type', GDSII.TEXTTYPE, 'Text type (integer).')
presentation = OptionalFlagsRecord('presentation', GDSII.PRESENTATION,"""
    Bit array that specifies how the text is presented (optional).
    Meaning of bits:

    * Bits 10 and 11 specify font number (0-3).
    * Bits 12 and 13 specify vertical justification (0 - top, 1 - middle, 2 - bottom).
    * Bits 14 and 15 specify horizontal justification (0 - left, 1 - center, 2 - rigth).
""")
string = StringRecord('string', GDSII.STRING, 'A string as bytes array.')
node_type = SimpleRecord('node_type', GDSII.NODETYPE, 'Node type (integer).')
box_type = SimpleRecord('box_type', GDSII.BOXTYPE, 'Box type (integer).')
properties = PropertiesRecord('properties', """ 
    Dictionary containing properties of an element.
    Keys should be integers. Values are byte strings.
""")
