# -*- coding: utf8 - *-
"""Cihai dataset for `Unihan`_, Han Unification from Unicode, Inc.

cihai.datasets.unihan
~~~~~~~~~~~~~~~~~~~~~

"""

from __future__ import absolute_import, division, print_function, \
    with_statement, unicode_literals

import os
import sys
import glob
import hashlib
import fileinput
import zipfile
import logging

from sqlalchemy import Table, String, Column, Integer, Index, select, or_, and_

from .. import conversion, CihaiDataset
from ..util import UnicodeReader, _dl_progress
from .._compat import StringIO, urlretrieve

__copyright__ = 'Copyright 2013 Tony Narlock.'
__license__ = 'BSD, see LICENSE for details.'

log = logging.getLogger(__name__)

# This is the Unihan_DictionaryLikeData as of 6.3.0
# The format is { 'FILENAME': ['fields'] }
UNIHAN_DATASETS = {
    'Unihan_DictionaryIndices.txt': [
        'kCheungBauerIndex',
        'kCowles',
        'kDaeJaweon',
        'kFennIndex',
        'kGSR',
        'kHanYu',
        'kIRGDaeJaweon',
        'kIRGDaiKanwaZiten',
        'kIRGHanyuDaZidian',
        'kIRGKangXi',
        'kKangXi',
        'kKarlgren',
        'kLau',
        'kMatthews',
        'kMeyerWempe',
        'kMorohashi',
        'kNelson',
        'kSBGY',
    ],
    'Unihan_DictionaryLikeData.txt': [
        'kCangjie',
        'kCheungBauer',
        'kCihaiT',
        'kFenn',
        'kFourCornerCode',
        'kFrequency',
        'kGradeLevel',
        'kHDZRadBreak',
        'kHKGlyph',
        'kPhonetic',
        'kTotalStrokes',
    ],
    'Unihan_IRGSources.txt': [
        'kIICore',
        'kIRG_GSource',
        'kIRG_HSource',
        'kIRG_JSource',
        'kIRG_KPSource',
        'kIRG_KSource',
        'kIRG_MSource',
        'kIRG_TSource',
        'kIRG_USource',
        'kIRG_VSource',
    ],
    'Unihan_NumericValues.txt': [
        'kAccountingNumeric',
        'kOtherNumeric',
        'kPrimaryNumeric',
    ],
    'Unihan_OtherMappings.txt': [
        'kBigFive',
        'kCCCII',
        'kCNS1986',
        'kCNS1992',
        'kEACC',
        'kGB0',
        'kGB1',
        'kGB3',
        'kGB5',
        'kGB7',
        'kGB8',
        'kHKSCS',
        'kIBMJapan',
        'kJis0',
        'kJis1',
        'kJIS0213',
        'kKPS0',
        'kKPS1',
        'kKSC0',
        'kKSC1',
        'kMainlandTelegraph',
        'kPseudoGB1',
        'kTaiwanTelegraph',
        'kXerox',
    ],
    'Unihan_RadicalStrokeCounts.txt': [
        'kRSAdobe_Japan1_6',
        'kRSJapanese',
        'kRSKangXi',
        'kRSKanWa',
        'kRSKorean',
        'kRSUnicode',
    ],
    'Unihan_Readings.txt': [
        'kCantonese',
        'kDefinition',
        'kHangul',
        'kHanyuPinlu',
        'kHanyuPinyin',
        'kJapaneseKun',
        'kJapaneseOn',
        'kKorean',
        'kMandarin',
        'kTang',
        'kVietnamese',
        'kXHC1983',
    ],
    'Unihan_Variants.txt': [
        'kCompatibilityVariant',
        'kSemanticVariant',
        'kSimplifiedVariant',
        'kSpecializedSemanticVariant',
        'kTraditionalVariant',
        'kZVariant',
    ]

}

UNIHAN_URL = 'http://www.unicode.org/Public/UNIDATA/Unihan.zip'

table_name = 'Unihan'
default_columns = ['ucn', 'char']
in_columns = lambda c, columns: c in columns + default_columns
not_junk = lambda line: line[0] != '#' and line != '\n'
flatten_datasets = lambda d: sorted({c for cs in d.values() for c in cs})


def check_install(metadata, install_dict=None):

    if not install_dict:
        install_dict = UNIHAN_DATASETS

    columns = flatten_datasets(install_dict) + default_columns

    if table_name in metadata.tables.keys():
        table = metadata.tables[table_name]
        if set(columns) == set(c.name for c in table.columns):
            return True
        else:
            return False
    else:
        return False


def save(url, filename, urlretrieve=urlretrieve, *args):
    """Separate download function for testability.

    :param url: URL to download
    :type url: str
    :param filename: destination to download to.
    :type filename: string
    :param urlretrieve: function to download file
    :param *args: accepts a callback for ``retrieve`` function progress.
    :returns: Result of ``retrieve`` function

    """
    return urlretrieve(url, filename, *args[2:])


def download(url, dest, urlretrieve=urlretrieve):
    """Download a file to a destination.

    :param url: URL to download from.
    :param type: str
    :param destination: file path where download is to be saved.
    :type str:
    :returns: destination where file downloaded to
    :rtype str:

    """

    datadir = os.path.dirname(dest)
    if not os.path.exists(datadir):
        os.makedirs(datadir)

    no_unihan_files_exist = lambda: not glob.glob(
        os.path.join(datadir, 'Unihan*.txt')
    )

    not_downloaded = lambda: not os.path.exists(
        os.path.join(datadir, 'Unihan.zip')
    )

    if no_unihan_files_exist():
        if not_downloaded():
            print('Downloading Unihan.zip...')
            save(url, dest, urlretrieve, _dl_progress)

    return dest


def extract(zip_filepath):
    """Extract zip file. Return :class:`zipfile.ZipFile` instance.

    :param zip_filepath: file to extract.
    :type zip_filepath: string
    :returns: The extracted zip.
    :rtype: :class:`zipfile.ZipFile`

    """

    datadir = os.path.dirname(zip_filepath)
    try:
        z = zipfile.ZipFile(zip_filepath)
    except zipfile.BadZipfile as e:
        print('%s. Unihan.zip incomplete or corrupt. Redownloading...' % e)
        download()
        z = zipfile.ZipFile(zip_filepath)
    z.extractall(datadir)

    return z


def csv_to_dictlists(csv_files, columns):
    """Return dict from Unihan CSV files.

    :param csv_files: file names in data dir
    :type csv_files: list
    :return: List of tuples for data loaded

    """

    data = fileinput.FileInput(files=csv_files, openhook=fileinput.hook_encoded('utf-8'))
    items = {}
    for l in data:
        if not_junk(l):
            l = l.strip().split('\t')
            if in_columns(l[1], columns):
                item = dict(zip(['ucn', 'field', 'value'], l))
                char = conversion.ucn_to_unicode(item['ucn'])
                if not char in items:
                    items[char] = dict.fromkeys(columns)
                    items[char]['ucn'] = item['ucn']
                items[char][item['field']] = item['value']
    return items


def create_table(columns, metadata):
    """Create table and return  :class:`sqlalchemy.Table`.

    :param columns: columns for table, i.e. ['kDefinition', 'kCantonese']
    :type columns: list
    :param metadata: Instance of sqlalchemy metadata
    :type metadata: :class:`sqlalchemy.schema.MetaData`
    :returns: Newly created table with columns and index.
    :rtype: :class:`sqlalchemy.schema.Table`

    """

    if not table_name in metadata.tables:
        table = Table(table_name, metadata)

        table.append_column(Column('char', String(12), primary_key=True))
        table.append_column(Column('ucn', String(12), primary_key=True))

        for column_name in columns:
            col = Column(column_name, String(256), nullable=True)
            table.append_column(col)

        Index('%s_unique_char' % table_name, table.c.char, unique=True)
        Index('%s_unique_char_ucn' % table_name, table.c.char, table.c.ucn, unique=True)

        return table
    else:
        return Table(table_name, metadata)


class Unihan(CihaiDataset):

    """Cihai dataset for `Unihan`_, Han Unification from Unicode, Inc.

    :meth:`~.install` creates the tables, :meth:`~.import_csv_to_table`
    dumps csv to database.

    This module is used by adding to a :class:`cihai.Cihai` instance:

    .. code-block:: python

        from cihai import Cihai

        c = Cihai()
        c.use(Unihan)
        c.get('好')
        >>> {
            'definition': 'good'
        }

    .. _Unihan: http://www.unicode.org/reports/tr38/

    :todo: Add a :obj:`dict` instance variable for the available lookups
        tables to search) and have a default that only searches certain keys.
    :todo: Specify desired result fields to search (e.g. 'kDefinition').

    """

    def __init__(self, cihai, engine, metadata, fields=None, *args, **kwargs):
        """Start an instance of Unihan to :meth:`~.get` or :meth:`reverse` data.

        :param fields: (optional, default: None) Unihan fields to search for by
            default. By default all columns in the installed CSV's are
            retrieved.
        :type fields: list

        """
        super(Unihan, self).__init__(cihai, engine, metadata)

        """
        from sqlalchemy.
            msg = "%s is not bound to an Engine or Connection.  "\
                   "Execution can not proceed without a database to execute "\
                   "against." % item
            bind = _bind_or_error(metadata,
                    msg="No engine is bound to this Table's MetaData. "
                    "Pass an engine to the Table via "
                    "autoload_with=<someengine>, "
                    "or associate the MetaData with an engine via "
                    "metadata.bind=<someengine>")
        """

        try:
            self.fields = [f for t, f in UNIHAN_DATASETS.items() if t in ['Unihan']]
        except:
            self.fields = [f for t, f in UNIHAN_DATASETS.items()]
        self.default_fields = self.fields

    def install(self, install_dict=None):
        """Install the raw csv information into CSV, return table.

        :param install_dict: (optional, default=None) filename in /data dir and
            the field names to install. You can view all in ``UNIHAN_DATASETS``
            installs all CSV's and fields by default.

            .. code-block:: python

                {
                    'Unihan_DictionaryIndices.txt': [
                        'kCheungBauerIndex',
                        'kCowles'
                    ]
                }

        :type install_dict: dict
        :rtype: :class:`sqlalchemy.schema.Table`

        """

        if not install_dict:
            install_dict = UNIHAN_DATASETS
        files = tuple(self.get_datapath(f) for f in install_dict.keys())
        columns = flatten_datasets(install_dict)

        data = csv_to_dictlists(files, columns)

        table = create_table(columns, self.metadata)
        self.metadata.create_all()

        data = [dict(char=char, **values) for char, values in data.items()]

        self.metadata.bind.execute(table.insert(), data)

        return table

    def get(self, request, response, *args, **kwargs):
        """Return chinese character data from Unihan data.

        :param request:
        :type request: string
        :param response:
        :type response: dict
        :param fields: (default:None) list of fields, e.g. ['kDefinition']
        :type fields: list
        :returns: Cihai response dictionary
        :rtype: dict

        """

        if not request.startswith('U+'):
            request = conversion.python_to_ucn(request)

        if not 'fields' in kwargs:
            fields = self.default_fields
        else:
            fields = kwargs['fields']

        table = Table('Unihan', self.metadata)
        andfields = [(table.c.field == t) for t in fields]
        andstmt = and_(*andfields)

        q = select([
            table.c.field
        ]).where(andstmt)

        query = select([table.c.value, table.c.char, table.c.field]).where(
            table.c.field == q,
        ).where(table.c.value == request)

        query = query.execute()

        if query:
            if not 'unihan' in response:
                response['unihan'] = {}
            for r in query:
                response['unihan'][r['field']] = r['value']

        if not response['unihan']:
            # don't return empty lists.
            del response['unihan']

        return response

    def reverse(self, request, response, *args, **kwargs):
        """Return reverse look-up of chinese characters from Unihan data.

        :param request:
        :type request: string
        :param response:
        :type response: dict
        :param fields: (default:None) list of fields, e.g. ['kDefinition']
        :type fields: list
        :returns: Cihai response dictionary
        :rtype: dict

        """

        if not 'fields' in kwargs:
            fields = self.default_fields
        else:
            fields = kwargs['fields']

        table = Table('Unihan', self.metadata)
        andfields = [(table.c.field == t) for t in fields]
        andstmt = and_(*andfields)

        q = select([
            table.c.field
        ]).where(andstmt)

        query = select([table.c.value, table.c.char, table.c.field]).where(
            table.c.field == q,
        ).where(table.c.value.like(request))

        query = query.execute()

        if query:
            if not 'unihan' in response:
                response['unihan'] = {}
            for r in query:
                char = conversion.ucn_to_unicode(r['char'])
                if not char in response['unihan']:
                    response['unihan'][char] = {}
                response['unihan'][char][r['field']] = r['value']

        if not response['unihan']:
            # don't return empty lists.
            del response['unihan']

        return response
