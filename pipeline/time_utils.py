from __future__ import annotations

import datetime as dt


def truncate_to_interval(now: dt.datetime, interval_seconds: int) -> dt.datetime:
    """Floor `now` to the most recent interval boundary since the epoch.

    This is the scheduler's "logical run slot" — used as `observed_at` by
    sources with no native history (e.g. GitHub) so that a scheduled run's
    retries all land on the same natural key instead of creating a new row
    per attempt.
    """
    epoch_seconds = now.timestamp()
    floored = epoch_seconds - (epoch_seconds % interval_seconds)
    return dt.datetime.fromtimestamp(floored, tz=dt.UTC)
