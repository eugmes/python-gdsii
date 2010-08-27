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
from __future__ import absolute_import
from . import tags, RecordData

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
            setattr(obj, self.priv_variable, value)
        return f

    def props(self):
        return {
                self.variable: property(self.getter(), self.setter(), doc=self.doc)
        }

    def read(self, instance, gen):
        raise NotImplementedError

    def save(self, instance, stream):
        raise NotImplementedError

    def __repr__(self):
        return '<property: %s>'%self.variable

class SecondVar(object):
    """Class that simplifies second property support."""
    def __init__(self, variable2, doc2):
        self.variable2 = variable2
        self.priv_variable2 = '_' + variable2
        self.doc2 = doc2

    def getter2(self):
        def f(obj):
            return getattr(obj, self.priv_variable2)
        return f

    def setter2(self):
        def f(obj, value):
            setattr(obj, self.priv_variable2, value)
        return f

    def property2(self):
        return property(self.getter2(), self.setter2(), doc=self.doc2)

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

    def save(self, instance, stream):
        RecordData(self.gds_record, (getattr(instance, self.priv_variable),)).save(stream)

class SimpleOptionalRecord(SimpleRecord):
    def optional_read(self, instance, unused_gen, rec):
        """
        Called when optional tag is found. `rec` contains that tag.
        `gen` is advanced to next record befor calling this function.
        """
        rec.check_size(1)
        setattr(instance, self.priv_variable, rec.data[0])

    def read(self, instance, gen):
        rec = gen.current
        if rec.tag == self.gds_record:
            next(gen)
            self.optional_read(instance, gen, rec)

    def save(self, instance, stream):
        data = getattr(instance, self.priv_variable, None)
        if data is not None:
            RecordData(self.gds_record, (data,)).save(stream)

class OptionalWholeRecord(SimpleOptionalRecord):
    """Class for records that need to store all data (not data[0])."""
    def optional_read(self, instance, unused_gen, rec):
        setattr(instance, self.priv_variable, rec.data)

    def save(self, instance, stream):
        data = getattr(instance, self.priv_variable, None)
        if data is not None:
            RecordData(self.gds_record, data).save(stream)

class PropertiesRecord(AbstractRecord):
    def read(self, instance, gen):
        rec = gen.current
        props = []
        while rec.tag == tags.PROPATTR:
            rec.check_size(1)
            propattr = rec.data[0]
            rec = next(gen)
            rec.check_tag(tags.PROPVALUE)
            props.append((propattr, rec.data))
            rec = next(gen)
        setattr(instance, self.priv_variable, props)

    def save(self, instance, stream):
        props = getattr(instance, self.priv_variable)
        for (propattr, propvalue) in props:
            RecordData(tags.PROPATTR, (propattr,)).save(stream)
            RecordData(tags.PROPVALUE, propvalue).save(stream)

class XYRecord(SimpleRecord):
    def read(self, instance, gen):
        rec = gen.current
        rec.check_tag(self.gds_record)
        setattr(instance, self.priv_variable, rec.points)
        next(gen)

    def save(self, instance, stream):
        pts = getattr(instance, self.priv_variable)
        RecordData(self.gds_record, points=pts).save(stream)

class StringRecord(SimpleRecord):
    def read(self, instance, gen):
        rec = gen.current
        rec.check_tag(self.gds_record)
        setattr(instance, self.priv_variable, rec.data)
        next(gen)

    def save(self, instance, stream):
        RecordData(self.gds_record, getattr(instance, self.priv_variable)).save(stream)

class ColRowRecord(AbstractRecord, SecondVar):
    def __init__(self, variable1, variable2, doc1, doc2):
        AbstractRecord.__init__(self, variable1, doc1)
        SecondVar.__init__(self, variable2, doc2)

    def props(self):
        res = AbstractRecord.props(self)
        res[self.variable2] = self.property2()
        return res

    def read(self, instance, gen):
        rec = gen.current
        rec.check_tag(tags.COLROW)
        rec.check_size(2)
        cols, rows = rec.data
        setattr(instance, self.priv_variable, cols)
        setattr(instance, self.priv_variable2, rows)
        next(gen)

    def save(self, instance, stream):
        col = getattr(instance, self.priv_variable)
        row = getattr(instance, self.priv_variable2)
        RecordData(tags.COLROW, (col, row)).save(stream)

class TimestampsRecord(SimpleRecord, SecondVar):
    def __init__(self, variable1, variable2, gds_record, doc1, doc2):
        SimpleRecord.__init__(self, variable1, gds_record, doc1)
        SecondVar.__init__(self, variable2, doc2)

    def props(self):
        res = SimpleRecord.props(self)
        res[self.variable2] = self.property2()
        return res

    def read(self, instance, gen):
        rec = gen.current
        rec.check_tag(self.gds_record)
        mod_time, acc_time = rec.times
        setattr(instance, self.priv_variable, mod_time)
        setattr(instance, self.priv_variable2, acc_time)
        next(gen)

    def save(self, instance, stream):
        mod_time = getattr(instance, self.priv_variable)
        acc_time = getattr(instance, self.priv_variable2)
        RecordData(self.gds_record, times=(mod_time, acc_time)).save(stream)

class STransRecord(OptionalWholeRecord):
    mag = SimpleOptionalRecord('mag', tags.MAG, 'Magnification (real, optional).')
    angle = SimpleOptionalRecord('angle', tags.ANGLE, 'Rotation angle (real, optional).')

    def props(self):
        res = dict(list(self.mag.props().items()) +
                list(self.angle.props().items()) +
                list(OptionalWholeRecord.props(self).items()))
        return res

    def optional_read(self, instance, gen, rec):
        setattr(instance, self.priv_variable, rec.data)
        self.mag.read(instance, gen)
        self.angle.read(instance, gen)

    def save(self, instance, stream):
        data = getattr(instance, self.priv_variable, None)
        if data is not None:
            OptionalWholeRecord.save(self, instance, stream)
            self.mag.save(instance, stream)
            self.angle.save(instance, stream)

class ACLRecord(SimpleOptionalRecord):
    def optional_read(self, instance, unused_gen, rec):
        setattr(instance, self.priv_variable, rec.acls)

    def save(self, instance, stream):
        data = getattr(instance, self.priv_variable, None)
        if data:
            RecordData(self.gds_record, acls=data).save(stream)

class FormatRecord(SimpleOptionalRecord, SecondVar):
    def __init__(self, variable1, variable2, gds_record, doc1, doc2):
        SimpleOptionalRecord.__init__(self, variable1, gds_record, doc1)
        SecondVar.__init__(self, variable2, doc2)

    def props(self):
        res = SimpleOptionalRecord.props(self)
        res[self.variable2] = self.property2()
        return res

    def optional_read(self, instance, gen, rec):
        SimpleOptionalRecord.optional_read(self, instance, gen, rec)
        fmt = rec.data[0]
        # MASKS are required for formats 1 and 3
        if fmt == 1 or fmt == 3:
            cur_rec = gen.curent
            masks = []
            while cur_rec.tag == tags.MASK:
                masks.append(cur_rec.data)
                cur_rec = next(gen)
            cur_rec.check_tag(tags.ENDMASKS)
            setattr(instance, self.priv_variable2, masks)
            next(gen)

    def write(self, instance, stream):
        fmt = getattr(instance, self.priv_variable, None)
        if fmt is not None:
            SimpleOptionalRecord.save(self, instance, stream)
            if fmt == 1 or fmt == 3:
                masks = getattr(instance, self.priv_variable2, [])
                for mask in masks:
                    RecordData(tags.MASK, mask).save(stream)
                RecordData(tags.ENDMASKS).save(stream)

class UnitsRecord(SimpleRecord, SecondVar):
    def __init__(self, variable1, variable2, gds_record, doc1, doc2):
        SimpleRecord.__init__(self, variable1, gds_record, doc1)
        SecondVar.__init__(self, variable2, doc2)

    def props(self):
        res = SimpleRecord.props(self)
        res[self.variable2] = self.property2()
        return res

    def read(self, instance, gen):
        rec = gen.current
        rec.check_tag(self.gds_record)
        rec.check_size(2)
        unit1, unit2 = rec.data
        setattr(instance, self.priv_variable, unit1)
        setattr(instance, self.priv_variable2, unit2)
        next(gen)

    def write(self, instance, stream):
        unit1 = getattr(instance, self.priv_variable)
        unit2 = getattr(instance, self.priv_variable2)
        RecordData(self.gds_record, [unit1, unit2]).write(stream)

def stream_class(cls):
    """
    Decorator for classes that can be read and written to a GDSII stream.

    Sets up GDSII properties. Class should have ``_gds_objs`` variable
    containing tuple with instances of :class:`AbstractRecord`.
    """
    for obj in cls._gds_objs:
        for (propname, prop) in obj.props().items():
            setattr(cls, propname, prop)
    return cls
