# $Id$


REMOTE_HOST=hacksaw.sourceforge.net
REMOTE_DIR=/home/groups/h/ha/hacksaw/htdocs/netsyslog
REMOTE_USER=ashtong

NAME=netsyslog
DOCDIR=doc

upload: .upload-html .upload-doc
#upload: $(DOCDIR)/index.html


.upload-html: *.html
	scp $? $(REMOTE_USER)@$(REMOTE_HOST):$(REMOTE_DIR)
	@touch .upload-root

$(DOCDIR)/index.html: ../../netsyslog/netsyslog.py
	epydoc -n $(NAME) --target $(DOCDIR) --no-private --no-frames \
		--url http://hacksaw.sourceforge.net/netsyslog/ \
		$?

.upload-doc: $(DOCDIR)/index.html
	scp -r $(DOCDIR) $(REMOTE_USER)@$(REMOTE_HOST):$(REMOTE_DIR)
