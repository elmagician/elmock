
####################
# Setup tasks	   #
####################
install_dev:
	pip install -e ".[dev]"

install: 
	pip install .

setup_venv:
	python3.10 -m venv venv

setup_dev: setup_venv
	( \
		. venv/bin/activate ; \
		pip install -e ".[dev]" ;\
	)

setup: setup_venv
	( \
		. venv/bin/activate ; \
		pip install . ;\
	)


####################
# Tasks       	   #
####################
build: setup.py
	python -m build

release: dist
	twine upload --skip-existing dist/*

####################
# Testing   	   #
####################
test:
	pytest -x .

lint:
	flake8 src tests
	mypy src

cover:
	coverage run --source=src -m pytest -xv .

coverage-report: cover
	coverage report -m --skip-empty  

coverage-gutter: cover
	coverage html --skip-empty -d coverage
	coverage xml --skip-empty

bandit:
	bandit -r app main.py

bandit-ci:
	bandit -r -ll -ii app main.py

test-all: lint cover
