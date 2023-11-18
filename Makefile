SHELL=/bin/bash
VENV_DIR=ve
PYTHON_VERSION=3.9
PIP_COMPILE=$(VENV_DIR)/bin/pip-compile -vU --no-emit-index-url --rebuild

.PHONY=update-requirements test-db test check black test
.DEFAULT_GOAL=test

$(VENV_DIR):
	virtualenv $(VENV_DIR) --python=python$(PYTHON_VERSION)
	$(VENV_DIR)/bin/pip install -r requirements.txt -r dev-requirements.txt  # Can't use pip-sync here because it has not been installed

update-requirements: export CUSTOM_COMPILE_COMMAND="make update-requirements"
update-requirements: requirements.in dev-requirements.in $(VENV_DIR)
	$(PIP_COMPILE) requirements.in -o requirements.txt
	$(PIP_COMPILE) dev-requirements.in -o dev-requirements.txt
	$(VENV_DIR)/bin/pip-sync requirements.txt dev-requirements.txt

check:
	$(VENV_DIR)/bin/mypy protoc_gen_mocks/
	$(VENV_DIR)/bin/pycodestyle protoc_gen_mocks/ 2>&1

black:
	$(VENV_DIR)/bin/black -t py39 -l 120 tests protoc_gen_mocks protc_gen_mocks_client

example: 
	$(VENV_DIR)/bin/python -m grpc_tools.protoc --plugin="protoc-gen-mocks=$$(which protoc-gen-mocks)" examples/*.proto --mocks_out=.  --proto_path=. --python_out=. --pyi_out=.	
