# $Id$
# (C) Cmed Ltd, 2004


import os
import unittest

import hacksaw


class ConfigTest(unittest.TestCase):

    def setUp(self):
        self.filename = 'test.conf'
        assert not os.path.exists(self.filename), \
               'Please move %s out of the way' % self.filename

    def tearDown(self):
        if os.path.exists(self.filename):
            os.remove(self.filename)

    def write_file(self, lines):
        file(self.filename, 'w').write(lines)        

    def test_spool_directory(self):
        """Check we can read the spool directory from the config file"""
        self.write_file('[general]\nspool: /var/spool/hacksaw')
        config = hacksaw.Config(self.filename)
        self.assertEqual(config.spool_directory, '/var/spool/hacksaw')


if __name__ == '__main__':
    unittest.main()
    
