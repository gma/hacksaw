# $Id$
# (C) Cmed Ltd, 2005


import socket
import syslog
import time
import unittest

import hacksaw.proc.remotesyslog


class PriPartTest(unittest.TestCase):

    def test_priority_format(self):
        """Check PRI is correctly formatted"""
        pri = hacksaw.proc.remotesyslog.PriPart(syslog.LOG_LOCAL4,
                                                syslog.LOG_NOTICE)
        self.assertEqual(str(pri), "<165>")


DEFAULT_TIMESTAMP = "Jun  7 09:00:00"
DEFAULT_HOSTNAME = "myhost"
DEFAULT_HEADER = "%s %s" % (DEFAULT_TIMESTAMP, DEFAULT_HOSTNAME)

    
class HeaderPartTest(unittest.TestCase):

    def mock_localtime(self):
        return (2005, 6, 7, 9, 0, 0, 1, 158, 1)  # see DEFAULT_TIMESTAMP

    def mock_gethostname(self):
        return "myhost"

    def setup_mock(self):
        self.real_localtime = time.localtime
        time.localtime = self.mock_localtime
        self.real_gethostname = socket.gethostname
        socket.gethostname = self.mock_gethostname

    def reset_mock(self):
        time.localtime = self.real_localtime
        socket.gethostname = self.real_gethostname

    def test_automatic_timestamp(self):
        """Check HEADER is automatically calculated if not set"""
        self.setup_mock()
        try:
            header = hacksaw.proc.remotesyslog.HeaderPart()
            self.assertEqual(str(header), DEFAULT_HEADER)
        finally:
            self.reset_mock()

    def test_incorrect_characters_disallowed(self):
        """Check only valid characters are used in the HEADER"""
        # Only allowed characters are ABNF VCHAR values and space.
        # Basically, if ord() returns between 32 and 126 inclusive
        # it's okay.
        self.setup_mock()
        try:
            bad_char = u"\x1f"  # printable, ord() returns 31
            header = hacksaw.proc.remotesyslog.HeaderPart()
            header.timestamp = header.timestamp[:-1] + bad_char
            self.assertEqual(str(header), DEFAULT_HEADER)
        finally:
            self.reset_mock()

    def test_set_timestamp_manually(self):
        """Check it is possible to set the timestamp in HEADER manually"""
        self.setup_mock()
        try:
            timestamp = "Jan 31 18:12:34"
            header = hacksaw.proc.remotesyslog.HeaderPart(timestamp=timestamp)
            self.assertEqual(str(header),
                             "%s %s" % (timestamp, DEFAULT_HOSTNAME))
        finally:
            self.reset_mock()

    def test_set_hostname_manually(self):
        """Check it is possible to set the hostname in HEADER manually"""
        self.setup_mock()
        try:
            hostname = "otherhost"
            header = hacksaw.proc.remotesyslog.HeaderPart(hostname=hostname)
            self.assertEqual(str(header),
                             "%s %s" % (DEFAULT_TIMESTAMP, hostname))
        finally:
            self.reset_mock()


# check format of time and hostname, set automatically if incorrect
#   - time is "Mmm dd hh:mm:ss" where dd has leading space, hh leading 0
#   - single space between time and hostname
#   - no space in hostname
#   - if using hostname, not IP, no dots allowed
# print message to stderr if badly formatted message encountered


class SyslogMessageTest(unittest.TestCase):

    def test_message_format(self):
        """Check syslog message is correctly constructed"""
        pri = hacksaw.proc.remotesyslog.PriPart(syslog.LOG_LOCAL4,
                                                syslog.LOG_NOTICE)
        header = hacksaw.proc.remotesyslog.HeaderPart(DEFAULT_TIMESTAMP,
                                                      DEFAULT_HOSTNAME)
        message = hacksaw.proc.remotesyslog.SyslogMessage(pri, header)
        self.assertEqual(str(message), "<165>%s" % DEFAULT_HEADER)
    
# trailing space after hostname
# maximum packet size is 1024 bytes


if __name__ == "__main__":
    unittest.main()
