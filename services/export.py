"""Export of the standings as CSV."""

from __future__ import annotations

import csv
from collections.abc import Iterable, Mapping
from io import StringIO

EXPORT_COLUMNS = ("TEAM", "GP", "W", "L", "OTL", "PTS", "GF", "GA", "DIFF")


def standings_to_csv(records: Iterable[Mapping[str, int | str]]) -> str:
    """Return the standings rows as CSV text with a header line (rank order is kept)."""
    buffer = StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(EXPORT_COLUMNS)
    writer.writerows(map(lambda record: tuple(record[column] for column in EXPORT_COLUMNS), records))
    return buffer.getvalue()
