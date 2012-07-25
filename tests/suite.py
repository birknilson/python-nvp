# -*- coding: utf-8 -*-
"""
NVP Test Suite.

This test suite will primarily iterate through the data source
located in the resource directory. Which contains decoded values
and their, expected, encoded counterparts.

Each decoded value will be encoded and then matched against the expected
value in the data source. The reverse is true for the encoded values in the
data source.

Although the data source is the main aspect of this test suite other
more specific test methods can reside here too.
"""

import sys
import json
import logging
import os.path
import unittest

try:
    # Utilize built-in collections.OrderedDict if Python >= 2.7
    from collections import OrderedDict as _BuiltinOrderedDict
    OrderedDict = _BuiltinOrderedDict  # Avoid Pyflakes warnings
except ImportError:
    from ordereddict import OrderedDict as _BackportedOrderedDict
    OrderedDict = _BackportedOrderedDict

try:
    import cStringIO as _cStringIO
    StringIO = _cStringIO.StringIO  # Avoid Pyflakes warnings
except ImportError:
    import StringIO as _StringIO
    StringIO = _StringIO.StringIO


def get_relative_as_abspath(path):
    return os.path.abspath(os.path.join(__file__, '../' + path))


# Insert the path of the source directory in which
# the local NVP module is located. Since the path is
# inserted in the beginning of the sys.path list the
# local version of the NVP module is ensured to be the one
# imported rather than one located in site-packages for instance.
sys.path.insert(0, get_relative_as_abspath('../'))
import nvp
import nvp.util


class TestUtils(unittest.TestCase):
    def test_is_string(self):
        self.assertTrue(nvp.util.is_string('Foobar'))

        self.assertFalse(nvp.util.is_string(dict(a=1)))
        self.assertFalse(nvp.util.is_string(1))
        self.assertFalse(nvp.util.is_string(1.33))
        self.assertFalse(nvp.util.is_string([3]))
        self.assertFalse(nvp.util.is_string((1,)))
        self.assertFalse(nvp.util.is_string(set([])))
        self.assertFalse(nvp.util.is_string(frozenset([])))

    def test_is_dict(self):
        self.assertTrue(nvp.util.is_dict(dict(a=1)))

        self.assertFalse(nvp.util.is_dict('Foobar'))
        self.assertFalse(nvp.util.is_dict(1))
        self.assertFalse(nvp.util.is_dict(1.33))
        self.assertFalse(nvp.util.is_dict([3]))
        self.assertFalse(nvp.util.is_dict((1,)))
        self.assertFalse(nvp.util.is_string(set([])))
        self.assertFalse(nvp.util.is_string(frozenset([])))

    def test_get_key_sequence_type(self):
        is_prefix = nvp.util.get_key_sequence_type('L_SOMEKEY0')
        is_bracket = nvp.util.get_key_sequence_type('somekey[0]')
        is_parentheses = nvp.util.get_key_sequence_type('somekey(0)')
        is_none = nvp.util.get_key_sequence_type('somekey')

        self.assertTrue((is_prefix == nvp.util.TYPE_SEQUENCE_PREFIX))
        self.assertTrue((is_bracket == nvp.util.TYPE_SEQUENCE_BRACKET))
        self.assertTrue((is_parentheses == nvp.util.TYPE_SEQUENCE_PARENTHESES))
        self.assertFalse(is_none)

    def test_key_sequence_type_exception(self):
        self.assertRaises(ValueError,
                          nvp.util.detect_key_sequence_index,
                          'invalid_sequence_type',
                          'somekey')


class TestAPI(unittest.TestCase):
    """The data source test case."""
    #: Name of keys containing encoded & decoded values in the data source
    METHOD_KEYS = ('encoded', 'decoded')
    #: Name of encoding & decoding functions in the NVP module
    METHOD_FILTERS = ('loads', 'dumps')

    def setUp(self):
        path = get_relative_as_abspath('resources/data.json')
        with open(path) as f:
            self.data_source = json.load(f)

    def sort_encoded_value(self, string):
        """Sort encoded value, i.e URL encoded string.

        This is achieved by retrieving the key-value pairs
        in a list which is then sorted in regular fashion.

        :param string: The encoded URL string
        """
        return '&'.join(sorted(string.split('&')))

    def sort_decoded_value(self, obj):
        """Sort decoded value, i.e data dictionary.

        This is achieved by iterating through the dictionary and converting
        it to an ``OrderedDict`` - initialized with the items which have been
        sorted depending on their corresponding keys.

        This method is recursive in order to ensure even dictionaries within
        the primary one is sorted too.

        :param obj: The data dictionary to sort
        """
        ret = {}
        for key, value in obj.items():
            if nvp.util.is_dict(value):
                value = self.sort_decoded_value(value)
            ret[key] = value

        ret = OrderedDict(sorted(ret.items(), key=lambda kwarg: kwarg[0]))
        return ret

    def ensure_sorted_value(self, value):
        """Ensure given value is sorted.

        This is required in order to ensure comparison will work as expected
        when dealing with dictionaries - either retrieved through decoding or
        in the encoding procedure.

        :param value: The value to sort
        """
        if not hasattr(value, '__getitem__'):
            raise ValueError('Value is required to be a sequence: %s' % value)

        # Check whether the value is a string
        if hasattr(value, 'join'):
            return self.sort_encoded_value(value)
        return self.sort_decoded_value(value)

    def get_stringio_value(self, value):
        fp = StringIO()
        fp.write(value)
        fp.seek(0)
        return fp

    def execute_coding(self, to_decode=True):
        """Run through data source values and verify that they are
        either encoded or decoded as expected.

        Since the data source contains the decoded values of the
        encoded strings they can easily be matched against each other
        to verify both the decoding & encoding procedures.

        Which coding method to utilize is determined by the value
        of the ``to_decode`` parameter.
        """
        # Retrieve target directory, i.e the one to test
        k_target = self.METHOD_KEYS[to_decode]
        target = self.data_source[k_target]

        # Retrieve outcome directory, i.e the one to match against
        k_outcome = self.METHOD_KEYS[(not to_decode)]
        outcome = self.data_source[k_outcome]

        # Retrieve the function of which the individual values
        # should be filtered through in order to decode or encode.
        filter_method_name = self.METHOD_FILTERS[to_decode]
        execute_filter = getattr(nvp, filter_method_name)

        for key, value in target.iteritems():
            to_match = self.ensure_sorted_value(outcome[key])
            filtered_value = self.ensure_sorted_value(execute_filter(value))

            is_correct_value = (filtered_value == to_match)
            self.assertTrue(is_correct_value)

    def test_dumps(self):
        """Test encoding all decoded data source values using nvp.dumps."""
        self.execute_coding(to_decode=False)

    def test_loads(self):
        """Test decoding all encoded data source values using nvp.loads."""
        self.execute_coding(to_decode=True)

    def test_load(self):
        # TODO: Once dumps is implemented and not merely an alias
        # to urllib.urlencode the value should be more complex here...
        value = {
            'foo': 'hello',
        }
        encoded_value = nvp.dumps(value)
        fp = self.get_stringio_value(encoded_value)
        loaded_value = nvp.load(fp)
        self.assertTrue(loaded_value == value)


if __name__ == '__main__':
    unittest.main()
