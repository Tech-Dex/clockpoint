#!/usr/bin/env bash

set -x

autoflake --remove-all-unused-imports --recursive --remove-unused-variables --in-place app/. --exclude=__init__.py
isort --multi-line=3 --trailing-comma --force-grid-wrap=0 --combine-as --line-width 88 app/.
black app/.
vulture app/. --min-confidence 70

autoflake --remove-all-unused-imports --recursive --remove-unused-variables --in-place alembic/. --exclude=__init__.py
isort --multi-line=3 --trailing-comma --force-grid-wrap=0 --combine-as --line-width 88 alembic/.
black alembic/.
vulture alembic/. --min-confidence 70