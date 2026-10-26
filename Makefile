.PHONY: setup run test eval eval-full
setup:
	python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
run:
	.venv/bin/uvicorn app.server:app --reload --port 8765
test:
	.venv/bin/python -m pytest -q
eval:
	.venv/bin/python -m eval.run_eval --mode retrieval
eval-full:
	.venv/bin/python -m eval.run_eval --mode full --judge
