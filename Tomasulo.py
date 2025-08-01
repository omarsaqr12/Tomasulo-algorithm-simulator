import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import re
from collections import defaultdict, deque

# Basic color theme
COLORS = {
    'bg': '#f0f0f0',
    'fg': '#333333',
    'accent': '#007acc'
}

# Instruction class to represent each instruction
class Instruction:
    def __init__(self, opcode, operands, pc):
        self.opcode = opcode
        self.operands = operands  # List of operands: [dest, src1, src2] or similar
        self.pc = pc
        self.issue_cycle = None
        self.start_exec_cycle = None
        self.end_exec_cycle = None
        self.write_cycle = None
        self.completed = False

    def __str__(self):
        return f"PC{self.pc}: {self.opcode} {' '.join(map(str, self.operands))}"

# Reservation Station class
class ReservationStation:
    def __init__(self, name, op_type, exec_cycles):
        self.name = name
        self.op_type = op_type
        self.exec_cycles = exec_cycles
        self.busy = False
        self.instruction = None
        self.vj = None
        self.vk = None
        self.qj = None
        self.qk = None
        self.a = None  # Offset or address
        self.cycles_left = 0
        self.executing = False

    def clear(self):
        self.busy = False
        self.instruction = None
        self.vj = self.vk = self.qj = self.qk = self.a = None
        self.cycles_left = 0
        self.executing = False

    def __str__(self):
        if not self.busy:
            return f"{self.name}: Free"
        instr = self.instruction
        status = "Exec" if self.executing else "Wait"
        return (f"{self.name}: {instr.opcode} "
                f"Vj={self.vj if self.vj is not None else self.qj or '-'} "
                f"Vk={self.vk if self.vk is not None else self.qk or '-'} "
                f"A={self.a or '-'} "
                f"{status} "
                f"CyclesLeft={self.cycles_left}")

# Basic Simulator class
class TomasuloSimulator:
    def __init__(self, root):
        self.root = root
        self.root.title("Tomasulo Simulator - Basic Version")
        
        # Basic state
        self.cycle = 1
        self.program = []
        self.current_pc = 0
        self.registers = [0] * 8  # R0 to R7, R0 is always 0
        self.register_status = [None] * 8  # Qi field
        self.memory = defaultdict(int)  # 16-bit addressable memory
        self.instructions = deque()  # Instruction queue
        
        # Initialize basic reservation stations
        self.res_stations = {
            'LOAD': [ReservationStation(f"LOAD{i}", 'LOAD', 5) for i in range(1, 3)],
            'STORE': [ReservationStation(f"STORE{i}", 'STORE', 5) for i in range(1, 3)],
            'ADD_SUB': [ReservationStation(f"ADD{i}", 'ADD_SUB', 2) for i in range(1, 5)],
            'MUL': [ReservationStation(f"MUL{i}", 'MUL', 10) for i in range(1, 3)],
            'BEQ': [ReservationStation(f"BEQ{i}", 'BEQ', 1) for i in range(1, 3)],
        }
        
        self.op_to_rs = {
            'LOAD': 'LOAD', 'STORE': 'STORE', 'BEQ': 'BEQ',
            'ADD': 'ADD_SUB', 'SUB': 'ADD_SUB',
            'MUL': 'MUL'
        }
        
        self.setup_basic_gui()

    def setup_basic_gui(self):
        # Configure root window
        self.root.configure(bg=COLORS['bg'])
        
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Input frame
        input_frame = ttk.LabelFrame(main_frame, text="Program Input")
        input_frame.pack(fill=tk.X, expand=False, pady=10)
        
        ttk.Label(input_frame, text="Assembly Program:").pack(anchor=tk.W)
        self.program_text = scrolledtext.ScrolledText(input_frame, width=60, height=8)
        self.program_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="Load Program", command=self.load_program).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Step", command=self.step).pack(side=tk.LEFT, padx=5)
        
        # Status
        self.status_label = ttk.Label(main_frame, text="Ready to load program")
        self.status_label.pack(pady=10)

    def parse_instruction(self, line, pc):
        """Basic instruction parsing - to be expanded"""
        parts = re.split(r'[,\s()]+', line.strip().upper())
        parts = [p for p in parts if p]
        opcode = parts[0]
        
        if opcode in ('ADD', 'SUB', 'MUL'):
            dest, src1, src2 = parts[1], parts[2], parts[3]
            return Instruction(opcode, [dest, src1, src2], pc)
        elif opcode == 'LOAD':
            dest, offset, src = parts[1], int(parts[2]), parts[3]
            return Instruction(opcode, [dest, src, offset], pc)
        else:
            # Placeholder for other instructions
            return Instruction(opcode, parts[1:], pc)

    def load_program(self):
        """Load and parse the program"""
        try:
            self.program.clear()
            self.instructions.clear()
            
            program_input = self.program_text.get("1.0", tk.END).strip().split('\n')
            pc = 0
            for line in program_input:
                if line.strip():
                    instr = self.parse_instruction(line, pc)
                    self.program.append(instr)
                    self.instructions.append(instr)
                    pc += 1
            
            self.status_label.configure(text=f"Loaded {len(self.program)} instructions")
            messagebox.showinfo("Success", "Program loaded successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load program: {e}")

    def step(self):
        """Basic step function - placeholder for now"""
        self.cycle += 1
        self.status_label.configure(text=f"Cycle: {self.cycle} (Step function not implemented yet)")

if __name__ == "__main__":
    root = tk.Tk()
    app = TomasuloSimulator(root)
    root.mainloop()