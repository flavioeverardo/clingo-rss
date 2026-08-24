# clingo-rss Roadmap

## What this project is

`clingo-rss` computes a **representative solution space (RSS)**: instead of
enumerating all answer sets of a program, it picks a diverse subset of them
and arranges that subset on an `N x N` grid so that spatial position reflects
similarity — answer sets placed in neighboring cells should be close to each
other (a self-organizing-map-style layout), giving a 2D "map" of an
otherwise huge/unstructured solution space.

The mechanism:
1. Collect a pool of candidate answer sets (facts under `#show`).
2. Compute a pairwise **distance** between answer sets — currently the size
   of the symmetric difference of their atoms ([distance.py](clingo-rss/utilities/distance.py)).
3. Build an ASP encoding that assigns one answer set to each of the `N*N`
   grid cells (`cluster(Cell, AnswerSet)`, one-to-one) and optimizes the sum
   of distances between grid-adjacent cells ([representative.lp](clingo-rss/lp/representative.lp)).
4. Render the resulting grid as an image (colors test only, via matplotlib)
   and optionally stitch a sequence of iterations into a GIF ([gif_maker.py](gif_maker.py)).

Five solving **approaches** are exposed on the CLI (`--approach`):
`plain`, `grid-propagator`, `inc-edges`, `inc-squares`, `inc-single-edge` —
one single-shot encoding-only approach, one custom propagator, and three
multi-shot/incremental strategies that grow the grid piece by piece (BFS
over edges, growing sub-squares, and one edge at a time) so intermediate
states can be visualized as an animation.

## Current state

**Only `--colors-test` works end to end.** In that mode, `N*N` synthetic
"answer sets" are generated as RGB colors bilinearly interpolated between
four corner colors ([colors.py](clingo-rss/utilities/colors.py)), encoded as
`color(r|g|b, n).` fact lists, and then arranged on the grid. This is a
stand-in problem used to visually sanity-check the layout/optimization
strategies (see `results/` and the `gif_maker.py` output referenced by
filenames like `inc-single-edge_19x19`).

The path for **real user-supplied ASP programs** (no `--colors-test`) is
present in [`__init__.py`](clingo-rss/__init__.py) — it grounds/solves the
given files and collects their answer sets — but it does not currently run:
`add_distances`/`add_nodes`/`add_edges` are only assigned inside the
`if self.__colors_test:` branch and are referenced unconditionally
afterwards, so calling clingo-rss on a real instance raises `NameError`.
Fixing this is the single highest-leverage next step, since it's what turns
this from "a color-grid demo" back into "a general RSS tool."

### Other things noticed while reading the code

- **`main()`'s docstring describes a design that isn't implemented.** It
  talks about building XOR/parity constraints to stratify-sample the answer
  set space ("Build the XORs to generate the desired number of clusters").
  No XOR construction exists anywhere in the code — answer sets for real
  instances are just fully enumerated via `control.solve(yield_=True)`,
  which won't scale to large/intractable spaces. The `--approach` help text
  still advertises a `stratified` option that isn't in the actual
  `approaches` list either. This all points at an abandoned/parked idea
  (parity-constraint stratified sampling) worth deciding on explicitly:
  revive it, or clean up the stale docs/help text that reference it.
- **`--type` option is fully commented out** (`__parse_type`, its
  `options.add(...)` call) — looks like the start of a plan to support
  multiple RSS "problem types" beyond the current representative/grid
  layout, never finished.
- **`grid-propagator` currently does nothing.** `GridPropagator.init()`
  watches atoms over the `active_edge/4` signature, but no rule in either
  `.lp` file derives `active_edge/4` — it only appears in commented-out
  `#show` lines. So `init()` finds zero atoms, adds zero watches, and
  `propagate()` is never invoked by clingo at all. Confirmed by running it:
  `grid-propagator` produces the exact same `Optimization` value as `plain`
  on the same instance, because the same `#minimize` in `representative.lp`
  is doing 100% of the work in both cases — the propagator just registers
  and sits idle. (A `clusters`-undefined bug also lives in `propagate()`'s
  display branch, but since `propagate()` never runs, it's unreachable dead
  code rather than a live crash — verified with `--display-sp`.) Fixing
  this needs a rule that actually derives `active_edge(X,Y,A1,A2)` from
  `edge/2` + `cluster/2`, plus a look at whether the propagator's
  nogood-on-distance-increase logic is even the right pruning strategy —
  a design decision, not a quick patch.
- **`GridPropagator.check()`** just prints a banner; the optimality-tracking
  logic it references (`self.__optimal` vs. current best) is stubbed out.
- **`translate()` in `__init__.py`** has a dead `elif`/reference to a
  `CheckPropagator` class that doesn't exist in the codebase — leftover
  from an earlier iteration.
- **Distance/objective direction was clearly experimented with**:
  [representative.lp](clingo-rss/lp/representative.lp) has both a
  `#minimize` (active) and a commented-out `#maximize` of the same
  adjacent-cell distance sum. Minimizing gives the SOM-like "smooth map"
  behavior described above; maximizing would instead spread the most
  different solutions apart. Worth documenting which behavior is intended
  as the default and why, since it's currently only discoverable by reading
  the comment.
- **Unused/dead code**: `calculate_incremental_distances` and
  `calculate_weights` in [distance.py](clingo-rss/utilities/distance.py) are
  never called.
- **No dependency manifest** (no `requirements.txt`/`pyproject.toml`) even
  though the code depends on `clingo`, `numpy`, `matplotlib`, `imageio`, and
  `Pillow`. `clingo` isn't installed in the current shell environment, so
  the project can't currently be run as-is without first setting that up.
  `.pyc` caches show it has previously run under Python 3.9 and 3.11 —
  worth pinning a supported range once dependencies are declared.
- **No tests, no CI.** The only way to check the encodings/propagator work
  is to run `--colors-test` and eyeball the rendered grid.
- [gif_maker.py](gif_maker.py) hardcodes `gif_name`, an output path, and a
  macOS-only font path (`/System/Library/Fonts/Supplemental/Helvetica.ttc`)
  — it's a one-off script rather than a reusable CLI step.
- `size/1` is threaded into the generated ASP instance and `#show`n, but
  isn't actually used by any constraint in `representative.lp` or
  `inc-representative.lp` — currently informational only.
- The distance threshold `k` passed to `calculate_distances`/`build_instance`
  is hardcoded to `1` at every call site rather than exposed as a CLI
  option, despite the code being structured to support a threshold.

## Priorities

The immediate focus is **finishing the colors-test pipeline** (all 5
approaches solid, no dead/broken code paths) and building an **interactive
viewer** on top of it. Generalizing to arbitrary user-supplied ASP
encodings is deliberately deferred until the colors-test path — the only
one that's actually exercised today — is in good shape end to end.

### 1. Get the codebase runnable again — done
- [requirements.txt](requirements.txt) now pins `clingo`, `numpy`,
  `matplotlib`, `imageio`, `Pillow`. Verified in a fresh venv on Python
  3.12.2 / clingo 5.8.2.
- Ran `--colors-test` for all 5 approaches (`plain`, `grid-propagator`,
  `inc-edges`, `inc-squares`, `inc-single-edge`) at small grid sizes —
  all complete and write PNGs under `results/` without crashing. This is
  the baseline the rest of phase 2 builds on.
- Still open: confirm behavior against other clingo versions if this needs
  to run on Python 3.9/3.11 too (the old `.pyc` caches suggest it has, but
  nothing pins a range yet beyond `requirements.txt`'s `clingo>=5.8,<6`).

### 2. Complete the colors-test pipeline
- Decide what `grid-propagator` is actually for, then either implement it
  properly (derive `active_edge/4`, fix/redesign the nogood logic in
  `propagate()`, remove the dead `clusters` reference in its display
  branch) or drop the approach — right now it silently does nothing, which
  is worse than not having it, since a user could reasonably believe it's
  affecting the result.
- Finish or remove `GridPropagator.check()`'s stubbed optimality tracking.
- `inc-edges`, `inc-squares`, and `inc-single-edge` are the most novel part
  of the project (multi-shot grounding to build the grid progressively) but
  have a lot of near-duplicated loop/`brave` bookkeeping across the three.
  Extract the common incremental-grounding loop and let all three share it,
  parameterized by the node-expansion strategy (BFS by edge / by sub-square
  / single edge).
- Explicitly decide and document minimize-vs-maximize adjacent distance as
  a CLI-selectable objective rather than a commented-out alternative in
  `representative.lp`, since both are legitimate RSS layouts (smooth
  topology-preserving map vs. maximally spread-out diverse sample).
- Expose the distance threshold `k` as a CLI option instead of the
  hardcoded `1`.
- ~~Reconcile `register_options` help text with the actual `approaches`
  list~~ — done: `--help` now lists the real 5 approaches with a one-line
  description of each instead of the stale `simple-opt`/`stratified` text.
- Remove or finish the commented `--type` option and the dead
  `CheckPropagator` reference in `translate()`.
- Turn `gif_maker.py` into a proper output step of a run (e.g.
  `--approach inc-* --animate`) instead of a separate hardcoded script, and
  drop the macOS-only hardcoded font path.
- Once the above is stable, benchmark all 5 approaches against each other
  (`--benchmark` flag already exists to suppress output) across grid sizes:
  wall-clock time, grounding size, and final grid distance-sum quality —
  concrete evidence for which incremental strategy is worth keeping.

### 3. Interactive solution-space viewer
The core interaction: lay out the completed `N x N` grid graphically: click
a cell to select its answer set and display it; click a second cell and
show both answer sets side by side plus their **intersection** (shared
atoms) — the size/content of that overlap is a direct, readable signal of
how similar or diverse the two selected solutions are, in place of (or
alongside) the numeric distance already computed by
[distance.py](clingo-rss/utilities/distance.py).

Open questions to settle before building:
- **UI stack.** A Python-native GUI (e.g. a desktop toolkit, or a small
  local web app driven by the existing matplotlib/grid rendering) is the
  likely direction, but the concrete choice isn't pinned down yet — decide
  once the colors-test grid output is stable enough to build a UI on top
  of, since the viewer should work against whatever `cluster(Cell, Answer)`
  result any of the 5 approaches produces, not just the static PNGs.
  For the animated approaches (`inc-*`), the "grid" is really a sequence of
  states — worth deciding whether the viewer should show only the final
  layout or let the user scrub through iterations too.
- **Selection UX beyond two cells.** Two-cell compare (select A, select B,
  show A, B, and A∩B) is the concrete starting point. Whether to support
  comparing more than two, or highlighting a whole neighborhood's pairwise
  similarity at once, can wait until the two-cell version is validated.
- **What "answer set" rendering means outside colors-test.** For the color
  demo, an answer set is just an RGB swatch — trivial to display. Once real
  ASP instances are supported (see below), the viewer needs a generic way
  to render/diff arbitrary atom sets (e.g. a plain text list of atoms with
  the shared ones highlighted), not just colors.

### 4. Generalize to arbitrary ASP encodings (deferred)
- Fix the `add_distances`/`add_nodes`/`add_edges` `NameError` for
  non-colors-test runs so arbitrary ASP programs can be turned into an RSS
  grid, not just the synthetic color demo.
- Add a small real-world example encoding (e.g. graph coloring or N-queens)
  as a second smoke test alongside the color test.
- Either implement or remove the XOR/parity-based stratified sampling
  described in `main()`'s docstring — right now the docstring promises
  something the code doesn't do (full enumeration via `solve(yield_=True)`
  instead), which won't scale and will mislead the next reader if left as
  is.
- Remove the unused `calculate_incremental_distances`/`calculate_weights`
  helpers in `distance.py`, or wire them in if they end up needed here.
