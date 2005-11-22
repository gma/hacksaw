# $Id$
# (C) Cmed Ltd, 2005


import syslog
import unittest

from pmock import *

import hacksaw.lib_test
import hacksaw.proc.remotesyslog


class RemoteSyslogTest(hacksaw.lib_test.ConfigTest):

    config_cls = hacksaw.proc.remotesyslog.Config

    def setUp(self):
        hacksaw.lib_test.ConfigTest.setUp(self)
        self.append_to_file("[hacksaw.proc.remotesyslog]")


class ConfigTest(RemoteSyslogTest):

    def test_get_hosts(self):
        """Check we can get list of hosts to which we send syslog packets"""
        self.append_to_file("hosts: %s" % "localhost, otherhost")
        self.assertEqual(self.config.hosts, ["localhost", "otherhost"])

    def test_get_facility(self):
        """Check we can get the syslog message facility"""
        self.append_to_file("facility: local0")
        self.assertEqual(self.config.facility, syslog.LOG_LOCAL0)

    def test_get_priority(self):
        """Check we can get the syslog message priority"""
        self.append_to_file("priority: info")
        self.assertEqual(self.config.priority, syslog.LOG_INFO)

    def test_error_priority(self):
        """Check priority 'error' converted to 'err'"""
        self.append_to_file("priority: error")
        self.assertEqual(self.config.priority, syslog.LOG_ERR)

    def test_warning_priority(self):
        """Check priority 'warn' converted to 'warning'"""
        self.append_to_file("priority: warn")
        self.assertEqual(self.config.priority, syslog.LOG_WARNING)


class LogMessageTest(unittest.TestCase):

    def setUp(self):
        self.line = 'Jun 23 14:02:37 hoopoo ldap[29913]: Hello  world\n'

    def test_date(self):
        """Check we can extract the date from a log message"""
        message = hacksaw.proc.remotesyslog.LogMessage(self.line)
        self.assertEqual(message.date, 'Jun 23 14:02:37')

    def test_date_single_figure_day(self):
        """Check we can extract the date when the day is a single digit"""
        line = 'Jun  1 14:02:37 hoopoo ldap[29913]: Hello  world\n'
        message = hacksaw.proc.remotesyslog.LogMessage(line)
        self.assertEqual(message.date, 'Jun  1 14:02:37')

    def test_hostname(self):
        """Check we can extract the hostname from a log message"""
        message = hacksaw.proc.remotesyslog.LogMessage(self.line)
        self.assertEqual(message.hostname, 'hoopoo')

    def test_process(self):
        """Check we can extract the process details from a log message"""
        message = hacksaw.proc.remotesyslog.LogMessage(self.line)
        self.assertEqual(message.process, 'ldap[29913]')
        
    def test_message(self):
        """Check we can extract the text from a log message"""
        message = hacksaw.proc.remotesyslog.LogMessage(self.line)
        self.assertEqual(message.text, 'Hello  world')
        

class ProcessorTest(RemoteSyslogTest):

    def test_get_process_only_name(self):
        """Check we can get the process name when there is no pid"""
        processor = hacksaw.proc.remotesyslog.Processor(self.config)
        name, pid = processor.split_process_info("myproc")
        self.assertEqual(name, "myproc")
        self.assertEqual(pid, None)
        
    def test_get_process_name_and_pid(self):
        """Check we can get the process name and pid when both set"""
        processor = hacksaw.proc.remotesyslog.Processor(self.config)
        name, pid = processor.split_process_info("myproc[123]")
        self.assertEqual(name, "myproc")
        self.assertEqual(pid, 123)

    def test_messages_sent_to_hosts(self):
        """Check syslog messages are sent to listed hosts"""
        self.append_to_file("facility: daemon")
        self.append_to_file("priority: warn")
        self.append_to_file("hosts: localhost")
        message = "Nov 22 08:59:54 myhost myproc[123]: Hello world!"

        class MockModule(object):

            pass

        class MockClass(object):

            def __call__(self, *args):
                self.initargs = args
                return self

        mockmod = MockModule()
        pri = MockClass()
        header = MockClass()
        msg = MockClass()
        packet = MockClass()
        
        mockmod.PriPart = pri
        mockmod.HeaderPart = header
        mockmod.MsgPart = msg
        mockmod.Packet = packet

        try:
            origmod = hacksaw.proc.remotesyslog.netsyslog
            hacksaw.proc.remotesyslog.netsyslog = mockmod
            
            processor = hacksaw.proc.remotesyslog.Processor(self.config)
            processor.create_packet(message)
            
            self.assertEqual(pri.initargs, (syslog.LOG_DAEMON,
                                            syslog.LOG_WARNING))
            self.assertEqual(header.initargs, ("Nov 22 08:59:54", "myhost"))
            self.assertEqual(msg.initargs, ("myproc", "Hello world!", 123))
            self.assertEqual(packet.initargs, (pri, header, msg))
        finally:
            hacksaw.proc.remotesyslog.netsyslog = origmod


if __name__ == "__main__":
    unittest.main()
