# Copyright (C) 2005 Graham Ashton <ashtong@users.sourceforge.net>
# $Id$


"""send messages to a remote syslog server

This module provides classes for constructing UDP packets that can be
sent to a remote syslog server. It attempts to follow the protocol
defined in RFC 3164.

The classes and attributes are named according to the terminology in
the RFC. In the absence of full documentation for this module you
should be able to read the RFC to work out how the code is
structured. If you are interested in sending syslog messages to a
remote server you shouldn't need to look any further than the Logger
class.

For more information see http://hacksaw.sourceforge.net/remotesyslog/

"""


__version__ = "0.1.0-dev"


import os
import socket
import sys
import time


class PriPart(object):

    def __init__(self, facility, severity):
        assert facility is not None
        assert severity is not None
        self.facility = facility
        self.severity = severity

    def __str__(self):
        value = self.facility + self.severity
        return "<%s>" % value


class HeaderPart(object):

    def __init__(self, timestamp=None, hostname=None):
        self.timestamp = timestamp
        self.hostname = hostname

    def __str__(self):
        return "%s %s" % (self.timestamp, self.hostname)

    def _get_timestamp(self):
        return self._timestamp

    def calculate_current_timestamp(self):
        localtime = time.localtime()
        day = time.strftime("%d", localtime)
        if day[0] == "0":
            day = " " + day[1:]
        value = time.strftime("%b %%s %H:%M:%S", localtime)
        return value % day

    def _timestamp_is_valid(self, value):
        if value is None:
            return False
        for char in value:
            if ord(char) < 32 or ord(char) > 126:
                return False
        return True
    
    def _set_timestamp(self, value):
        if not self._timestamp_is_valid(value):
            value = self.calculate_current_timestamp()
        self._timestamp = value

    timestamp = property(_get_timestamp, _set_timestamp)

    def _get_hostname(self):
        return self._hostname

    def _set_hostname(self, value):
        if value is None:
            value = socket.gethostname()
        self._hostname = value

    hostname = property(_get_hostname, _set_hostname)


class MsgPart(object):

    MAX_TAG_LEN = 32

    def __init__(self, tag=None, content=""):
        self.tag = tag
        self.content = content

    def __str__(self):
        return self.tag + self.content

    def _get_tag(self):
        return self._tag

    def _set_tag(self, value):
        if value is None:
            value = sys.argv[0]
        self._tag = value[:self.MAX_TAG_LEN]

    tag = property(_get_tag, _set_tag)

    def _get_content(self):
        return self._content

    def _prepend_seperator(self, value):
        try:
            first_char = value[0]
        except IndexError:
            pass
        else:
            if first_char.isalnum():
                value = ": " + value
        return value

    def _set_content(self, value):
        value = self._prepend_seperator(value)
        self._content = value

    content = property(_get_content, _set_content)

    def include_pid(self):
        self.content = "[%d]" % os.getpid() + self.content


class SyslogMessage(object):

    MAX_LEN = 1024

    def __init__(self, pri, header, msg):
        self.pri = pri
        self.header = header
        self.msg = msg

    def __str__(self):
        message = "%s%s %s" % (self.pri, self.header, self.msg)
        return message[:self.MAX_LEN]


class Logger(object):

    PORT = 514

    def __init__(self):
        self._sockets = []

    def add_host(self, hostname):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect((hostname, self.PORT))
        self._sockets.append(sock)

    def log(self, facility, level, text):
        pri = PriPart(facility, level)
        header = HeaderPart()
        msg = MsgPart(content=text)
        data = str(SyslogMessage(pri, header, msg))
        for sock in self._sockets:
            sock.send(data)
