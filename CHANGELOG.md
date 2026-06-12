# Changelog

All notable changes to this project are documented in this file.

## [Unreleased]
- Added runtime `/reload_model` endpoint to `backend_api` for hot model reloads.
- Orchestrator `run_all.py` now waits for backend `/health` before starting dependent services.
- Streamlit frontend reads `API_URL` from environment (works in Docker and local runs).
- Added `scripts/wait_for_services.py` for CI/service readiness checks.
- Added Docker healthchecks for `backend` and `frontend` in `docker-compose.yml`.
- Tidied `README.md` and added presentable run instructions.

## [2026-06-12]
- Initial cleanup: removed legacy backend duplication and fixed model loading issues.
