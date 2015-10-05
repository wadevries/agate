#!/usr/bin/env Python

import datetime
from decimal import Decimal

try:
    import unittest2 as unittest
except ImportError:
    import unittest

try:
    from unittest.mock import Mock
except:
    from mock import Mock

from agate import Table
from agate.aggregations import *
from agate.columns import Column
from agate.data_types import *
from agate.exceptions import *

class TestSimpleAggregation(unittest.TestCase):
    def setUp(self):
        self.rows = (
            (1, 2, 'a'),
            (2, 3, 'b'),
            (None, 4, 'c')
        )

        self.number_type = Number()
        self.text_type = Text()

        self.columns = (
            ('one', self.number_type),
            ('two', self.number_type),
            ('three', self.text_type)
        )

        self.table = Table(self.rows, self.columns)

    def test_caching(self):
        length = Length()
        length.run = Mock(return_value=33)

        self.assertEqual(self.table.columns['one']._aggregate_cache, {})
        self.assertEqual(self.table.columns['one'].aggregate(length), 33)
        self.assertEqual(self.table.columns['one']._aggregate_cache, { 'Length': 33 })
        self.assertEqual(length.run.call_count, 1)
        self.assertEqual(self.table.columns['one'].aggregate(length), 33)
        self.assertEqual(length.run.call_count, 1)

    def test_any(self):
        with self.assertRaises(ValueError):
            self.table.columns['one'].aggregate(Any())

        self.assertEqual(self.table.columns['one'].aggregate(Any(lambda d: d == 2)), True)
        self.assertEqual(self.table.columns['one'].aggregate(Any(lambda d: d == 5)), False)

    def test_all(self):
        with self.assertRaises(ValueError):
            self.table.columns['one'].aggregate(All())

        self.assertEqual(self.table.columns['one'].aggregate(All(lambda d: d != 5)), True)
        self.assertEqual(self.table.columns['one'].aggregate(All(lambda d: d == 2)), False)

    def test_length(self):
        rows = (
            (1, 2, 'a'),
            (2, 3, 'b'),
            (None, 4, 'c'),
            (1, 2, 'a'),
            (1, 2, 'a')
        )

        table = Table(rows, self.columns)

        self.assertEqual(table.columns['one'].aggregate(Length()), 5)
        self.assertEqual(table.columns['two'].aggregate(Length()), 5)

    def test_count(self):
        rows = (
            (1, 2, 'a'),
            (2, 3, 'b'),
            (None, 4, 'c'),
            (1, 2, 'a'),
            (1, 2, 'a')
        )

        table = Table(rows, self.columns)

        self.assertEqual(table.columns['one'].aggregate(Count(1)), 3)
        self.assertEqual(table.columns['one'].aggregate(Count(4)), 0)
        self.assertEqual(table.columns['one'].aggregate(Count(None)), 1)

class TestBooleanAggregation(unittest.TestCase):
    def test_any(self):
        column = Column(Boolean(), None, 'one')
        column.get_data = lambda: (True, False, None)
        self.assertEqual(column.aggregate(Any()), True)

        column.get_data = lambda: (False, False, None)
        self.assertEqual(column.aggregate(Any()), False)

    def test_all(self):
        column = Column(Boolean(), None, 'one')
        column.get_data = lambda: (True, True, None)
        self.assertEqual(column.aggregate(All()), False)

        column.get_data = lambda: (True, True, True)
        self.assertEqual(column.aggregate(All()), True)

class TestDateTimeAggregation(unittest.TestCase):
    def test_min(self):
        column = Column(DateTime(), None, 'one')
        column.get_data_without_nulls = lambda: (
            datetime.datetime(1994, 3, 3, 6, 31),
            datetime.datetime(1994, 3, 3, 6, 30, 30),
            datetime.datetime(1994, 3, 3, 6, 30)
        )

        self.assertEqual(column.aggregate(Min()), datetime.datetime(1994, 3, 3, 6, 30))

    def test_max(self):
        column = Column(DateTime(), None, 'one')
        column.get_data_without_nulls = lambda: (
            datetime.datetime(1994, 3, 3, 6, 31),
            datetime.datetime(1994, 3, 3, 6, 30, 30),
            datetime.datetime(1994, 3, 3, 6, 30)
        )

        self.assertEqual(column.aggregate(Max()), datetime.datetime(1994, 3, 3, 6, 31))

class TestNumberAggregation(unittest.TestCase):
    def setUp(self):
        self.rows = (
            (Decimal('1.1'), Decimal('2.19'), 'a'),
            (Decimal('2.7'), Decimal('3.42'), 'b'),
            (None, Decimal('4.1'), 'c'),
            (Decimal('2.7'), Decimal('3.42'), 'c')
        )

        self.number_type = Number()
        self.text_type = Text()

        self.columns = (
            ('one', self.number_type),
            ('two', self.number_type),
            ('three', self.text_type)
        )

        self.table = Table(self.rows, self.columns)

    def test_max_precision(self):
        self.assertEqual(self.table.columns['one'].aggregate(MaxPrecision()), 1)
        self.assertEqual(self.table.columns['two'].aggregate(MaxPrecision()), 2)

        with self.assertRaises(DataTypeError):
            self.table.columns['three'].aggregate(MaxPrecision())

    def test_sum(self):
        self.assertEqual(self.table.columns['one'].aggregate(Sum()), Decimal('6.5'))
        self.assertEqual(self.table.columns['two'].aggregate(Sum()), Decimal('13.13'))

        with self.assertRaises(DataTypeError):
            self.table.columns['three'].aggregate(Sum())

    def test_min(self):
        with self.assertRaises(DataTypeError):
            self.table.columns['three'].aggregate(Min())

        self.assertEqual(self.table.columns['one'].aggregate(Min()), Decimal('1.1'))
        self.assertEqual(self.table.columns['two'].aggregate(Min()), Decimal('2.19'))

    def test_max(self):
        with self.assertRaises(DataTypeError):
            self.table.columns['three'].aggregate(Max())

        self.assertEqual(self.table.columns['one'].aggregate(Max()), Decimal('2.7'))
        self.assertEqual(self.table.columns['two'].aggregate(Max()), Decimal('4.1'))

    def test_mean(self):
        with self.assertRaises(NullCalculationError):
            self.table.columns['one'].aggregate(Mean())

        with self.assertRaises(DataTypeError):
            self.table.columns['three'].aggregate(Mean())

        self.assertEqual(self.table.columns['two'].aggregate(Mean()), Decimal('3.2825'))

    def test_median(self):
        with self.assertRaises(NullCalculationError):
            self.table.columns['one'].aggregate(Median())

        with self.assertRaises(DataTypeError):
            self.table.columns['three'].aggregate(Median())

        self.assertEqual(self.table.columns['two'].aggregate(Median()), Decimal('3.42'))

    def test_mode(self):
        with self.assertRaises(NullCalculationError):
            self.table.columns['one'].aggregate(Mode())

        with self.assertRaises(DataTypeError):
            self.table.columns['three'].aggregate(Mode())

        self.assertEqual(self.table.columns['two'].aggregate(Mode()), Decimal('3.42'))

    def test_iqr(self):
        with self.assertRaises(NullCalculationError):
            self.table.columns['one'].aggregate(IQR())

        with self.assertRaises(DataTypeError):
            self.table.columns['three'].aggregate(IQR())

        self.assertEqual(self.table.columns['two'].aggregate(IQR()), Decimal('0.955'))

    def test_variance(self):
        with self.assertRaises(NullCalculationError):
            self.table.columns['one'].aggregate(Variance())

        with self.assertRaises(DataTypeError):
            self.table.columns['three'].aggregate(Variance())

        self.assertEqual(self.table.columns['two'].aggregate(Variance()).quantize(Decimal('0.0001')), Decimal('0.6332'))

    def test_population_variance(self):
        with self.assertRaises(NullCalculationError):
            self.table.columns['one'].aggregate(PopulationVariance())

        with self.assertRaises(DataTypeError):
            self.table.columns['three'].aggregate(PopulationVariance())

        self.assertEqual(self.table.columns['two'].aggregate(PopulationVariance()).quantize(Decimal('0.0001')), Decimal('0.4749'))

    def test_stdev(self):
        with self.assertRaises(NullCalculationError):
            self.table.columns['one'].aggregate(StDev())

        with self.assertRaises(DataTypeError):
            self.table.columns['three'].aggregate(StDev())

        self.assertAlmostEqual(self.table.columns['two'].aggregate(StDev()).quantize(Decimal('0.0001')), Decimal('0.7958'))

    def test_population_stdev(self):
        with self.assertRaises(NullCalculationError):
            self.table.columns['one'].aggregate(PopulationStDev())

        with self.assertRaises(DataTypeError):
            self.table.columns['three'].aggregate(PopulationStDev())

        self.assertAlmostEqual(self.table.columns['two'].aggregate(PopulationStDev()).quantize(Decimal('0.0001')), Decimal('0.6891'))

    def test_mad(self):
        with self.assertRaises(NullCalculationError):
            self.table.columns['one'].aggregate(MAD())

        with self.assertRaises(DataTypeError):
            self.table.columns['three'].aggregate(MAD())

        self.assertAlmostEqual(self.table.columns['two'].aggregate(MAD()), Decimal('0'))

    def test_percentiles(self):
        with self.assertRaises(NullCalculationError):
            self.table.columns['one'].aggregate(Percentiles())

        rows = [(n,) for n in range(1, 1001)]

        table = Table(rows, (('ints', self.number_type),))

        percentiles = table.columns['ints'].aggregate(Percentiles())

        self.assertEqual(percentiles[0], Decimal('1'))
        self.assertEqual(percentiles[25], Decimal('250.5'))
        self.assertEqual(percentiles[50], Decimal('500.5'))
        self.assertEqual(percentiles[75], Decimal('750.5'))
        self.assertEqual(percentiles[99], Decimal('990.5'))
        self.assertEqual(percentiles[100], Decimal('1000'))

    def test_percentiles_locate(self):
        rows = [(n,) for n in range(1, 1001)]

        table = Table(rows, (('ints', self.number_type),))

        percentiles = table.columns['ints'].aggregate(Percentiles())

        self.assertEqual(percentiles.locate(251), Decimal('25'))
        self.assertEqual(percentiles.locate(260), Decimal('25'))
        self.assertEqual(percentiles.locate(261), Decimal('26'))

        with self.assertRaises(ValueError):
            percentiles.locate(0)

        with self.assertRaises(ValueError):
            percentiles.locate(1012)

    def test_quartiles(self):
        """
        CDF quartile tests from:
        http://www.amstat.org/publications/jse/v14n3/langford.html#Parzen1979
        """
        with self.assertRaises(NullCalculationError):
            self.table.columns['one'].aggregate(Quartiles())

        # N = 4
        rows = [(n,) for n in [1, 2, 3, 4]]

        table = Table(rows, (('ints', self.number_type),))

        quartiles = table.columns['ints'].aggregate(Quartiles())

        for i, v in enumerate(['1', '1.5', '2.5', '3.5', '4']):
            self.assertEqual(quartiles[i], Decimal(v))

        # N = 5
        rows = [(n,) for n in [1, 2, 3, 4, 5]]

        table = Table(rows, (('ints', self.number_type),))

        quartiles = table.columns['ints'].aggregate(Quartiles())

        for i, v in enumerate(['1', '2', '3', '4', '5']):
            self.assertEqual(quartiles[i], Decimal(v))

        # N = 6
        rows = [(n,) for n in [1, 2, 3, 4, 5, 6]]

        table = Table(rows, (('ints', self.number_type),))

        quartiles = table.columns['ints'].aggregate(Quartiles())

        for i, v in enumerate(['1', '2', '3.5', '5', '6']):
            self.assertEqual(quartiles[i], Decimal(v))

        # N = 7
        rows = [(n,) for n in [1, 2, 3, 4, 5, 6, 7]]

        table = Table(rows, (('ints', self.number_type),))

        quartiles = table.columns['ints'].aggregate(Quartiles())

        for i, v in enumerate(['1', '2', '4', '6', '7']):
            self.assertEqual(quartiles[i], Decimal(v))

        # N = 8 (doubled)
        rows = [(n,) for n in [1, 1, 2, 2, 3, 3, 4, 4]]

        table = Table(rows, (('ints', self.number_type),))

        quartiles = table.columns['ints'].aggregate(Quartiles())

        for i, v in enumerate(['1', '1.5', '2.5', '3.5', '4']):
            self.assertEqual(quartiles[i], Decimal(v))

        # N = 10 (doubled)
        rows = [(n,) for n in [1, 1, 2, 2, 3, 3, 4, 4, 5, 5]]

        table = Table(rows, (('ints', self.number_type),))

        quartiles = table.columns['ints'].aggregate(Quartiles())

        for i, v in enumerate(['1', '2', '3', '4', '5']):
            self.assertEqual(quartiles[i], Decimal(v))

        # N = 12 (doubled)
        rows = [(n,) for n in [1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6]]

        table = Table(rows, (('ints', self.number_type),))

        quartiles = table.columns['ints'].aggregate(Quartiles())

        for i, v in enumerate(['1', '2', '3.5', '5', '6']):
            self.assertEqual(quartiles[i], Decimal(v))

        # N = 14 (doubled)
        rows = [(n,) for n in [1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7]]

        table = Table(rows, (('ints', self.number_type),))

        quartiles = table.columns['ints'].aggregate(Quartiles())

        for i, v in enumerate(['1', '2', '4', '6', '7']):
            self.assertEqual(quartiles[i], Decimal(v))

    def test_quartiles_locate(self):
        """
        CDF quartile tests from:
        http://www.amstat.org/publications/jse/v14n3/langford.html#Parzen1979
        """
        # N = 4
        rows = [(n,) for n in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]]

        table = Table(rows, (('ints', self.number_type),))

        quartiles = table.columns['ints'].aggregate(Quartiles())

        self.assertEqual(quartiles.locate(2), Decimal('0'))
        self.assertEqual(quartiles.locate(4), Decimal('1'))
        self.assertEqual(quartiles.locate(6), Decimal('2'))
        self.assertEqual(quartiles.locate(8), Decimal('3'))

        with self.assertRaises(ValueError):
            quartiles.locate(0)

        with self.assertRaises(ValueError):
            quartiles.locate(11)

    def test_quintiles(self):
        with self.assertRaises(NullCalculationError):
            self.table.columns['one'].aggregate(Quintiles())

        rows = [(n,) for n in range(1, 1001)]

        table = Table(rows, (('ints', self.number_type),))

        table.columns['ints'].aggregate(Quintiles())

    def test_deciles(self):
        with self.assertRaises(NullCalculationError):
            self.table.columns['one'].aggregate(Quintiles())

        rows = [(n,) for n in range(1, 1001)]

        table = Table(rows, (('ints', self.number_type),))

        table.columns['ints'].aggregate(Deciles())

class TestTextAggregation(unittest.TestCase):
    def test_max_length(self):
        column = Column(Text(), None, 'one')
        column.get_data = lambda: ('a', 'gobble', 'wow')
        self.assertEqual(column.aggregate(MaxLength()), 6)

    def test_max_length_invalid(self):
        column = Column(Number(), None, 'one')
        column.get_data = lambda: (1, 2, 3)

        with self.assertRaises(DataTypeError):
            column.aggregate(MaxLength())
