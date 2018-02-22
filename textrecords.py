from jsonschema import Draft4Validator, ValidationError
from os.path import dirname, join
from json import load as json_load
from copy import deepcopy
from abc import ABCMeta
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

    @classproperty
    def delim_regex(cls):
        return ''.join(['\\x{:s}'.format(c.encode('unicode_escape').hex()) for c in cls.delimiter])


class ParseRuleFixed(ParseRuleCompound):
    pass


class ParseRulePrimitive(ParseRule):

    @classmethod
    def regex_str(cls):
        return cls._regex_str


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

    @property
    def regex_str(cls):
        return cls._regex_str

    def __new__(mcs, name, parents, dct):

        # @property
        # def regex_str_prop(c):
        #     return c._regex_str
        # mcs.regex_str = regex_str_prop

        if '_field_name' not in dct:
            dct['_field_name'] = None

        is_primitive = 'properties' not in dct['_schema']
        if is_primitive:
            compound_superclass = (ParseRulePrimitiveDelimited
                                   if issubclass(dct['_parent'], ParseRuleDelimited)
                                   else ParseRulePrimitiveFixed)
            parents = (ParseRulePrimitiveMeta.primitive_switch(dct['_schema']['type']), compound_superclass, ) + parents
        else:
            def getitem(c, k):
                if isinstance(k, int):
                    if 0 <= k < len(c):
                        return c._fields[c._fields_idx[k]]
                    else:
                        raise IndexError('Index out of range: {0:d} not between 0 and {1:d}'.format(k, c._len))
                elif isinstance(k, str):
                    return c._fields[k]
                else:
                    raise IndexError('Index must be of type `str` or `int`')
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

            def len_func(c):
                return len(c._fields_idx)
            mcs.__len__ = len_func
            # @property
            # def regex_str_prop(cls):
            #     return cls._regex_str
            # mcs.regex_str = regex_str_prop

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
                                                   {'_schema': obj,
                                                    '_field_name': obj['name'],
                                                    '_parent': cls})
                fields_idx.append(obj['name'])

            cls._fields = fields
            cls._fields_idx = tuple(fields_idx)

            regex_array = []
            for fld in cls:
                if issubclass(fld, ParseRulePrimitive):
                    regex_array.append('({:s})'.format(fld._regex_str))
                else:
                    regex_array.append(fld.regex_str)
            if issubclass(cls, ParseRuleDelimited):
                cls._regex_str = cls.delim_regex.join(regex_array)
            else:
                cls._regex_str = ''.join(regex_array)
        else:
            if issubclass(cls, ParseRulePrimitiveDelimited):
                cls._regex_str = '[^{:s}]*'.format(cls.parent.delim_regex)
            else:
                cls._regex_str = '.{{{:d}}}'.format(dct['_schema']['length'])

        def init(self, data, level):
            pass

        return cls


class ParseRulePrimitiveMeta(ParseRuleMeta):

    _primitive_classes = {
        'string': ParseRuleString,
        'integer': ParseRuleInteger,
        'number': ParseRuleNumber
    }

    @classmethod
    def primitive_switch(mcs, k):
        return mcs._primitive_classes[k]

    def __new__(mcs, name, parents, dct):
        cls = super().__new__(mcs, name, parents, dct)


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

    @property
    def schema(cls):
        return cls._schema

    @property
    def root_class(cls):
        return cls._root_class
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
