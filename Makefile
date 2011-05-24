.PHONY: test flakes tags clean release official

all: test

test:
	@attest -rquickfix

flakes:
	@pyflakes attest

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
