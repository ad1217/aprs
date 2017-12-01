#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Python APRS Module Function Definitions."""

import aprs  # pylint: disable=R0801

__author__ = 'Greg Albrecht W2GMD <oss@undef.net>'  # NOQA pylint: disable=R0801
__copyright__ = 'Copyright 2017 Greg Albrecht and Contributors'  # NOQA pylint: disable=R0801
__license__ = 'Apache License, Version 2.0'  # NOQA pylint: disable=R0801

def default_data_handler(data: bytes, data_type: bytes) -> bytes:
    """
    Handler for Undefined Data Types.
    """
    try:
        decoded_data = data.decode('UTF-8')
    except UnicodeDecodeError as ex:
        decoded_data = data.decode('UTF-8', 'backslashreplace')

    return aprs.InformationField(decoded_data, data_type)
