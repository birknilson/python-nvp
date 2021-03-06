# -*- coding: utf-8 -*-
"""
Pythonic implementation of the NVP format.

NVP is in essence nothing else than regular HTTP query strings in
which keys can conform to one of three conventions in order to specify
their relationship - hierarchically - to each other.

For instance the query string::

    ?foo[0].a=1&foo[0].b=2&foo[1]='helloworld'&foobar=1337

Is intended to reflect the following hierarchical dictionary::

    {
        'foo': [
            {
                'a': 1,
                'b': 2
            },
            'helloworld'
        ],
        'foobar': 1337
    }

The shown query string utilized the bracket style of indicating sequences.
There are two other methods of achieving this in NVP. Sigh.

Instead of brackets parentheses are supported too. In which case the
previous query string could be re-written using this convention to::

    foo(0).a=1&foo(0).b=2&foo(1)='helloworld'&foobar=1337

The last method is the default one which uses underscores to indicate
hierarchical depth. In other words FOO_0_BAR in the underscore convention
is the same as FOO[0].BAR in the bracket convention. However, there is one
significant difference and that is how list values are represented. In
such cases the underscore convention is a bit tricky in that it appends
the final index to the last hierarchical key. For instance the following
data structure:

    {
        'foo': [
            {
                'a': [1, 2, 3]
            }
        ]
    }

Would, using the underscore convention, result in the following string:

    foo_0_a0=1&foo_0_a1=2&foo_0_a2=3

The underscore convention - as shown above - have uppercased keys in general.

The NVP format was introduced by PayPal and is heavily utilized in
their API suites. More information about the format is thus best found
in their documentation at::

    http://bit.ly/ruw99i


However, although the list is short, other services utilize the format
in their API too. For instance Payson - a Swedish payment provider.

The purpose with this package is to enable more Pythonic implementations
of these APIs and to significantly ease communication with them.

This package will expose an API similar to ``simplejson``, ``marshal``
and ``pickle``, i.e using load & loads to decode and dump & dumps to encode.
"""

__author__ = 'Birk Nilson <birk@tictail.com>'
__version__ = '0.0.1-dev'
__all__ = [
    'util',
    'dump', 'dumps',
    'load', 'loads',
]


from urllib import urlencode
from urlparse import parse_qs
from nvp import util


# Convention aliases
CONVENTIONS = util.CONVENTIONS
CONVENTION_BRACKET = util.CONVENTION_BRACKET
CONVENTION_PARENTHESES = util.CONVENTION_PARENTHESES
CONVENTION_UNDERSCORE = util.CONVENTION_UNDERSCORE


###############################################################################
# ENCODING & DECODING API
###############################################################################

def dumps(obj,
          convention=util.DEFAULT_CONVENTION,
          key_filter=None,
          value_filter=None):
    """Encode given ``obj`` into an NVP query string.

    :param obj: The dictionary to encode
    :param convention: The convention to utilize in encoding keys
                       corresponding to non-string sequences, e.g lists.
    :param key_filter: Function in which all keys should be filtered through.
                       Allowing key conversion from lowercase to uppercase
                       or vice versa for example.
    :param value_filter: Function in which all values should be filtered
                         through. In order to UTF-8 encode values for
                         example.
    """
    return urlencode(util.get_hierarchical_pairs(
        obj, convention=convention,
        key_filter=key_filter, value_filter=value_filter,
    ))


def dump(obj,
         fp,
         convention=util.DEFAULT_CONVENTION,
         key_filter=None,
         value_filter=None):
    """Encode given ``obj`` into an NVP query string.
    Save the encoded value of ``obj`` to the file-like object ``fp``
    which is required to support the ``write`` operation.

    :param obj: The dictionary to encode
    :param fp: The file pointer in which the encoded value should be stored
    :param convention: The convention to utilize in encoding keys
                       corresponding to non-string sequences, e.g lists.
    :param key_filter: Function in which all keys should be filtered through.
                       Allowing key conversion from lowercase to uppercase
                       or vice versa for example.
    :param value_filter: Function in which all values should be filtered
                         through. In order to UTF-8 encode values for
                         example.
    """
    kwargs = locals()
    del kwargs['fp']
    fp.write(dumps(**kwargs))


def loads(string,
          keep_blank_values=False,
          strict_parsing=False,
          get_hierarchical=True,
          key_filter=None,
          value_filter=None):
    """Decode given NVP ``string`` into a dictionary.

    :param string: The encoded NVP string to decode
    :param keep_blank_values: Whether to retain keys with undefined values
    :param strict_parsing: Whether to use strict parsing of the query string
    :param get_hierarchical: Whether to decode into a single-level or
                             hierarchical dictionary.
    :param key_filter: Function in which all keys should be filtered through.
                       Allowing key conversion from lowercase to uppercase
                       or vice versa for example.
    :param value_filter: Function in which all values should be filtered
                         through. In order to UTF-8 decode values for
                         example.
    """
    # In case we receive an object which is considered False in an expression
    # we return an empty dictionary. The reason is because NVP is in essence
    # query strings in their encoded format, i.e they are expected to contain
    # key-value pairs.
    if not string:
        return {}

    # In case the value is not a string we consider it decoded since no other
    # type is allowed nor can be decoded in this implementation.
    if not util.is_string(string):
        return string

    pairs = util.get_filtered_pairs(
        parse_qs(string, keep_blank_values=keep_blank_values),
        key_filter=key_filter, value_filter=value_filter,
    )

    params = dict(pairs)
    if not get_hierarchical:
        return params
    return util.get_hierarchical_dict(params)


def load(fp,
         keep_blank_values=False,
         strict_parsing=False,
         get_hierarchical=True,
         key_filter=None,
         value_filter=None):
    """Decode given NVP ``fp`` into a dictionary.
    Where ``fp`` is a file-like object supporting the ``read`` operation.

    :param fp: File-like object supporting the read operation
    :param keep_blank_values: Whether to retain keys with undefined values
    :param strict_parsing: Whether to use strict parsing of the query string
    :param get_hierarchical: Whether to decode into a single-level or
                             hierarchical dictionary.
    :param key_filter: Function in which all keys should be filtered through.
                       Allowing key conversion from lowercase to uppercase
                       or vice versa for example.
    :param value_filter: Function in which all values should be filtered
                         through. In order to UTF-8 decode values for
                         example.
    """
    kwargs = locals()
    del kwargs['fp']
    return loads(fp.read(), **kwargs)
