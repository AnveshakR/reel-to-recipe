import logging
import subprocess
import time
import sys
from contextlib import contextmanager

import requests

from CONFIG import CONTAINERS, STARTUP_TIMEOUT, POLL_INTERVAL

logger = logging.getLogger(__name__)


def _docker(args: list[str]) -> subprocess.CompletedProcess:
    """Run a docker command and return the result.

    Args:
        args: List of arguments to pass after 'docker'.

    Returns:
        CompletedProcess instance with stdout and stderr captured.
    """
    return subprocess.run(
        ["docker"] + args,
        capture_output=True,
        text=True,
    )


def is_running(container: str) -> bool:
    """Check whether a Docker container is currently running.

    Args:
        container: Name of the Docker container.

    Returns:
        True if the container is running, False otherwise.
    """
    result = _docker(["inspect", "--format", "{{.State.Running}}", container])
    return result.stdout.strip() == "true"


def wait_until_ready(container: str, start_time: float, timeout: int = STARTUP_TIMEOUT) -> bool:
    """Poll a container's health URL until it responds or the timeout is reached.

    Args:
        container: Name of the Docker container.
        start_time: Unix timestamp when the wait began.
        timeout: Maximum seconds to wait before giving up.

    Returns:
        True if the container became ready within the timeout, False otherwise.
    """
    url = CONTAINERS[container]
    deadline = start_time + timeout
    logger.info("[%s] Waiting to be ready (timeout %ss)...", container, timeout)
    while time.time() < deadline:
        try:
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                elapsed = time.time() - start_time
                logger.info("[%s] Ready in %.1fs.", container, elapsed)
                return True
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(POLL_INTERVAL)
    elapsed = time.time() - start_time
    logger.warning("[%s] Timed out after %.1fs.", container, elapsed)
    return False


def start(container: str) -> bool:
    """Start a container and wait until it is ready.

    Args:
        container: Name of the Docker container to start.

    Returns:
        True if the container started and passed its health check, False otherwise.
    """
    t0 = time.time()
    if is_running(container):
        logger.info("[%s] Already running, waiting for health check...", container)
        return wait_until_ready(container, start_time=t0)

    logger.info("Starting %s...", container)
    result = _docker(["start", container])
    if result.returncode != 0:
        logger.error("[%s] docker start failed: %s", container, result.stderr.strip())
        return False

    return wait_until_ready(container, start_time=t0)


def stop(container: str) -> bool:
    """Stop a container gracefully.

    Args:
        container: Name of the Docker container to stop.

    Returns:
        True if the container was stopped successfully, False otherwise.
    """
    if not is_running(container):
        logger.info("[%s] Already stopped.", container)
        return True

    logger.info("Stopping %s...", container)
    result = _docker(["stop", container])
    if result.returncode != 0:
        logger.error("[%s] docker stop failed: %s", container, result.stderr.strip())
        return False

    logger.info("[%s] Stopped.", container)
    return True


@contextmanager
def running(container: str):
    """Context manager that starts a container on entry and stops it on exit.

    Args:
        container: Name of the Docker container to manage.
    """
    ok = start(container)
    if not ok:
        stop(container)
        raise RuntimeError(f"Failed to start container: {container}")
    try:
        yield
    finally:
        stop(container)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    if len(sys.argv) != 3 or sys.argv[1] not in ("start", "stop"):
        logger.error("Usage: python model_manager.py <start|stop> <container>  [%s]", ", ".join(CONTAINERS))
        sys.exit(1)

    action, container = sys.argv[1], sys.argv[2]
    if container not in CONTAINERS:
        logger.error("Unknown container '%s'. Options: %s", container, ", ".join(CONTAINERS))
        sys.exit(1)

    if action == "start":
        success = start(container)
    else:
        success = stop(container)

    sys.exit(0 if success else 1)
