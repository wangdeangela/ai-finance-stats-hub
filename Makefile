.PHONY: setup demo test streamlit clean

setup:
	python3 -m venv .venv
	.venv/bin/pip install -r requirements-dev.txt

demo:
	python main.py --demo

test:
	pytest tests/

streamlit:
	streamlit run app.py

clean:
	rm -rf .pytest_cache __pycache__ src/**/__pycache__
