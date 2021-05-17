
####################
# Setup tasks	   #
####################
install_dev:
	pip install -e ".[dev]"

install: 
	pip install .

setup_venv:
	python3.9 -m venv venv
	. venv/bin/activate

setup_dev:
	python3.9 -m venv venv
	. venv/bin/activate
	pip install -e ".[dev]"

setup: 
	python3.9 -m venv venv
	. venv/bin/activate
	pip install .


####################
# Testing   	   #
####################
test:
	pytest -x .

lint:
	flake8 main.py app tests
	mypy main.py app tests

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