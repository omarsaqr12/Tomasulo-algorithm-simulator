# Architecture review and verification gaps (2026-09-16)

Baseline `main`: `d6aaf801b61296f08823c17a4f1af3f5d30a2002`. Scope: only `omarsaqr12/Tomasulo-algorithm-simulator`.

## Calibration and architecture

This is an instructional Python/Tk application, not synthesizable RTL. Its behavioral sources of truth are `parse_instruction`, `simulate_cycle`, the station and register state, and the GUI handlers in `tomasulo_simulator.py`. Review requires known-answer instruction programs, RAW/WAR/WAW and control-flow checks, cycle-timing invariants, memory ordering, and a separate GUI smoke test. A screenshot or the report alone cannot validate execution semantics.

## Source-reviewed findings

- **Confirmed:** `setup_gui` registers a hover handler that calls `tree.set_tag_configure(...)`. Tkinter `ttk.Treeview` offers `tag_configure`, not `set_tag_configure`; hovering an item can raise `AttributeError`.
- **Confirmed:** issue assigns a reservation-station tag to any arithmetic/load destination, including R0; write-back can assign a nonzero result to `registers[0]`. This contradicts the README's hardwired-zero claim.
- **Confirmed:** `simulate_cycle` iterates through every completed station and writes all their results in the same cycle. A single-bus arbitration/throughput constraint is not implemented.
- **Strong concern:** load/store operations may execute out of program order and there is no explicit memory disambiguation or reorder buffer. Memory correctness of overlapping accesses is not established.
- **Strong concern:** taken branches and calls requeue original `Instruction` objects from `self.program`; repeated dynamic instances overwrite the same timing/completion fields. IPC and timing-table provenance on loops are therefore not reliable.
- **Confirmed:** arithmetic masks to 16 bits and returns unsigned display values; input memory values over 32767 are not signed-normalized even though the README claimed signed 16-bit values.
- **Documentation mismatch:** cycle scheduling is write→execute→issue, not issue→execute→write as the previous README claimed. `run_to_end` is synchronous and its maximum-cycle behavior does not clearly distinguish terminated from aborted runs.
- **Example mismatch:** `t4.txt` calls a negative/nonexistent PC; `t5.txt` branches to a negative PC; `t6.txt` contains memory-field comments incompatible with `map(int, line.split(':'))`.

## Changes and test evidence

The PR adds headless smoke tests for parsing and LOAD→ADD forwarding, plus `expectedFailure` tests that explicitly document the R0 and shared-CDB departures. An expected failure is **not** a repaired bug or a successful conformance test. The README and example guide now distinguish what exists from unverified or broken behavior. A GitHub Actions workflow executes the headless suite; its result must be checked separately. Syntax of the new test file was checked locally; full runtime execution of the original simulator was unavailable via the current connector-only checkout.

## File review coverage and blockers

Inspected the entire main Python source, README, example README, all seven input files, `.gitignore`, and repository tree. The existing LICENSE is a legal artifact, not independently audited. `femTomas-Design-Report.docx` could not be downloaded through the GitHub connector because it only returns UTF-8 text; its pages and figures were **not** visually reviewed. No code change to the large combined GUI/simulation module is claimed in this PR. The high-impact semantic issues require tested implementation fixes before advertising cycle accuracy or architectural correctness.

## Follow-up engineering work

Separate simulation state from Tk widgets; add dynamic instruction IDs, robust operand/register validation, control-flow bounds and loop tests, memory dependency checks, deterministic CDB arbitration, immutable R0 handling, GUI exception handling, and integration tests with independent golden traces. Only change cycle/IPC claims once those tests pass. Do not introduce speculative execution, superscalar issue, or an RTL port merely for portfolio breadth.
