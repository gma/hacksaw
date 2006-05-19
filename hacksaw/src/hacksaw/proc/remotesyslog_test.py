# $Id$
# (C) Cmed Ltd, 2005


import syslog
import unittest

import pmock

import hacksaw.lib_test
import hacksaw.proc.remotesyslog as remotesyslog


class StandardConfigTest(hacksaw.lib_test.ConfigTest):

    config_cls = remotesyslog.Config

    def setUp(self):
        hacksaw.lib_test.ConfigTest.setUp(self)
        self.append_to_file("[hacksaw.proc.remotesyslog]")


class BasicConfigTest(StandardConfigTest):

    def test_get_hosts(self):
        """Check we can get list of hosts to which we send syslog packets"""
        self.append_to_file("hosts: %s" % "localhost, otherhost")
        self.read_config()
        self.assertEqual(self.config.hosts, ["localhost", "otherhost"])

    def test_get_facility(self):
        """Check we can get the syslog message facility"""
        self.append_to_file("facility: local0")
        self.read_config()
        self.assertEqual(self.config.facility, syslog.LOG_LOCAL0)

    def test_get_priority(self):
        """Check we can get the syslog message priority"""
        self.append_to_file("priority: info")
        self.read_config()
        self.assertEqual(self.config.priority, syslog.LOG_INFO)

    def test_error_priority(self):
        """Check priority 'error' converted to 'err'"""
        self.append_to_file("priority: error")
        self.read_config()
        self.assertEqual(self.config.priority, syslog.LOG_ERR)

    def test_warning_priority(self):
        """Check priority 'warn' converted to 'warning'"""
        self.append_to_file("priority: warn")
        self.read_config()
        self.assertEqual(self.config.priority, syslog.LOG_WARNING)


class RuleNameTest(unittest.TestCase):

    def test_identify_good_rule(self):
        """Check we can analyse well named rules"""
        rule_type, index = remotesyslog.Config.identify_rule("match1")
        self.assertEqual(rule_type, "match")
        self.assertEqual(index, "1")

    def test_identify_bad_rule(self):
        """Check we don't break when analysing badly named rules"""
        self.assertRaises(remotesyslog.BadRuleName,
                          remotesyslog.Config.identify_rule, "wibble1")


class IgnoreConfigTest(StandardConfigTest):

    config_cls = remotesyslog.Config

    def setUp(self):
        super(IgnoreConfigTest, self).setUp()
        self.append_to_file("[hacksaw.proc.remotesyslog.ignore]")
        self.append_to_file(r"match1: \bcat")
        self.append_to_file("end1: dog")
        self.append_to_file("match2: start")
        self.append_to_file("end2: stop")
        self.read_config()

    def test_rule_parsing(self):
        """Check we can parse the ignore rules"""
        self.assert_(self.config.ignore_rules.has_key("1"))
        self.assert_(self.config.ignore_rules.has_key("2"))
        self.assertEqual(self.config.ignore_rules["1"]["match"], r"\bcat")

    def test_get_ignore_patterns(self):
        """Check we can get the regexps for ignoring messages"""
        self.assertEqual(self.config.ignore_patterns,
                         [(r"\bcat", "dog"), ("start", "stop")])


class LogMessageTest(unittest.TestCase):

    # TODO: move to hacksaw.lib (it's also used by other processors)

    def setUp(self):
        self.line = 'Jun 23 14:02:37 hoopoo ldap[29913]: Hello  world\n'

    def test_date(self):
        """Check we can extract the date from a log message"""
        message = remotesyslog.LogMessage(self.line)
        self.assertEqual(message.date, 'Jun 23 14:02:37')

    def test_date_single_figure_day(self):
        """Check we can extract the date when the day is a single digit"""
        line = 'Jun  1 14:02:37 hoopoo ldap[29913]: Hello  world\n'
        message = remotesyslog.LogMessage(line)
        self.assertEqual(message.date, 'Jun  1 14:02:37')

    def test_hostname(self):
        """Check we can extract the hostname from a log message"""
        message = remotesyslog.LogMessage(self.line)
        self.assertEqual(message.hostname, 'hoopoo')

    def test_process(self):
        """Check we can extract the process details from a log message"""
        message = remotesyslog.LogMessage(self.line)
        self.assertEqual(message.process, 'ldap[29913]')
        
    def test_message(self):
        """Check we can extract the text from a log message"""
        message = remotesyslog.LogMessage(self.line)
        self.assertEqual(message.text, 'Hello  world')
        

class ActionTestCase(unittest.TestCase):

    def test_handle_message(self):
        """Check base class action calls successor: action_1 --> successor"""
        message = "Hello World!"
        successor = pmock.Mock()
        successor.expects(pmock.once()).handle_message(pmock.eq(message))
        action = remotesyslog.Action(None, successor)
        action.handle_message(message)
        successor.verify()


class ActionChainTest(unittest.TestCase):

    def test_construct_actions(self):
        """Check that actions are passed the processor on construction"""
        
        class FakeAction(object):

            def __init__(self, processor, successor):
                self.processor = processor
                self.successor = successor

        processor = pmock.Mock()
        action_classes = [FakeAction]
        chain = remotesyslog.ActionChain(processor,
                                                      action_classes)
        action = chain.get_action(0)
        self.assertEquals(action.processor, processor)
        
    def test_actions_constructed_and_linked(self):
        """Check that the actions are linked correctly"""

        class FakeAction(remotesyslog.Action):

            def __init__(self, processor, successor):
                self._successor = successor
                self.message = None

            def handle_message(self, message):
                self.message = message
                super(FakeAction, self).handle_message(message)

        class FakeTerminatingAction(FakeAction):

            def handle_message(self, message):
                self.message = message

        action_classes = [FakeAction for idx in range(2)]
        action_classes.append(FakeTerminatingAction)
        action_chain = remotesyslog.ActionChain(pmock.Mock(), action_classes)
        message = "One Two"
        action_chain.handle_message(message)
        for idx in range(3):
            action = action_chain.get_action(idx)
            self.assertEquals(action.message, message)


class ProcessorTest(StandardConfigTest):

    def test_get_process_only_name(self):
        """Check we can get the process name when there is no pid"""
        self.read_config()
        processor = remotesyslog.Processor(self.config)
        name, pid = processor.split_process_info("myproc")
        self.assertEqual(name, "myproc")
        self.assertEqual(pid, None)
        
    def test_get_process_name_and_pid(self):
        """Check we can get the process name and pid when both set"""
        self.read_config()
        processor = remotesyslog.Processor(self.config)
        name, pid = processor.split_process_info("myproc[123]")
        self.assertEqual(name, "myproc")
        self.assertEqual(pid, 123)

    def test_messages_sent_to_hosts(self):
        """Check syslog messages are sent to listed hosts"""
        self.append_to_file("facility: daemon")
        self.append_to_file("priority: warn")
        self.append_to_file("hosts: localhost")
        self.read_config()
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
            origmod = remotesyslog.netsyslog
            remotesyslog.netsyslog = mockmod
            
            processor = remotesyslog.Processor(self.config)
            processor.create_packet(message)
            
            self.assertEqual(pri.initargs,
                             (syslog.LOG_DAEMON, syslog.LOG_WARNING))
            self.assertEqual(header.initargs, ("Nov 22 08:59:54", "myhost"))
            self.assertEqual(msg.initargs, ("myproc", "Hello world!", 123))
            self.assertEqual(packet.initargs, (pri, header, msg))
        finally:
            remotesyslog.netsyslog = origmod


class SingleLineFilterTest(StandardConfigTest):

    def test_ignore_single_message(self):
        """Check SingleLineFilter handles a message specified to be ignored"""
        self.append_to_file("[hacksaw.proc.remotesyslog.ignore]")
        self.append_to_file("match3: .*yourhost.*")
        self.read_config()
        message = "Nov 22 08:59:54 yourhost myproc[123]: Hello world!"
        processor = remotesyslog.Processor(self.config)
        processor.set_action_chain(
            [remotesyslog.SingleLineFilter])
        processor.handle_message(message)
        message = "Nov 22 08:59:54 myhost myproc[123]: Hello world!"
        self.assertRaises(remotesyslog.UnhandledMessageError,
                          processor.handle_message, message)    


class MultiLineFilterTest(StandardConfigTest):

    def setUp(self):
        super(MultiLineFilterTest, self).setUp()
        self._dispatched_messages = []

    def test_ingore_multiple_lines(self):
        """Check we can ignore groups of log messages"""

        class MockDispatcher(remotesyslog.Action):

            def handle_message(self_, message):
                self._dispatched_messages.append(message)
        
        self.append_to_file("[hacksaw.proc.remotesyslog.ignore]")
        self.append_to_file(r"match-stuff: .*start.*")
        self.append_to_file(r"end-stuff: .*last line\b")
        self.read_config()
        messages = [
            "Nov 22 08:59:54 yourhost myproc[123]: Hello!",
            "Nov 22 08:59:55 yourhost myproc[123]: start!",
            "Nov 22 08:59:56 yourhost myproc[123]: middle!",
            "Nov 22 08:59:56 myhost myproc[123]: middle!",
            "Nov 22 08:59:56 yourhost myproc[321]: not last line_",
            "Nov 22 08:59:57 yourhost myproc[123]: last line this time",
            "Nov 22 08:59:58 yourhost myproc[123]: Bye!",
        ]
        processor = remotesyslog.Processor(self.config)
        processor.set_action_chain([remotesyslog.SingleLineFilter,
                                    remotesyslog.MultiLineFilter,
                                    MockDispatcher]
        )
        for message in messages:
            processor.handle_message(message)
        expected_dispatched = [messages[0], messages[3], messages[4],
                               messages[6]]
        self.assertEquals(self._dispatched_messages, expected_dispatched)


if __name__ == "__main__":
    unittest.main()
