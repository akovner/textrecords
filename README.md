# textrecords
A python tool to convert records from fixed-width and delimited files into dictionaries

## Summary
The **textrecords** package provides a simple API for converting delimited and fixed-width text records into
dictionaries and vice-versa. Features include:

* nested parse rules
* a parse rule builder
* support for multiple record types in the same stream
* support for json-schema validation

## JSON schema
This project does not attempt to reproduce the functionality of a schema validator. Instead, **textrecords**
requires the minimum information to convert a line of text into a json-like data structure. Schema validation
can be achieved by including a json schema in the text record parse rule, either directly or by reference.
