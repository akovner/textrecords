from unittest import TestCase
from jsonschema import Draft4Validator, ValidationError
from pathlib import Path
from os.path import dirname, join
from json import load as json_load
from operator import itemgetter
from collections import OrderedDict
from copy import deepcopy
import re

with open(join(dirname(__file__), 'schemas', 'textrecord.json'), 'rt') as f:
    textrecord_schema = json_load(f)
validator = Draft4Validator(textrecord_schema)

def merge_dicts(*dict_args):
    """
    Given any number of dicts, shallow copy and merge into a new dict,
    precedence goes to key value pairs in latter dicts.
    """
    result = {}
    for dictionary in dict_args:
        result.update(dictionary)
    return result

class ReadClassPropertyDescriptor:
    def __init__(self, fget):
        self.fget = fget

    def __get__(self, instance, owner):
        if owner is None:
            owner = type(instance)
        return self.fget.__get__(instance, owner)()


def classproperty(fget):
    if not isinstance(fget, (classmethod, staticmethod)):
        fget = classmethod(fget)

    return ReadClassPropertyDescriptor(fget)


class RecordSchema:

    @classproperty
    def schema(cls):
        return cls._schema

    @classproperty
    def root_class(cls):
        return cls._root_class


class ParseRule():

    @classproperty
    def parent(cls):
        return cls._parent

    @classproperty
    def field_name(cls):
        return cls._field_name


class ParseRuleCompound(ParseRule):
    pass


class ParseRuleDelimited(ParseRuleCompound):
    @classproperty
    def delimiter(cls):
        return cls._delimiter


class ParseRuleFixed(ParseRuleCompound):
    @classproperty
    def len(cls):
        pass


class ParseRulePrimitive(ParseRule):
    pass


class ParseRulePrimitiveFixed(ParseRulePrimitive):
    pass


class ParseRulePrimitiveDelimited(ParseRulePrimitive):
    pass


class ParseRuleString(ParseRulePrimitive):
    pass


class ParseRuleInteger(ParseRulePrimitive):
    pass


class ParseRuleNumber(ParseRulePrimitive):
    pass


class ParseRuleMeta(type):

    @staticmethod
    def primitive_switch(k):
        d = {
            'string': ParseRuleString,
            'integer': ParseRuleInteger,
            'number': ParseRuleNumber
        }
        return d[k]

    def __new__(mcs, name, parents, dct):
        if '_field_name' not in dct:
            dct['_field_name'] = None

        is_primitive = isinstance(dct['_schema'], str)
        if is_primitive:
            compound_superclass = (ParseRulePrimitiveDelimited
                                   if issubclass(dct['_parent'], ParseRuleDelimited)
                                   else ParseRulePrimitiveFixed)
            if compound_superclass is ParseRuleDelimited:
                dct['_regex_str'] = '([^{0:s}]*)'.format(dct['_parent'].delimiter)
                dct['_re'] = re.compile(dct['_regex_str'])

                def init(self, rem):
                    m = self._regex.match(rem)
                    self._raw = m.group(1)
                    self._remainder = m.group(2)
            else:
                pass

            parents = (mcs.primitive_switch(dct['_schema']), compound_superclass, ) + parents
        else:

            def getitem(c, k):
                return c._fields[k]
            mcs.__getitem__ = getitem

            def iter(c):
                c._iter_place = 0
                return c
            mcs.__iter__ = iter

            def next(c):
                if c._iter_place >= len(c._fields_idx):
                    raise StopIteration
                else:
                    k = c._fields_idx[c._iter_place]
                    c._iter_place += 1
                    return c._fields[k]
            mcs.__next__ = next


            if 'delimiter' in dct['_schema']:
                dct['_delimiter'] = dct['_schema']['delimiter']
                parents = (ParseRuleDelimited, ) + parents
            else:
                parents = (ParseRuleFixed, ) + parents

        cls = super(ParseRuleMeta, mcs).__new__(mcs, name, parents, dct)
        if not is_primitive:
            fields = {}
            fields_idx = []
            for i, obj in enumerate(dct['_schema']['properties']):
                fields[obj['name']] = ParseRuleMeta('{0:s}_{1:s}'.format(name, obj['name']),
                                                   (),
                                                   {'_schema': deepcopy(obj['type']),
                                                    '_field_name': obj['name'],
                                                    '_parent': cls})
                fields_idx.append(obj['name'])

            cls._fields = fields
            cls._fields_idx = tuple(fields_idx)

            regex = []
            for fld in mcs:
                regex.append(fld.regex)

        return cls


class RecordSchemaMeta(type):
    def __new__(mcs, name, parents, dct):
        # Test that schema exists in the dictionary, and is a valid textrecord schema
        if '_schema' not in dct:
            raise IndexError('`_schema` class member must be defined')
        try:
            validator.validate(dct['_schema'])
        except ValidationError:
            raise ValidationError('`_schema` failed to validate')

        if RecordSchema not in parents:
            parents = (RecordSchema, ) + parents
        cls = super(RecordSchemaMeta, mcs).__new__(mcs, name, parents, dct)
        cls._root_class = ParseRuleMeta('{:s}_root'.format(name), (), {'_schema': deepcopy(dct['_schema']),
                                                                       '_parent': cls})
        return cls
        # fields = dct['_fields']
        # if 'delimiter' in sch:
        #     pass
        # else:
        #     if isinstance(sch, dict):
        #         for name, obj in sch['properties'].items():
        #             if isinstance(obj['type'], str):
        #                 fields[name] = get_fixed_parserule_class(obj['type'])
        #             elif 'delimiter' in obj['type']:
        #                 fields[name] = ParseRuleFixedMeta('', (), {'schema': obj['type']})
        #             else:
        #                 fields[name] = ParseRuleDelimMeta('', (), {'schema': obj['type']})
        #
        #     else:
        #         for obj in sch:
        #             if isinstance(obj['type'], str):
        #                 pass

