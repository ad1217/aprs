#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Python APRS Module Class Definitions."""

import itertools
import logging
import socket
import time

import pkg_resources
import requests

import aprs  # pylint: disable=R0801

__author__ = 'Greg Albrecht W2GMD <oss@undef.net>'  # NOQA pylint: disable=R0801
__copyright__ = 'Copyright 2017 Greg Albrecht and Contributors'  # NOQA pylint: disable=R0801
__license__ = 'Apache License, Version 2.0'  # NOQA pylint: disable=R0801


class APRS(object):

    """APRS Object."""

    _logger = logging.getLogger(__name__)  # pylint: disable=R0801
    if not _logger.handlers:  # pylint: disable=R0801
        _logger.setLevel(aprs.LOG_LEVEL)  # pylint: disable=R0801
        _console_handler = logging.StreamHandler()  # pylint: disable=R0801
        _console_handler.setLevel(aprs.LOG_LEVEL)  # pylint: disable=R0801
        _console_handler.setFormatter(aprs.LOG_FORMAT)  # pylint: disable=R0801
        _logger.addHandler(_console_handler)  # pylint: disable=R0801
        _logger.propagate = False  # pylint: disable=R0801

    def __init__(self, user: bytes, password: bytes=b'-1') -> None:
        if isinstance(user, str):
            user = bytes(user, 'UTF-8')
        if isinstance(password, str):
            password = bytes(password, 'UTF-8')
        self.user = user

        try:
            version = bytes(pkg_resources.get_distribution(  # NOQA pylint: disable=E1101
                'aprs').version, 'UTF-8')
        except:  # pylint: disable=W0702
            version = b'GIT'
        version_str = b'Python APRS Module v' + version

        self._auth = b' '.join(
            [b'user', user, b'pass', password, b'vers', version_str])

        self._full_auth = None
        self.interface = None
        self.use_i_construct = False

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

    def receive(self, callback=None, frame_handler=aprs.Frame.parse):
        """
        Abstract method for receiving messages from APRS-IS.
        """
        pass


class TCP(APRS):

    """APRS-IS TCP Class."""

    def __init__(self, user: bytes, password: bytes, servers: bytes=b'',
                 aprs_filter: bytes=b'') -> None:
        super(TCP, self).__init__(user, password)
        servers = servers or aprs.APRSIS_SERVERS  # Unicode
        aprs_filter = aprs_filter or b'/'.join([b'p', user])  # Unicode
        if isinstance(aprs_filter, str):
            aprs_filter = bytes(aprs_filter, 'UTF-8')

        # Unicode
        self._full_auth = b' '.join([self._auth, b'filter', aprs_filter])

        self.servers = itertools.cycle(servers)
        self.use_i_construct = True
        self._connected = False

    def start(self):
        """
        Connects & logs in to APRS-IS.
        """
        while not self._connected:
            servers = next(self.servers)
            if b':' in servers:
                server, port = servers.split(b':')
                port = int(port)
            else:
                server = servers
                port = aprs.APRSIS_FILTER_PORT

            try:
                addr_info = socket.getaddrinfo(server, port)

                self.interface = socket.socket(*addr_info[0][0:3])

                # Connect
                self._logger.info(
                    "Connect To %s:%i", addr_info[0][4][0], port)

                self.interface.connect(addr_info[0][4])

                server_hello = self.interface.recv(1024)

                self._logger.info(
                    'Connect Result "%s"', server_hello.rstrip())

                # Auth
                self._logger.info(
                    "Auth To %s:%i", addr_info[0][4][0], port)

                _full_auth = self._full_auth + b'\n\r'

                self.interface.sendall(_full_auth)

                server_return = self.interface.recv(1024)
                self._logger.info(
                    'Auth Result "%s"', server_return.rstrip())

                self._connected = True
            except socket.error as ex:
                self._logger.exception(ex)
                self._logger.warn(
                    "Error when connecting to %s:%d: '%s'",
                    server, port, str(ex))
                time.sleep(1)

    def send(self, frame):
        """
        Sends frame to APRS-IS.

        :param frame: Frame to send to APRS-IS.
        :type frame: str
        """
        self._logger.info('Sending frame="%s"', frame)

        # Unicode Sandwich: Send bytes.
        _frame = bytes(frame + b'\n\r')

        return self.interface.send(_frame)

    def receive(self, callback=None, frame_handler=aprs.Frame.parse):
        """
        Receives from APRS-IS.

        :param callback: Optional callback to deliver frame to.
        :type callback: func

        :returns: Nothing, but calls a callback with an Frame object.
        :rtype: None
        """
        self._logger.info(
            'Receive started with callback="%s" and frame_handler="%s"',
            callback, frame_handler)

        # Unicode Sandwich: Receive Bytes.
        recvd_data = bytes()

        try:
            while 1:
                recv_data = self.interface.recv(aprs.RECV_BUFFER)

                if not recv_data:
                    break

                recvd_data += recv_data

                self._logger.debug('recv_data="%s"', recv_data.strip())

                if recvd_data.endswith(b'\r\n'):
                    lines = recvd_data.strip().split(b'\r\n')
                    recvd_data = bytes()
                else:
                    lines = recvd_data.split(b'\r\n')
                    recvd_data = lines.pop(-1)

                for line in lines:
                    if line.startswith(b'#'):
                        if b'logresp' in line:
                            self._logger.debug('logresp="%s"', line)
                        # We log all received data anyway, so no need to log
                        # it here again:
                        # else:
                        #    self._logger.debug('unknown response="%s"', line)
                    else:
                        self._logger.debug('line="%s"', line)
                        if callback:
                            if frame_handler:
                                callback(frame_handler(line))
                            else:
                                callback(line)
                        else:
                            self._logger.info('No callback set?')

        except socket.error as sock_err:
            self._logger.exception(sock_err)
            raise


class UDP(APRS):

    """APRS-IS UDP Class."""

    def __init__(self, user, password='-1', server=None, port=None):
        super(UDP, self).__init__(user, password)
        server = server or aprs.APRSIS_SERVERS[0]
        port = port or aprs.APRSIS_RX_PORT
        self._addr = (server, int(port))
        self.use_i_construct = True

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
        self._logger.info('Sending frame="%s"', frame)
        content = b"\n".join([self._auth, str(frame)])
        return self.interface.sendto(content, self._addr)


class HTTP(APRS):

    """APRS-IS HTTP Class."""

    def __init__(self, user: bytes, password: bytes=b'-1', url: bytes=b'',
                 headers=None) -> None:
        super(HTTP, self).__init__(user, password)
        self.url = url or aprs.APRSIS_URL
        self.headers = headers or aprs.APRSIS_HTTP_HEADERS
        self.use_i_construct = True

    def start(self):
        """
        Connects & logs in to APRS-IS.
        """
        self.interface = requests.post

    def send(self, frame: bytes) -> bool:
        """
        Sends frame to APRS-IS.

        :param frame: Frame to send to APRS-IS.
        :type frame: str
        """
        if isinstance(frame, str):
            frame = aprs.Frame.parse(frame)
        if isinstance(frame, aprs.Frame):
            frame = bytes(frame)
        self._logger.info('Sending frame="%s"', frame)
        content = b"\n".join([self._auth, frame])
        result = self.interface(self.url, data=content, headers=self.headers)
        return result.status_code == 204
