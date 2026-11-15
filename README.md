# A request nested past Python's recursion limit is a 500 from Django REST framework, not a 400

Django REST framework 3.18.3, Django 6.1.3 (and 5.2.19), Python 3.13.5.

1. `python3 -m venv .venv`
2. `.venv/bin/pip install -r requirements.txt`
3. `.venv/bin/python repro.py`

`repro.py` sends three requests through Django's request handler, with no
database or server, to a view whose serializer has one `JSONField`: a malformed
JSON body, a JSON body nested 200,000 arrays deep, and a form field holding the
same nesting.

Expected: all three are refused with a 400.

Actual: only the malformed body is.

    malformed JSON body : 400 {"detail":"JSON parse error - Expecting value: line 1 column 13 (char 12)"}
    nested JSON body    : 500 RecursionError('maximum recursion depth exceeded while decoding a JSON array from a unicode string')
    nested form field   : 500 RecursionError('maximum recursion depth exceeded while decoding a JSON array from a unicode string')

Why: Python's `json` raises `RecursionError`, not `ValueError`, for a document
nested past the interpreter's recursion limit. `JSONParser.parse` turns only a
`ValueError` into its `ParseError`, and `JSONField.to_internal_value` only a
`TypeError` or `ValueError` into its `invalid` error. On Python 3.13 the limit
is a fixed count near 10,000 levels; on 3.14 it is the thread's stack, which is
why the script nests far deeper than that.
