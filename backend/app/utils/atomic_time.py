"""
Utilities for atomic clock synchronization and drift calculations.
"""

import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import httpx

logger = logging.getLogger(__name__)

# WorldTimeAPI endpoint (UTC only; other zones are converted locally)
WORLD_TIME_API_URL = "https://worldtimeapi.org/api/timezone/Etc/UTC"
API_TIMEOUT = 3.0  # seconds

# The offset between the reference clock and the server clock barely moves,
# so it is fetched at most once per window instead of on every request.
OFFSET_TTL_SECONDS = 60
FAILURE_TTL_SECONDS = 10

# (monotonic expiry, offset from server clock, came from the reference clock)
_offset_cache: Optional[Tuple[float, timedelta, bool]] = None


def resolve_timezone(tz: str) -> ZoneInfo:
    """Return the zone for an IANA name, or raise ValueError."""
    try:
        return ZoneInfo(tz or "UTC")
    except (ZoneInfoNotFoundError, ValueError, TypeError) as exc:
        raise ValueError(f"Unknown timezone: {tz}") from exc


async def _fetch_offset() -> Tuple[timedelta, bool]:
    try:
        async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
            response = await client.get(WORLD_TIME_API_URL)
            response.raise_for_status()
            reference = datetime.fromisoformat(response.json()["datetime"])
        return reference - datetime.now(timezone.utc), True
    except httpx.TimeoutException:
        logger.warning("WorldTimeAPI timeout after %ss, using server time", API_TIMEOUT)
    except httpx.HTTPError as e:
        logger.warning("WorldTimeAPI HTTP error: %s, using server time", e)
    except (KeyError, ValueError) as e:
        logger.error("Failed to parse WorldTimeAPI response: %s, using server time", e)
    except Exception as e:
        logger.error("Unexpected error fetching atomic time: %s, using server time", e)
    return timedelta(0), False


async def get_atomic_time(tz: str = "UTC") -> Tuple[datetime, bool]:
    """
    Current reference time in the given IANA timezone.

    Returns (datetime, is_atomic_source). is_atomic_source is False when the
    reference clock could not be reached and server time was used.
    Raises ValueError for an unknown timezone.
    """
    global _offset_cache
    zone = resolve_timezone(tz)
    now = time.monotonic()
    if _offset_cache is None or _offset_cache[0] <= now:
        offset, is_atomic = await _fetch_offset()
        ttl = OFFSET_TTL_SECONDS if is_atomic else FAILURE_TTL_SECONDS
        _offset_cache = (now + ttl, offset, is_atomic)
    _, offset, is_atomic = _offset_cache
    return (datetime.now(timezone.utc) + offset).astimezone(zone), is_atomic


def calculate_drift_spd(
    initial_reference_time: datetime,
    initial_watch_seconds: int,
    current_reference_time: datetime,
    current_watch_seconds: int,
) -> float:
    """
    Calculate watch drift in seconds per day.

    Formula:
        drift_spd = ((watch_elapsed - reference_elapsed) / hours_elapsed) * 24

    Where:
        - watch_elapsed = current_watch_seconds - initial_watch_seconds
        - reference_elapsed = (current_reference_time - initial_reference_time) in seconds
        - Positive drift = watch running fast
        - Negative drift = watch running slow

    Args:
        initial_reference_time: Atomic time when initial reading was taken
        initial_watch_seconds: Watch seconds position at initial (0, 15, 30, or 45)
        current_reference_time: Atomic time when current reading was taken
        current_watch_seconds: Watch seconds position at current (0, 15, 30, or 45)

    Returns:
        Drift in seconds per day (positive = fast, negative = slow)

    Example:
        Initial: atomic time 12:00:00, watch at :00
        Current: atomic time 12:06:15 (6.25 minutes later), watch at :15

        reference_elapsed = 375 seconds (6.25 minutes)
        watch_elapsed = 15 seconds
        drift = ((15 - 375) / (375/3600)) * 24 = -360 / 0.104 * 24 = -83,077 spd

        This would indicate a severely slow watch, which makes sense since
        only 15 seconds passed on the watch while 375 seconds passed in reality.
    """
    # Calculate elapsed time on reference clock (in seconds)
    reference_elapsed_td = current_reference_time - initial_reference_time
    reference_elapsed_seconds = reference_elapsed_td.total_seconds()

    # Calculate elapsed time on watch (in seconds)
    # Handle wrap-around: if current < initial, watch went through a minute boundary
    watch_elapsed_seconds = current_watch_seconds - initial_watch_seconds
    if watch_elapsed_seconds < 0:
        watch_elapsed_seconds += 60  # Add one minute

    # Calculate drift
    # Positive drift means watch is running fast (watch advanced more than reference)
    # Negative drift means watch is running slow (watch advanced less than reference)
    drift_seconds = watch_elapsed_seconds - reference_elapsed_seconds

    # Convert to seconds per day
    hours_elapsed = reference_elapsed_seconds / 3600
    if hours_elapsed == 0:
        raise ValueError("Time elapsed must be greater than zero")

    drift_spd = (drift_seconds / hours_elapsed) * 24

    logger.debug(
        f"Drift calculation: reference_elapsed={reference_elapsed_seconds}s, "
        f"watch_elapsed={watch_elapsed_seconds}s, "
        f"drift={drift_seconds}s over {hours_elapsed:.2f}h = {drift_spd:.2f} spd"
    )

    return round(drift_spd, 2)


def validate_reading_pair(
    initial_time: datetime,
    subsequent_time: datetime,
    min_hours: float = 6.0,
    max_days: int = 90,
) -> Tuple[bool, Optional[str]]:
    """
    Validate that two readings can be paired for drift calculation.

    Args:
        initial_time: Reference time of initial reading
        subsequent_time: Reference time of subsequent reading
        min_hours: Minimum hours between readings (default 6)
        max_days: Maximum days between readings (default 90)

    Returns:
        Tuple of (is_valid, error_message)
        error_message is None if valid
    """
    time_diff = subsequent_time - initial_time
    hours_elapsed = time_diff.total_seconds() / 3600
    days_elapsed = time_diff.days

    # Check minimum time
    if hours_elapsed < min_hours:
        return (
            False,
            f"Minimum {min_hours} hours required between readings (got {hours_elapsed:.1f}h)",
        )

    # Check maximum time
    if days_elapsed > max_days:
        return (
            False,
            f"Maximum {max_days} days allowed between readings (got {days_elapsed} days)",
        )

    # Check that subsequent is actually after initial
    if time_diff.total_seconds() <= 0:
        return False, "Subsequent reading must be after initial reading"

    return True, None
