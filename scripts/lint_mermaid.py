#!/usr/bin/env python3
"""Structural linter for ```mermaid blocks in the audit markdown.

Mermaid's parser is tolerant in places and brittle in others. The failures that
actually bite in a published repo are not exotic: an unbalanced bracket, a label
containing a bare parenthesis, a `class` line naming a node that does not exist,
or a classDef that was never defined. This checks exactly those, plus fence
balance, so a broken diagram never reaches GitHub.

Usage:
    python scripts/lint_mermaid.py [path ...]

Exits non-zero if any problem is found.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# A node definition looks like:  ID["label"]  or  ID{"label"}  or  ID("label")
NODE_DEF = re.compile(r'\b([A-Za-z_][A-Za-z0-9_]*)\s*(\[|\{|\()')
SUBGRAPH = re.compile(r'^\s*subgraph\s+([A-Za-z_][A-Za-z0-9_]*)\s*(\[|$)')
CLASS_LINE = re.compile(r'^\s*class\s+([A-Za-z0-9_,.\s]+?)\s+([A-Za-z_][A-Za-z0-9_]*)\s*$')
CLASSDEF_LINE = re.compile(r'^\s*classDef\s+([A-Za-z_][A-Za-z0-9_]*)')
STYLE_LINE = re.compile(r'^\s*style\s+([A-Za-z_][A-Za-z0-9_]*)')

# Characters that must not appear inside an unquoted label.
UNSAFE_UNQUOTED = set('(){}#;,%$')


def extract_blocks(text: str) -> list[tuple[int, str]]:
    """Return (start_line, body) for every fenced mermaid block."""
    blocks: list[tuple[int, str]] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        if lines[i].strip().lower().startswith('```mermaid'):
            start = i + 2  # 1-based line number of first body line
            i += 1
            body: list[str] = []
            while i < len(lines) and not lines[i].strip().startswith('```'):
                body.append(lines[i])
                i += 1
            blocks.append((start, '\n'.join(body)))
        i += 1
    return blocks


def check_fences(path: Path, text: str) -> list[str]:
    """Fence parity for the whole file."""
    n = sum(1 for ln in text.splitlines() if ln.strip().startswith('```'))
    if n % 2:
        return [f'{path}: unbalanced code fences ({n} fence markers)']
    return []


def check_block(path: Path, start: int, body: str) -> list[str]:
    errs: list[str] = []
    where = f'{path}:{start}'

    defined_nodes: set[str] = set()
    subgraph_ids: set[str] = set()
    classdefs: set[str] = set()

    for offset, raw in enumerate(body.splitlines()):
        lineno = start + offset
        line = raw.rstrip()

        # Bracket and quote balance per line.
        for open_ch, close_ch in (('[', ']'), ('{', '}'), ('(', ')')):
            if line.count(open_ch) != line.count(close_ch):
                # Edge labels legitimately use ( ) inside |...| on one line; only
                # flag when the imbalance is outside a quoted label.
                stripped = re.sub(r'"[^"]*"', '', line)
                if stripped.count(open_ch) != stripped.count(close_ch):
                    errs.append(
                        f'{where}+{offset}: unbalanced {open_ch}{close_ch}: {line.strip()!r}'
                    )

        if line.count('"') % 2:
            errs.append(f'{where}+{offset}: odd number of double quotes: {line.strip()!r}')

        # Node / subgraph collection.
        m = SUBGRAPH.match(line)
        if m:
            subgraph_ids.add(m.group(1))
            continue
        if re.match(r'^\s*end\s*$', line):
            continue

        for nid, bracket in NODE_DEF.findall(line):
            defined_nodes.add(nid)

        # Unquoted label sanity: any [...] whose content is not quoted.
        for label in re.findall(r'\[([^\]]*)\]', line):
            inner = label.strip()
            if not inner:
                continue
            if not (inner.startswith('"') and inner.endswith('"')):
                bad = sorted(UNSAFE_UNQUOTED & set(inner))
                if bad:
                    errs.append(
                        f'{where}+{offset}: unquoted label contains {bad}: {inner!r}'
                    )

        m = CLASSDEF_LINE.match(line)
        if m:
            classdefs.add(m.group(1))

        m = STYLE_LINE.match(line)
        if m:
            sid = m.group(1)
            if sid not in subgraph_ids and sid not in defined_nodes:
                errs.append(f'{where}+{offset}: style targets unknown id {sid!r}')

        m = CLASS_LINE.match(line)
        if m:
            targets = [t.strip() for t in m.group(1).split(',') if t.strip()]
            style = m.group(2)
            for t in targets:
                if t not in defined_nodes and t not in subgraph_ids:
                    errs.append(f'{where}+{offset}: class targets unknown node {t!r}')
            if style not in classdefs:
                errs.append(f'{where}+{offset}: class uses undefined classDef {style!r}')

    return errs


def main(paths: list[str]) -> int:
    problems: list[str] = []
    total = 0

    for p in paths:
        path = Path(p)
        if not path.exists():
            problems.append(f'{path}: no such file')
            continue
        text = path.read_text(encoding='utf-8')
        blocks = extract_blocks(text)
        total += len(blocks)
        problems += check_fences(path, text)
        for start, body in blocks:
            problems += check_block(path, start, body)
        if blocks:
            print(f'{path}: {len(blocks)} mermaid block(s)')

    print(f'\ntotal mermaid blocks: {total}')
    if problems:
        print(f'\nFAILED - {len(problems)} problem(s):')
        for p in problems:
            print(f'  - {p}')
        return 1

    print('OK - all mermaid blocks pass structural checks')
    return 0


if __name__ == '__main__':
    args = sys.argv[1:]
    if not args:
        root = Path(__file__).resolve().parent.parent
        args = sorted(
            str(f) for f in root.rglob('*.md')
            if 'contracts' not in f.parts
        )
    sys.exit(main(args))
