"""Load all CSV files from a folder (data/games) with the import pipeline."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from functools import reduce
from pathlib import Path

from models import Game
from services.importer import RowError, import_games_from_csv


@dataclass(frozen=True)
class FileImport:
    """Result of importing one CSV file from the folder."""

    name: str
    accepted: int
    errors: tuple[RowError, ...]


def csv_files(folder: Path) -> tuple[Path, ...]:
    """Return the CSV files of the folder sorted by name (empty if the folder does not exist)."""
    return tuple(sorted(folder.glob("*.csv"))) if folder.is_dir() else ()


def read_text(path: Path) -> str | None:
    """Read a UTF-8 file (with or without BOM), None if it is not UTF-8."""
    try:
        return path.read_bytes().decode("utf-8-sig")
    except UnicodeDecodeError:
        return None


def import_file(
    state: tuple[tuple[Game, ...], tuple[FileImport, ...]], file: tuple[str, str | None]
) -> tuple[tuple[Game, ...], tuple[FileImport, ...]]:
    """Import one (name, text) file; games of earlier files count as already imported."""
    games, reports = state
    name, text = file
    if text is None:
        return games, reports + (FileImport(name, 0, (RowError(1, "file must be UTF-8 encoded"),)),)
    new_games, errors = import_games_from_csv(text, existing=games)
    return games + new_games, reports + (FileImport(name, len(new_games), errors),)


def import_files(files: Iterable[tuple[str, str | None]]) -> tuple[tuple[Game, ...], tuple[FileImport, ...]]:
    """Import several (name, text) files in order with reduce and return (games, reports)."""
    return reduce(import_file, files, ((), ()))


def load_games_folder(folder: Path) -> tuple[tuple[Game, ...], tuple[FileImport, ...]]:
    """Read every CSV file of the folder and import it."""
    return import_files(map(lambda path: (path.name, read_text(path)), csv_files(folder)))
