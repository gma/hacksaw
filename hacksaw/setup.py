# $Id$
# (C) Cmed Ltd, 2004


from distutils.core import setup


setup(name="hacksaw",
      version="0.2.0-dev",
      author="Cmed Technology",
      author_email="developers@cmedltd.com",
      url="http://hacksaw.sourceforge.net/",
      download_url="http://hacksaw.sourceforge.net/download.html",
      description="Log file monitoring and alerting",
      package_dir={"": "src"},
      packages=["hacksaw", "hacksaw.proc"],
      scripts=["src/processlogs.py", "src/run-processor.py",
               "scripts/pull-logs.sh", "scripts/push-logs.sh"],
      data_files=[("etc", ["etc/hacksaw.conf"])],
      )
