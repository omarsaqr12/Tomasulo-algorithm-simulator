import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import re
from collections import defaultdict, deque

# Enhanced color theme
COLORS = {
    'bg': '#f0f0f0',
    'fg': '#333333',
    'accent': '#007acc',
    'accent_hover': '#005c99',
    'success': '#28a745',
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
        self.wrote_result = False  # Track if result was written

    def clear(self):
        self.busy = False
        self.instruction = None
        self.vj = self.vk = self.qj = self.qk = self.a = None
        self.cycles_left = 0
        self.executing = False
        self.wrote_result = False

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

# Enhanced Simulator class with better GUI
class TomasuloSimulator:
    def __init__(self, root):
        self.root = root
        self.root.title("Tomasulo Simulator - Enhanced GUI")
        
        # Set up styling
        self.setup_styles()
        
        # Enhanced state
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
        
        # Enhanced reservation stations with configurable parameters
        self.res_stations = {}
        self.op_to_rs = {
            'LOAD': 'LOAD', 'STORE': 'STORE', 'BEQ': 'BEQ',
            'CALL': 'CALL_RET', 'RET': 'CALL_RET',
            'ADD': 'ADD_SUB', 'SUB': 'ADD_SUB',
            'NOR': 'NOR', 'MUL': 'MUL'
        }
        
        # Hardware configuration entries
        self.hw_config_entries = {}
        
        self.setup_enhanced_gui()

    def setup_styles(self):
        """Set up enhanced styling"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure custom styles with colors
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
        
        style.configure("TButton",
            padding=6,
            background=COLORS['accent'],
            foreground='white')

    def setup_enhanced_gui(self):
        # Configure root window background
        self.root.configure(bg=COLORS['bg'])
        
        # Main scrollable frame
        main_canvas = tk.Canvas(self.root, bg=COLORS['bg'])
        main_canvas.pack(fill=tk.BOTH, expand=True)
        
        main_scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=main_canvas.yview)
        main_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        main_canvas.configure(yscrollcommand=main_scrollbar.set)
        
        main_frame = ttk.Frame(main_canvas)
        main_canvas.create_window((0, 0), window=main_frame, anchor="nw")
        
        # Hardware Configuration Frame
        hw_config_frame = ttk.LabelFrame(main_frame, text="Hardware Configuration", padding="10")
        hw_config_frame.pack(fill=tk.X, expand=False, padx=10, pady=10)
        
        # Create configuration for each instruction type
        instruction_types = [
            ('LOAD', 'Load/Store'),
            ('STORE', 'Load/Store'),
            ('BEQ', 'Branch'),
            ('CALL_RET', 'Call/Return'),
            ('ADD_SUB', 'Add/Subtract'),
            ('NOR', 'NOR'),
            ('MUL', 'Multiply')
        ]

        for i, (op_type, display_name) in enumerate(instruction_types):
            row_frame = ttk.Frame(hw_config_frame)
            row_frame.pack(fill=tk.X, pady=2)

            ttk.Label(row_frame, text=f"{display_name}:").pack(side=tk.LEFT, padx=5)

            ttk.Label(row_frame, text="RS Count:").pack(side=tk.LEFT, padx=5)
            rs_entry = ttk.Entry(row_frame, width=5)
            rs_entry.pack(side=tk.LEFT, padx=5)
            
            # Default values
            default_rs = {'LOAD': '2', 'STORE': '2', 'BEQ': '2', 'CALL_RET': '1', 'ADD_SUB': '4', 'NOR': '2', 'MUL': '2'}
            rs_entry.insert(0, default_rs[op_type])

            ttk.Label(row_frame, text="Exec Cycles:").pack(side=tk.LEFT, padx=5)
            cycles_entry = ttk.Entry(row_frame, width=5)
            cycles_entry.pack(side=tk.LEFT, padx=5)
            
            # Default cycles
            default_cycles = {'LOAD': '6', 'STORE': '6', 'BEQ': '1', 'CALL_RET': '1', 'ADD_SUB': '2', 'NOR': '1', 'MUL': '10'}
            cycles_entry.insert(0, default_cycles[op_type])

            self.hw_config_entries[op_type] = (rs_entry, cycles_entry)

        # Enhanced Input frame
        input_frame = ttk.Frame(main_frame, padding="10")
        input_frame.pack(fill=tk.X, expand=False, padx=10, pady=10)
        
        # Program input
        input_left = ttk.Frame(input_frame)
        input_left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        ttk.Label(input_left, text="Assembly Program (one per line):").pack(anchor=tk.W)
        self.program_text = scrolledtext.ScrolledText(input_left, width=50, height=10)
        self.program_text.pack(fill=tk.BOTH, expand=True)
        
        # Starting PC
        input_middle = ttk.Frame(input_frame)
        input_middle.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        ttk.Label(input_middle, text="Starting PC:").pack(anchor=tk.W)
        self.start_pc_entry = ttk.Entry(input_middle)
        self.start_pc_entry.pack(fill=tk.X, pady=(5, 0))
        self.start_pc_entry.insert(0, "0")
        
        # Memory input
        input_right = ttk.Frame(input_frame)
        input_right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))
        ttk.Label(input_right, text="Memory (addr:value, one per line):").pack(anchor=tk.W)
        self.memory_text = scrolledtext.ScrolledText(input_right, width=30, height=10)
        self.memory_text.pack(fill=tk.BOTH, expand=True)

        # Instructions display
        instr_frame = ttk.LabelFrame(main_frame, text="Instructions")
        instr_frame.pack(fill=tk.X, expand=False, padx=10, pady=10)
        
        # Create instructions Treeview with scrollbars
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
        
        # Configure columns
        self.instr_tree.heading("#0", text="")
        self.instr_tree.heading("PC", text="PC")
        self.instr_tree.heading("Instruction", text="Instruction")
        self.instr_tree.heading("Issue", text="Issue")
        self.instr_tree.heading("StartExec", text="Start Exec")
        self.instr_tree.heading("EndExec", text="End Exec")
        self.instr_tree.heading("Write", text="Write")
        
        self.instr_tree.column("#0", width=20, stretch=tk.NO)
        self.instr_tree.column("PC", width=60, stretch=tk.NO)
        self.instr_tree.column("Instruction", width=150, stretch=tk.YES)
        self.instr_tree.column("Issue", width=60, stretch=tk.NO)
        self.instr_tree.column("StartExec", width=80, stretch=tk.NO)
        self.instr_tree.column("EndExec", width=80, stretch=tk.NO)
        self.instr_tree.column("Write", width=60, stretch=tk.NO)

        # Enhanced buttons with styling
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Button(button_frame, text="Load Program", command=self.load_program).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Step", command=self.step).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Run to End", command=self.run_to_end).pack(side=tk.LEFT, padx=5)

        # Status frame with cycle and PC display
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        status_bar = ttk.Frame(status_frame)
        status_bar.pack(fill=tk.X, pady=(0, 10))
        self.cycle_label = ttk.Label(status_bar, text="Cycle: 1")
        self.cycle_label.pack(side=tk.LEFT, padx=(0, 20))
        self.pc_label = ttk.Label(status_bar, text="Current PC: 0")
        self.pc_label.pack(side=tk.LEFT)

        # Update canvas scroll region
        def configure_scroll_region(event):
            main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        main_frame.bind('<Configure>', configure_scroll_region)

    def parse_instruction(self, line, pc):
        """Enhanced instruction parsing"""
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
        """Initialize reservation stations based on configuration"""
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
        """Enhanced program loading with memory initialization"""
        try:
            if not self.initialize_reservation_stations():
                return

            # Reset simulator state
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
        """Placeholder step function - simulation logic to be added"""
        self.cycle += 1
        self.update_display()

    def run_to_end(self):
        """Placeholder run function"""
        messagebox.showinfo("Info", "Run to end functionality will be implemented in next version")

    def update_display(self):
        """Update GUI display elements"""
        self.cycle_label.configure(text=f"Cycle: {self.cycle}")
        self.pc_label.configure(text=f"Current PC: {self.current_pc}")
        
        # Clear instructions tree
        for item in self.instr_tree.get_children():
            self.instr_tree.delete(item)
        
        # Update instructions display
        for instr in self.program:
            values = (
                instr.pc,
                f"{instr.opcode} {' '.join(map(str, instr.operands))}",
                instr.issue_cycle or "-",
                instr.start_exec_cycle or "-",
                instr.end_exec_cycle or "-",
                instr.write_cycle or "-"
            )
            self.instr_tree.insert("", "end", text="", values=values)

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Tomasulo Simulator - Day 2")
    root.geometry("1200x800")
    app = TomasuloSimulator(root)
    root.mainloop()