"""
Salsa grammar analysis — CoMPAS3D dataset.
Parses all Together-track annotations, normalises each description into
structured components, then computes transition (bigram) frequencies and
hold-state transitions.
"""

import re
import csv
from pathlib import Path
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Optional
import json

# ── data model ─────────────────────────────────────────────────────────────────

@dataclass
class Move:
    raw: str
    move_type: str          # canonical move family
    hold_in: str            # hold state entering this move
    hold_out: str           # hold state leaving this move (may equal hold_in)
    follower_turn: str      # none / left / right / double_right / double_left
    leader_turn: str        # none / left / right
    ending: str             # none / comb / check / break / throw / drop / lasso / body_roll
    pair: int
    song: int
    take: int
    level: str

# ── normalisation rules ─────────────────────────────────────────────────────────

LEVEL = {1: 'Beginner', 2: 'Intermediate', 3: 'Beginner', 4: 'Intermediate',
         5: 'Professional', 6: 'Intermediate', 7: 'Professional',
         8: 'Beginner', 9: 'Professional'}


def _has(text, *patterns):
    return any(re.search(p, text, re.IGNORECASE) for p in patterns)


def normalise_move_type(raw: str) -> str:
    t = raw.lower()
    if _has(t, r'\bbasic step\b'):           return 'Basic'
    if _has(t, r'\bside basic\b'):           return 'Side Basic'
    if _has(t, r'\bcross.?back basic\b'):    return 'Cross-Back Basic'
    if _has(t, r'\bback basic\b'):           return 'Back Basic'
    if _has(t, r'\bxbl\b'):                  return 'XBL'
    if _has(t, r'\bcopa\b'):                 return 'Copa'
    if _has(t, r'\bnatural top\b'):          return 'Natural Top'
    if _has(t, r'\bsuzy q\b'):               return 'Suzy Q'
    if _has(t, r'\bwalk.{0,10}around\b',
               r'\baround.{0,10}walk\b'):    return 'Walks Around'
    if _has(t, r'\bchange of direction\b'):  return 'Change of Directions'
    if _has(t, r'\bdile que no\b'):          return 'Dile que no'
    if _has(t, r'\benchufla\b'):             return 'Enchufla'
    if _has(t, r'\bhand throw\b'):           return 'Hand Throw'
    if _has(t, r'\bright.{0,10}throw\b',
               r'\bleft.{0,10}throw\b',
               r'\bdouble.{0,6}throw\b',
               r'\bsingle.{0,6}throw\b'):    return 'Hand Throw'
    if _has(t, r'\bbody roll\b'):            return 'Body Roll'
    if _has(t, r'\bbody shake\b'):           return 'Body Shake'
    if _has(t, r'\bcomb\b'):                 return 'Comb'
    if _has(t, r'\bcheck\b'):                return 'Check'
    if _has(t, r'\blasso\b'):                return 'Lasso'
    if _has(t, r'\barm lock\b'):             return 'Arm Lock'
    if _has(t, r'\bopen break\b'):           return 'Open Break'
    # turn-only moves (no XBL prefix)
    if _has(t, r'\bright turn\b', r'\bleft turn\b'): return 'Turn'
    return 'Other'


def normalise_hold(raw: str) -> str:
    t = raw.lower()
    if _has(t, r'\bcrossed hold\b', r'\bcrossed hand\b'): return 'crossed'
    if _has(t, r'\bleft hl\b', r'\bleft hammerlock\b'):   return 'hl_left'
    if _has(t, r'\bright hl\b', r'\bright hammerlock\b'): return 'hl_right'
    if _has(t, r'\bnormal closed hold\b', r'\bnormal closed hand\b',
               r'\bclosed hold\b'):                        return 'closed'
    if _has(t, r'\bnormal open hold\b', r'\bopen hold\b',
               r'\bopen hand\b'):                          return 'open'
    if _has(t, r'\bembrace\b'):                            return 'embrace'
    if _has(t, r'\bshadow\b'):                             return 'shadow'
    # default: most moves stay in whatever hold they were in
    return ''   # unknown / inherit


def normalise_follower_turn(raw: str) -> str:
    t = raw.lower()
    if _has(t, r'double.{0,10}right.{0,10}(turn|for the follower)',
               r'double right'):           return 'double_right'
    if _has(t, r'double.{0,10}left.{0,10}(turn|for the follower)',
               r'double left'):            return 'double_left'
    if _has(t, r'right.{0,30}follower|follower.{0,30}right'): return 'right'
    if _has(t, r'left.{0,30}follower|follower.{0,30}left'):    return 'left'
    if _has(t, r'outside.{0,10}turn'):     return 'right'   # outside = right
    if _has(t, r'inside.{0,10}turn'):      return 'left'    # inside  = left
    return 'none'


def normalise_leader_turn(raw: str) -> str:
    t = raw.lower()
    if _has(t, r'right.{0,30}leader|leader.{0,30}right'): return 'right'
    if _has(t, r'left.{0,30}leader|leader.{0,30}left'):   return 'left'
    return 'none'


def normalise_ending(raw: str) -> str:
    t = raw.lower()
    if _has(t, r'\bcomb\b'):     return 'comb'
    if _has(t, r'\bcheck\b'):    return 'check'
    if _has(t, r'\bbreak\b'):    return 'break'
    if _has(t, r'\bthrow\b'):    return 'throw'
    if _has(t, r'\bdrop\b'):     return 'drop'
    if _has(t, r'\blasso\b'):    return 'lasso'
    if _has(t, r'\bbody roll\b'):return 'body_roll'
    return 'none'


# ── hold tracking ───────────────────────────────────────────────────────────────
# Explicit hold-out rules: given a move and its description, what hold do we exit in?

def infer_hold_out(raw: str, hold_in: str) -> str:
    t = raw.lower()
    # explicit hold mentioned
    out = normalise_hold(raw)
    if out:
        return out
    # XBL always resolves to open (unless crossed stated, already caught above)
    if _has(t, r'\bxbl\b'):
        return 'open'
    # Change of directions swaps position, usually stays in same hold
    if _has(t, r'\bchange of direction\b'):
        return hold_in
    # hand throws generally leave in crossed
    if _has(t, r'\bthrow\b'):
        return 'crossed'
    # comb leaves in open
    if _has(t, r'ends with comb', r'comb on'):
        return 'open'
    # check leaves in whatever hold it states; default: inherit
    return hold_in


# ── parsing ─────────────────────────────────────────────────────────────────────

def parse_file(path: Path) -> list[Move]:
    m = re.search(r'Pair(\d+)_song(\d+)_take(\d+)', path.name)
    if not m:
        return []
    pair, song, take = int(m[1]), int(m[2]), int(m[3])
    level = LEVEL.get(pair, 'Unknown')

    rows = []
    with open(path, newline='', encoding='utf-8') as f:
        for row in csv.reader(f, delimiter='\t'):
            if len(row) < 9:
                continue
            if row[0].strip() != 'Together':
                continue
            desc = row[8].strip()
            if not desc:
                continue
            rows.append({'sec': float(row[3]), 'desc': desc})

    rows.sort(key=lambda r: r['sec'])

    moves = []
    hold = 'open'   # default starting hold
    for row in rows:
        raw = row['desc']
        hold_in = hold
        hold_out = infer_hold_out(raw, hold_in)

        moves.append(Move(
            raw=raw,
            move_type=normalise_move_type(raw),
            hold_in=hold_in,
            hold_out=hold_out,
            follower_turn=normalise_follower_turn(raw),
            leader_turn=normalise_leader_turn(raw),
            ending=normalise_ending(raw),
            pair=pair, song=song, take=take, level=level,
        ))
        hold = hold_out

    return moves


def load_all(annot_dir: Path) -> list[Move]:
    all_moves = []
    for path in sorted(annot_dir.glob('*.txt')):
        all_moves.extend(parse_file(path))
    return all_moves


# ── analysis ────────────────────────────────────────────────────────────────────

def analyse(moves: list[Move]):
    print(f"\n{'='*70}")
    print(f"  SALSA GRAMMAR ANALYSIS — CoMPAS3D  ({len(moves)} annotated phrases)")
    print(f"{'='*70}\n")

    # ── 1. Move type frequency by level ─────────────────────────────────────
    print("── 1. MOVE TYPE FREQUENCY ──────────────────────────────────────────\n")
    levels = ['Beginner', 'Intermediate', 'Professional']
    by_level = defaultdict(list)
    for m in moves:
        by_level[m.level].append(m)

    type_counts_total = Counter(m.move_type for m in moves)
    header = f"{'Move Type':<22}" + "".join(f"{l:>14}" for l in levels) + f"{'TOTAL':>10}"
    print(header)
    print('-' * len(header))
    for mtype, total in type_counts_total.most_common():
        row = f"{mtype:<22}"
        for l in levels:
            n = sum(1 for m in by_level[l] if m.move_type == mtype)
            pct = 100 * n / len(by_level[l]) if by_level[l] else 0
            row += f"{n:>7} ({pct:>4.1f}%)"
        row += f"{total:>10}"
        print(row)

    # ── 2. Hold state distribution ───────────────────────────────────────────
    print("\n── 2. HOLD STATE AT MOVE START ─────────────────────────────────────\n")
    hold_counts = Counter(m.hold_in for m in moves)
    for hold, n in hold_counts.most_common():
        print(f"  {hold:<12} {n:>4}  {'█' * (n // 3)}")

    # ── 3. Hold transitions ──────────────────────────────────────────────────
    print("\n── 3. HOLD TRANSITIONS (from → to, count ≥ 3) ─────────────────────\n")
    hold_trans = Counter((m.hold_in, m.hold_out) for m in moves)
    for (h_in, h_out), n in hold_trans.most_common():
        if n < 3:
            continue
        arrow = "→" if h_in != h_out else "↺"
        print(f"  {h_in:<10} {arrow} {h_out:<10} {n:>4}  {'█' * (n // 4)}")

    # ── 4. Move bigrams (what follows what) ─────────────────────────────────
    print("\n── 4. MOVE BIGRAMS — by sequence (count ≥ 3) ───────────────────────\n")
    # build per-sequence chains
    seqs: dict[tuple, list[Move]] = defaultdict(list)
    for m in moves:
        seqs[(m.pair, m.song, m.take)].append(m)

    bigrams: Counter = Counter()
    for seq_moves in seqs.values():
        for a, b in zip(seq_moves, seq_moves[1:]):
            bigrams[(a.move_type, b.move_type)] += 1

    print(f"  {'A → B':<40} {'count':>5}  {'Beginner':>9} {'Interm.':>8} {'Prof.':>7}")
    print('  ' + '-' * 76)
    # per-level bigram counts
    level_bigrams = defaultdict(Counter)
    for m in moves:
        seqs2: dict[tuple, list[Move]] = defaultdict(list)
    for m in moves:
        seqs2[(m.pair, m.song, m.take, m.level)].append(m)
    for key, seq_moves in seqs2.items():
        lvl = key[3]
        for a, b in zip(seq_moves, seq_moves[1:]):
            level_bigrams[lvl][(a.move_type, b.move_type)] += 1

    for (a, b), n in bigrams.most_common(40):
        if n < 3:
            break
        beg = level_bigrams['Beginner'][(a, b)]
        mid = level_bigrams['Intermediate'][(a, b)]
        pro = level_bigrams['Professional'][(a, b)]
        print(f"  {a:<20} → {b:<17} {n:>5}  {beg:>9} {mid:>8} {pro:>7}")

    # ── 5. What follows XBL? ─────────────────────────────────────────────────
    print("\n── 5. WHAT FOLLOWS XBL? ────────────────────────────────────────────\n")
    after_xbl = Counter()
    for seq_moves in seqs.values():
        for a, b in zip(seq_moves, seq_moves[1:]):
            if a.move_type == 'XBL':
                after_xbl[b.move_type] += 1
    for mtype, n in after_xbl.most_common(15):
        print(f"  {mtype:<25} {n:>4}  {'█' * (n // 2)}")

    # ── 6. What precedes XBL? ────────────────────────────────────────────────
    print("\n── 6. WHAT PRECEDES XBL? ───────────────────────────────────────────\n")
    before_xbl = Counter()
    for seq_moves in seqs.values():
        for a, b in zip(seq_moves, seq_moves[1:]):
            if b.move_type == 'XBL':
                before_xbl[a.move_type] += 1
    for mtype, n in before_xbl.most_common(15):
        print(f"  {mtype:<25} {n:>4}  {'█' * (n // 2)}")

    # ── 7. Turn chaining: consecutive turns ──────────────────────────────────
    print("\n── 7. TURN SEQUENCES (consecutive Turn/XBL-with-turn phrases) ──────\n")
    turn_moves = {'Turn', 'XBL'}
    turn_bigrams = Counter()
    for seq_moves in seqs.values():
        for a, b in zip(seq_moves, seq_moves[1:]):
            if a.move_type in turn_moves and b.move_type in turn_moves:
                tag_a = f"{a.move_type}({a.follower_turn},{a.leader_turn})"
                tag_b = f"{b.move_type}({b.follower_turn},{b.leader_turn})"
                turn_bigrams[(tag_a, tag_b)] += 1
    print(f"  {'A':45} → {'B':45} n")
    print('  ' + '-' * 100)
    for (a, b), n in turn_bigrams.most_common(20):
        print(f"  {a:<45}   {b:<45} {n}")

    # ── 8. Hold context per move type ────────────────────────────────────────
    print("\n── 8. HOLD CONTEXT PER MOVE TYPE ───────────────────────────────────\n")
    hold_by_type: dict[str, Counter] = defaultdict(Counter)
    for m in moves:
        hold_by_type[m.move_type][m.hold_in] += 1
    for mtype, total in type_counts_total.most_common(12):
        holds = hold_by_type[mtype]
        parts = ", ".join(f"{h}:{n}" for h, n in holds.most_common(4))
        print(f"  {mtype:<22} {parts}")

    # ── 9. Trigrams ───────────────────────────────────────────────────────────
    print("\n── 9. COMMON TRIGRAMS (count ≥ 3) ─────────────────────────────────\n")
    trigrams: Counter = Counter()
    for seq_moves in seqs.values():
        for a, b, c in zip(seq_moves, seq_moves[1:], seq_moves[2:]):
            trigrams[(a.move_type, b.move_type, c.move_type)] += 1
    for (a, b, c), n in trigrams.most_common(30):
        if n < 3:
            break
        print(f"  {a:<20} → {b:<20} → {c:<20} {n:>4}")

    # ── 10. Run lengths (how many Basic steps in a row) ───────────────────────
    print("\n── 10. CONSECUTIVE BASIC STEP RUNS ─────────────────────────────────\n")
    run_counter: Counter = Counter()
    for seq_moves in seqs.values():
        run = 0
        for m in seq_moves:
            if m.move_type in ('Basic', 'Side Basic', 'Cross-Back Basic', 'Back Basic'):
                run += 1
            else:
                if run > 0:
                    run_counter[run] += 1
                run = 0
        if run > 0:
            run_counter[run] += 1
    for run_len in sorted(run_counter):
        n = run_counter[run_len]
        print(f"  {run_len} basic(s) in a row: {n:>4}  {'█' * (n // 3)}")

    # ── 11. XBL turn variation breakdown ─────────────────────────────────────
    print("\n── 11. XBL TURN VARIATIONS ─────────────────────────────────────────\n")
    xbl_moves = [m for m in moves if m.move_type == 'XBL']
    xbl_turns = Counter((m.follower_turn, m.leader_turn) for m in xbl_moves)
    total_xbl = len(xbl_moves)
    print(f"  {'Follower turn':<16} {'Leader turn':<14} {'Count':>6}  {'%':>5}")
    print('  ' + '-' * 50)
    for (ft, lt), n in xbl_turns.most_common():
        print(f"  {ft:<16} {lt:<14} {n:>6}  {100*n/total_xbl:>4.1f}%")

    # ── 12. Ending decoration frequency ─────────────────────────────────────
    print("\n── 12. MOVE ENDINGS / DECORATIONS ─────────────────────────────────\n")
    end_counts = Counter(m.ending for m in moves if m.ending != 'none')
    for ending, n in end_counts.most_common():
        pct = 100 * n / len(moves)
        print(f"  {ending:<14} {n:>4}  ({pct:.1f}% of all phrases)")

    print()


# ── node/edge output for wiring diagram ────────────────────────────────────────

def export_graph(moves: list[Move], out_path: Path):
    """Export bigram graph as JSON for visualisation."""
    seqs: dict[tuple, list[Move]] = defaultdict(list)
    for m in moves:
        seqs[(m.pair, m.song, m.take)].append(m)

    edges: Counter = Counter()
    for seq_moves in seqs.values():
        for a, b in zip(seq_moves, seq_moves[1:]):
            edges[(a.move_type, b.move_type)] += 1

    # hold-tagged nodes (move_type × hold_in)
    hold_edges: Counter = Counter()
    for seq_moves in seqs.values():
        for a, b in zip(seq_moves, seq_moves[1:]):
            hold_edges[
                (f"{a.move_type}[{a.hold_in}]", f"{b.move_type}[{b.hold_in}]")
            ] += 1

    nodes = list({m.move_type for m in moves})
    edge_list = [{"from": a, "to": b, "weight": n}
                 for (a, b), n in edges.items() if n >= 2]

    hold_nodes = list({f"{m.move_type}[{m.hold_in}]" for m in moves})
    hold_edge_list = [{"from": a, "to": b, "weight": n}
                      for (a, b), n in hold_edges.items() if n >= 2]

    out_path.write_text(json.dumps({
        "nodes": nodes,
        "edges": edge_list,
        "hold_nodes": hold_nodes,
        "hold_edges": hold_edge_list,
    }, indent=2))
    print(f"Graph data written to {out_path}")


# ── main ────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    annot_dir = Path(__file__).parent / 'annotations'
    moves = load_all(annot_dir)
    analyse(moves)
    export_graph(moves, Path(__file__).parent / 'graph.json')
