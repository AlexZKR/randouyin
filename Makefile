.PHONY: tests

requirements:
	python3.12 -m pip install --upgrade pip -r requirements.txt -r requirements-dev.txt \
	&& playwright install --with-deps

local:
	docker compose up --build

debug:
	docker compose up -f docker-compose.yaml -f docker-compose.debug.yaml up --build

format:
	ruff check --fix

tests:
	pytest --cov=randouyin --cov-report=term-missing
