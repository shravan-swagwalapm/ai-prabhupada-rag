#!/usr/bin/env python3
"""
Thread-safe circuit breaker for external services (ElevenLabs, etc.)

States:
  CLOSED  — normal operation, requests pass through
  OPEN    — too many failures, requests blocked for RECOVERY_TIMEOUT_SECS
  (auto-resets to CLOSED after recovery timeout)
"""
from __future__ import annotations

import collections
import logging
import threading
import time

logger = logging.getLogger(__name__)

FAILURE_THRESHOLD = 3
FAILURE_WINDOW_SECS = 60
RECOVERY_TIMEOUT_SECS = 300  # 5 minutes


class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = FAILURE_THRESHOLD,
        failure_window_secs: float = FAILURE_WINDOW_SECS,
        recovery_timeout_secs: float = RECOVERY_TIMEOUT_SECS,
    ):
        self._failure_threshold = failure_threshold
        self._failure_window_secs = failure_window_secs
        self._recovery_timeout_secs = recovery_timeout_secs

        self._failures: collections.deque = collections.deque()
        self._opened_at: float | None = None
        self._lock = threading.Lock()

    def is_open(self) -> bool:
        """Check if the circuit breaker is open (blocking requests)."""
        with self._lock:
            if self._opened_at is None:
                return False

            # Check if recovery timeout has passed
            elapsed = time.monotonic() - self._opened_at
            if elapsed >= self._recovery_timeout_secs:
                logger.info(
                    "Circuit breaker auto-reset after %.0fs recovery timeout",
                    elapsed,
                )
                self._opened_at = None
                self._failures.clear()
                return False

            return True

    def record_failure(self) -> None:
        """Record a failure. Opens the breaker if threshold is exceeded."""
        now = time.monotonic()
        with self._lock:
            # If already open, just log
            if self._opened_at is not None:
                return

            self._failures.append(now)

            # Purge failures outside the window
            cutoff = now - self._failure_window_secs
            while self._failures and self._failures[0] < cutoff:
                self._failures.popleft()

            if len(self._failures) >= self._failure_threshold:
                self._opened_at = now
                logger.warning(
                    "Circuit breaker OPENED after %d failures in %.0fs window",
                    len(self._failures),
                    self._failure_window_secs,
                )

    def record_success(self) -> None:
        """Record a success. Clears failure count (but does NOT close an open breaker)."""
        with self._lock:
            self._failures.clear()
