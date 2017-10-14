from unittest import TestCase
from jsonschema import Draft4Validator, ValidationError
from pathlib import Path
from os.path import dirname, join
from json import load as json_load
from operator import itemgetter
from collections import OrderedDict

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


class ParseRule():
    def __call__(self, *args, **kwargs):
        """

        :param *args: path to a data element
        :type *args: str or integer
        :param **kwargs:
        :return: The object or value at that location
        """
        pass

    def schema(self):
        """
        The schema or schema fragment for this parse rule
        :return: dict or array
        """


class ParseRuleMeta(type):
    def __new__(cls, name, parents, dct):
        if 'schema' not in dct:
            raise IndexError('`schema` class member must be defined')

        sch = dct['schema']
        try:
            validator.validate(sch)
        except ValidationError:
            raise ValidationError('`schema` failed to validate')

        dct['_root'] =
        dct['_fields'] = OrderedDict()
        fields = dct['_fields']
        if 'delimiter' in sch:
            pass
        else:
            if isinstance(sch, dict):
                for name, obj in sch['properties'].items():
                    if isinstance(obj['type'], str):
                        fields[name] = get_fixed_parserule_class(obj['type'])
                    elif 'delimiter' in obj['type']:
                        fields[name] = ParseRuleFixedMeta('', (), {'schema': obj['type']})
                    else:
                        fields[name] = ParseRuleDelimMeta('', (), {'schema': obj['type']})

            else:
                for obj in sch:
                    if isinstance(obj['type'], str):
                        pass


class ParseRuleDelimMeta(type):
    def __new__(cls, name, parents, dct):
        pass


class ParseRuleFixedMeta(type):
    def __new__(cls, name, parents, dct):
        pass


def get_fixed_parserule_class(type):
    if type == 'string':
        return ParseRuleStringFixed
    elif type == 'numeric':
        return ParseRuleNumericFixed
    elif type == 'integer':
        return ParseRuleIntegerFixed
    else:
        raise ValueError('argument `type` must be in the set {`string`, `numeric`, `integer`}')


class ParseRule:
    pass


class ParseRuleComposite(ParseRule):
    pass


class ParseRuleFixedWidth(ParseRuleComposite):
    def __init__(self, schema):
        self._parse_rules = []

        if isinstance(schema['properties'], dict):
            for name, obj in schema['properties'].items():
                pass
        else:
            for obj in schema['properties']:
                if isinstance(obj['type'], str):
                    if obj['type'] == 'string':
                        self._parse_rules.append(ParseRuleStringFixed(obj))
                    elif obj['type'] == 'integer':
                        self._parse_rules.append(ParseRuleIntegerFixed(obj))
                    else:
                        self._parse_rules.append(ParseRuleNumericFixed(obj))
                else:
                    if 'delimiter' in obj:
                        self._parse_rules.append(ParseRuleDelimited(obj))
                    else:
                        self._parse_rules.append(ParseRuleFixedWidth(obj))

    def parse(self, s):
        ret = {}
        for pr in self._parse_rules:



class ParseRuleDelimited(ParseRuleComposite):
    def __init__(self, schema):
        self._delimiter = schema['delimiter']
        self._parse_rules = []

        if isinstance(schema['properties'], dict):
            pr_defs = []
            for name, orig in schema['properties'].items():
                obj = orig.copy()
                obj['name'] = name
                pr_defs.append(obj)
            pr_defs = sorted(pr_defs, key=itemgetter('location'))
            for pr_def in pr_defs:
                del pr_def['location']
                
            for pr_def in pr_defs:
                if isinstance(pr_def['type'], str):
                    if pr_def['type'] == 'string':
                        self._parse_rules.append(ParseRuleStringDelim(pr_def))
                    elif pr_def['type'] == 'integer':
                        self._parse_rules.append(ParseRuleIntegerDelim(pr_def))
                    else:
                        self._parse_rules.append(ParseRuleNumericDelim(pr_def))
                elif 'delimited' in pr_def:
                    self._parse_rules.append(ParseRule)
                else:
                    pass


class ParseRulePrimitive(ParseRule):
    pass


class ParseRulePrimitiveFixed(ParseRulePrimitive):
    def __init__(self, schema):
        self._name = schema['name']

    def parse(self, s):


class ParseRuleInteger(ParseRulePrimitive):


class ParseRuleIntegerFixedPadded(ParseRuleInteger, ParseRulePrimitive, ParseRulePadded):
    def __init__(self, schema):
        super().__init__(self, schema)

    def parse(self, s):
        raw_string = super().pa


class ParseRulePrimitiveDelim(ParseRulePrimitive):
    pass


class ParseRuleStringFixed(ParseRulePrimitiveFixed):
    def __init__(self, name):
        pass


class ParseRuleIntegerFixed(ParseRulePrimitiveFixed):
    def __init__(self, name):
        pass


class ParseRuleNumericFixed(ParseRulePrimitiveFixed):
    def __init__(self):
        pass


class ParseRuleStringFixed(ParseRulePrimitiveFixed):
    def __init__(self, name):
        pass


class ParseRuleIntegerFixed(ParseRulePrimitiveFixed):
    def __init__(self, name):
        pass


class ParseRuleNumericFixed(ParseRulePrimitiveFixed):
    def __init__(self):
        pass


class ParseRuleStringDelim(ParseRulePrimitiveDelim):
    def __init__(self, name):
        pass


class ParseRuleIntegerDelim(ParseRulePrimitiveDelim):
    def __init__(self, name):
        pass


class ParseRuleNumericDelim(ParseRulePrimitiveDelim):
    def __init__(self):
        pass


class RecordReader:
    """
    The primary class for reading records line-by-line from a text file

    :param rules: A set of parse rules in one of the following forms:
        - A dictionary, file-like object or file path whose contents conform
          to the json schema for parsing text records
        - A :class:`ParseRule` object
    """
    def __init__(self, schema):
        validator.validate(schema)
        if 'delimited' in schema:
            self._root = ParseRuleDelimited(schema)
        else:
            self._root = ParseRuleFixedWidth(schema)


class TestSchemaValidity(TestCase):
    def test_textrecord_schema_validity(self):
        self.assertIsNone(Draft4Validator.check_schema(textrecord_schema))

    def test_example_schema_validity(self):
        for path in Path(join(dirname(__file__), 'examples', 'schemas')).glob('*.json'):
            with open(path, 'rt') as f:
                sch = json_load(f)
            err_count = 0
            for error in validator.iter_errors(sch):
                err_count += 1
                print(error.message)
            self.assertEquals(err_count, 0)
