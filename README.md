# femTomas — Out-of-Order Processor Simulator

> A cycle-accurate simulator of the **Tomasulo algorithm** for a 16-bit RISC processor, with an interactive GUI for visualizing out-of-order execution cycle by cycle.

<p>
  <img alt="Python" src="https://img.shields.io/badge/Python-3.8%2B-blue?logo=python&logoColor=white">
  <img alt="GUI" src="https://img.shields.io/badge/GUI-Tkinter-orange">
  <img alt="Dependencies" src="https://img.shields.io/badge/dependencies-none-brightgreen">
  <img alt="License" src="https://img.shields.io/badge/license-MIT-green">
</p>

---

## Overview

**femTomas** models how a modern superscalar CPU executes instructions **out of order** while preserving correct program semantics. It implements [Tomasulo's algorithm](https://en.wikipedia.org/wiki/Tomasulo%27s_algorithm) — the same dynamic-scheduling technique used in real processors — including **reservation stations**, **register renaming**, and a **common data bus (CDB)** for result forwarding.

The simulator runs a small RISC assembly program and lets you **step through it one cycle at a time** (or run to completion), watching reservation stations fill, dependencies resolve, and results broadcast on the CDB. It then reports performance metrics such as IPC and branch-misprediction rate.

Built as a deep-dive into computer architecture (CSCE 3301 – Computer Architecture).

## What it demonstrates

- **Dynamic scheduling** with Tomasulo's algorithm (out-of-order issue, execute, and write-back)
- **Register renaming** via per-register status tags (`Qi`) + reservation-station tags, eliminating WAR and WAW hazards
- **Dependency tracking** (RAW hazards) through `Qj`/`Qk` operand tags and CDB result forwarding
- **Cycle-accurate timing** of each instruction's issue / execute / write stages
- Configurable microarchitecture (functional-unit latencies and reservation-station counts)
- A clear, didactic **GUI** that makes the internal CPU state observable

## Features

- **Cycle-by-cycle stepping** or **run-to-completion** execution
- Live views of:
  - Reservation Stations (busy state, operands, tags, status, cycles remaining)
  - Register file (values + `Qi` rename tags)
  - Memory (non-zero locations)
  - Per-instruction timing table (Issue / Start Exec / End Exec / Write)
- **Configurable hardware**:
  - Number of reservation stations per instruction class
  - Execution latency per functional unit
- **Performance metrics**: total cycles, IPC (instructions per cycle), and branch-misprediction percentage
- **Non-speculative** execution with an *Always-Not-Taken* branch policy (branches resolve before dependent control flow proceeds)
- Zero external dependencies — pure Python standard library + Tkinter

## Instruction Set

A simplified 16-bit RISC ISA with 8 registers (`R0`–`R7`, where `R0` is hardwired to 0).

| Category             | Instruction            | Description                         |
| -------------------- | ---------------------- | ----------------------------------- |
| **Load/Store**       | `LOAD rA, offset(rB)`  | Load word from memory into `rA`.    |
|                      | `STORE rA, offset(rB)` | Store `rA` value into memory.       |
| **Conditional**      | `BEQ rA, rB, offset`   | Branch if `rA == rB`.               |
| **Call/Return**      | `CALL label`           | Store `PC+1` in `R1` and jump to label. |
|                      | `RET`                  | Return to address in `R1`.          |
| **Arithmetic/Logic** | `ADD rA, rB, rC`       | `rA = rB + rC`                      |
|                      | `SUB rA, rB, rC`       | `rA = rB - rC`                      |
|                      | `NOR rA, rB, rC`       | `rA = ~(rB \| rC)`                  |
|                      | `MUL rA, rB, rC`       | `rA = (rB × rC) mod 2¹⁶`            |

## Getting Started

### Prerequisites

- Python **3.8+**
- Tkinter (bundled with standard Python on Windows/macOS; on Debian/Ubuntu install via `sudo apt install python3-tk`)

### Run

```bash
git clone https://github.com/omarsaqr12/Tomasulo-algorithm-simulator.git
cd Tomasulo-algorithm-simulator
python tomasulo_simulator.py
```

Then, in the GUI:

1. Enter (or paste) an assembly program — one instruction per line.
2. Set the starting PC.
3. Optionally initialize memory (`address:value`, one per line).
4. Configure reservation-station counts and execution latencies.
5. Click **Load Program**, then **Step** through cycle by cycle or **Run to End**.

Sample programs live in [`examples/`](examples/) — see [`examples/README.md`](examples/README.md) for the input format.

## How it works

Each simulated cycle advances four pipeline activities in Tomasulo order:

1. **Issue** — the next in-order instruction is placed into a free reservation station of the matching type. Source operands are read either as values (if ready) or as **tags** pointing at the producing station; the destination register is renamed to this station.
2. **Execute** — a station begins executing once both operands are available, counting down its functional-unit latency. Independent instructions execute **out of order**.
3. **Write** — on completion, the result is broadcast on the **common data bus**, updating the register file and any waiting reservation stations in the same cycle.
4. **Commit of control flow** — branches/`CALL`/`RET` resolve at write-back; mispredictions (under the Always-Not-Taken policy) redirect the instruction stream.

This design naturally removes false (WAR/WAW) dependencies through renaming while honoring true (RAW) dependencies through tag-based forwarding.

### Default microarchitecture

| Unit            | Reservation Stations | Execution Latency (cycles) |
| --------------- | :------------------: | :------------------------: |
| Load            | 2                    | 6 (2 address + 4 memory)   |
| Store           | 2                    | 6 (2 address + 4 memory)   |
| Branch (`BEQ`)  | 2                    | 1                          |
| Call/Return     | 1                    | 1                          |
| Add/Sub         | 4                    | 2                          |
| NOR             | 2                    | 1                          |
| Multiply        | 2                    | 10                         |

All values are editable in the GUI before loading a program.

## Project Structure

```
.
├── tomasulo_simulator.py        # Simulator core + Tkinter GUI
├── examples/                    # Sample assembly programs & memory inputs
│   └── README.md                # Input-format guide
├── femTomas-Design-Report.docx  # Detailed design report
└── README.md
```

## Assumptions & Limitations

- **Non-speculative**: a branch must resolve before dependent control flow continues.
- **Always-Not-Taken** branch prediction (mispredictions are counted and reported).
- Memory and registers are **16-bit signed integers**.
- `R0` is hardwired to **0**.
- **Single-issue** front end (one instruction issued per cycle).

## License

Released under the [MIT License](LICENSE).
