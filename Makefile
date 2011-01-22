.PHONY: test tags

all: test

test:
	@python runtests.py -rquickfix

tags:
	ctags -R attest
