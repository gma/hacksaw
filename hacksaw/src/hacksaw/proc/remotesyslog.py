# $Id$
# (C) Cmed Ltd, 2004


import socket
import time

import hacksaw.lib


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


class SyslogMessage(object):

    def __init__(self, pri, header):
        self.pri = pri
        self.header = header

    def __str__(self):
        return "%s%s" % (self.pri, self.header)
    

class Processor(hacksaw.lib.Processor):

    pass


class Config(hacksaw.lib.Config):

    pass
