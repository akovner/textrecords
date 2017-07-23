from unittest import TestCase
from jsonschema import Draft4Validator
from pathlib import Path
from os.path import dirname, join
from json import load as json_load

with open(join(dirname(__file__), 'schemas', 'textrecord.json'), 'rt') as f:
    textrecord_schema = json_load(f)

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
        self._validator = Draft4Validator(textrecord_schema)

    def test_textrecord_schema_validity(self):
        self.assertIsNone(Draft4Validator.check_schema(textrecord_schema))

    def test_example_schema_validity(self):
        for path in Path(join(dirname(__file__), 'examples', 'schemas')).glob('*.json'):
            with open(path, 'rt') as f:
                sch = json_load(f)
            err_count = 0
            for error in self._validator.iter_errors(sch):
                err_count += 1
                print(error.message)
            self.assertEquals(err_count, 0)
