.PHONY: clean install-dev lint type-check check-code format

DIRS_WITH_CODE = code
DIRS_WITH_ACTORS = actors

clean:
	rm -rf .venv .mypy_cache .pytest_cache .ruff_cache __pycache__

install-dev:
	cd $(DIRS_WITH_CODE) && pip install --upgrade pip poetry && poetry install --with main,dev,opengauss && poetry run pre-commit install && cd ..

lint:
	poetry run -C $(DIRS_WITH_CODE) ruff check

type-check:
	poetry run -C $(DIRS_WITH_CODE) mypy

check-code: lint type-check

format:
	poetry run -C $(DIRS_WITH_CODE) ruff check --fix
	poetry run -C $(DIRS_WITH_CODE) ruff format

pydantic-model:
	datamodel-codegen --input $(DIRS_WITH_ACTORS)/opengauss/.actor/input_schema.json --output $(DIRS_WITH_CODE)/src/models/opengauss_input_model.py  --input-file-type jsonschema  --field-constraints  --enum-field-as-literal all


# Integration tests are marked with @pytest.mark.integration_test
# You will require all databased running to run these tests.
# Check docker-compose.yml for the list of databases.
test-integration:
	poetry run -C $(DIRS_WITH_CODE) pytest --with-integration

test-unit:
	poetry run -C $(DIRS_WITH_CODE) pytest

test: test-unit test-integration
