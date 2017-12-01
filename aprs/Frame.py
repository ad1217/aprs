#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import typing

import aprs  # pylint: disable=R0801

AprsFrame = typing.TypeVar('AprsFrame', bound='aprs.Frame')

class Frame(object):

    """
    Frame Class.

    Defines the components of an AX.25/APRS Frame.
    """

    __slots__ = ['source', 'destination', 'path', 'info']

    _logger = logging.getLogger(__name__)  # pylint: disable=R0801
    if not _logger.handlers:  # pylint: disable=R0801
        _logger.setLevel(aprs.LOG_LEVEL)  # pylint: disable=R0801
        _console_handler = logging.StreamHandler()  # pylint: disable=R0801
        _console_handler.setLevel(aprs.LOG_LEVEL)  # pylint: disable=R0801
        _console_handler.setFormatter(aprs.LOG_FORMAT)  # pylint: disable=R0801
        _logger.addHandler(_console_handler)  # pylint: disable=R0801
        _logger.propagate = False  # pylint: disable=R0801

    def __init__(self, source: bytes=b'', destination: bytes=b'',
                 path: list=[], info: bytes=b'') -> None:
        self.source = aprs.Callsign.parse(source)
        self.destination = aprs.Callsign.parse(destination)
        # TODO: Add parse_path function
        self.path = path
        self.info = aprs.InformationField.parse(info)

    @classmethod
    def parse(cls, raw_frame: typing.Union[bytes, str]) -> AprsFrame:
        """
        Parses an AX.25/APRS Frame from either plain-text or AX.25.
        """
        if isinstance(raw_frame, cls):
            return raw_frame
        elif isinstance(raw_frame, str):
            return cls.from_text(bytes(raw_frame, 'UTF-8'))
        elif isinstance(raw_frame, (bytearray, bytes)):
            if aprs.ADDR_INFO_DELIM in raw_frame:
                return cls.from_ax25(raw_frame)
            else:
                return cls.from_text(raw_frame)


    @classmethod
    def from_text(cls, raw_frame: bytes) -> AprsFrame:
        """
        Parses and Extracts the components of a str Frame.
        """
        parsed_frame = cls()
        _path = []

        # Source>Destination
        sd_delim = raw_frame.index(b'>')

        parsed_frame.set_source(raw_frame[:sd_delim])

        # Path:Info
        pi_delim = raw_frame.index(b':')

        parsed_path = raw_frame[sd_delim + 1:pi_delim]
        if b',' in parsed_path:
            for path in parsed_path.split(b','):
                _path.append(path)
            parsed_frame.set_destination(_path.pop(0))
            parsed_frame.set_path(_path)
        else:
            parsed_frame.set_destination(parsed_path)

        parsed_frame.set_info(raw_frame[pi_delim + 1:])

        return parsed_frame

    @classmethod
    def from_ax25(cls, raw_frame: bytes) -> AprsFrame:
        """
        Parses and Extracts the components of an AX.25-Encoded Frame.
        """
        kiss_call = False

        _frame = raw_frame.strip(aprs.AX25_FLAG)
        if (_frame.startswith(aprs.KISS_DATA_FRAME) or
                _frame.endswith(aprs.KISS_DATA_FRAME)):
            _frame = _frame.lstrip(aprs.KISS_DATA_FRAME)
            _frame = _frame.rstrip(aprs.KISS_DATA_FRAME)
            kiss_call = True

        # Use these two fields as the address/information delimiter
        frame_addressing, frame_information = _frame.split(aprs.ADDR_INFO_DELIM)

        info_field = frame_information.rstrip(b'\xFF\x07')

        destination = aprs.Callsign.from_ax25(frame_addressing, kiss_call)
        source = aprs.Callsign.from_ax25(frame_addressing[7:], kiss_call)

        paths = frame_addressing[7+7:]
        n_paths = int(len(paths) / 7)
        n = 0
        path = []
        while n < n_paths:
            path.append(aprs.Callsign.from_ax25(paths[:7]))
            paths = paths[7:]
            n += 1

        return cls(source, destination, path, info_field)

    def __repr__(self) -> str:
        """
        Returns a string representation of this Object.
        """
        full_path = [str(self.destination)]
        full_path.extend([str(p) for p in self.path])
        frame = "%s>%s:%s" % (
            self.source,
            ','.join(full_path),
            self.info
        )
        return frame

    def __bytes__(self) -> bytes:
        full_path = [bytes(self.destination)]
        full_path.extend([bytes(p) for p in self.path])
        frame = b"%s>%s:%s" % (
            bytes(self.source),
            b','.join(full_path),
            bytes(self.info)
        )
        return frame

    def set_source(self, source: typing.Union[str, bytes]) -> None:
        self.source = aprs.Callsign.parse(source)

    def set_destination(self, destination: typing.Union[str, bytes]) -> None:
        self.destination = aprs.Callsign.parse(destination)

    def set_path(self, path=[]) -> None:
        self.path = [aprs.Callsign.parse(pth) for pth in path]

    def update_path(self, update: bytes) -> None:
        self.path.append(aprs.Callsign.parse(update))

    def set_info(self, info: typing.Union[str, bytes]) -> None:
        self.info = aprs.InformationField.parse(info)

    def encode_ax25(self) -> bytes:
        """
        Encodes an APRS Frame as AX.25.
        """
        encoded_frame = []
        encoded_frame.append(aprs.AX25_FLAG)
        encoded_frame.append(self.destination.encode_ax25())
        encoded_frame.append(self.source.encode_ax25())
        for path_call in self.path:
            encoded_frame.append(path_call.encode_ax25())
        encoded_frame.append(aprs.ADDR_INFO_DELIM)
        encoded_frame.append(bytes(self.info))

        fcs = aprs.FCS()
        for bit in encoded_frame:
            fcs.update_bit(bit)

        encoded_frame.append(fcs.digest())
        encoded_frame.append(aprs.AX25_FLAG)

        return b''.join(encoded_frame)


class PositionFrame(Frame):

    __slots__ = ['lat', 'lng', 'source', 'destination', 'path', 'table',
                 'symbol', 'comment', 'ambiguity']

    _logger = logging.getLogger(__name__)  # pylint: disable=R0801
    if not _logger.handlers:  # pylint: disable=R0801
        _logger.setLevel(aprs.LOG_LEVEL)  # pylint: disable=R0801
        _console_handler = logging.StreamHandler()  # pylint: disable=R0801
        _console_handler.setLevel(aprs.LOG_LEVEL)  # pylint: disable=R0801
        _console_handler.setFormatter(aprs.LOG_FORMAT)  # pylint: disable=R0801
        _logger.addHandler(_console_handler)  # pylint: disable=R0801
        _logger.propagate = False  # pylint: disable=R0801

    def __init__(self, source: bytes, destination: bytes, path: typing.List,
                 table: bytes, symbol: bytes, comment: bytes, lat: float,
                 lng: float, ambiguity: float) -> None:
        self.table = table
        self.symbol = symbol
        self.comment = comment
        self.lat = lat
        self.lng = lng
        self.ambiguity = ambiguity
        info = self.create_info_field()
        super(PositionFrame, self).__init__(source, destination, path, info)

    def create_info_field(self) -> bytes:
        enc_lat = aprs.dec2dm_lat(self.lat)
        enc_lat_amb = bytes(aprs.ambiguate(enc_lat, self.ambiguity), 'UTF-8')
        enc_lng = aprs.dec2dm_lng(self.lng)
        enc_lng_amb = bytes(aprs.ambiguate(enc_lng, self.ambiguity), 'UTF-8')
        frame = [
            b'=',
            enc_lat_amb,
            self.table,
            enc_lng_amb,
            self.symbol,
            self.comment
        ]
        return b''.join(frame)
