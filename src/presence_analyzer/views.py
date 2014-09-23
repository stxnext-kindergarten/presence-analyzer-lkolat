# -*- coding: utf-8 -*-
"""
Defines views.
"""

import calendar
from flask import Flask, redirect, abort, render_template, url_for

from presence_analyzer.main import app
from presence_analyzer.utils import (
    jsonify,
    get_data,
    mean,
    group_by_weekday,
    starts_ends_mean_of_presence,
)

import logging
log = logging.getLogger(__name__)  # pylint: disable=invalid-name


@app.route('/')
def mainpage():
    """
    Redirects to front page.
    """
    return redirect('/templates/presence_weekday.html')


@app.route('/api/v1/users', methods=['GET'])
@jsonify
def users_view():
    """
    Users listing for dropdown.
    """
    data = get_data()
    return [
        {'user_id': i, 'name': 'User {0}'.format(str(i))}
        for i in data.keys()
    ]


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
        abort(204)

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


@app.route('/templates/<template_name>', methods=['GET'])
def render_templates(template_name):
    """
    Renders template.
    """
    return render_template(template_name)


@app.route('/templates/presence_weekday.html', methods=['GET', 'POST'])
def render_presence_weekday_view():
    """
    Renders presence weekday view
    """
    return render_template("presence_weekday.html")


@app.route('/templates/mean_time_weekday.html', methods=['GET', 'POST'])
def render_mean_time_weekday_view():
    """
    Renders mean time weekday view
    """
    return render_template("mean_time_weekday.html")


@app.route('/templates/presence_start_end.html', methods=['GET', 'POST'])
def render_presence_start_end_view():
    """
    Renders presence start end view
    """
    return render_template("presence_start_end.html")
