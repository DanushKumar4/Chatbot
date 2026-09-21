"""CLI script to start a background worker.

Usage:
    python -m scripts.worker
    python -m scripts.worker --poll-interval 2
"""

import argparse
import logging
from app.worker import Worker


def main():
    parser = argparse.ArgumentParser(description="Start a SmartBank background worker")
    parser.add_argument("--poll-interval", type=float, default=1.0,
                        help="Seconds between poll cycles (default: 1.0)")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    worker = Worker()
    print(f"Starting worker {worker.worker_id}")
    print(f"Poll interval: {args.poll_interval}s")
    print("Press Ctrl+C to stop\n")

    worker.run_forever(poll_interval=args.poll_interval)


if __name__ == "__main__":
    main()
