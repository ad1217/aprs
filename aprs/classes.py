#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""APRS Class Definitions"""

import logging
import logging.handlers
import socket

import kiss
import requests

import aprs

__author__ = 'Greg Albrecht W2GMD <oss@undef.net>'
__license__ = 'Apache License, Version 2.0'
__copyright__ = 'Copyright 2016 Orion Labs, Inc.'


class APRS(object):

    """APRS Object."""

    _logger = logging.getLogger(__name__)
    if not _logger.handlers:
        _logger.setLevel(aprs.LOG_LEVEL)
        _console_handler = logging.StreamHandler()
        _console_handler.setLevel(aprs.LOG_LEVEL)
        _console_handler.setFormatter(aprs.LOG_FORMAT)
        _logger.addHandler(_console_handler)
        _logger.propagate = False

    def __init__(self, user, password='-1'):
        self.user = user
        self._auth = ' '.join(
            ['user', user, 'pass', password, 'vers', aprs.APRSIS_SW_VERSION])
        self._full_auth = None
        self.interface = None

    def start(self):
        """
        Abstract method for starting connection to APRS-IS.
        """
        pass

    def send(self, message):
        """
        Abstract method for sending messages to APRS-IS.
        """
        pass

    def receive(self, callback=None):
        """
        Abstract method for receiving messages from APRS-IS.
        """
        pass


class APRSFrame(object):

    """
    APRSFrame Class.

    Defines the components of an APRS Frame and can decode a frame
    from either ASCII or KISS.
    """

    __slots__ = ['frame', 'source', 'destination', 'path', 'text']

    _logger = logging.getLogger(__name__)
    if not _logger.handlers:
        _logger.setLevel(aprs.LOG_LEVEL)
        _console_handler = logging.StreamHandler()
        _console_handler.setLevel(aprs.LOG_LEVEL)
        _console_handler.setFormatter(aprs.LOG_FORMAT)
        _logger.addHandler(_console_handler)
        _logger.propagate = False

    def __init__(self, frame=None):
        self.source = ''
        self.destination = 'APRS'
        self.path = []
        self.text = ''
        if frame is not None:
            self.frame = kiss.strip_df_start(frame)
            self.parse()

    def __repr__(self):
        full_path = [str(self.destination)]
        full_path.extend([str(p) for p in self.path])
        frame = "%s>%s:%s" % (
            self.source,
            ','.join(full_path),
            self.text
        )
        return frame.encode('UTF-8')

    def to_h(self):
        """
        Returns an APRSFrame as a Hex String.
        """
        return str(self).encode('hex')

    def parse(self, frame=None):
        """
        Parses an APRSFrame from either ASCII or KISS Encoded frame.
        """
        # Allows to be called as class method:
        if frame is not None:
            self.frame = frame

        try:
            self.parse_kiss()
        except IndexError as exc:
            self._logger.info('Not a KISS Frame? %s', self.frame.encode('hex'))

        if not self.source or not self.destination:
            try:
                self.parse_text()
            except UnicodeDecodeError as exc:
                self._logger.info(
                    'Cannot decode frame=%s', self.frame.encode('hex'))
                self._logger.exception(exc)

    def parse_text(self):
        """
        Parses and Extracts the components of an ASCII-Encoded APRSFrame.
        """
        frame_so_far = ''

        for char in self.frame.decode('UTF-8'):
            if '>' in char and not self.source:
                self.source = Callsign(frame_so_far)
                frame_so_far = ''
            elif ':' in char and not self.path:
                if ',' in frame_so_far:
                    self.path = []
                    for path in frame_so_far.split(',')[1:]:
                        self.path.append(Callsign(path))

                    self.destination = Callsign(frame_so_far.split(',')[0])
                else:
                    self.destination = Callsign(frame_so_far)
                frame_so_far = ''
            else:
                frame_so_far = ''.join([frame_so_far, char])

        self.text = frame_so_far.encode('UTF-8')

    def parse_kiss(self):
        """
        Parses and Extracts the components of an KISS-Encoded APRSFrame.
        """
        frame_len = len(self.frame)

        if frame_len < 16:
            self._logger.debug('Frame len(%s) < 16, Exiting.', frame_len)
            return

        for raw_slice in range(0, frame_len):

            # Is address field length correct?
            # Find the first ODD Byte followed by the next boundary:
            if (ord(self.frame[raw_slice]) & 0x01
                    and ((raw_slice + 1) % 7) == 0):

                i = (raw_slice + 1) / 7

                # Less than 2 callsigns?
                if 1 < i < 11:
                    # For frames <= 70 bytes
                    if frame_len >= raw_slice + 2:
                        if (ord(self.frame[raw_slice + 1]) & 0x03 == 0x03 and
                                ord(self.frame[raw_slice + 2]) in
                                [0xf0, 0xcf]):
                            self._extract_kiss_text(raw_slice)
                            self._extract_kiss_destination()
                            self._extract_kiss_source()
                            self._extract_kiss_path(i)

    def encode_kiss(self):
        """
        Encodes an APRSFrame as KISS.
        """
        enc_frame = ''.join([
            self.destination.encode_kiss(),
            self.source.encode_kiss(),
            ''.join([path_call.encode_kiss() for path_call in self.path])
        ])
        return ''.join([
            enc_frame[:-1],
            chr(ord(enc_frame[-1]) | 0x01),
            kiss.SLOT_TIME,
            chr(0xF0),
            self.text.encode('UTF-8')
        ])

    def _extract_kiss_text(self, raw_slice):
        """
        Extracts a Text portion of a KISS-Encoded APRSFrame.
        """
        self.text = self.frame[raw_slice + 3:]

    def _extract_kiss_source(self):
        """
        Extracts a Source Callsign of a KISS-Encoded APRSFrame.
        """
        self.source = Callsign(self.frame[7:])

    def _extract_kiss_destination(self):
        """
        Extracts a Destination Callsign of a KISS-Encoded APRSFrame.
        """
        self.destination = Callsign(self.frame)

    def _extract_kiss_path(self, start):
        """
        Extracts path from raw APRS KISS frame.
        """
        for i in range(2, start):
            path_call = Callsign(self.frame[i * 7:])

            if path_call:
                if ord(self.frame[i * 7 + 6]) & 0x80:
                    path_call.digi = True

                self.path.append(path_call)


class Callsign(object):

    """
    Callsign Class.
    Defines parts of a Callsign decoded from either ASCII or KISS.
    """

    _logger = logging.getLogger(__name__)
    if not _logger.handlers:
        _logger.setLevel(aprs.LOG_LEVEL)
        _console_handler = logging.StreamHandler()
        _console_handler.setLevel(aprs.LOG_LEVEL)
        _console_handler.setFormatter(aprs.LOG_FORMAT)
        _logger.addHandler(_console_handler)
        _logger.propagate = False

    __slots__ = ['callsign', 'ssid', 'digi']

    def __init__(self, callsign):
        self.callsign = ''
        self.ssid = str(0)
        self.digi = False
        self.parse(callsign)

    def __repr__(self):
        if int(self.ssid) > 0:
            call_repr = '-'.join([self.callsign, str(self.ssid)])
        else:
            call_repr = self.callsign

        if self.digi:
            return ''.join([call_repr, '*'])
        else:
            return call_repr

    def to_h(self):
        """
        Returns a Callsign as a Hex String.
        """
        return str(self).encode('hex')

    def parse(self, callsign):
        """
        Parse and extract the components of a Callsign from ASCII or KISS.
        """
        try:
            self._extract_callsign_from_kiss_frame(callsign)
        except IndexError:
            self._logger.debug(
                'Not a KISS Callsign? "%s"', callsign.encode('hex'))

        if not aprs.valid_callsign(self.callsign):
            self.parse_text(callsign)

        if not aprs.valid_callsign(self.callsign):
            raise aprs.BadCallsignError(
                'Could not extract callsign from %s',
                self.callsign.encode('hex'))

    def parse_text(self, callsign):
        """
        Parses and extracts a Callsign and SSID from an ASCII-Encoded APRS
        Callsign or Callsign-SSID.

        :param callsign: ASCII-Encoded APRS Callsign
        :type callsign: str
        """
        self._logger.debug('callsign=%s', callsign.encode('hex'))
        _callsign = callsign
        ssid = str(0)

        if '-' in callsign:
            _callsign, ssid = callsign.split('-')

        if _callsign[-1] == '*':
            _callsign = _callsign[:-1]
            self.digi = True

        self.callsign = _callsign.lstrip().rstrip()
        self.ssid = ssid.lstrip().rstrip()

    def encode_kiss(self):
        """
        Encodes Callsign (or Callsign-SSID) as KISS.
        """
        encoded_ssid = (int(self.ssid) << 1) | 0x60
        _callsign = self.callsign

        if self.digi:
            # _callsign = ''.join([_callsign, '*'])
            encoded_ssid |= 0x80

        # Pad the callsign to at least 6 characters.
        while len(_callsign) < 6:
            _callsign = ''.join([_callsign, ' '])

        encoded_callsign = ''.join([chr(ord(p) << 1) for p in _callsign])

        return ''.join([encoded_callsign, chr(encoded_ssid)])

    def _extract_callsign_from_kiss_frame(self, frame):
        """
        Extracts a Callsign and SSID from a KISS-Encoded APRS Frame.

        :param frame: KISS-Encoded APRS Frame as str of octs.
        :type frame: str
        """
        self._logger.debug('frame=%s', frame.encode('hex'))
        callsign = ''.join([chr(ord(x) >> 1) for x in frame[:6]])
        self.callsign = callsign.lstrip().rstrip()
        self.ssid = str((ord(frame[6]) >> 1) & 0x0F)


class APRSSerialKISS(kiss.SerialKISS):

    """APRS interface for KISS serial devices."""

    def __init__(self, port, speed, strip_df_start=False):
        super(APRSSerialKISS, self).__init__(port, speed, strip_df_start)
        self.send = self.write
        self.receive = self.read

    def write(self, frame):
        """Writes APRS-encoded frame to KISS device.

        :param frame: APRS frame to write to KISS device.
        :type frame: str
        """
        super(APRSSerialKISS, self).write(frame.encode_kiss())


class APRSTCPKISS(kiss.TCPKISS):

    """APRS interface for KISS serial devices."""

    def __init__(self, host, port, strip_df_start=False):
        super(APRSTCPKISS, self).__init__(host, port, strip_df_start)
        self.send = self.write
        self.receive = self.read

    def write(self, frame):
        """
        Writes APRS-encoded frame to KISS device.

        :param frame: APRS frame to write to KISS device.
        :type frame: str
        """
        super(APRSTCPKISS, self).write(frame.encode_kiss())


class TCPAPRS(APRS):

    """APRS-IS TCP Class."""

    def __init__(self, user, password='-1', server=None, port=None,
                 aprs_filter=None):
        super(TCPAPRS, self).__init__(user, password)
        server = server or aprs.APRSIS_SERVER
        port = port or aprs.APRSIS_FILTER_PORT
        self.address = (server, int(port))
        aprs_filter = aprs_filter or '/'.join(['p', user])
        self._full_auth = ' '.join([self._auth, 'filter', aprs_filter])

    def start(self):
        """
        Connects & logs in to APRS-IS.
        """
        self.interface = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._logger.info('Connecting to to "%s"', self.address)
        self.interface.connect(self.address)

        self._logger.debug('Sending full_auth=%s', self._full_auth)
        self.interface.sendall(self._full_auth + '\n\r')

    def send(self, frame):
        """
        Sends frame to APRS-IS.

        :param frame: Frame to send to APRS-IS.
        :type frame: str
        """
        self._logger.debug('frame="%s"', frame)
        return self.interface.sendall("%s\n\r" % frame)  # Ensure cast->str.

    def receive(self, callback=None):
        """
        Receives from APRS-IS.

        :param callback: Optional callback to deliver frame to.
        :type callback: func

        :returns: Nothing, but calls a callback with an APRSFrame object.
        :rtype: None
        """
        recvd_data = ''

        try:
            while 1:
                recv_data = self.interface.recv(aprs.RECV_BUFFER)

                if not recv_data:
                    break

                recvd_data += recv_data

                self._logger.debug('recv_data=%s', recv_data.strip())

                if recvd_data.endswith('\r\n'):
                    lines = recvd_data.strip().split('\r\n')
                    recvd_data = ''
                else:
                    lines = recvd_data.split('\r\n')
                    recvd_data = str(lines.pop(-1))

                for line in lines:
                    if line.startswith('#'):
                        if 'logresp' in line:
                            self._logger.debug('logresp=%s', line)
                    else:
                        self._logger.debug('line=%s', line)
                        if callback:
                            callback(APRSFrame(line))

        except socket.error as sock_err:
            self._logger.error(sock_err)
            raise


class UDPAPRS(APRS):

    """APRS-IS UDP Class."""

    def __init__(self, user, password='-1', server=None, port=None):
        super(UDPAPRS, self).__init__(user, password)
        server = server or aprs.APRSIS_SERVER
        port = port or aprs.APRSIS_RX_PORT
        self._addr = (server, int(port))

    def start(self):
        """
        Connects & logs in to APRS-IS.
        """
        self.interface = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def send(self, frame):
        """
        Sends frame to APRS-IS.

        :param frame: Frame to send to APRS-IS.
        :type frame: str
        """
        self._logger.debug('frame="%s"', frame)
        content = "\n".join([self._auth, str(frame)])
        return self.interface.sendto(content, self._addr)


class HTTPAPRS(APRS):

    """APRS-IS HTTP Class."""

    def __init__(self, user, password='-1', url=None, headers=None):
        super(HTTPAPRS, self).__init__(user, password)
        self.url = url or aprs.APRSIS_URL
        self.headers = headers or aprs.APRSIS_HTTP_HEADERS

    def start(self):
        """
        Connects & logs in to APRS-IS.
        """
        self.interface = requests.post

    def send(self, frame):
        """
        Sends frame to APRS-IS.

        :param frame: Frame to send to APRS-IS.
        :type frame: str
        """
        content = "\n".join([self._auth, str(frame)])
        result = self.interface(self.url, data=content, headers=self.headers)
        return result.status_code == 204


# WIP 2016-12-14
class APRSLocationFrame(APRSFrame):
    # WIP 2016-12-14

    """
    APRSLocationFrame Class.

    Defines the components of an APRS Location Frame and can decode a frame
    from either ASCII or KISS.
    """

    __slots__ = ['frame', 'source', 'destination', 'path', 'text']

    def __init__(self, frame=None):
        super(APRSLocationFrame, self).__init__(frame)
        self.symbol_table = ''
        self.symbol_code = ''
        self.latitude = ''
        self.longitude = ''

    def __repr__(self):
        full_path = [str(self.destination)]
        full_path.extend([str(p) for p in self.path])
        frame = "%s>%s:%s" % (
            self.source,
            ','.join(full_path),
            self.text
        )
        return frame.encode('UTF-8')
