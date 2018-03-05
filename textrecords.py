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


class ParseRuleType(type):

    @property
    def regex_str(cls):
        return cls._regex_str

    def __new__(mcs, name, parents, dct):
        if '_field_name' not in dct:
            dct['_field_name'] = None

        cls = super(ParseRuleType, mcs).__new__(mcs, name, parents, dct)
        return cls


class ParseRulePrimitiveType(ParseRuleType):
    pass


class ParseRulePrimitiveFixedType(ParseRulePrimitiveType):
    def __len__(cls):
        return cls._length


def is_primitive(dct):
    return 'properties' in dct


class ParseRuleCompoundType(ParseRuleType):

    def __new__(typ, name, parents, dct):
        if 'delimiter' in dct['_schema']:
            dct['_delimiter'] = dct['_schema']['delimiter']
            parents = (ParseRuleDelimited, ) + parents
        else:
            parents = (ParseRuleFixed, ) + parents
        cls = super(ParseRuleCompoundType, typ).__new__(typ, name, parents, dct)

        return cls

    def __init__(cls):
        fields = {}
        fields_idx = []
        for i, obj in enumerate(cls._schema['properties']):
            parent_type = ParseRulePrimitiveType if is_primitive(obj['name']) else ParseRuleCompoundType
            fields[obj['name']] = parent_type('{0:s}_{1:s}'.format(type(cls).__name__, obj['name']),
                                               (),
                                               {'_schema': obj,
                                                '_field_name': obj['name'],
                                                '_supnode': cls})
            fields_idx.append(obj['name'])

        cls._fields = fields
        cls._fields_idx = tuple(fields_idx)

        if issubclass(cls, ParseRuleCompound):
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
                cls._length = cls._schema['length']
                cls._regex_str = '.{{{:d}}}'.format(cls._length)

        def init(self, data):
            print(data)
        cls.__init__ = init

    def __getitem__(cls, k):
        if isinstance(k, int):
            if 0 <= k < len(cls):
                return cls._fields[cls._fields_idx[k]]
            else:
                raise IndexError('Index out of range: {0:d} not between 0 and {1:d}'.format(k, len(cls)))
        elif isinstance(k, str):
            return cls._fields[k]
        else:
            raise IndexError('Index must be of type `str` or `int`')

    def __iter__(cls):
        cls._iter_place = 0
        return cls

    def __next__(cls):
        if cls._iter_place >= len(cls._fields_idx):
            raise StopIteration
        else:
            k = cls._fields_idx[cls._iter_place]
            cls._iter_place += 1
            return cls._fields[k]

    def __len__(cls):
        return len(cls._fields_idx)


primitive_switch = {
    'string': ParseRuleString,
    'integer': ParseRuleInteger,
    'number': ParseRuleNumber
}


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
        cls._root_class = ParseRuleType('{:s}_root'.format(name), (), {'_schema': deepcopy(dct['_schema']),
                                                                       '_parent': cls,
                                                                       '_depth': 0})
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
