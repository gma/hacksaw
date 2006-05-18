# $Id$
# (C) Cmed Ltd, 2005


import ConfigParser
import re
import syslog

import netsyslog

import hacksaw.lib


class LogMessage(object):

    # This class was blatantly stolen from the Band Saw source.
    # See http://bandsaw.sourceforge.net/.

    regex = r"([^\s]+\s+[^\s]+\s+[^\s]+)\s+([^\s]+)\s+([^\s]+):\s(.*)"
    pattern = re.compile(regex)
    
    def __init__(self, line):
        self.match = LogMessage.pattern.match(line)

    def _get_message_part(self, index):
        try:
            return self.match.groups()[index]
        except AttributeError:
            return ""

    def _get_date(self):
        return self._get_message_part(0)

    date = property(_get_date)
    
    def _get_hostname(self):
        return self._get_message_part(1)

    hostname = property(_get_hostname)

    def _get_process(self):
        return self._get_message_part(2)

    process = property(_get_process)

    def _get_text(self):
        return self._get_message_part(3)

    text = property(_get_text)


class Processor(hacksaw.lib.Processor):

    def __init__(self, config):
        super(Processor, self).__init__(config)
        self._action_chain = None
        self.set_action_chain(
            [SingleLineFilter, MultiLineFilter, MessageDispatcher]
        )

    def set_action_chain(self, action_classes):
        self._action_chain = ActionChain(self, action_classes)

    def split_process_info(self, text):
        if "[" in text:
            name, pid = text.split("[")
            pid = int(pid[:-1])
        else:
            name = text
            pid = None
        return name, pid

    def create_packet(self, message):
        log = LogMessage(message)
        pri = netsyslog.PriPart(self.config.facility, self.config.priority)
        header = netsyslog.HeaderPart(log.date, log.hostname)
        process_name, pid = self.split_process_info(log.process)
        msg = netsyslog.MsgPart(process_name, log.text, pid)
        return netsyslog.Packet(pri, header, msg)

    def handle_message(self, message):
        self._action_chain.handle_message(message)


class ActionChain(object):

    def __init__(self, processor, action_classes):
        self._actions = self._construct_and_link_actions(processor,
                                                         action_classes)

    def _construct_and_link_actions(self, processor, action_classes):
        actions = []
        reversed_classes = reversed(action_classes)
        successor = None
        for class_ in reversed_classes:
            successor = class_(processor, successor)
            actions.insert(0, successor)
        return actions

    def get_action(self, index):
        return self._actions[index]

    def handle_message(self, message):
        self.get_action(0).handle_message(message)


class UnhandledMessageError(Exception):

    pass


class Action(object):

    def __init__(self, processor, successor):
        self._processor = processor
        self._successor = successor

    def handle_message(self, message):
        if self._successor is None:
            raise UnhandledMessageError('The message "%s" was not handled' %
                                        message)
        self._successor.handle_message(message)


class SingleLineFilter(Action):

    def __init__(self, processor, successor):
        super(SingleLineFilter, self).__init__(processor, successor)
        self._ignore_regexps = self._setup_regexps(
            self._processor.config.ignore_patterns
        )

    def _setup_regexps(self, ignore_patterns):
        """Extract and compile the single-line ignore patterns"""
        regexps = []
        for pattern_tuple in ignore_patterns:
            if len(pattern_tuple) == 1:
                regexps.append(re.compile(pattern_tuple[0]))
        return regexps

    def handle_message(self, message):
        for regexp in self._ignore_regexps:
            if regexp.match(message):
                return
        super(SingleLineFilter, self).handle_message(message)


class MultiLineFilter(Action):

    def __init__(self, processor, successor):
        super(MultiLineFilter, self).__init__(processor, successor)
        self._ignore_regexps = self._setup_regexps(
            self._processor.config.ignore_patterns)
        self._currently_ignored_loggers = {}
    
    def _setup_regexps(self, ignore_patterns):
        # Extract and compile the multi-line ignore patterns.
        regexps = []
        for pattern_tuple in ignore_patterns:
            if len(pattern_tuple) == 2:
                regexps.append((re.compile(pattern_tuple[0]),
                                re.compile(pattern_tuple[1])))
        return regexps

    def handle_message(self, message):
        log = LogMessage(message)
        logger_id = (log.hostname, log.process)
        if logger_id in self._currently_ignored_loggers:
            if self._currently_ignored_loggers[logger_id].match(message):
                del self._currently_ignored_loggers[logger_id]
            return
        else:
            for ignore_tuple in self._ignore_regexps:
                if ignore_tuple[0].match(message):
                    self._currently_ignored_loggers[logger_id] = \
                                                               ignore_tuple[1]
                    return
        super(MultiLineFilter, self).handle_message(message)


class MessageDispatcher(Action):

    def __init__(self, processor, successor):
        super(MessageDispatcher, self).__init__(processor, successor)

    def handle_message(self, message):
        packet = self._processor.create_packet(message)
        logger = netsyslog.Logger()
        for host in self._processor.config.hosts:
            logger.add_host(host)
        logger.send_packet(packet)


class Config(hacksaw.lib.Config):

    FACILITY = "facility"
    HOSTS = "hosts"
    PRIORITY = "priority"
    IGNORE_PATTERNS = "ignore"

    def _get_facility(self):
        name = self._get_item(Config.FACILITY)
        constant = "LOG_" + name.upper()
        return getattr(syslog, constant)

    facility = property(_get_facility)

    def _get_priority(self):
        name = self._get_item(Config.PRIORITY)
        if name == "warn":
            name = "warning"
        elif name == "error":
            name = "err"
        constant = "LOG_" + name.upper()
        return getattr(syslog, constant)

    priority = property(_get_priority)

    def _get_hosts(self):
        return [hostname.strip() for hostname in
                self._get_item(Config.HOSTS).split(",")]

    hosts = property(_get_hosts)

    def _get_ignore_patterns(self):
        try:
            ignore_expression = self._get_item(Config.IGNORE_PATTERNS)
            return eval(ignore_expression)
        except ConfigParser.NoOptionError:
            return []

    ignore_patterns = property(_get_ignore_patterns)
