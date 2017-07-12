from unittest import TestCase
from jsonschema import Draft4Validator
from os.path import dirname, join
from json import load as json_load

with open(join(dirname(__file__), 'schemas', 'textrecord.json'), 'rt') as f:
    schema = json_load(f)

class ParseRule:
    pass


class ParseRuleFixedWidth(ParseRule):
    pass


class ParseRuleDelimited(ParseRule):
    pass


class RecordReader:
    """
    The primary class for reading records line-by-line from a text file

    :param rules: A set of parse rules in one of the following forms:
        - A dictionary, file-like object or file path whose contents conform
          to the json schema for parsing text records
        - A :class:`ParseRule` object
    """
    def __init__(self, *args):
        pass


class TestSchemaValidity(TestCase):
    def setUp(self):
        self._validator = Draft4Validator(schema)

    def test_schema_validity(self):
        self.assertIsNone(Draft4Validator.check_schema(schema))

    def test_nameaddress_validity(self):
        with open(join(dirname(__file__), 'examples', 'name_address.json'), 'rt') as f:
            s = json_load(f)
        err_count = 0
        for error in self._validator.iter_errors(s):
            err_count += 1
            print(error.message)
        self.assertEquals(err_count, 0)

    def test_nameaddressnested_validity(self):
        with open(join(dirname(__file__), 'examples', 'name_address_nested.json'), 'rt') as f:
            s = json_load(f)
        err_count = 0
        for error in self._validator.iter_errors(s):
            err_count += 1
            print(error.message)
        self.assertEquals(err_count, 0)

    def test_nameaddress_fixed_validity(self):
        with open(join(dirname(__file__), 'examples', 'name_address_fixed.json'), 'rt') as f:
            s = json_load(f)
        err_count = 0
        for error in self._validator.iter_errors(s):
            err_count += 1
            print(error.message)
        self.assertEquals(err_count, 0)
