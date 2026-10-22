#!/bin/sh
set -eu

alembic upgrade head

if [ "${RUN_SEED:-false}" = "true" ]; then
    python scripts/seed.py
fi

if [ "$#" -eq 0 ]; then
    set -- uvicorn app.main:app --host 0.0.0.0
fi

if [ "$1" = "uvicorn" ]; then
    case " $* " in
        *" --port "*) ;;
        *) set -- "$@" --port "${PORT:-8000}" ;;
    esac
fi

exec "$@"
