# -*- coding: utf-8 -*-
"""Tests for cihai.

cihai.testsuite.cihai
~~~~~~~~~~~~~~~~~~~~~

Test :class:`Cihai` object. Other tests will use an instance of ``Cihai``
using the ``test_config.yml``.

"""

from __future__ import absolute_import, division, print_function, \
    with_statement, unicode_literals

import os
import tempfile
import logging
import unittest

import sqlalchemy

from sqlalchemy import Table, MetaData

import cihai

from .helpers import TestCase
from ..util import get_datafile
from .. import Cihai, CihaiDataset

log = logging.getLogger(__name__)


class MyDataset(CihaiDataset):
    def hey(self):
        pass

    def __init__(self, *args, **kwargs):
        CihaiDataset.__init__(self, *args, **kwargs)


class CihaiHelper(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = os.path.abspath(os.path.join(
            os.path.dirname(__file__),
            'test_config.yml'
        ))

        return cls

    def setUp(self):
        self.cihai = Cihai.from_file(self.config)


class CihaiTestCase(TestCase):
    """Cihai object initialization, defaults, configuration.

    """
    def test_config_defaults(self):
        """Test config defaults."""

        cihai = Cihai.from_file()

        self.assertTrue(hasattr(cihai.config, 'debug'))
        self.assertFalse(cihai.config.debug)

    def test_config_dict_args(self):
        """Accepts dict as config."""

        expected = 'world'

        cihai = Cihai({
            'hello': expected
        })

        result = cihai.config.hello

        self.assertEqual(result, expected)

    def test_config_loads_module(self):
        pass

    def test_config_loads_package_modules(self):
        pass

    def test_yaml_config_and_override(self):
        config = os.path.abspath(os.path.join(
            os.path.dirname(__file__),
            'test_config.yml'
        ))

        cihai = Cihai.from_cli(['-c', config])

        self.assertTrue(cihai.config.debug)

    def test_data_path_default(self):

        expected = os.path.abspath(os.path.join(
            os.path.dirname(cihai.__file__),
            'data/'
        ))

        c = Cihai.from_file()
        result = c.config.get('data_path')

        self.assertEqual(expected, result)

    def test_data_path_by_config_custom(self):
        """Test default data_path from config."""
        expected = '/home/r00t'

        cihai = Cihai({
            'data_path': expected
        })

        mydataset = cihai.use(MyDataset)

        result = mydataset.get_datapath('data_path')
        self.assertIn(expected, result)


class DatasetTestCase(CihaiHelper):

    def test_cihai_database_uses_same_metadata(self):
        """CihaiDataset subclasses uses the same MetaData instance."""

        c = self.cihai
        mydataset = c.use(MyDataset)
        self.assertEqual(mydataset.metadata, self.cihai.metadata)

    def test_has_application_custom_config(self):

        expected = '/home/r00t'

        cihai = Cihai({
            'data_path': expected
        })

        mydataset = cihai.use(MyDataset)

        result = mydataset.cihai.config.get('data_path')
        self.assertEqual(expected, result)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(CihaiTestCase))
    suite.addTest(unittest.makeSuite(DatasetTestCase))
    return suite
