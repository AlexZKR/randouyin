requirements:
	python3.12 -m pip install --upgrade pip -r requirements.txt -r requirements-dev.txt

format:
	ruff check --fix

tests:
	pytest
