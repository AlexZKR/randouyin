.PHONY: tests

requirements:
	python3.12 -m pip install --upgrade pip -r requirements.txt -r requirements-dev.txt \
	&& playwright install chromium --with-deps

local:
	docker compose up --build

format:
	ruff check --fix

tests:
	pytest --cov=randouyin --cov-report=term-missing
