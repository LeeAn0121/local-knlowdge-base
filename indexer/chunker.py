"""Header-aware Markdown chunker (raw-source extraction)."""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path

from indexer.models import Chunk

CHUNK_MAX_CHARS = 2000
CHUNK_OVERLAP_CHARS = 200
CHUNK_MIN_CHARS = 100

# Matches ATX headings: "## Title" or "## Title ##"
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)(?:\s+#+)?\s*$")


@dataclass
class Section:
    heading_text: str
    heading_level: int  # 1-6, 0 for pre-heading content
    breadcrumb: list[str] = field(default_factory=list)
    content: str = ""
    char_start: int = 0
    char_end: int = 0


def _compute_chunk_id(file_path: str, chunk_index: int, text: str) -> str:
    raw = f"{file_path}:{chunk_index}:{text[:64]}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _split_into_sentences(text: str, max_chars: int, overlap: int) -> list[tuple[int, int]]:
    """
    Returns list of (start, end) character ranges for sub-chunks.
    Splits at sentence/paragraph boundaries.
    """
    boundaries: list[int] = [0]
    for m in re.finditer(r"(?<=[.!?])\s+|\n\n+", text):
        boundaries.append(m.end())
    boundaries.append(len(text))

    ranges: list[tuple[int, int]] = []
    chunk_start = 0

    while chunk_start < len(text):
        chunk_end = chunk_start + max_chars

        if chunk_end >= len(text):
            ranges.append((chunk_start, len(text)))
            break

        # Find the nearest boundary before chunk_end
        best = chunk_end
        for b in boundaries:
            if chunk_start < b <= chunk_end:
                best = b

        ranges.append((chunk_start, best))
        # Next chunk starts with overlap
        overlap_start = max(chunk_start, best - overlap)
        next_start = overlap_start
        # Advance to next natural boundary to avoid tiny slivers
        for b in boundaries:
            if b > overlap_start:
                next_start = b
                break
        if next_start <= chunk_start:
            next_start = best
        chunk_start = next_start

    return ranges


def _parse_sections(file_path: str, source: str) -> list[Section]:
    """
    Parse markdown into sections by extracting raw source lines per heading.
    This preserves all formatting (lists, tables, code blocks, etc.) correctly.
    """
    lines = source.splitlines(keepends=True)

    # Build cumulative char offsets for each line start
    line_starts: list[int] = []
    pos = 0
    for line in lines:
        line_starts.append(pos)
        pos += len(line)
    line_starts.append(pos)  # sentinel: end of file

    # Find all ATX headings
    heading_positions: list[tuple[int, int, str]] = []  # (line_idx, level, text)
    for i, line in enumerate(lines):
        m = _HEADING_RE.match(line.rstrip("\n\r"))
        if m:
            level = len(m.group(1))
            text = m.group(2).strip()
            heading_positions.append((i, level, text))

    sections: list[Section] = []

    # Pre-heading content (before first heading)
    first_heading_line = heading_positions[0][0] if heading_positions else len(lines)
    pre_content = "".join(lines[:first_heading_line]).strip()
    if pre_content:
        sections.append(Section(
            heading_text="",
            heading_level=0,
            breadcrumb=[],
            content=pre_content,
            char_start=0,
            char_end=line_starts[first_heading_line],
        ))

    heading_stack: list[tuple[int, str]] = []  # (level, text)

    for i, (line_num, level, heading_text) in enumerate(heading_positions):
        # Content spans from the line after the heading to before the next heading
        content_start_line = line_num + 1
        content_end_line = heading_positions[i + 1][0] if i + 1 < len(heading_positions) else len(lines)

        content = "".join(lines[content_start_line:content_end_line]).strip()

        char_start = line_starts[line_num]
        char_end = line_starts[content_end_line]

        # Update breadcrumb stack
        heading_stack = [(l, t) for l, t in heading_stack if l < level]
        heading_stack.append((level, heading_text))
        breadcrumb = [t for _, t in heading_stack]

        sections.append(Section(
            heading_text=heading_text,
            heading_level=level,
            breadcrumb=breadcrumb,
            content=content,
            char_start=char_start,
            char_end=char_end,
        ))

    return sections


def chunk_file(
    file_path: str,
    file_hash: str,
    source: str,
    max_chars: int = CHUNK_MAX_CHARS,
    overlap_chars: int = CHUNK_OVERLAP_CHARS,
    min_chars: int = CHUNK_MIN_CHARS,
) -> list[Chunk]:
    """
    Parse a markdown file and return a list of Chunk objects.
    Each chunk corresponds to a section or sub-section of the file.
    """
    sections = _parse_sections(file_path, source)
    chunks: list[Chunk] = []
    global_idx = 0

    for section in sections:
        text = section.content.strip()
        if not text or len(text) < min_chars:
            continue

        breadcrumb_str = " > ".join(section.breadcrumb) if section.breadcrumb else "(intro)"

        if len(text) <= max_chars:
            chunk = Chunk(
                chunk_id=_compute_chunk_id(file_path, global_idx, text),
                file_path=file_path,
                file_hash=file_hash,
                heading_breadcrumb=breadcrumb_str,
                heading_level=section.heading_level,
                chunk_index=global_idx,
                total_chunks_in_section=1,
                text=text,
                char_start=section.char_start,
                char_end=section.char_end,
            )
            chunks.append(chunk)
            global_idx += 1
        else:
            sub_ranges = _split_into_sentences(text, max_chars, overlap_chars)
            total = len(sub_ranges)
            for sub_i, (start, end) in enumerate(sub_ranges):
                sub_text = text[start:end].strip()
                if len(sub_text) < min_chars:
                    continue
                label = f"{breadcrumb_str} (part {sub_i + 1}/{total})" if total > 1 else breadcrumb_str
                chunk = Chunk(
                    chunk_id=_compute_chunk_id(file_path, global_idx, sub_text),
                    file_path=file_path,
                    file_hash=file_hash,
                    heading_breadcrumb=label,
                    heading_level=section.heading_level,
                    chunk_index=global_idx,
                    total_chunks_in_section=total,
                    text=sub_text,
                    char_start=section.char_start + start,
                    char_end=section.char_start + end,
                )
                chunks.append(chunk)
                global_idx += 1

    return chunks


def chunk_file_from_path(
    path: Path,
    file_hash: str,
    docs_root: Path,
    **kwargs,
) -> list[Chunk]:
    """Read a file from disk and chunk it. file_path is relative to docs_root."""
    source = path.read_text(encoding="utf-8", errors="replace")
    rel_path = str(path.relative_to(docs_root)).replace("\\", "/")
    return chunk_file(rel_path, file_hash, source, **kwargs)
