SHELL := /bin/bash

install:
    pip3 install -r requirements.txt

run:
	python3 manage.py loaddata stock_data
    python3 manage.py runserver

migration:
    python3 manage.py makemigrations

migrate:
    python3 manage.py migrate

superuser:
    python3 manage.py createsuperuser

