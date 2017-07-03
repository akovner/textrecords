from unittest import TestCase
from jsonschema import validate, Draft4Validator
from os.path import dirname, join
from yaml import load


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
        with open(join(dirname(__file__), 'schemas', 'textrecord.schema.yaml'), 'rt') as f:
            self.schema = load(f)

    def test_metaschema_validity(self):
        self.assertIsNone(Draft4Validator.check_schema(self.schema))

    def test_nameaddress_delimited_validity(self):
        with open(join(dirname(__file__), 'examples', 'name_address.dlm.yaml'), 'rt') as f:
            s = load(f)
        res = Draft4Validator(self.schema).validate(s)
        self.assertIsNone(res)

