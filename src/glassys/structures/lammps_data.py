"""Reader for LAMMPS data files (``write_data`` / ``read_data`` format)."""

from __future__ import annotations

import re
from pathlib import Path

from pymatgen.core import Structure
from pymatgen.core.periodic_table import Element

LAMMPS_DATA_SUFFIXES = (".data", ".lmp", ".lammps", ".lammpsdata")

# Column layout per atom style: (type column, first of the x/y/z columns),
# both counted from 0 where column 0 is the atom id.
_ATOM_STYLE_COLUMNS: dict[str, tuple[int, int]] = {
    "atomic": (1, 2),
    "charge": (1, 3),
    "molecular": (2, 3),
    "bond": (2, 3),
    "angle": (2, 3),
    "full": (2, 4),
    "sphere": (1, 4),
    "dipole": (1, 3),
}

_BOX_LINE = re.compile(r"^\s*(\S+)\s+(\S+)\s+([xyz])lo\s+[xyz]hi\b")
_TILT_LINE = re.compile(r"^\s*(\S+)\s+(\S+)\s+(\S+)\s+xy\s+xz\s+yz\b")
_COUNT_LINE = re.compile(r"^\s*(\d+)\s+(atoms|atom types)\s*$")
_SECTION_NAMES = {
    "Atoms",
    "Velocities",
    "Masses",
    "Bonds",
    "Angles",
    "Dihedrals",
    "Impropers",
    "Ellipsoids",
    "Lines",
    "Triangles",
    "Bodies",
    "Atom Type Labels",
    "Bond Type Labels",
    "Angle Type Labels",
    "Dihedral Type Labels",
    "Improper Type Labels",
}


def looks_like_lammps_data(payload: bytes, filename: str) -> bool:
    name = Path(filename).name.lower()
    if name.endswith(LAMMPS_DATA_SUFFIXES) or name.startswith("data."):
        return True
    head = payload[:8192].decode("utf-8", errors="ignore")
    return any(_BOX_LINE.match(line) for line in head.splitlines()[:40])


def read_lammps_data(payload: bytes) -> Structure:
    """Parse a LAMMPS data file into a periodic pymatgen Structure.

    Elements come from the ``Atom Type Labels`` section, a ``# Symbol``
    comment on a ``Masses`` line, the nearest atomic mass, or (without any
    of those) the element whose atomic number equals the type id.
    """
    # Imported lazily: pymatgen.io.lammps pulls in pandas, which would slow server startup.
    from pymatgen.io.lammps.data import LammpsBox

    lines = payload.decode("utf-8", errors="ignore").splitlines()
    header, sections = _split_sections(lines[1:])

    bounds: dict[str, list[float]] = {}
    tilt: list[float] | None = None
    atom_count: int | None = None
    for line in header:
        if match := _BOX_LINE.match(line):
            bounds[match.group(3)] = [float(match.group(1)), float(match.group(2))]
        elif match := _TILT_LINE.match(line):
            tilt = [float(match.group(index)) for index in (1, 2, 3)]
        elif (match := _COUNT_LINE.match(_strip_comment(line))) and match.group(2) == "atoms":
            atom_count = int(match.group(1))

    if set(bounds) != {"x", "y", "z"}:
        raise ValueError("LAMMPS data file is missing xlo/xhi, ylo/yhi or zlo/zhi box bounds.")
    if "Atoms" not in sections:
        raise ValueError("LAMMPS data file has no Atoms section.")

    style_hint, atom_lines = sections["Atoms"]
    rows = [_strip_comment(line).split() for line in atom_lines]
    rows = [row for row in rows if row]
    if not rows:
        raise ValueError("LAMMPS data file contains no atoms.")
    if atom_count is not None and len(rows) != atom_count:
        raise ValueError(
            f"Header declares {atom_count} atoms but the Atoms section has {len(rows)}."
        )

    type_col, xyz_col = _atom_columns(style_hint, len(rows[0]))
    rows.sort(key=lambda row: int(row[0]))
    type_ids = [int(row[type_col]) for row in rows]
    origin = [bounds[axis][0] for axis in "xyz"]
    coords = [[float(row[xyz_col + axis]) - origin[axis] for axis in range(3)] for row in rows]

    symbols = _type_symbols(sorted(set(type_ids)), sections)
    box = LammpsBox([bounds[axis] for axis in "xyz"], tilt)
    return Structure(
        box.to_lattice(),
        [symbols[type_id] for type_id in type_ids],
        coords,
        coords_are_cartesian=True,
    )


def _split_sections(
    lines: list[str],
) -> tuple[list[str], dict[str, tuple[str, list[str]]]]:
    header: list[str] = []
    sections: dict[str, tuple[str, list[str]]] = {}
    current: list[str] | None = None
    for line in lines:
        keyword, _, comment = line.partition("#")
        keyword = keyword.strip()
        if keyword in _SECTION_NAMES:
            current = []
            sections[keyword] = (comment.strip(), current)
        elif current is None:
            header.append(line)
        else:
            current.append(line)
    return header, sections


def _strip_comment(line: str) -> str:
    return line.split("#", 1)[0].strip()


def _atom_columns(style_hint: str, column_count: int) -> tuple[int, int]:
    style = style_hint.split()[0].split("/")[0] if style_hint else ""
    if style:
        if style not in _ATOM_STYLE_COLUMNS:
            raise ValueError(f"Unsupported LAMMPS atom style '{style}'.")
        return _ATOM_STYLE_COLUMNS[style]

    # No style comment: infer from the column count, allowing trailing image flags.
    by_count = {5: "atomic", 6: "charge", 7: "full"}
    for count in (column_count, column_count - 3):
        if count in by_count:
            return _ATOM_STYLE_COLUMNS[by_count[count]]
    raise ValueError(
        f"Cannot infer the LAMMPS atom style from {column_count} columns; "
        "add a style comment such as 'Atoms # atomic'."
    )


def _type_symbols(
    type_ids: list[int],
    sections: dict[str, tuple[str, list[str]]],
) -> dict[int, str]:
    symbols: dict[int, str] = {}

    for line in sections.get("Atom Type Labels", ("", []))[1]:
        parts = _strip_comment(line).split()
        if len(parts) >= 2 and (symbol := _element_symbol(parts[1])):
            symbols[int(parts[0])] = symbol

    for line in sections.get("Masses", ("", []))[1]:
        body, _, comment = line.partition("#")
        parts = body.split()
        if len(parts) < 2:
            continue
        type_id = int(parts[0])
        if type_id in symbols:
            continue
        label = comment.split()[0] if comment.split() else ""
        symbols[type_id] = _element_symbol(label) or _element_from_mass(float(parts[1]))

    for type_id in type_ids:
        if type_id not in symbols:
            try:
                symbols[type_id] = Element.from_Z(type_id).symbol
            except ValueError:
                symbols[type_id] = "H"
    return symbols


def _element_symbol(label: str) -> str | None:
    candidate = label.strip().capitalize()
    return candidate if Element.is_valid_symbol(candidate) else None


def _element_from_mass(mass: float) -> str:
    return min(Element, key=lambda element: abs(float(element.atomic_mass) - mass)).symbol
