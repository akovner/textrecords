from unittest import TestCase
from jsonschema import Draft4Validator, ValidationError
from pathlib import Path
from os.path import dirname, join
from json import load as json_load
from operator import itemgetter
from collections import OrderedDict
from copy import deepcopy

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


class ParseRuleStringFixed(ParseRulePrimitiveFixed, ParseRuleString):
    pass


class ParseRuleIntegerFixed(ParseRulePrimitiveFixed, ParseRuleInteger):
    pass


class ParseRuleNumberFixed(ParseRulePrimitiveFixed, ParseRuleNumber):
    pass


class ParseRuleStringDelimited(ParseRulePrimitiveDelimited, ParseRuleString):
    pass


class ParseRuleIntegerDelimited(ParseRulePrimitiveDelimited, ParseRuleInteger):
    pass


class ParseRuleNumberDelimited(ParseRulePrimitiveDelimited, ParseRuleNumber):
    pass


class ParseRuleMeta(type):
    def __new__(mcs, name, parents, dct):
        if '_field_name' not in dct:
            dct['_field_name'] = None

        is_parent_delimited = issubclass(dct['_parent'], ParseRuleDelimited)
        compound_superclass = ParseRulePrimitiveDelimited if is_parent_delimited else ParseRulePrimitiveFixed

        primitive_switch = {
            'string': ParseRuleString,
            'integer': ParseRuleInteger,
            'number': ParseRuleNumber
        }

        is_primitive = isinstance(dct['_schema'], str)
        if is_primitive:
            parents = (primitive_switch[dct['_schema']], compound_superclass, ) + parents
        elif 'delimiter' in dct['_schema']:
            dct['_delimiter'] = dct['_schema']['delimiter']
            parents = (ParseRuleDelimited, ) + parents
        else:
            parents = (ParseRuleFixed, ) + parents

        cls = super(ParseRuleMeta, mcs).__new__(mcs, name, parents, dct)
        if not is_primitive:
            fields = {}
            for obj in dct['_schema']['properties']:
                fields[obj['name']] = ParseRuleMeta('{0:s}_{1:s}'.format(name, obj['name']),
                                                   (),
                                                   {'_schema': deepcopy(obj['type']),
                                                    '_field_name': obj['name'],
                                                    '_parent': cls})
            cls._fields = fields

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

