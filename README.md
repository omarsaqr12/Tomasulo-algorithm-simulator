# femTomas – Tomasulo Algorithm Simulator

## 📌 Overview
**femTomas** is a graphical simulator for the **Tomasulo algorithm** designed for a simplified 16-bit RISC processor without speculation.  
It allows users to simulate program execution, monitor reservation stations, register files, and memory in real-time, and evaluate performance metrics.

This project is based on **CSCE 3301 – Computer Architecture (Spring 2025) Project 2** specifications.

---

## ✨ Features
- **GUI-based simulator** built with Python and Tkinter.
- Supports **cycle-by-cycle execution** or **full program run**.
- Displays:
  - Reservation Stations status
  - Register file values
  - Memory (non-zero locations)
  - Instruction timing table
- **Configurable hardware organization**:
  - Set number of Reservation Stations per instruction type.
  - Set execution cycles per functional unit.
- Supports **all required instructions**:
  - Load/Store (`LOAD`, `STORE`)
  - Conditional Branch (`BEQ`)
  - Call/Return (`CALL`, `RET`)
  - Arithmetic & Logic (`ADD`, `SUB`, `NOR`, `MUL`)
- Performance metrics:
  - Total Cycles
  - IPC (Instructions Per Cycle)
  - Branch Misprediction Percentage
- **Always Not Taken** branch predictor (non-speculative).

---

## 🖥️ Instruction Set
| Category            | Instruction                | Description |
|---------------------|----------------------------|-------------|
| **Load/Store**      | `LOAD rA, offset(rB)`       | Load word from memory into rA. |
|                     | `STORE rA, offset(rB)`      | Store rA value into memory. |
| **Conditional**     | `BEQ rA, rB, offset`        | Branch if rA == rB. |
| **Call/Return**     | `CALL label`                | Store PC+1 in R1 and jump to label. |
|                     | `RET`                       | Return to address in R1. |
| **Arithmetic/Logic**| `ADD rA, rB, rC`            | rA = rB + rC |
|                     | `SUB rA, rB, rC`            | rA = rB - rC |
|                     | `NOR rA, rB, rC`            | rA = ~(rB \| rC) |
|                     | `MUL rA, rB, rC`            | rA = (rB × rC) mod 2¹⁶ |

---

## 📂 Project Structure
```
.
├── Tomasulo.py              # Main simulator source code
├── Project2Description.pdf  # Project specification document
├── README.md                # This file
└── tests/                   # Example assembly programs & data
```

---

## 🚀 Installation & Running
### Prerequisites
- Python **3.8+**
- Tkinter (comes pre-installed with most Python distributions)

### Steps
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/femTomas.git
   cd femTomas
   ```
2. Run the simulator:
   ```bash
   python Tomasulo.py
   ```
3. Use the GUI to:
   - Enter the assembly program.
   - Specify starting PC.
   - Initialize memory values.
   - Configure Reservation Stations & execution cycles.
   - Step through or run to completion.

---

## 📊 Example Output
At the end of simulation, the program shows:
- **Summary** tab:
  - Total Cycles
  - Instructions Completed
  - IPC
  - Branch statistics
- **Instruction Timing** tab:
  - Issue cycle
  - Execution start & end cycles
  - Write cycle

---

## 🛠️ Bonus Features Implemented
- Full **educational GUI** with step-by-step monitoring.
- Customizable hardware organization.

---

## 📌 Limitations & Assumptions
- **No speculation** (branch execution waits until branch resolution).
- **Always Not Taken** branch prediction.
- Memory and registers are **16-bit signed integers**.
- R0 is always **0** and cannot be changed.
- Single-issue pipeline.

---

## 👨‍💻 Authors
- *Your Name* – *Your Student ID*  
- *Partner Name* – *Partner Student ID*

---

## 📜 License
This project is for educational purposes as part of **CSCE 3301 – Computer Architecture**.
