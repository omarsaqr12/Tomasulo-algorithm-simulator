# femTomas: Tomasulo teaching simulator

A Python/Tkinter visualization of **in-order issue and potentially out-of-order execution** for a simplified 16-bit RISC-like instruction set. Step through reservation-station occupancy, operand tags, register renaming, memory state, and instruction timing. Developed as a computer-architecture coursework project; it is an educational model rather than a verified processor or a measured hardware implementation.

## What to inspect

The single application module, [`tomasulo_simulator.py`](tomasulo_simulator.py), defines `Instruction` (timing and operands), `ReservationStation` (operand/tag and latency state), and `TomasuloSimulator` (Tk GUI plus simulation scheduler). Its `simulate_cycle()` clears old stations, writes completed results, advances execution, and issues at most one instruction. Operand tags forward results to dependent stations; `BEQ`, `CALL`, and `RET` hold further issue while control flow resolves. The GUI shows reservation stations, registers, nonzero memory, and per-instruction timing.

This project is useful for *exploring* RAW dependencies, dynamic scheduling and branch behavior. The implementation's schedule and performance statistics have **not** been independently compared against a reference processor model. In particular, do not interpret its output as validated cycle-accurate hardware behavior.

## Run the GUI

Python 3 with Tkinter is required (on Debian/Ubuntu, install `python3-tk`). There are no other third-party Python packages.

```sh
git clone https://github.com/omarsaqr12/Tomasulo-algorithm-simulator.git
cd Tomasulo-algorithm-simulator
python3 tomasulo_simulator.py
```

Paste instructions into **Assembly Program**, and optional `address:value` lines into **Memory**. Choose a starting PC and positive reservation-station counts/latencies, click **Load Program**, then **Step** or **Run to End**. Avoid arbitrary code execution or unbounded programs: the UI becomes unresponsive while running to completion. The existing cycle safeguard is not a fully verified termination guarantee.

For a first demonstration, use the assembly and memory sections in [`examples/t1.txt`](examples/t1.txt) separately. The example files are **not** a direct file-import format; there is no GUI file loader. See [`examples/README.md`](examples/README.md) for cases and caveats.

### ISA syntax

| Form | Intent |
| --- | --- |
| `LOAD R1, 0(R2)` / `STORE R1, 0(R2)` | Load or store at `R2 + offset` |
| `ADD R3, R1, R2`, `SUB`, `NOR`, `MUL` | Two-register arithmetic or bitwise operation |
| `BEQ R1, R2, 2` | Conditional branch, using the implementation's `instruction_PC + offset` target |
| `CALL 5` / `RET` | Absolute call target, save return PC to R1, return via R1 |

`CALL` accepts an integer in the signed seven-bit range -64..63 but not every such target refers to a valid program instruction. Register indices, memory addresses, and branch targets are not comprehensively validated. Arithmetic operations mask results to 16 bits; displayed results are **not consistently signed-normalized**. The README does not imply a formally specified ISA.

## Verification and known limitations

Run the new headless checks using `python3 -m unittest discover -s tests -v`. They cover instruction parsing and a load-to-add dependency without opening a display. Two documented architectural-invariant checks are marked `expectedFailure`: writes to R0 can change its value, and more than one completed result can write in a cycle despite the README's earlier single-CDB implication. Expected failures are **known bugs, not passes**. See [`docs/AUDIT.md`](docs/AUDIT.md) for their evidence and other risks.

Additional unverified areas include load/store ordering, loops/repeated dynamic instructions (program instruction objects are reused), branch/call/return edge cases, invalid register names, accurate timing/IPC accounting, memory bounds and GUI interactions. The mouse-hover callback currently invokes a nonexistent Tkinter `Treeview.set_tag_configure()` method, which may raise on hover. There is no claim of complete ISA conformance, superscalar issue, speculative execution, hardware synthesis, or benchmarked speedup.

## Repository map and provenance

- [`tomasulo_simulator.py`](tomasulo_simulator.py) — full GUI and simulation implementation.
- [`tests/test_headless.py`](tests/test_headless.py) — headless smoke and documented known-gap tests.
- [`examples/`](examples/) — coursework-era assembly/memory scenarios; some are intentionally invalid or contain comments unsupported by the input parser.
- [`femTomas-Design-Report.docx`](femTomas-Design-Report.docx) — original design report (historical artifact, not independent validation).

Contributions beyond the repository's visible authorship history cannot be reliably separated among collaborators from the available source. Code is distributed under the existing [MIT License](LICENSE); check the report's reuse terms separately.
