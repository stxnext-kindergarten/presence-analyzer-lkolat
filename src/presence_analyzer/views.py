# -*- coding: utf-8 -*-
"""
Defines views.
"""

import calendar
import logging
import locale
from flask import redirect, abort, url_for
from flask.ext.mako import render_template, MakoTemplates
from mako.exceptions import TopLevelLookupException

from presence_analyzer.main import app
from presence_analyzer.utils import (
    jsonify,
    get_data,
    get_users_names,
    mean,
    group_by_weekday,
    starts_ends_mean_of_presence,
)

log = logging.getLogger(__name__)  # pylint: disable=invalid-name

mako = MakoTemplates(app)


@app.route('/')
def mainpage():
    """
    Redirects to front page.
    """
    return redirect(url_for(
        'main_view',
        template_name='presence_weekday'
        )
    )


@app.route('/api/v1/users', methods=['GET'])
@jsonify
def users_view():
    """
    Users listing for dropdown.
    """
    names = get_users_names()
    data = [
        {'user_id': i, 'name': names[i]['name']}
        for i in names.keys()
    ]
    locale.setlocale(locale.LC_COLLATE, "")
    sorted_data = sorted(data, key=lambda tup: tup['name'], cmp=locale.strcoll)
    return sorted_data


@app.route('/api/v1/mean_time_weekday/<int:user_id>', methods=['GET'])
@jsonify
def mean_time_weekday_view(user_id):
    """
    Returns mean presence time of given user grouped by weekday.
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        abort(404)

    weekdays = group_by_weekday(data[user_id])
    result = [
        (calendar.day_abbr[weekday], mean(intervals))
        for weekday, intervals in enumerate(weekdays)
    ]

    return result


@app.route('/api/v1/presence_weekday/<int:user_id>', methods=['GET'])
@jsonify
def presence_weekday_view(user_id):
    """
    Returns total presence time of given user grouped by weekday.
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        abort(404)

    weekdays = group_by_weekday(data[user_id])
    result = [
        (calendar.day_abbr[weekday], sum(intervals))
        for weekday, intervals in enumerate(weekdays)
    ]

    result.insert(0, ('Weekday', 'Presence (s)'))
    return result


@app.route('/api/v1/presence_start_end/<int:user_id>', methods=['GET'])
@jsonify
def presence_start_end_view(user_id):
    """
    Returns start and end time of given user grouped by weekday.
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        abort(404)

    raw_result = starts_ends_mean_of_presence(data[user_id])
    result = []
    for k in raw_result:
        result.append([
            calendar.day_abbr[k],
            [
                int(mean(raw_result[k]['starts'])),
                int(mean(raw_result[k]['ends'])),
            ]
        ])
    return result


@app.route('/<template_name>', methods=['GET'])
def main_view(template_name=None):
    """
    Returns main page.
    """
    try:
        template = "{}.html".format(template_name)
        return render_template(template, site=template_name)
    except TopLevelLookupException:
        abort(404)
