"""The eval decks: download links and checksums. PDFs stay out of git because some slides contain
third-party images excluded from MIT's license (see evals/SOURCES.md). Run: python -m evals.decks"""

from __future__ import annotations

import hashlib
from pathlib import Path

import httpx

DECKS_DIR = Path(__file__).parent / "decks"
BASE = (
    "https://ocw.mit.edu/courses/6-0001-introduction-to-computer-science-and-programming-in-python-fall-2016"
)
DECKS = {
    "mit6_0001_lec1": (
        "e921a690079369751bcce3e34da6c6ee_MIT6_0001F16_Lec1.pdf",
        "26d1bd5f1c42489dc0ffe8b3610bc245f1278d7035f368013e5a58c7cd8a890c",
    ),
    "mit6_0001_lec2": (
        "ba2947b25b1580e4a84df0ec5dbe5cdd_MIT6_0001F16_Lec2.pdf",
        "c65fb02d7a68f9bdbd9f715ff9f1a8eec61235510bb931ca5c2f039b2ea3adf9",
    ),
    "mit6_0001_lec3": (
        "b9b9a82a29e8746db1facfbd30c07940_MIT6_0001F16_Lec3.pdf",
        "fa3357521ac4e1a07091dbec1c0e920252a1dfc6b3315a3924eb734c79cfcf03",
    ),
    "mit6_0001_lec4": (
        "6ba59859535f1566dd57a7279aeba5d1_MIT6_0001F16_Lec4.pdf",
        "eac916af74cd039a9f1a85a611e1ef5776a14e1ae0f4a0e6b3fccbcb2e782530",
    ),
    "mit6_0001_lec5": (
        "1776670e271578eeb99fc25975f20586_MIT6_0001F16_Lec5.pdf",
        "a5f0a9da11b4209292e592e4fbfd152e932385847aa26c99c2cacd9eee143f54",
    ),
}


def fetch_decks(decks_dir: Path = DECKS_DIR) -> list[Path]:
    """Download any missing deck and verify every checksum, so results are always from the same files."""
    decks_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for name, (remote, sha256) in DECKS.items():
        path = decks_dir / f"{name}.pdf"
        if not path.exists():
            r = httpx.get(f"{BASE}/{remote}", follow_redirects=True, timeout=60)
            r.raise_for_status()
            path.write_bytes(r.content)
        if hashlib.sha256(path.read_bytes()).hexdigest() != sha256:
            raise ValueError(f"Checksum mismatch for {path.name}: the source file changed")
        paths.append(path)
    return paths


if __name__ == "__main__":
    print(f"{len(fetch_decks())} decks ready in {DECKS_DIR}")
