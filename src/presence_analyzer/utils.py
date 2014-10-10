# -*- coding: utf-8 -*-
"""
Helper functions used in views.
"""

import csv
import xml.etree.ElementTree as etree
import urllib
import os
import logging
import threading

from json import dumps
from functools import wraps
from datetime import datetime

from flask import Response

from presence_analyzer.main import app
log = logging.getLogger(__name__)  # pylint: disable=invalid-name

LOCK = threading.Lock()
CACHE = {}
TIME = {}


def jsonify(function):
    """
    Creates a response with the JSON representation of wrapped function result.
    """
    @wraps(function)
    def inner(*args, **kwargs):
        """
        This docstring will be overridden by @wraps decorator.
        """
        return Response(
            dumps(function(*args, **kwargs)),
            mimetype='application/json'
        )
    return inner


def lock(function):
    @wraps(function)
    def inner():
        with LOCK:
            result = function()
            return result
    return inner


def cache(time, method_name):

    def inner(method):
        @wraps(method)
        def wrapped():
            if CACHE.get(method_name):
                if (
                    TIME.get(method_name) is not None and
                    (
                        datetime.now() - TIME.get(method_name)
                    ).total_seconds() < time
                ):
                    return CACHE.get(method_name)
                else:
                    result = method()
                    CACHE[method_name] = result
                    TIME[method_name] = datetime.now()
                    return result
            else:
                result = method()
                CACHE[method_name] = result
                TIME[method_name] = datetime.now()
                return result
        return wrapped
    return inner


@lock
@cache(600, 'get_data')
def get_data():
    """
    Extracts presence data from CSV file and groups it by user_id.

    It creates structure like this:
    data = {
        'user_id': {
            datetime.date(2013, 10, 1): {
                'start': datetime.time(9, 0, 0),
                'end': datetime.time(17, 30, 0),
            },
            datetime.date(2013, 10, 2): {
                'start': datetime.time(8, 30, 0),
                'end': datetime.time(16, 45, 0),
            },
        }
    }
    """
    data = {}
    with open(app.config['DATA_CSV'], 'r') as csvfile:
        presence_reader = csv.reader(csvfile, delimiter=',')
        for i, row in enumerate(presence_reader):
            if len(row) != 4:
                # ignore header and footer lines
                continue

            try:
                user_id = int(row[0])
                date = datetime.strptime(row[1], '%Y-%m-%d').date()
                start = datetime.strptime(row[2], '%H:%M:%S').time()
                end = datetime.strptime(row[3], '%H:%M:%S').time()
            except (ValueError, TypeError):
                log.debug('Problem with line %d: ', i, exc_info=True)

            data.setdefault(user_id, {})[date] = {'start': start, 'end': end}

    return data


def get_users_names():
    """
    Extracts users data from XML file
    """
    users_data = {}
    tree = etree.parse(app.config['USERS_DB_FILE'])
    users = tree.find('users')
    for user in users:
        name = user.find('name').text
        user_id = int(os.path.split(user.find('avatar').text)[1])
        users_data.setdefault(user_id, {'name': name.encode("utf-8")})

    return users_data


def update_user_names():
    """
    Updates file with user names
    """
    with open(app.config['USERS_DB_FILE'], "w") as xml_file:
        xml_file.write(urllib.urlopen(app.config['USERS_SOURCE']).read())


def group_by_weekday(items):
    """
    Groups presence entries by weekday.
    """
    result = [[], [], [], [], [], [], []]  # one list for every day in week
    for date in items:
        start = items[date]['start']
        end = items[date]['end']
        result[date.weekday()].append(interval(start, end))
    return result


def seconds_since_midnight(time):
    """
    Calculates amount of seconds since midnight.
    """
    return time.hour * 3600 + time.minute * 60 + time.second


def interval(start, end):
    """
    Calculates inverval in seconds between two datetime.time objects.
    """
    return seconds_since_midnight(end) - seconds_since_midnight(start)


def mean(items):
    """
    Calculates arithmetic mean. Returns zero for empty lists.
    """
    return float(sum(items)) / len(items) if len(items) > 0 else 0


def starts_ends_mean_of_presence(items):
    """
    Calculates arithmetic mean of starts and ends of presence by weekday.
    """
    result = {i: {'starts': [], 'ends': []} for i in range(7)}

    for entry in items:
        result[entry.weekday()]['starts'].append(
            seconds_since_midnight(items[entry]['start'])
        )
        result[entry.weekday()]['ends'].append(
            seconds_since_midnight(items[entry]['end'])
        )
    return result
