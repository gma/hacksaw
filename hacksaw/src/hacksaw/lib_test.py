# $Id$
# (C) Cmed Ltd, 2004


import os
import unittest

import hacksaw.lib


class ConfigTest(unittest.TestCase):

    config_cls = None

    def append_to_file(self, line):
        file(self.filename, 'a').write(line + '\n')
        self.config = self.config_cls(self.filename)

    def setUp(self):
        self.filename = 'test.conf'
        assert not os.path.exists(self.filename), \
               'Please move %s out of the way' % self.filename

    def tearDown(self):
        if os.path.exists(self.filename):
            os.remove(self.filename)


class GeneralConfigTest(ConfigTest):

    config_cls = hacksaw.lib.GeneralConfig

    def test_missing_file(self):
        """Check we raise a config error if there's no config file"""
        self.assertRaises(IOError, hacksaw.lib.GeneralConfig, self.filename)

    def test_get_spool_directory(self):
        """Check we can read the spool directory from the config file"""
        self.append_to_file('[general]')
        self.append_to_file('spool: /var/spool/hacksaw')
        self.assertEqual(self.config.spool_directory, '/var/spool/hacksaw')

    def test_get_processors(self):
        """Check we can read the processors from the config file"""
        self.append_to_file('[general]')
        self.append_to_file(
            'processors: hacksaw.proc.email, hacksaw.proc.syslog')
        self.assertEqual(self.config.processors, ['hacksaw.proc.email',
                                                  'hacksaw.proc.syslog'])
    
if __name__ == '__main__':
    unittest.main()
