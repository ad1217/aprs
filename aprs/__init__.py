#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Python APRS Module.

"""
Python APRS Module.
~~~~


:author: Greg Albrecht W2GMD <oss@undef.net>
:copyright: Copyright 2017 Greg Albrecht and Contributors
:license: Apache License, Version 2.0
:source: <https://github.com/ampledata/aprs>

"""

from .constants import (LOG_FORMAT, LOG_LEVEL, APRSIS_SW_VERSION,  # NOQA
                        APRSIS_HTTP_HEADERS, APRSIS_SERVERS,
                        APRSIS_FILTER_PORT, APRSIS_RX_PORT, RECV_BUFFER,
                        APRSIS_URL, DEFAULT_TOCALL, AX25_FLAG,
                        AX25_CONTROL_FIELD, AX25_PROTOCOL_ID, ADDR_INFO_DELIM,
                        DATA_TYPE_MAP, KISS_DATA_FRAME)

from .exceptions import BadCallsignError  # NOQA

from .util import valid_callsign  # NOQA

from .geo_util import dec2dm_lat, dec2dm_lng, ambiguate  # NOQA

from .fcs import FCS  # NOQA

from .Frame import Frame, PositionFrame

from .Callsign import Callsign

from .InformationField import InformationField

from .classes import (APRS, TCP, UDP, HTTP) # NOQA


__author__ = 'Greg Albrecht W2GMD <oss@undef.net>'  # NOQA pylint: disable=R0801
__copyright__ = 'Copyright 2017 Greg Albrecht and Contributors'  # NOQA pylint: disable=R0801
__license__ = 'Apache License, Version 2.0'  # NOQA pylint: disable=R0801
