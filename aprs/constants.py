#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Python APRS Module Constants."""

import logging
import os

__author__ = 'Greg Albrecht W2GMD <oss@undef.net>'  # NOQA pylint: disable=R0801
__copyright__ = 'Copyright 2017 Greg Albrecht and Contributors'  # NOQA pylint: disable=R0801
__license__ = 'Apache License, Version 2.0'  # NOQA pylint: disable=R0801


if bool(os.environ.get('DEBUG')):
    LOG_LEVEL = logging.DEBUG
    logging.debug('Debugging Enabled via DEBUG Environment Variable.')
else:
    LOG_LEVEL = logging.INFO

LOG_FORMAT = logging.Formatter(
    ('%(asctime)s aprs %(levelname)s %(name)s.%(funcName)s:%(lineno)d - '
     '%(message)s'))

APRSIS_SERVERS = [b'rotate.aprs.net', b'noam.aprs2.net']

APRSIS_SW_VERSION = b'APRS Python Module'

APRSIS_HTTP_HEADERS = {
    'content-type': 'application/octet-stream',
    'accept': 'text/plain'
}

APRSIS_FILTER_PORT = int(os.environ.get('APRSIS_FILTER_PORT', 14580))
APRSIS_RX_PORT = int(os.environ.get('APRSIS_RX_PORT', 8080))
APRSIS_URL = os.environ.get('APRSIS_URL', b'http://srvr.aprs-is.net:8080')

RECV_BUFFER = int(os.environ.get('RECV_BUFFER', 1024))

DEFAULT_TOCALL = b'APYT70'

# AX.25 Flag — The flag field at each end of the frame is the bit sequence
#              0x7E that separates each frame.
AX25_FLAG = b'\x7E'
# AX.25 Control Field — This field is set to 0x03 (UI-frame).
AX25_CONTROL_FIELD = b'\x03'
# AX.25 Protocol ID — This field is set to 0xf0 (no layer 3 protocol).
AX25_PROTOCOL_ID = b'\xF0'
# A good place to split AX.25 Address from Information fields.
ADDR_INFO_DELIM = AX25_CONTROL_FIELD + AX25_PROTOCOL_ID

DATA_TYPE_MAP = {
    '\x1c': 'current_mice_beta',
    '\x1d': 'old_mice_beta',
    '!': 'position_nots_nomsg', # or Ultimeter 2000 WX Station
    '#': 'peet_bros_uii_weather',
    '$': 'raw_gps', # or Ultimeter 2000
    '%': 'agrelo_dfjr_microfinder',
    '&': 'reserved_map_feature',
    "'": 'old_mice', # Current data for TM-D700
    ')': 'item',
    '*': 'peet_bros_uii_weather',
    '+': 'reserved_shelter_data_with_time',
    ',': 'invalid_or_test',
    '.': 'reserved_space_weather',
    '/': 'position_ts_nomsg',
    ':': 'message',
    ';': 'object',
    '<': 'station_capabilities',
    '=': 'position_nots_msg',
    '>': 'status',
    '?': 'query',
    '@': 'position_ts_msg',
    'T': 'telemetry',
    '[': 'maidenhead_beacon', # obsolete
    '_': 'weather',
    '`': 'current_mice', # Except in TM-D700
    '{': 'user_defined',
    '}': 'third_party'}

# KISS Command Codes
# http://en.wikipedia.org/wiki/KISS_(TNC)#Command_Codes
KISS_DATA_FRAME = b'\x00'
