# -*- coding: utf-8 -*-
"""
Presence analyzer unit tests.
"""
import os.path
import json
import datetime
import unittest

from presence_analyzer import main, utils


TEST_DATA_CSV = os.path.join(
    os.path.dirname(__file__), '..', '..', 'runtime', 'data', 'test_data.csv'
)
TEST_USERS_XML = os.path.join(
    os.path.dirname(__file__), '..', '..', 'runtime', 'data', 'test_users.xml'
)
TEST_CACHE_CSV = os.path.join(
    os.path.dirname(__file__), '..', '..', 'runtime', 'data', 'test_cache.csv'
)


# pylint: disable=maybe-no-member, too-many-public-methods
class PresenceAnalyzerViewsTestCase(unittest.TestCase):
    """
    Views tests.
    """
    def check_status_and_content_type(self, path):
        resp = self.client.get(path)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        return json.loads(resp.data)

    def setUp(self):
        """
        Before each test, set up a environment.
        """
        main.app.config.update({'DATA_CSV': TEST_DATA_CSV})
        main.app.config.update({'USERS_DB_FILE': TEST_USERS_XML})
        self.client = main.app.test_client()

    def tearDown(self):
        """
        Get rid of unused objects after each test.
        """
        pass

    def test_mainpage(self):
        """
        Test main page redirect.
        """
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(resp.headers['Location'].endswith('/presence_weekday'))

    def test_api_users(self):
        """
        Test users listing.
        """
        data = self.check_status_and_content_type('/api/v1/users')
        self.assertEqual(
            data,
            [
                {u'name': u'Maciej Z.', u'user_id': 10},
                {u'name': u'Maciej D.', u'user_id': 11},
            ],
        )
        self.assertEqual(len(data), 2)

    def test_mean_time_weekday(self):
        """
        Test mean presence time of given user grouped by weekday.
        """
        self.assertEqual(
            self.check_status_and_content_type(
                '/api/v1/mean_time_weekday/10',
            ),
            [
                [u'Mon', 0],
                [u'Tue', 30047.0],
                [u'Wed', 24465.0],
                [u'Thu', 23705.0],
                [u'Fri', 0],
                [u'Sat', 0],
                [u'Sun', 0],
            ],
        )

    def test_presence_weekday(self):
        """
        Test total presence time of given user grouped by weekday.
        """
        self.assertEqual(
            self.check_status_and_content_type('/api/v1/presence_weekday/10'),
            [
                [u'Weekday', u'Presence (s)'],
                [u'Mon', 0],
                [u'Tue', 30047],
                [u'Wed', 24465],
                [u'Thu', 23705],
                [u'Fri', 0],
                [u'Sat', 0],
                [u'Sun', 0],
            ],
        )

    def test_presence_start_end(self):
        """
        Test mean time of starts and ends of given user grouped by weekday.
        """
        self.assertListEqual(
            self.check_status_and_content_type(
                '/api/v1/presence_start_end/11'
            ),
            [
                [u'Mon', [33134, 57257]],
                [u'Tue', [33590, 50154]],
                [u'Wed', [33206, 58527]],
                [u'Thu', [35602, 58586]],
                [u'Fri', [47816, 54242]],
                [u'Sat', [0, 0]],
                [u'Sun', [0, 0]],
            ]
        )

    def test_main_view(self):
        """
        Test main view
        """
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.content_type, 'text/html; charset=utf-8')
        self.assertTrue(resp.headers['Location'].endswith('/presence_weekday'))
        resp = self.client.get('/presence_weekday')
        self.assertIn('Presence by weekday', resp.data)
        resp = self.client.get('/mean_time_weekday')
        self.assertIn('Presence mean time by weekday', resp.data)
        resp = self.client.get('/presence_start_end')
        self.assertIn('Presence start-end weekday', resp.data)
        resp = self.client.get('/undefined')
        self.assertEqual(resp.status_code, 404)


class PresenceAnalyzerUtilsTestCase(unittest.TestCase):
    """
    Utility functions tests.
    """

    def setUp(self):
        """
        Before each test, set up a environment.
        """
        main.app.config.update({'DATA_CSV': TEST_DATA_CSV})
        main.app.config.update({'USERS_DB_FILE': TEST_USERS_XML})

    def tearDown(self):
        """
        Get rid of unused objects after each test.
        """
        pass

    def test_get_data(self):
        """
        Test parsing of CSV file.
        """
        data = utils.get_data()
        self.assertIsInstance(data, dict)
        self.assertItemsEqual(data.keys(), [10, 11])
        sample_date = datetime.date(2013, 9, 10)
        self.assertIn(sample_date, data[10])
        self.assertItemsEqual(data[10][sample_date].keys(), ['start', 'end'])
        self.assertEqual(
            data[10][sample_date]['start'],
            datetime.time(9, 39, 5)
        )

    def test_get_users_names(self):
        """
        Test parsing of xml file
        """
        data = utils.get_users_names()
        self.assertIsInstance(data, dict)
        self.assertItemsEqual(data.keys(), [10, 11])
        sample_data = 'name'
        self.assertIn(sample_data, data[10])
        self.assertItemsEqual(data[10].keys(), ['name'])
        self.assertEqual(
            data[10]['name'],
            'Maciej Z.'
        )

    def test_group_by_weekday(self):
        """
        Test group presence entries by weekday
        """
        data = utils.get_data()
        result = utils.group_by_weekday(data[10])
        self.assertEqual(result[2][0], 24465)
        self.assertEqual(result[3][0], 23705)
        self.assertIsInstance(result, list)

    def test_seconds_since_midnight(self):
        """
        Test of calculating amount of seconds since midnight
        """
        self.assertEqual(
            utils.seconds_since_midnight(datetime.time(2, 20, 35)),
            8435,
        )
        self.assertEqual(
            utils.seconds_since_midnight(datetime.time(22, 33, 44)),
            81224,
        )

    def test_interval(self):
        """
        Test of calculating interval
        """
        self.assertEqual(
            utils.interval(
                datetime.time(2, 20, 35), datetime.time(3, 25, 35),
            ),
            3900,
        )
        self.assertEqual(
            utils.interval(
                datetime.time(10, 05, 10), datetime.time(13, 40, 55),
            ),
            12945,
        )

    def test_mean(self):
        """
        Test of calculating arithmetic mean
        """
        self.assertEqual(
            utils.mean([1.3, 2.7, 5]),
            3,
        )
        self.assertAlmostEqual(
            utils.mean(
                [5.234, -2.34, 1.113, 3.2412, -0.1853, 0.54, 0.797],
            ),
            1.1999857,
        )
        self.assertEqual(utils.mean([]), 0)

    def test_starts_ends_mean_of_presence(self):
        """
        Test arithmetic mean of starts and ends of presence by weekday
        """
        data = utils.get_data()
        result = utils.starts_ends_mean_of_presence(data[11])
        self.assertDictEqual(
            result,
            {
                0: {'starts': [33134], 'ends': [57257]},
                1: {'starts': [33590], 'ends': [50154]},
                2: {'starts': [33206], 'ends': [58527]},
                3: {'starts': [37116, 34088], 'ends': [60085, 57087]},
                4: {'starts': [47816], 'ends': [54242]},
                5: {'starts': [], 'ends': []},
                6: {'starts': [], 'ends': []},
            }
        )
        self.assertIsInstance(result, dict)

    def test_cache(self):
        """
        Test caching of CSV file
        """
        result = utils.get_data()
        main.app.config.update({'DATA_CSV': TEST_CACHE_CSV})
        result_cached = utils.get_data()
        self.assertEqual(result_cached, result)
        utils.TIME = {}
        utils.CACHE = {}
        new_result = utils.get_data()
        self.assertNotEqual(new_result, result)
        main.app.config.update({'DATA_CSV': TEST_DATA_CSV})
        utils.TIME = {}
        utils.CACHE = {}


def suite():
    """
    Default test suite.
    """
    base_suite = unittest.TestSuite()
    base_suite.addTest(unittest.makeSuite(PresenceAnalyzerViewsTestCase))
    base_suite.addTest(unittest.makeSuite(PresenceAnalyzerUtilsTestCase))
    return base_suite


if __name__ == '__main__':
    unittest.main()
