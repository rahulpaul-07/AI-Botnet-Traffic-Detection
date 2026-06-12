"""Wait for essential SENTINEL services to become available.

Usage:
    python scripts/wait_for_services.py --backend http://localhost:8000/health --dashboard http://localhost:8501

This script exits with code 0 when both services respond with HTTP 200 (or the health endpoint returns JSON with status 'online'),
otherwise exits with non-zero after timeout.
"""
from __future__ import annotations
import argparse
import time
import sys
import requests


def wait_for_url(url: str, timeout: int = 30, interval: float = 1.0) -> bool:
    end = time.time() + timeout
    while time.time() < end:
        try:
            r = requests.get(url, timeout=2)
            if r.status_code == 200:
                # If JSON with 'status' key is present, prefer checking it
                try:
                    data = r.json()
                    if isinstance(data, dict) and data.get('status') in ('online', 'ok', 'ONLINE'):
                        return True
                except Exception:
                    return True
        except Exception:
            pass
        time.sleep(interval)
    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--backend', default='http://localhost:8000/health', help='Backend health URL')
    parser.add_argument('--dashboard', default='http://localhost:8501', help='Dashboard base URL')
    parser.add_argument('--timeout', type=int, default=30, help='Seconds to wait for each service')
    args = parser.parse_args()

    print(f"Waiting for backend at {args.backend} (timeout {args.timeout}s)")
    ok_backend = wait_for_url(args.backend, timeout=args.timeout)
    print(f"Backend OK: {ok_backend}")

    print(f"Waiting for dashboard at {args.dashboard} (timeout {args.timeout}s)")
    ok_dashboard = wait_for_url(args.dashboard, timeout=args.timeout)
    print(f"Dashboard OK: {ok_dashboard}")

    if ok_backend and ok_dashboard:
        print("All services are up.")
        sys.exit(0)
    else:
        print("One or more services failed to become ready within timeout.")
        sys.exit(2)


if __name__ == '__main__':
    main()
