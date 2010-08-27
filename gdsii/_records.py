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
    def read(self, instance, gen):
        rec = gen.current
        if rec.tag == self.gds_record:
            rec.check_size(1)
            setattr(instance, self.priv_variable, rec.data[0])
            next(gen)

    def save(self, instance, stream):
        try:
            data = getattr(instance, self.priv_variable)
        except AttributeError:
            data = None
        if data is not None:
            RecordData(self.gds_record, (data,)).save(stream)

class OptionalFlagsRecord(SimpleRecord):
    def read(self, instance, gen):
        rec = gen.current
        if rec.tag == self.gds_record:
            setattr(instance, self.priv_variable, rec.data)
            next(gen)

    def save(self, instance, stream):
        try:
            data = getattr(instance, self.priv_variable)
        except AttributeError:
            data = None
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

class OptionalStringRecord(SimpleOptionalRecord):
    def read(self, instance, gen):
        rec = gen.current
        if rec.tag == self.gds_record:
            setattr(instance, self.priv_variable, rec.data)

    def save(self, instance, stream):
        try:
            value = getattr(instance, self.priv_variable)
        except AttributeError:
            value = None
        if value is not None:
            RecordData(self.gds_record, value).save(stream)

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
            setattr(obj, self.priv_variable2, value)
        return f

    def props(self):
        res = AbstractRecord.props(self)
        res[self.variable2] =  property(self.getter2(), self.setter2(), doc=self.doc2)
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

class TimestampsRecord(SimpleRecord):
    def __init__(self, variable1, variable2, gds_record, doc1, doc2):
        SimpleRecord.__init__(self, variable1, gds_record, doc1)
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

    def props(self):
        res = SimpleRecord.props(self)
        res[self.variable2] =  property(self.getter2(), self.setter2(), doc=self.doc2)
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

class STransRecord(OptionalFlagsRecord):
    mag = SimpleOptionalRecord('mag', tags.MAG, 'Magnification (real, optional).')
    angle = SimpleOptionalRecord('angle', tags.ANGLE, 'Rotation angle (real, optional).')

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

    def save(self, instance, stream):
        try:
            data = getattr(instance, self.priv_variable)
        except AttributeError:
            data = None

        if data is not None:
            OptionalFlagsRecord.save(self, instance, stream)
            self.mag.save(instance, stream)
            self.angle.save(instance, stream)

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
