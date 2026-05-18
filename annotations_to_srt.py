#!/usr/bin/env python3
"""
Convert CoMPAS3D salsa dance annotation .txt files to .srt subtitle files.

The annotation files are TSV exports from ELAN with columns:
  Category  Role  StartTime(HH:MM:SS.mmm)  StartTime(s)
  EndTime(HH:MM:SS.mmm)  EndTime(s)  Duration(HH:MM:SS.mmm)  Duration(s)  Description

Usage:
  python annotations_to_srt.py Pair1_song1_take1.txt
  python annotations_to_srt.py Pair1/*.txt --output-dir subtitles/
  python annotations_to_srt.py file.txt --tracks Together
  python annotations_to_srt.py file.txt --no-labels
"""

import sys
import csv
import argparse
from pathlib import Path


KNOWN_CATEGORIES = {'Together', 'Separate_Leader', 'Separate_Follower', 'Errors'}

ROLE_LABELS = {
    'Together': '',
    'Separate_Leader': 'Leader',
    'Separate_Follower': 'Follower',
    'Errors': 'Error',
}


def ts_to_srt(ts: str) -> str:
    """Convert HH:MM:SS.mmm to SRT format HH:MM:SS,mmm with exactly 3 decimal digits."""
    if '.' in ts:
        hms, frac = ts.rsplit('.', 1)
        frac = frac.ljust(3, '0')[:3]
        return f"{hms},{frac}"
    return f"{ts},000"


def load_annotations(path: Path) -> list[dict]:
    rows = []
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter='\t')
        for row in reader:
            if len(row) < 9:
                continue
            category = row[0].strip()
            if category not in KNOWN_CATEGORIES:
                continue  # skip header rows or unrecognised lines
            try:
                rows.append({
                    'category': category,
                    'role': row[1].strip(),
                    'start_ts': row[2].strip(),
                    'start_sec': float(row[3]),
                    'end_ts': row[4].strip(),
                    'end_sec': float(row[5]),
                    'description': row[8].strip(),
                })
            except (ValueError, IndexError):
                continue
    return rows


def build_srt(annotations: list[dict], tracks: list[str], label_roles: bool) -> str:
    filtered = [a for a in annotations if a['category'] in tracks]
    filtered.sort(key=lambda a: (a['start_sec'], a['end_sec']))

    # Build raw subtitle list with optional role labels
    entries = []
    for a in filtered:
        label = ROLE_LABELS.get(a['category'], '')
        text = f"[{label}] {a['description']}" if (label_roles and label) else a['description']
        entries.append({'start_ts': a['start_ts'], 'end_ts': a['end_ts'],
                        'start_sec': a['start_sec'], 'text': text})

    # Merge entries that share the exact same time range into one subtitle block
    merged: list[dict] = []
    for entry in entries:
        if (merged
                and merged[-1]['start_ts'] == entry['start_ts']
                and merged[-1]['end_ts'] == entry['end_ts']):
            merged[-1]['text'] += '\n' + entry['text']
        else:
            merged.append(dict(entry))

    parts = []
    for i, entry in enumerate(merged, 1):
        start = ts_to_srt(entry['start_ts'])
        end = ts_to_srt(entry['end_ts'])
        parts.append(f"{i}\n{start} --> {end}\n{entry['text']}")

    return '\n\n'.join(parts) + '\n' if parts else ''


def main():
    parser = argparse.ArgumentParser(
        description='Convert CoMPAS3D annotation .txt files to .srt subtitle files.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
tracks:
  Together            moves performed by both dancers in sync
  Separate_Leader     leader-only moves
  Separate_Follower   follower-only moves
  Errors              annotated errors (misinterpreted signal, misstep, etc.)

examples:
  %(prog)s Pair1_song1_take1.txt
  %(prog)s Pair1/**/*.txt --output-dir subtitles/
  %(prog)s file.txt --tracks Together
  %(prog)s file.txt --tracks Together,Errors --no-labels
""",
    )
    parser.add_argument('input', nargs='+', help='Annotation .txt file(s) to convert')
    parser.add_argument(
        '--tracks', '-t',
        default='Together,Separate_Leader,Separate_Follower',
        help='Comma-separated annotation tracks to include (default: Together,Separate_Leader,Separate_Follower)',
    )
    parser.add_argument(
        '--no-labels', action='store_true',
        help='Omit [Leader] / [Follower] / [Error] prefixes from subtitle text',
    )
    parser.add_argument(
        '--output-dir', '-o',
        help='Directory to write .srt files (default: same directory as each input file)',
    )
    args = parser.parse_args()

    tracks = [t.strip() for t in args.tracks.split(',') if t.strip()]
    invalid = [t for t in tracks if t not in KNOWN_CATEGORIES]
    if invalid:
        print(f"Warning: unknown track(s): {', '.join(invalid)}", file=sys.stderr)
        print(f"Valid options: {', '.join(sorted(KNOWN_CATEGORIES))}", file=sys.stderr)

    output_dir = Path(args.output_dir) if args.output_dir else None
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)

    for input_str in args.input:
        input_path = Path(input_str)
        if not input_path.exists():
            print(f"Error: file not found: {input_path}", file=sys.stderr)
            continue

        annotations = load_annotations(input_path)
        if not annotations:
            print(f"Warning: no annotations parsed from {input_path}", file=sys.stderr)
            continue

        srt_content = build_srt(annotations, tracks, label_roles=not args.no_labels)

        out_path = (output_dir or input_path.parent) / input_path.with_suffix('.srt').name
        out_path.write_text(srt_content, encoding='utf-8')

        n_entries = srt_content.count('\n\n') + (1 if srt_content.strip() else 0)
        print(f"{out_path}  ({n_entries} subtitle entries from {len(annotations)} annotations)")


if __name__ == '__main__':
    main()
