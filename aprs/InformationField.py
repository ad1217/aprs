#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

import aprs  # pylint: disable=R0801

class InformationField(object):

    """
    Class for APRS 'Information' Field.
    """

    _logger = logging.getLogger(__name__)  # pylint: disable=R0801
    if not _logger.handlers:  # pylint: disable=R0801
        _logger.setLevel(aprs.LOG_LEVEL)  # pylint: disable=R0801
        _console_handler = logging.StreamHandler()  # pylint: disable=R0801
        _console_handler.setLevel(aprs.LOG_LEVEL)  # pylint: disable=R0801
        _console_handler.setFormatter(aprs.LOG_FORMAT)  # pylint: disable=R0801
        _logger.addHandler(_console_handler)  # pylint: disable=R0801
        _logger.propagate = False  # pylint: disable=R0801

    __slots__ = ['data_type', 'data', 'safe']

    def __init__(self, data: bytes=b'', data_type: bytes=b'undefined',
                 safe: bool=False) -> None:
        self.data = data
        self.data_type = data_type
        self.safe = safe

    @classmethod
    def parse(cls, raw_data: bytes, handler=None) -> bytes:
        if not raw_data:
            return bytes()
        elif isinstance(raw_data, cls):
            return raw_data
        elif isinstance(raw_data, (bytearray, bytes)):
            data_type = b''
            data_type_field = chr(raw_data[0])
            data_type = aprs.DATA_TYPE_MAP.get(data_type_field)

            if data_type:
                if handler:
                    handler_func = getattr(
                        handler,
                        "handle_data_type_%s" % data_type,
                        None
                    )
                    return handler_func(raw_data, data_type)

            return cls(raw_data, data_type, safe=True)

    def __repr__(self) -> str:
        if self.safe:
            try:
                decoded_data = self.data.decode('UTF-8')
            except UnicodeDecodeError as ex:
                decoded_data = self.data.decode('UTF-8', 'backslashreplace')
            return decoded_data
        else:
            return self.data.decode()

    def __bytes__(self) -> bytes:
        return self.data
