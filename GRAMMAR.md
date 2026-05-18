# A Grammar of Salsa — Empirical Analysis of CoMPAS3D

> Analysis of 1,053 annotated 8-count phrases across 19 sequences (7 beginner,
> 8 intermediate, 4 professional).  All statistics are from the `analyze.py`
> output unless noted.

---

## 1  The Vocabulary

The dataset has ~31 named move types.  After normalisation, they reduce to a
small working vocabulary:

| Symbol | Move | Frequency | Notes |
|--------|------|-----------|-------|
| **B**  | Basic step (any flavour) | 226 (21%) | Also Side Basic, Cross-Back, Back Basic |
| **X**  | XBL (Cross Body Lead)    | 431 (41%) | The dominant "word" |
| **T**  | Isolated Turn            | 135 (13%) | Turns not attached to an XBL |
| **Cp** | Copa                     |  33 ( 3%) | Pivot → redirect |
| **W**  | Walks Around             |  14 ( 1%) | Circular walking |
| **Nt** | Natural Top              |   9 ( 1%) | Continuous circular |
| **Sq** | Suzy Q                   |  11 ( 1%) | Footwork pattern |
| **Ht** | Hand Throw               |  45 ( 4%) | One- or two-hand throw |

*Decorators* (suffixes that modify the preceding move):

| Symbol | Decorator | Freq |
|--------|-----------|------|
| **·c** | Comb      | 98   |
| **·k** | Check     | 76   |
| **·t** | (into) Throw | 77 |
| **·b** | Break     | 35   |
| **·d** | Drop      | 16   |

---

## 2  Hold States as Types

The most important hidden variable in salsa is *what the hands are doing*.
The hold is literally the "channel" through which the leader communicates with
the follower.  There are 7 distinguishable states in the data:

```
open     — leader's R hand holds follower's L hand (standard open position)
closed   — standard ballroom: leader's R hand on follower's back
crossed  — hands crossed (leader R→follower R, or both)
hl_left  — follower's left arm in hammerlock behind back
hl_right — follower's right arm in hammerlock
embrace  — both arms held, follower facing away ("Titanic" / shadow frame)
shadow   — side-by-side, matching orientation
```

**Distribution:** open (59%) >> crossed (28%) > closed (5%) > hl_left (5%)

The hold is a *state machine*.  The most common transitions:

```
open  ←→  crossed   (90 each way — the dominant toggle)
open   →  closed    (26)   closed  →  open   (25)
open   →  hl_left   (19)   hl_left →  open   (14)
open   →  embrace   (10)   embrace →  open   (10)
```

This is the **type system** of salsa: moves are typed by their
`hold_in → hold_out` signature, and you can only chain moves whose types
compose.

---

## 3  Grammar Rules

### Rule 1 — The Phrase Unit is the 8-Count

Every annotation is one 8-count musical phrase (~2.5 s at ~95 BPM).
The *sentence* of salsa is a sequence of 8-counts.

### Rule 2 — Level determines the "default word"

```
Beginner:      B B B B … (51% basics; XBL only 10%)
Intermediate:  X X X X … (64% XBL; basics almost absent)
Professional:  X X X X … (52% XBL; more Copa/Natural Top/Nt variety)
```

Beginners fill the space between moves with Basic steps.
Intermediate and professional dancers chain XBL continuously — Basic is a
*rest*, not the default.

### Rule 3 — XBL chains dominate above beginner level

The most common bigram at every non-beginner level is **X → X** (227 instances,
53% of all XBL transitions).  The most common trigram overall is
**X → X → X** (133 instances).

This is the key structural insight: **intermediate/professional salsa is
essentially a sequence of XBL variants** punctuated by Copa, Natural Top,
or a brief Basic reset.

### Rule 4 — Basic step is the "rest" or "reset"

When a Basic appears it usually runs in groups (106 instances of B→B) and
precedes either another phrase or an XBL.

```
Most common Basic transitions:
  B → B   (106)   — holding pattern, filling musical space
  B → X   ( 50)   — launching into XBL
  B → T   ( 40)   — launching into a turn (beginner context)
```

Long runs of basics (≥3) occur almost exclusively in beginner sequences.

### Rule 5 — Turns alternate direction

Looking at consecutive turn/XBL-with-turn pairs:

```
XBL(follower:left)  → XBL(follower:right)   32   ← alternation
XBL(follower:right) → XBL(follower:left)    23   ← alternation
XBL(follower:right, leader:right) → XBL(follower:left) 21
```

**Turns strongly tend to alternate direction.**  Inside turn (left for follower)
followed by outside turn (right) is the most natural pairing.  This mirrors the
conservation of angular momentum in social dance — spinning the follower one way
then immediately the other "unwinds" the connection.

Consecutive same-direction turns also occur (XBL left→left: 9, right→right: 11)
but these are less common and typically resolve with a hand change.

### Rule 6 — Comb and Copa are "parenthetical clauses"

```
X → Comb → X   (29 instances)   ← most common "comb sandwich"
X → Copa → X   (17 instances)
X → T → X      (13 instances)
```

Comb and Copa act as *sub-phrases* — they begin and end in XBL context.
They function syntactically like parentheses: `X (·c X)* X`.

Copa is also frequently the *resolution* of a prior XBL:
`X → Cp → X` reads as "XBL sets up the copa pivot, which launches the next XBL."

### Rule 7 — Hand Throw opens a crossed-hold sub-phrase

```
T  → Ht  ( 9)   — turn leads into throw
X  → Ht  (14)   — XBL leads into throw
Ht → X   (16)   — throw resolves via XBL
Ht → Ht  (12)   — throws can chain (double hand throw)
Ht → T   ( 6)   — throw followed by turn
```

Hand throws transition the hold from open→crossed (or crossed→crossed).  Once
in crossed hold the phrase tends to resolve either via a turned XBL or another
throw, before returning to open.

### Rule 8 — XBL hold context

```
XBL variants by hold entering:
  open hold:    268  (62%)
  crossed hold:  91  (21%)
  closed hold:   27  ( 6%)
  hl_left:       21  ( 5%)
```

XBL is possible in *any* hold, but it preferentially operates in open.
XBL in crossed hold typically signals a "resolution" move that exits crossed
and returns to open.

### Rule 9 — Walks Around and Natural Top as extended phrases

Walks Around always resolves back to XBL (11/14 times).
Natural Top chains with itself (4 instances) before resolving to XBL (5).
Both function as "extended elaborations" that consume multiple 8-counts before
returning to the main XBL chain.

---

## 4  Simplified Grammar (BNF)

```
sequence  ::= phrase+
phrase    ::= basic_phrase | xbl_phrase | turn_phrase | elaboration

basic_phrase ::= B+                     -- rest / fill

xbl_phrase   ::= X[hold][turns][·dec]*  -- core unit
               | xbl_phrase xbl_phrase  -- chaining

turn_phrase  ::= T[dir][who] T[dir][who]*  -- isolated turns, usually beginner

elaboration  ::= Cp xbl_phrase          -- copa → XBL resolution
               | Nt+  xbl_phrase        -- natural top loop → XBL
               | W    xbl_phrase        -- walks around → XBL
               | Ht+  (T | xbl_phrase)  -- throw(s) → resolve

dec ::= ·c | ·k | ·t | ·b | ·d         -- decorator suffixes

hold  ::= [open | crossed | closed | hl_left | hl_right | embrace | shadow]
turns ::= (follower: none|L|R|LL|RR) × (leader: none|L|R)
```

The **canonical salsa sentence** at intermediate level is thus:
```
[B B] X[open,none,none] → X[open,L,none]·c → X[open,R,R] → Cp → X[open,none,none] → …
```
("Two basics to settle, then: plain XBL, XBL with follower inside turn ending
with comb, XBL with both turning right, copa, plain XBL, …")

---

## 5  Wiring Diagram Notation

This is where category theory gives us a clean language.

### 5.1  The Category **Salsa**

Define a category **Salsa** where:

- **Objects** are hold states: `{open, closed, crossed, hl_left, hl_right, embrace, shadow}`
- **Morphisms** are dance moves: a move `M : A → B` takes the couple from hold
  state `A` to hold state `B`
- **Composition** is temporal chaining: if `A →[M1]→ B →[M2]→ C`, then
  `A →[M2∘M1]→ C`
- **Identity** morphism at each object is "stand still / rest in hold A"

Examples of typed moves:

```
Basic      : H   → H      (hold-preserving for any H)
XBL        : open → open
XBL·throw  : open → crossed
XBL(cxd)   : crossed → open
RightHandThrow : open → crossed
LeftHandThrow  : open → crossed
CopaResolve    : crossed → open   (or open → open)
NaturalTop : open → open
HammerLock : open → hl_left
```

A *phrase* is a composable sequence of morphisms — a path through the object
(hold-state) graph.

### 5.2  String Diagram Notation

In a string diagram, objects are **wires** and morphisms are **boxes**.
Time flows left to right.  Wires flow horizontally between boxes.

Wire colour codes the hold state:

```
━━━━━━━━━━  open     (white / thin)
══════════  crossed  (orange / double)
──────────  closed   (blue / dashed)
┄┄┄┄┄┄┄┄┄  hl_left  (purple / dotted)
```

A move is a labelled box; its left wire is `hold_in`, right wire is `hold_out`:

```
         ┌─────┐         ┌───────┐         ┌─────┐
━━━━━━━━━┥  B  ┝━━━━━━━━━┥  X   ┝━━━━━━━━━┥  X  ┝━━━━━━━
         └─────┘         └───────┘         └─────┘
  open           open             open             open
```

A hold-changing move:

```
         ┌──────────┐              ┌──────────┐
━━━━━━━━━┥ Ht(R)    ┝══════════════┥ X(cxd)  ┝━━━━━━━━━
         └──────────┘              └──────────┘
  open               crossed                    open
```
("Right hand throw lands in crossed hold; XBL with crossed hold resolves back
to open.")

### 5.3  Two-Wire Notation (Monoidal Category)

Each dancer has two hands.  A richer notation uses a **symmetric monoidal
category** where the tensor product `L ⊗ F` models the couple simultaneously.
Each wire represents one hand-connection:

```
  Leader: ─── LH ──────────────────────────────────
                     ┌──────────────┐
                     │  XBL·inside  │
  ─── RH ──────────  │  turn for F  │  ──── RH ────
                     └──────────────┘
  Follower: ─ LF ──────────────────────────────────
```

This lets you represent the *crossing* of hands explicitly:

```
  open hold:    L_R ─────────── F_L      (one wire: R→L)
  crossed hold: L_R ──╲╱─────── F_R      (wires cross)
  double hold:  L_R ─────────── F_L      (two wires)
                L_L ─────────── F_R
```

### 5.4  Compact Linear Notation

For quick written notation, use:

```
[hold] MoveName(follower_turn, leader_turn) [→hold]
```

Omit unchanged holds.  Use `f` = follower, `l` = leader, `R/L` = right/left
turn, `RR` = double-right.

Example — the most common intermediate pattern:

```
open: B  ·  X(−,−)  ·  X(L,−)·c  ·  X(R,R)  →cxd  ·  X(−,−)  →open  ·  Cp  ·  X(−,−)
```

Read: "Basic, plain XBL, inside-turn XBL with comb, double-right XBL into
crossed, plain XBL resolving from crossed, copa, plain XBL."

### 5.5  Common Sub-Phrases ("Idioms")

These are the most frequent "compound words":

```
Idiom name              Notation                           Count
─────────────────────────────────────────────────────────────────
Plain chain             X(−,−) · X(−,−)                     93
Inside-outside pair     X(L,−) · X(R,−)  or reverse         55
Comb sandwich           X · X(−,−)·c · X                    29
Copa wrap               X(−,−) · Cp · X(−,−)                17
Throw-resolve           X · Ht →cxd · X(cxd) →open         ~20
Both-turn               X(R,R) · X(L,−)                     21
Shadow-check            X(L,−)·k · X(−,−)                    8
```

---

## 6  What This Means for a Beginner

The empirical grammar suggests a clear learning progression:

**Stage 1 — Master the 8-count**
The entire structure rests on the musical phrase.  Every move is exactly one
8-count.  Feel the "1" of each phrase.

**Stage 2 — Learn the two default states**
Open hold and crossed hold are 87% of all positions.  Know how to enter and
exit each.

**Stage 3 — Understand XBL as the "verb"**
The XBL is not one move — it is a *family* parameterised by
(follower_turn × leader_turn × hold).  The plain XBL `X(−,−)` is the
identity morphism of open hold — it moves the follower across but returns
to the same state.  Every other XBL variant is a decorated version of this.

**Stage 4 — Learn the turn-alternation rule**
After an inside turn, offer an outside turn.  After a right, offer a left.
This is not a strict rule but it is by far the most common pattern in the data
(32 inside→outside vs. 9 inside→inside at the top level).

**Stage 5 — Learn the Comb and Copa as "punctuation"**
`X·c` (XBL ending with a comb) is the salsa equivalent of a comma — it keeps
the flow going and signals another XBL is coming.
Copa is a full stop or clause boundary — it resets the phrase and the couple
often faces a new direction afterward.

**Stage 6 — Chain XBLs without filling with basics**
The biggest qualitative difference between beginner and intermediate is this:
intermediates replace every `B B B B` with `X X X X`.  The Basic is not
wrong — it's just relatively empty space.

---

## 7  Summary Graph

The empirical transition graph (→ `graph.json`) has the following major edges
(weight ≥ 10):

```
        ┌─────────────────────────────────────────┐
        │                 (227)                   │
        ▼                                         │
      ┌───┐  →Comb(36)→  ┌──────┐  →XBL(32)→    │
 ───→ │XBL│              │ Comb │                 │
      └───┘  ←Comb(32)←  └──────┘                 │
        │                                         │
        ├──→ Turn (42) ──→ Basic (46) ─────────────┘
        │                                ▲
        ├──→ Copa  (20) ──────────────────┘
        │
        ├──→ Basic (28) ──→ Basic (106) ──┐
        │         ▲                       │
        └─────────┴──── (50) ─────────────┘
```

The XBL node is the "attractor" of the grammar — almost every path leads back
to it.
