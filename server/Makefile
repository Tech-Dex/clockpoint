start-dev:
	uvicorn run:app --reload

start-prod:
	uvicorn run:app

upgrade:
	pip --disable-pip-version-check list --outmdated --format=json | python -c "import json, sys; print('\n'.join([x['name'] for x in json.load(sys.stdin)]))" | xargs -n1 pip install -U