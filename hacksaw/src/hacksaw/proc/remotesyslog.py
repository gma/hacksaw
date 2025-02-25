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
            [SingleLineFilter, MultiLineFilter, MessageDispatcher])

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
        for cls in reversed_classes:
            successor = cls(processor, successor)
            actions.insert(0, successor)
        return actions

    def get_action(self, index):
        return self._actions[index]

    def handle_message(self, message):
        self.get_action(0).handle_message(message)


class UnhandledMessageError(RuntimeError):

    pass


class Action(object):

    def __init__(self, processor, successor):
        self._processor = processor
        self._successor = successor

    def handle_message(self, message):
        if self._successor is None:
            raise UnhandledMessageError(
                'The message "%s" was not handled' % message)
        self._successor.handle_message(message)


class SingleLineFilter(Action):

    def __init__(self, processor, successor):
        super(SingleLineFilter, self).__init__(processor, successor)
        self._ignore_regexes = self._setup_regexes(
            self._processor.config.ignore_patterns)

    def _setup_regexes(self, ignore_patterns):
        """Extract and compile the single-line ignore patterns"""
        regexes = []
        for pattern_tuple in ignore_patterns:
            if len(pattern_tuple) == 1:
                regexes.append(re.compile(pattern_tuple[0]))
        return regexes

    def handle_message(self, message):
        for regex in self._ignore_regexes:
            if regex.search(message):
                return
        super(SingleLineFilter, self).handle_message(message)


class MultiLineFilter(Action):

    def __init__(self, processor, successor):
        super(MultiLineFilter, self).__init__(processor, successor)
        self._ignore_regexes = self._setup_regexes(
            self._processor.config.ignore_patterns)
        self._currently_ignored_loggers = {}
    
    def _setup_regexes(self, ignore_patterns):
        # Extract and compile the multi-line ignore patterns.
        regexes = []
        for pattern_tuple in ignore_patterns:
            if len(pattern_tuple) == 2:
                start, end = pattern_tuple
                regexes.append((re.compile(start), re.compile(end)))
        return regexes

    def handle_message(self, message):
        log = LogMessage(message)
        logger_id = (log.hostname, log.process)
        if logger_id in self._currently_ignored_loggers:
            if self._currently_ignored_loggers[logger_id].search(message):
                del self._currently_ignored_loggers[logger_id]
            return
        else:
            for start_regex, end_regex in self._ignore_regexes:
                if start_regex.search(message):
                    self._currently_ignored_loggers[logger_id] = end_regex
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


class BadRuleName(RuntimeError):

    pass


class Config(hacksaw.lib.Config):

    FACILITY = "facility"
    HOSTS = "hosts"
    PRIORITY = "priority"
    IGNORE_SECTION = "ignore"
    RULE_START = "match"
    RULE_END = "end"

    def __init__(self, filename):
        super(Config, self).__init__(filename)
        self.ignore_rules = self._parse_ignore_rules()

    @staticmethod
    def identify_rule(item):
        match = re.match("(match|end)(.+)", item)
        if match is None:
            raise BadRuleName, item
        rule_type, rule_id = match.groups()
        return rule_type, rule_id

    def _parse_ignore_rules(self):
        rules = {}
        try:
            for key, value in self.parser.items(self._get_ignore_section()):
                rule_type, rule_id = self.identify_rule(key)
                rules.setdefault(rule_id, {})[rule_type] = value
        except ConfigParser.NoSectionError:
            pass
        return rules

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

    def _get_ignore_section(self):
        return ".".join((self._get_section(), self.IGNORE_SECTION))

    def _get_ignore_patterns(self):
        patterns = []
        for rule_id in self.ignore_rules.keys():
            if self.RULE_START in self.ignore_rules[rule_id]:
                rule = [self.ignore_rules[rule_id][self.RULE_START]]
                if self.RULE_END in self.ignore_rules[rule_id]:
                    rule.append(self.ignore_rules[rule_id][self.RULE_END])
                patterns.append(tuple(rule))
        return patterns

    ignore_patterns = property(_get_ignore_patterns)

    def _get_item(self, item):
        try:
            if item.startswith(self.RULE_START) or \
                   item.startswith(self.RULE_END):
                section_name = self._get_ignore_section()
            else:
                section_name = self._get_section()
            return self.parser.get(section_name, item)
        except ConfigParser.NoSectionError, e:
            raise hacksaw.lib.ConfigError, e
