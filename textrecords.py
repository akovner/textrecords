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


class ParseRule():
    pass


class RecordSchema:

    @classproperty
    def schema(cls):
        return cls._schema

    @classproperty
    def root_class(cls):
        return cls._root_class


class ParseRuleDelimited(ParseRule):
    @classproperty
    def delimiter(cls):
        return cls._delimiter


class ParseRuleMeta(type):
    def __new__(mcs, name, parents, dct):
        if 'delimiter' in dct['_schema']:
            dct['_delimiter'] = dct['_schema']['delimiter']
            parents = (ParseRuleDelimited, ) + parents
            props = {}
            for obj in dct['_schema']['properties']:
                props[obj['name']] = ParseRuleMeta('{0:s}_{1:s}'.format(name, obj['name']),
                                                   (),
                                                   {'_schema': deepcopy(obj), 'parent': mcs})

        return super(ParseRuleMeta, mcs).__new__(mcs, name, parents, dct)


class RecordSchemaMeta(type):
    def __new__(mcs, name, parents, dct):
        # Test that schema exists in the dictionary, and is a valid textrecord schema
        if '_schema' not in dct:
            raise IndexError('`_schema` class member must be defined')
        try:
            validator.validate(dct['_schema'])
        except ValidationError:
            raise ValidationError('`_schema` failed to validate')

        dct['_root_class'] = ParseRuleMeta('{:s}_root'.format(name), (), {'_schema': deepcopy(dct['_schema']), 'parent': mcs})

        if RecordSchema not in parents:
            parents = (RecordSchema, ) + parents

        return super(RecordSchemaMeta, mcs).__new__(mcs, name, parents, dct)
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

