install:
	cd src && pip install -r requirements.txt

run:
	cd src && AWS_PROFILE=nuglif APP_LOGLEVEL=DEBUG python3 agent.py

src/requirements.txt:
	cd src && pip freeze > requirements.txt

build: src/requirements.txt
	docker build -t tfdriftagent:latest .