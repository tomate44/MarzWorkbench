# -*- coding: utf-8 -*-
"""
Marz Workbench for FreeCAD 0.19+.
https://github.com/mnesarco/MarzWorkbench
"""

__author__       = "Frank D. Martinez. M."
__copyright__    = "Copyright 2020, Frank D. Martinez. M."
__license__      = "GPLv3"
__maintainer__   = "https://github.com/mnesarco"


from marz_attrs import rgetattr, rsetattr
import re
from functools import reduce

class FreecadPropertyHelper:

    DEFAULT_NAME_PATTERN = re.compile(r'(^[a-z])|\.(\w)')

    @staticmethod
    def getDefaultName(path):
        """Converts path to Name: obj.attrX.attrY => Obj_AttrX_AttrY"""
        def replacer(match):
            (first, g) = match.groups()
            if first: return first.upper()
            else: return f'_{g.upper()}'
        return FreecadPropertyHelper.DEFAULT_NAME_PATTERN.sub(replacer, path)

    def __init__(self, path, default=None, description=None, name=None, section=None, ui="App::PropertyLength", enum=None, options=None, mode=0):
        self.path = path
        self.default = default
        self.name = name or FreecadPropertyHelper.getDefaultName(path)
        if enum or options:
            self.ui = 'App::PropertyEnumeration'
        else:
            self.ui = ui
        self.enum = enum
        self.options = options
        self.section = section or self.name.partition('_')[0]
        self.description = description or self.name.rpartition('_')[2]
        self.mode = 0

    def init(self, obj):
        f = obj.addProperty(self.ui, self.name, self.section, self.description, self.mode)
        if self.ui == 'App::PropertyEnumeration':
            if self.options:
                setattr(f, self.name, self.options())
            elif self.enum:
                setattr(f, self.name, [x.value for x in list(self.enum)])
        self.reset(obj)

    def reset(self, obj):
        self.setval(obj, self.default)

    def getval(self, obj):
        if hasattr(obj, self.name):
            v = getattr(obj, self.name)
            if self.enum:
                return self.enum(v)
            elif hasattr(v, 'Value'):
                return v.Value
            else:
                return v

    def setval(self, obj, value):
        if hasattr(obj, self.name):
            if self.enum:
                setattr(obj, self.name, value.value)
            else:
                attr = getattr(obj, self.name)
                if hasattr(attr, 'Value'):
                    attr.Value = value
                else:
                    setattr(obj, self.name, value)

    def serialize(self, obj, state):
        if self.enum:
            state[self.name] = self.getval(obj).value
        else:
            state[self.name] = self.getval(obj)

    def deserialize(self, obj, state):
        if self.enum:
            self.setval(obj, self.enum(state[self.name]))    
        else:
            self.setval(obj, state[self.name])

    def copyToModel(self, obj, modelObj):
        changed = False
        if hasattr(obj, self.name):
            newVal = self.getval(obj)
            oldVal = rgetattr(modelObj, self.path)
            if newVal != oldVal:
                rsetattr(modelObj, self.path, newVal)
                changed = True
        return changed        

class FreecadPropertiesHelper:

    def __init__(self, properties):
        self.properties = properties

    def getProperty(self, obj, name):
        return self.properties.get(name).getval(obj)

    def setProperty(self, obj, name, value):
        self.properties.get(name).setval(obj, value)

    def createProperties(self, obj):
        for prop in self.properties:
            prop.init(obj)

    def propertiesToModel(self, objModel, obj):
        return reduce(lambda a,b: a or b, [p.copyToModel(obj, objModel) for p in self.properties])

    def getStateFromProperties(self, obj):
        state = {}
        state["_fc_name"] = obj.Name
        for prop in self.properties:
            prop.serialize(obj, state)
        return state

    def setPropertiesFromState(self, obj, state):
        for prop in self.properties:
            prop.deserialize(obj, state)

    def setDefaults(self, obj):
        for prop in self.properties:
            prop.reset(obj)

