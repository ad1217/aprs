#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import typing

import aprs  # pylint: disable=R0801

AprsCallsign = typing.TypeVar('AprsCallsign', bound='aprs.Callsign')

class Callsign(object):

    """
    Callsign Class.

    Defines parts of an APRS AX.25 Callsign.
    """

    _logger = logging.getLogger(__name__)  # pylint: disable=R0801
    if not _logger.handlers:  # pylint: disable=R0801
        _logger.setLevel(aprs.LOG_LEVEL)  # pylint: disable=R0801
        _console_handler = logging.StreamHandler()  # pylint: disable=R0801
        _console_handler.setLevel(aprs.LOG_LEVEL)  # pylint: disable=R0801
        _console_handler.setFormatter(aprs.LOG_FORMAT)  # pylint: disable=R0801
        _logger.addHandler(_console_handler)  # pylint: disable=R0801
        _logger.propagate = False  # pylint: disable=R0801

    __slots__ = ['callsign', 'ssid', 'digi']

    def __init__(self, callsign: bytes=b'', ssid: bytes=b'0',
                 digi: bool=False) -> None:
        self.callsign: bytes = callsign
        self.ssid: bytes = ssid
        self.digi: bool = digi

    @classmethod
    def parse(cls, raw_callsign: bytes) -> AprsCallsign:
        """
        Parses an AX.25/APRS Callsign from plain-text or AX.25 input.
        """
        if isinstance(raw_callsign, cls):
            return raw_callsign
        try:
            return cls.from_ax25(raw_callsign)
        except:
            if isinstance(raw_callsign, str):
                return cls.from_text(bytes(raw_callsign, 'UTF-8'))
            else:
                return cls.from_text(raw_callsign)

    @classmethod
    def from_text(cls, raw_callsign: bytes) -> AprsCallsign:
        """
        Parses an AX.25/APRS Callsign & SSID from a plain-text AX.25/APRS Frame.
        """
        _callsign = raw_callsign
        ssid = b'0'
        digi = False

        if b'*' in _callsign:
            _callsign = _callsign.strip(b'*')
            digi = True

        if b'-' in _callsign:
            _callsign, ssid = _callsign.split(b'-')

        parsed_callsign: AprsCallsign = cls(_callsign, ssid, digi)

        return parsed_callsign

    @classmethod
    def from_ax25(cls, raw_callsign: bytes, kiss_call: bool=False) -> AprsCallsign:
        """
        Extracts a Callsign and SSID from a AX.25 Encoded APRS Frame.

        :param frame: AX.25 Encoded APRS Frame.
        :type frame: str
        """
        _callsign = bytes()
        digi = False

        for _chunk in raw_callsign[:6]:
            chunk = _chunk & 0xFF
            if chunk & 1:
                # aprx: /* Bad address-end flag ? */
                raise aprs.BadCallsignError('Bad address-end flag.')

            # Shift by one bit:
            chunk = chunk >> 1
            chr_chunk = chr(chunk)

            if chr_chunk.isalnum():
                _callsign += bytes([chunk])

        # 7th byte carries SSID or digi:
        seven_chunk = raw_callsign[6] & 0xFF
        ssid = (seven_chunk >> 1) & 0x0F  # Limit it to 4 bits.

        # FIXME gba@20170809: This works for KISS frames, but not otherwise.
        # Should consult: https://github.com/chrissnell/GoBalloon/blob/master/ax25/encoder.go
        if kiss_call:
            if seven_chunk >> 1 & 0x80:
                digi = True
        else:
            if seven_chunk & 0x80:
                digi = True

        return cls(_callsign, ssid, digi)


    def __repr__(self) -> str:
        _callsign = self.callsign.decode()
        _ssid = self.ssid.decode()
        call_repr = _callsign

        # Don't print callsigns with ssid 0.
        if _ssid:
            try:
                if int(_ssid) > 0:
                    call_repr = '-'.join([_callsign, _ssid])
            except ValueError:
                if _ssid != 0:
                    call_repr = '-'.join([_callsign, _ssid])

        # If callsign was digipeated, append '*'.
        if self.digi:
            return ''.join([call_repr, '*'])
        else:
            return call_repr

    def __bytes__(self) -> bytes:
        _callsign = self.callsign
        _ssid = self.ssid
        call_repr = _callsign

        # Don't print callsigns with ssid 0.
        if _ssid:
            try:
                if int(_ssid) > 0:
                    call_repr = b'-'.join([_callsign, _ssid])
            except ValueError:
                if _ssid != 0:
                    call_repr = b'-'.join([_callsign, _ssid])

        # If callsign was digipeated, append '*'.
        if self.digi:
            return b''.join([call_repr, b'*'])
        else:
            return call_repr

    def set_callsign(self, callsign: bytes) -> None:
        self.callsign = callsign

    def set_ssid(self, ssid: bytes=b'0') -> None:
        if isinstance(ssid, bytes):
            self.ssid = ssid
        else:
            self.ssid = bytes(str(ssid), 'UTF-8')

    def set_digi(self, digi: bool) -> None:
        self.digi = digi

    def encode_ax25(self) -> bytearray:
        """
        Encodes Callsign as AX.25.
        """
        _callsign = self.callsign
        encoded_callsign = []

        encoded_ssid = (int(self.ssid) << 1) | 0x60

        if self.digi:
            # _callsign = ''.join([_callsign, '*'])
            encoded_ssid |= 0x80

        # Pad the callsign to at least 6 characters.
        while len(_callsign) < 6:
            _callsign += b' '

        for pos in _callsign:
            encoded_callsign.append(bytes([pos << 1]))

        encoded_callsign.append(bytes([encoded_ssid]))

        return b''.join(encoded_callsign)
