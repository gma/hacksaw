# Copyright (C) 2005 Graham Ashton <ashtong@users.sourceforge.net>
#
# $Id$


from distutils.core import setup

import netsyslog


if __name__ == "__main__":
    setup(name="netsyslog",
          description="Send log messages to remote syslog servers",
          version=netsyslog.__version__,
          author="Graham Ashton",
          author_email="ashtong@users.sourceforge.net",
          url="http://hacksaw.sourceforge.net/netsyslog/",
          py_modules=["netsyslog"],
          )
