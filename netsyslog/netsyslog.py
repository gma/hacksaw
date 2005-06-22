# Copyright (C) 2005 Graham Ashton <ashtong@users.sourceforge.net>
#
# This module is free software, and you may redistribute it and/or modify
# it under the same terms as Python itself, so long as this copyright message
# and disclaimer are retained in their original form.
#
# IN NO EVENT SHALL THE AUTHOR BE LIABLE TO ANY PARTY FOR DIRECT, INDIRECT,
# SPECIAL, INCIDENTAL, OR CONSEQUENTIAL DAMAGES ARISING OUT OF THE USE OF
# THIS CODE, EVEN IF THE AUTHOR HAS BEEN ADVISED OF THE POSSIBILITY OF SUCH
# DAMAGE.
#
# THE AUTHOR SPECIFICALLY DISCLAIMS ANY WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE.  THE CODE PROVIDED HEREUNDER IS ON AN "AS IS" BASIS,
# AND THERE IS NO OBLIGATION WHATSOEVER TO PROVIDE MAINTENANCE,
# SUPPORT, UPDATES, ENHANCEMENTS, OR MODIFICATIONS.
#
# $Id$


"""send log messages to remote syslog server

netsyslog enables you to construct syslog messages and send them (via
UDP) to a remote syslog server directly from Python. Unlike other
syslog modules it allows you to set the metadata (e.g. time, host
name, program name, etc.) yourself, giving you full control over the
contents of the UDP packets that it creates.

The module also allows you to send log messages that contain the
current time, local hostname and calling program name (i.e. the
typical requirement of a logging package) to one or more syslog
servers.

The format of the UDP packets sent by netsyslog adheres closely to
that defined in RFC 3164.

For more information see http://hacksaw.sourceforge.net/netsyslog/.

"""


__version__ = "0.1.0-dev"


import os
import socket
import sys
import time


class PriPart(object):

    """The PRI part of the message (see RFC 3164)."""

    def __init__(self, facility, severity):
        """Initialise the object, specifying facility and severity.

        Specify the arguments using constants from the syslog module
        (e.g. syslog.LOG_USER, syslog.LOG_INFO).

        """
        assert facility is not None
        assert severity is not None
        self.facility = facility
        self.severity = severity

    def __str__(self):
        value = self.facility + self.severity
        return "<%s>" % value


class HeaderPart(object):

    """The HEADER part of the message

    The HEADER contains a timestamp (that MUST be formatted according
    to the specification and a hostname field).

    """

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

    timestamp = property(_get_timestamp, _set_timestamp, None,
                         """The local time when the message was written.

                         Must follow the format 'Mmm DD HH:MM:SS'.  If
                         the day of the month is less than 10, then it
                         MUST be represented as a space and then the
                         number.""")

    def _get_hostname(self):
        return self._hostname

    def _set_hostname(self, value):
        if value is None:
            value = socket.gethostname()
        self._hostname = value

    hostname = property(_get_hostname, _set_hostname, None,
                        """The hostname where the log message was created.

                        Should be the first part of the hostname, or
                        an IP address. Should NOT be set to a fully
                        qualified domain name.

                        """)


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


class Message(object):

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
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._hostnames = {}
        self._include_pid = False

    def include_pid(self):
        self._include_pid = True
        
    def add_host(self, hostname):
        self._hostnames[hostname] = 1

    def remove_host(self, hostname):
        del self._hostnames[hostname]

    def _send_data_to_hosts(self, data):
        for hostname in self._hostnames:
            self._sock.sendto(data, (hostname, self.PORT))

    def log(self, facility, level, text):
        pri = PriPart(facility, level)
        header = HeaderPart()
        msg = MsgPart(content=text)
        if self._include_pid:
            msg.include_pid()
        data = str(Message(pri, header, msg))
        self._send_data_to_hosts(data)

    def send_message(self, message):
        self._send_data_to_hosts(str(message))
