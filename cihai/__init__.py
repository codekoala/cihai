#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""China fit in to a python package.

Cihai
-----

:class:`Cihai` is a python client for accessing relational CJK datasets.

Cihai also includes utilities for converting current datasets into relational
data (for query by SQL, joins, etc.).

Internals
~~~~~~~~~

An instance of ``Cihai`` may use one or more ``dataset``. The dataset
provides a primary datasource (from the internet, or a CSV) in form friendly
to relational databases.

.. code-block:: python

    from cihai import Cihai
    from cihai.datasets.unihan import Unihan

    c = Cihai()  # creates a new Cihai instance.
    c.use(Unihan())  # Cihai to use Unihan plugin.

A new cihai instance is bound to :class:`sqlalchemy.schema.MetaData` - this
holds database connection information and :class:`sqlalchemy.schema.Table`'s.

This means plugins like :class:`~.datasets.unihan.Unihan` have full access to
relational sqlalchemy MetaData.

:copyright: Copyright 2013-2014 Tony Narlock.
:license: BSD, see LICENSE for details

"""

from __future__ import absolute_import, division, print_function, \
    with_statement, unicode_literals

__title__ = 'cihai'
__version__ = '0.0.1'
__author__ = 'Tony Narlock'
__license__ = 'BSD 3-clause'
__copyright__ = 'Copyright 2013-2014 Tony Narlock'

from . import log, util, conversion

from .cihai import Cihai, CihaiDataset
