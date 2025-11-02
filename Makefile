.PHONY: test flakes lint format tags clean install sync build release official

all: test

install:
	@uv sync

sync:
	@uv sync --all-extras

test:
	@uv run attest -rquickfix

flakes:
	@uv run ruff check attest

lint:
	@uv run ruff check attest

format:
	@uv run ruff format attest

fix:
	@uv run ruff check --fix attest

tags:
	@ctags -R attest

clean:
	@git clean -ndx
	@echo
	@echo | xargs -p git clean -fdx

build:
	@uv build

release: build
	@echo "Built distribution packages"

official:
	@uv run tox -e ALL
	@echo "Run 'uv publish' to upload to PyPI"
