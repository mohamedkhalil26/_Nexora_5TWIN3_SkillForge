#!/usr/bin/env bash
# Guide Render 1.3 : build lance a chaque deploiement.
set -o errexit
pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate --no-input
