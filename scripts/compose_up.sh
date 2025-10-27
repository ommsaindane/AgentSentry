#!/usr/bin/env bash
set -euo pipefail
cd infra
docker compose --env-file ./.env up --build