import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import re
from collections import defaultdict, deque

# Complete color theme
COLORS = {
    'bg': '#f0f0f0',
    'fg': '#333333',
    'accent': '#007acc',
    'accent_hover': '#005c99',
    'success': '#28a745',
    'success_hover': '#218838',
    'warning': '#ffc107',
    'error': '#dc3545',
    'header_bg': '#e9ecef',
    'alternate_row': '#f8f9fa'
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
        self.wrote_result = False
        self.just_wrote = False

    def clear(self):
        self.busy = False
        self.instruction = None
        self.vj = self.vk = self.qj = self.qk = self.a = None
        self.cycles_left = 0
        self.executing = False
        self.wrote_result = False
        self.just_wrote = False

    def __str__(self):
        if not self.busy:
            return f"{self.name}: Free"
        instr = self.instruction
        status = "Wrote" if self.wrote_result else ("Exec" if self.executing else "Wait")
        return (f"{self.name}: {instr.opcode} "
                f"Vj={self.vj if self.vj is not None else self.qj or '-'} "
                f"Vk={self.vk if self.vk is not None else self.qk or '-'} "
                f"A={self.a or '-'} "
                f"{status} "
                f"CyclesLeft={self.cycles_left}")

# Simulator class with complete simulation logic
class TomasuloSimulator:
    def __init__(self, root):
        self.root = root
        self.root.title("Tomasulo Simulator - Complete Simulation")
        
        # Set up styling
        self.setup_styles()
        
        # Complete state
        self.cycle = 1
        self.program = []
        self.current_pc = 0
        self.pending_control_flow = False
        self.registers = [0] * 8  # R0 to R7, R0 is always 0
        self.register_status = [None] * 8  # Qi field
        self.memory = defaultdict(int)  # 16-bit addressable memory
        self.instructions = deque()  # Instruction queue
        self.completed_instructions = 0
        self.branch_count = 0
        self.mispredictions = 0
        self.max_cycles = 1000  # Maximum number of cycles to prevent infinite loops
        
        # Complete reservation stations
        self.res_stations = {}
        self.op_to_rs = {
            'LOAD': 'LOAD', 'STORE': 'STORE', 'BEQ': 'BEQ',
            'CALL': 'CALL_RET', 'RET': 'CALL_RET',
            'ADD': 'ADD_SUB', 'SUB': 'ADD_SUB',
            'NOR': 'NOR', 'MUL': 'MUL'
        }
        
        self.hw_config_entries = {}
        self.debug_trace = True
        
        self.setup_complete_gui()

    def setup_styles(self):
        """Complete styling setup"""
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure("Treeview",
            background=COLORS['bg'],
            foreground=COLORS['fg'],
            fieldbackground=COLORS['bg'],
            rowheight=25)
        
        style.configure("Treeview.Heading",
            background=COLORS['header_bg'],
            foreground=COLORS['fg'],
            font=('Arial', 10, 'bold'))
        
        style.map("Treeview",
            background=[('selected', COLORS['accent'])],
            foreground=[('selected', 'white')])

    def setup_complete_gui(self):
        # Complete GUI setup similar to day2 but with reservation stations, registers, and memory displays
        self.root.configure(bg=COLORS['bg'])
        
        main_canvas = tk.Canvas(self.root, bg=COLORS['bg'])
        main_canvas.pack(fill=tk.BOTH, expand=True)
        
        main_scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=main_canvas.yview)
        main_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        main_canvas.configure(yscrollcommand=main_scrollbar.set)
        
        main_frame = ttk.Frame(main_canvas)
        main_canvas.create_window((0, 0), window=main_frame, anchor="nw")
        
        # Hardware Configuration (same as day2)
        hw_config_frame = ttk.LabelFrame(main_frame, text="Hardware Configuration", padding="10")
        hw_config_frame.pack(fill=tk.X, expand=False, padx=10, pady=10)
        
        instruction_types = [
            ('LOAD', 'Load/Store'), ('STORE', 'Load/Store'), ('BEQ', 'Branch'),
            ('CALL_RET', 'Call/Return'), ('ADD_SUB', 'Add/Subtract'), ('NOR', 'NOR'), ('MUL', 'Multiply')
        ]

        for op_type, display_name in instruction_types:
            row_frame = ttk.Frame(hw_config_frame)
            row_frame.pack(fill=tk.X, pady=2)

            ttk.Label(row_frame, text=f"{display_name}:").pack(side=tk.LEFT, padx=5)
            ttk.Label(row_frame, text="RS Count:").pack(side=tk.LEFT, padx=5)
            rs_entry = ttk.Entry(row_frame, width=5)
            rs_entry.pack(side=tk.LEFT, padx=5)
            
            default_rs = {'LOAD': '2', 'STORE': '2', 'BEQ': '2', 'CALL_RET': '1', 'ADD_SUB': '4', 'NOR': '2', 'MUL': '2'}
            rs_entry.insert(0, default_rs[op_type])

            ttk.Label(row_frame, text="Exec Cycles:").pack(side=tk.LEFT, padx=5)
            cycles_entry = ttk.Entry(row_frame, width=5)
            cycles_entry.pack(side=tk.LEFT, padx=5)
            
            default_cycles = {'LOAD': '6', 'STORE': '6', 'BEQ': '1', 'CALL_RET': '1', 'ADD_SUB': '2', 'NOR': '1', 'MUL': '10'}
            cycles_entry.insert(0, default_cycles[op_type])

            self.hw_config_entries[op_type] = (rs_entry, cycles_entry)

        # Input frame (same as day2)
        input_frame = ttk.Frame(main_frame, padding="10")
        input_frame.pack(fill=tk.X, expand=False, padx=10, pady=10)
        
        input_left = ttk.Frame(input_frame)
        input_left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        ttk.Label(input_left, text="Assembly Program (one per line):").pack(anchor=tk.W)
        self.program_text = scrolledtext.ScrolledText(input_left, width=50, height=10)
        self.program_text.pack(fill=tk.BOTH, expand=True)
        
        input_middle = ttk.Frame(input_frame)
        input_middle.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        ttk.Label(input_middle, text="Starting PC:").pack(anchor=tk.W)
        self.start_pc_entry = ttk.Entry(input_middle)
        self.start_pc_entry.pack(fill=tk.X, pady=(5, 0))
        self.start_pc_entry.insert(0, "0")
        
        input_right = ttk.Frame(input_frame)
        input_right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))
        ttk.Label(input_right, text="Memory (addr:value, one per line):").pack(anchor=tk.W)
        self.memory_text = scrolledtext.ScrolledText(input_right, width=30, height=10)
        self.memory_text.pack(fill=tk.BOTH, expand=True)

        # Instructions display
        instr_frame = ttk.LabelFrame(main_frame, text="Instructions")
        instr_frame.pack(fill=tk.X, expand=False, padx=10, pady=10)
        
        instr_scroll_frame = ttk.Frame(instr_frame)
        instr_scroll_frame.pack(fill=tk.BOTH, expand=True)
        
        instr_h_scroll = ttk.Scrollbar(instr_scroll_frame, orient="horizontal")
        instr_h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        instr_v_scroll = ttk.Scrollbar(instr_scroll_frame, orient="vertical")
        instr_v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.instr_tree = ttk.Treeview(instr_scroll_frame, 
                                      columns=("PC", "Instruction", "Issue", "StartExec", "EndExec", "Write"),
                                      xscrollcommand=instr_h_scroll.set, yscrollcommand=instr_v_scroll.set)
        self.instr_tree.pack(fill=tk.BOTH, expand=True)
        
        instr_h_scroll.config(command=self.instr_tree.xview)
        instr_v_scroll.config(command=self.instr_tree.yview)
        
        # Configure instruction tree columns
        for col, text in [("#0", ""), ("PC", "PC"), ("Instruction", "Instruction"), 
                         ("Issue", "Issue"), ("StartExec", "Start Exec"), ("EndExec", "End Exec"), ("Write", "Write")]:
            self.instr_tree.heading(col, text=text)
        
        # Set column widths
        self.instr_tree.column("#0", width=20, stretch=tk.NO)
        self.instr_tree.column("PC", width=60, stretch=tk.NO)
        self.instr_tree.column("Instruction", width=150, stretch=tk.YES)
        for col in ["Issue", "StartExec", "EndExec", "Write"]:
            self.instr_tree.column(col, width=80, stretch=tk.NO)

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Button(button_frame, text="Load Program", command=self.load_program).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Step", command=self.step).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Run to End", command=self.run_to_end).pack(side=tk.LEFT, padx=5)

        # Status and displays
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        status_bar = ttk.Frame(status_frame)
        status_bar.pack(fill=tk.X, pady=(0, 10))
        self.cycle_label = ttk.Label(status_bar, text="Cycle: 1")
        self.cycle_label.pack(side=tk.LEFT, padx=(0, 20))
        self.pc_label = ttk.Label(status_bar, text="Current PC: 0")
        self.pc_label.pack(side=tk.LEFT)

        # Reservation stations display
        rs_frame = ttk.LabelFrame(status_frame, text="Reservation Stations")
        rs_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        rs_scroll_frame = ttk.Frame(rs_frame)
        rs_scroll_frame.pack(fill=tk.BOTH, expand=True)
        
        rs_h_scroll = ttk.Scrollbar(rs_scroll_frame, orient="horizontal")
        rs_h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        rs_v_scroll = ttk.Scrollbar(rs_scroll_frame, orient="vertical")
        rs_v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.rs_tree = ttk.Treeview(rs_scroll_frame, columns=("Name", "Busy", "Op", "Vj", "Vk", "Qj", "Qk", "A", "Status", "Cycles"),
                                   xscrollcommand=rs_h_scroll.set, yscrollcommand=rs_v_scroll.set)
        self.rs_tree.pack(fill=tk.BOTH, expand=True)
        
        rs_h_scroll.config(command=self.rs_tree.xview)
        rs_v_scroll.config(command=self.rs_tree.yview)
        
        # Configure RS tree
        rs_columns = [("#0", "Type", 100), ("Name", "Name", 80), ("Busy", "Busy", 50), ("Op", "Op", 60),
                     ("Vj", "Vj", 60), ("Vk", "Vk", 60), ("Qj", "Qj", 60), ("Qk", "Qk", 60),
                     ("A", "A", 60), ("Status", "Status", 80), ("Cycles", "Cycles Left", 80)]
        
        for col, text, width in rs_columns:
            self.rs_tree.heading(col, text=text)
            self.rs_tree.column(col, width=width, stretch=tk.NO if col != "#0" else tk.NO)

        # Bottom frame with registers and memory
        bottom_frame = ttk.Frame(status_frame)
        bottom_frame.pack(fill=tk.BOTH, expand=True)
        
        # Registers
        reg_frame = ttk.LabelFrame(bottom_frame, text="Registers")
        reg_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        reg_scroll_frame = ttk.Frame(reg_frame)
        reg_scroll_frame.pack(fill=tk.BOTH, expand=True)
        
        self.reg_tree = ttk.Treeview(reg_scroll_frame, columns=("Value", "Qi"))
        self.reg_tree.pack(fill=tk.BOTH, expand=True)
        
        self.reg_tree.heading("#0", text="Register")
        self.reg_tree.heading("Value", text="Value")
        self.reg_tree.heading("Qi", text="Qi")
        
        # Memory
        mem_frame = ttk.LabelFrame(bottom_frame, text="Memory (non-zero)")
        mem_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        mem_scroll_frame = ttk.Frame(mem_frame)
        mem_scroll_frame.pack(fill=tk.BOTH, expand=True)
        
        self.mem_tree = ttk.Treeview(mem_scroll_frame, columns=("Value",))
        self.mem_tree.pack(fill=tk.BOTH, expand=True)
        
        self.mem_tree.heading("#0", text="Address")
        self.mem_tree.heading("Value", text="Value")

        # Update canvas scroll region
        def configure_scroll_region(event):
            main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        main_frame.bind('<Configure>', configure_scroll_region)

    def parse_instruction(self, line, pc):
        """Complete instruction parsing"""
        parts = re.split(r'[,\s()]+', line.strip().upper())
        parts = [p for p in parts if p]
        opcode = parts[0]

        if opcode == 'LOAD':
            dest, offset, src = parts[1], int(parts[2]), parts[3]
            return Instruction(opcode, [dest, src, offset], pc)
        elif opcode == 'STORE':
            src_data, offset, src_addr = parts[1], int(parts[2]), parts[3]
            return Instruction(opcode, [src_data, src_addr, offset], pc)
        elif opcode == 'BEQ':
            rA, rB, offset = parts[1], parts[2], int(parts[3])
            return Instruction(opcode, [rA, rB, offset], pc)
        elif opcode == 'CALL':
            label = int(parts[1])
            if not -64 <= label <= 63:
                raise ValueError(f"CALL label must be a 7-bit signed constant (-64 to 63), got {label}")
            return Instruction(opcode, [label], pc)
        elif opcode == 'RET':
            return Instruction(opcode, [], pc)
        elif opcode in ('ADD', 'SUB', 'NOR', 'MUL'):
            dest, src1, src2 = parts[1], parts[2], parts[3]
            return Instruction(opcode, [dest, src1, src2], pc)
        else:
            raise ValueError(f"Unknown opcode: {opcode}")

    def initialize_reservation_stations(self):
        """Initialize reservation stations"""
        self.res_stations.clear()

        for op_type, (rs_entry, cycles_entry) in self.hw_config_entries.items():
            try:
                num_rs = int(rs_entry.get())
                exec_cycles = int(cycles_entry.get())
                if num_rs < 1 or exec_cycles < 1:
                    raise ValueError("Values must be positive integers")
                
                actual_cycles = exec_cycles - 1 if op_type in ['LOAD', 'STORE'] else exec_cycles
                
                self.res_stations[op_type] = [
                    ReservationStation(f"{op_type}{i}", op_type, actual_cycles)
                    for i in range(1, num_rs + 1)
                ]
            except ValueError as e:
                messagebox.showerror("Error", f"Invalid configuration for {op_type}: {str(e)}")
                return False
        return True

    def load_program(self):
        """Complete program loading"""
        try:
            if not self.initialize_reservation_stations():
                return

            # Reset state
            self.cycle = 1
            self.program.clear()
            self.instructions.clear()
            self.current_pc = int(self.start_pc_entry.get())
            self.pending_control_flow = False
            self.registers = [0] * 8
            self.register_status = [None] * 8
            self.memory.clear()
            self.completed_instructions = self.branch_count = self.mispredictions = 0
            
            for rs_list in self.res_stations.values():
                for rs in rs_list:
                    rs.clear()

            # Load memory
            memory_input = self.memory_text.get("1.0", tk.END).strip().split('\n')
            for line in memory_input:
                if ':' in line:
                    addr, value = map(int, line.split(':'))
                    if value < 0:
                        value = value & 0xFFFF
                        if value & 0x8000:
                            value = value - 0x10000
                    else:
                        value = value & 0xFFFF
                    self.memory[addr] = value

            # Parse program
            program_input = self.program_text.get("1.0", tk.END).strip().split('\n')
            pc = self.current_pc
            for line in program_input:
                if line.strip():
                    instr = self.parse_instruction(line, pc)
                    self.program.append(instr)
                    self.instructions.append(instr)
                    pc += 1
            
            self.update_display()
            messagebox.showinfo("Success", "Program loaded successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load program: {e}")

    def step(self):
        """Complete single step simulation"""
        if not self.instructions and all(not rs.busy for rs_list in self.res_stations.values() for rs in rs_list):
            self.show_results()
            return
        self.simulate_cycle()
        self.cycle += 1
        self.update_display()

    def run_to_end(self):
        """Complete run to end simulation"""
        while self.instructions or any(rs.busy for rs_list in self.res_stations.values() for rs in rs_list):
            self.simulate_cycle()
            self.cycle += 1
        self.update_display()
        self.show_results()

    def simulate_cycle(self):
        """Complete simulation cycle implementation"""
        # Check for maximum cycle limit
        if self.cycle > self.max_cycles:
            messagebox.showerror("Error", f"Simulation stopped: Maximum cycle limit ({self.max_cycles}) reached.")
            self.instructions.clear()
            self.pending_control_flow = False
            for rs_list in self.res_stations.values():
                for rs in rs_list:
                    rs.clear()
            return

        # Clear reservation stations that wrote results in previous cycle
        for rs_list in self.res_stations.values():
            for rs in rs_list:
                if rs.wrote_result:
                    rs.clear()

        # Write stage: broadcast results on CDB
        completed = []
        for rs_list in self.res_stations.values():
            for rs in rs_list:
                if rs.busy and rs.executing and rs.cycles_left <= 0 and not rs.wrote_result:
                    completed.append(rs)

        if completed:
            for rs in completed:
                instr = rs.instruction
                instr.write_cycle = self.cycle
                result = None
                dest_reg = None

                # Execute instruction logic
                if instr.opcode == 'LOAD':
                    addr = rs.vj + rs.a
                    result = self.memory[addr]
                    dest_reg = int(instr.operands[0][1:])
                elif instr.opcode in ('ADD', 'SUB', 'NOR', 'MUL'):
                    rB, rC = rs.vj, rs.vk
                    if instr.opcode == 'ADD':
                        result = (rB + rC) & 0xFFFF
                    elif instr.opcode == 'SUB':
                        result = (rB - rC) & 0xFFFF
                    elif instr.opcode == 'NOR':
                        result = (~(rB | rC)) & 0xFFFF
                    elif instr.opcode == 'MUL':
                        result = (rB * rC) & 0xFFFF
                    dest_reg = int(instr.operands[0][1:])
                elif instr.opcode == 'STORE':
                    addr = rs.vj + rs.a
                    self.memory[addr] = rs.vk

                # Broadcast on CDB
                if result is not None and dest_reg is not None:
                    if self.register_status[dest_reg] == rs.name:
                        self.registers[dest_reg] = result
                        self.register_status[dest_reg] = None
                    
                    # Update other reservation stations
                    for rs_list in self.res_stations.values():
                        for other_rs in rs_list:
                            if other_rs.qj == rs.name:
                                other_rs.vj = result
                                other_rs.qj = None
                                other_rs.just_wrote = True
                            if other_rs.qk == rs.name:
                                other_rs.vk = result
                                other_rs.qk = None
                                other_rs.just_wrote = True

                # Handle control flow for BEQ (simplified)
                if instr.opcode == 'BEQ':
                    rA, rB = rs.vj, rs.vk
                    self.branch_count += 1
                    if rA == rB:  # Taken
                        self.mispredictions += 1
                        target_pc = instr.pc + 1 + (instr.operands[2] - 1)
                        self.current_pc = target_pc
                        self.instructions.clear()
                        # Reload instructions from new PC (simplified)
                    else:
                        self.current_pc = instr.pc + 1
                    self.pending_control_flow = False

                instr.completed = True
                self.completed_instructions += 1
                rs.wrote_result = True

        # Execute stage
        for rs_list in self.res_stations.values():
            for rs in rs_list:
                if rs.busy and not rs.executing and rs.qj is None and rs.qk is None and not rs.just_wrote:
                    rs.executing = True
                    rs.cycles_left = rs.exec_cycles
                    rs.instruction.start_exec_cycle = self.cycle
                elif rs.executing and rs.cycles_left > 0:
                    rs.cycles_left -= 1
                    if rs.cycles_left == 0:
                        rs.instruction.end_exec_cycle = self.cycle
                rs.just_wrote = False

        # Issue stage
        if self.instructions and not self.pending_control_flow:
            instr = self.instructions[0]
            rs_type = self.op_to_rs[instr.opcode]
            rs_list = self.res_stations[rs_type]
            free_rs = next((rs for rs in rs_list if not rs.busy), None)
            
            if free_rs:
                self.instructions.popleft()
                free_rs.busy = True
                free_rs.instruction = instr
                instr.issue_cycle = self.cycle

                # Set up reservation station based on instruction type
                if instr.opcode == 'LOAD':
                    rB_idx = int(instr.operands[1][1:])
                    free_rs.a = instr.operands[2]
                    if self.register_status[rB_idx]:
                        free_rs.qj = self.register_status[rB_idx]
                    else:
                        free_rs.vj = self.registers[rB_idx]
                    dest_idx = int(instr.operands[0][1:])
                    self.register_status[dest_idx] = free_rs.name
                elif instr.opcode == 'STORE':
                    rA_idx = int(instr.operands[0][1:])
                    rB_idx = int(instr.operands[1][1:])
                    free_rs.a = instr.operands[2]
                    if self.register_status[rB_idx]:
                        free_rs.qj = self.register_status[rB_idx]
                    else:
                        free_rs.vj = self.registers[rB_idx]
                    if self.register_status[rA_idx]:
                        free_rs.qk = self.register_status[rA_idx]
                    else:
                        free_rs.vk = self.registers[rA_idx]
                elif instr.opcode == 'BEQ':
                    rA_idx, rB_idx = int(instr.operands[0][1:]), int(instr.operands[1][1:])
                    if self.register_status[rA_idx]:
                        free_rs.qj = self.register_status[rA_idx]
                    else:
                        free_rs.vj = self.registers[rA_idx]
                    if self.register_status[rB_idx]:
                        free_rs.qk = self.register_status[rB_idx]
                    else:
                        free_rs.vk = self.registers[rB_idx]
                    self.pending_control_flow = True
                elif instr.opcode in ('ADD', 'SUB', 'NOR', 'MUL'):
                    rB_idx, rC_idx = int(instr.operands[1][1:]), int(instr.operands[2][1:])
                    dest_idx = int(instr.operands[0][1:])
                    if self.register_status[rB_idx]:
                        free_rs.qj = self.register_status[rB_idx]
                    else:
                        free_rs.vj = self.registers[rB_idx]
                    if self.register_status[rC_idx]:
                        free_rs.qk = self.register_status[rC_idx]
                    else:
                        free_rs.vk = self.registers[rC_idx]
                    self.register_status[dest_idx] = free_rs.name

    def update_display(self):
        """Complete display update"""
        self.cycle_label.configure(text=f"Cycle: {self.cycle}")
        self.pc_label.configure(text=f"Current PC: {self.current_pc}")

        # Clear all trees
        for tree in [self.rs_tree, self.reg_tree, self.mem_tree, self.instr_tree]:
            for item in tree.get_children():
                tree.delete(item)

        # Update Reservation Stations
        rs_parents = {}
        for rs_type, rs_list in self.res_stations.items():
            rs_parents[rs_type] = self.rs_tree.insert("", "end", text=rs_type, open=True)
            for rs in rs_list:
                op = rs.instruction.opcode if rs.busy and rs.instruction else ""
                status = "Wrote" if rs.wrote_result else "Executing" if rs.executing else "Waiting" if rs.busy else ""
                
                values = [rs.name, "Yes" if rs.busy else "No", op,
                         rs.vj if rs.vj is not None else "",
                         rs.vk if rs.vk is not None else "",
                         rs.qj if rs.qj is not None else "",
                         rs.qk if rs.qk is not None else "",
                         rs.a if rs.a is not None else "",
                         status, rs.cycles_left if rs.busy else ""]
                self.rs_tree.insert(rs_parents[rs_type], "end", values=values)

        # Update Registers
        for i, (val, qi) in enumerate(zip(self.registers, self.register_status)):
            self.reg_tree.insert("", "end", text=f"R{i}", values=(val, qi or "-"))

        # Update Memory
        for addr, val in sorted(self.memory.items()):
            if val != 0:
                self.mem_tree.insert("", "end", text=str(addr), values=(val,))

        # Update Instructions
        for instr in self.program:
            values = (instr.pc, f"{instr.opcode} {' '.join(map(str, instr.operands))}",
                     instr.issue_cycle or "-", instr.start_exec_cycle or "-",
                     instr.end_exec_cycle or "-", instr.write_cycle or "-")
            self.instr_tree.insert("", "end", text="", values=values)

    def show_results(self):
        """Basic results display"""
        total_cycles = self.cycle
        ipc = self.completed_instructions / total_cycles if total_cycles > 0 else 0
        mispred_pct = (self.mispredictions / self.branch_count * 100) if self.branch_count > 0 else 0

        result_text = f"""Simulation Complete!

Total Cycles: {total_cycles}
Instructions Completed: {self.completed_instructions}
IPC: {ipc:.2f}
Conditional Branches: {self.branch_count}
Branch Mispredictions: {self.mispredictions}
Misprediction Percentage: {mispred_pct:.2f}%"""

        messagebox.showinfo("Simulation Results", result_text)

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Tomasulo Simulator - Day 3")
    root.geometry("1200x800")
    app = TomasuloSimulator(root)
    root.mainloop()
