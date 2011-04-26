.PHONY: test tags clean release official

all: test

test:
	@python runtests.py -rquickfix

tags:
	@ctags -R attest

clean:
	@git clean -ndx
	@echo
	@echo | xargs -p git clean -fdx

release:
	@python setup.py release sdist build_sphinx -Ea

official:
	@tox -e ALL
	@echo | xargs -p python setup.py upload_docs release sdist upload
