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
