.PHONY: install normalize match test zip clean

install:
	python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt

normalize:
	python -m src.cli normalize --input ./tests/data --out ./out

match:
	python -m src.cli match --normalized ./out/normalized_products.jsonl --out ./out

profile:
	python -m src.cli profile --input ./tests/data --out ./out

evaluate:
	python -m src.evaluate --normalized ./out/normalized_products.jsonl --out ./reports

test:
	pytest -q

zip:
	python -c "import shutil; shutil.make_archive('retail-normalizer','zip','.')"

clean:
	rm -rf out reports retail-normalizer.zip .pytest_cache __pycache__
