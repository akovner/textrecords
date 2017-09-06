from unittest import TestCase
from jsonschema import Draft4Validator
from pathlib import Path
from os.path import dirname, join
from json import load as json_load

with open(join(dirname(__file__), 'schemas', 'textrecord.json'), 'rt') as f:
    textrecord_schema = json_load(f)
validator = Draft4Validator(textrecord_schema)


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


class ParseRuleDelimited(ParseRuleComposite):
    def __init__(self, schema):
        self._delimiter = schema['delimiter']


class ParseRulePrimitive(ParseRule):
    pass


class ParseRulePrimitiveFixed(ParseRulePrimitive):
    pass


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
