ARGS := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))

wait_for_db:
	until pg_isready; do sleep 1; done

migrate: wait_for_db
	python3 manage.py makemigrations analyst --no-input

create_tables: migrate
	python3 manage.py migrate --no-input

collect_static:
	python3 manage.py collectstatic --no-input

create_superuser:
	echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='admin') or User.objects.create_superuser('admin', 'admin@myproject.com', 'password')" | python3 manage.py shell

load_fixtures: wait_for_db create_tables
	echo "from tests.conftest import AnalysisTestDatas; import os.path; from analyst.settings import FIXTURE_PATH; AnalysisTestDatas(os.path.join(FIXTURE_PATH, 'base', 'fixtures.json'))" | python3 manage.py shell

run_dev_server:
	python3 manage.py runserver 0.0.0.0:8080

run_uwsgi:
	uwsgi --ini confs/uwsgi/analyst.ini

run_dev: create_tables create_superuser load_fixtures run_dev_server

sh:
	bash

py:
	python3 manage.py shell

ipy:
	python3 manage.py shell -i ipython

isort:
	python3 -m isort

test: create_tables
	pytest

coverage:
	pytest

coverage_local:
	pytest

lint:
	python3 -m flake8

dump:
	mkdir -p generated
	python3 manage.py dumpdata analyst > generated/db.json

load:
	python3 manage.py loaddata generated/db.json

piprot:
	piprot

clean:
	find -name "*.pyc" -o -name "__pycache__" | tac | xargs rm -rf
