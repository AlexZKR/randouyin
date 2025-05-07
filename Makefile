requirements:
	python3.12 -m pip install --upgrade pip -r requirements.txt -r requirements-dev.txt \
	&& playwright install chromium

format:
	ruff check --fix

tests:
	pytest
