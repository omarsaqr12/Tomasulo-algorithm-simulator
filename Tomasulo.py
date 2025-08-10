import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import re
from collections import defaultdict, deque
import platform

# Color theme
COLORS = {
    'bg': '#f0f0f0',
    'fg': '#333333',
    'accent': '#007acc',
    'accent_hover': '#005c99',
    'success': '#28a745',
    'success_hover': '#218838',
    'warning': '#ffc107',
    'warning_hover': '#e0a800',
    'error': '#dc3545',
    'error_hover': '#c82333',
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
        self.wrote_result = False  # New flag to track if result was written but RS not cleared yet
        self.just_wrote = False  # New flag to track if result was just written in current cycle

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

# Simulator class
class TomasuloSimulator:
    def __init__(self, root):
        self.root = root
        self.root.title("Tomasulo Simulator - femTomas")
        
        # Set theme and style
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
        
        style.configure("TLabel",
            padding=3,
            background=COLORS['bg'],
            foreground=COLORS['fg'])
        
        style.configure("TFrame",
            background=COLORS['bg'],
            padding=5)
        
        style.configure("TLabelframe",
            background=COLORS['bg'],
            padding=10)
        
        style.configure("TLabelframe.Label",
            font=('Arial', 11, 'bold'),
            foreground=COLORS['accent'])
        
        # Configure text widget colors
        text_config = {
            'bg': 'white',
            'fg': COLORS['fg'],
            'insertbackground': COLORS['fg'],
            'selectbackground': COLORS['accent'],
            'selectforeground': 'white',
            'font': ('Consolas', 10)
        }
        
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

        # Initialize reservation stations with default values
        self.res_stations = {}
        self.op_to_rs = {
            'LOAD': 'LOAD', 'STORE': 'STORE', 'BEQ': 'BEQ',
            'CALL': 'CALL_RET', 'RET': 'CALL_RET',
            'ADD': 'ADD_SUB', 'SUB': 'ADD_SUB',
            'NOR': 'NOR', 'MUL': 'MUL'
        }

        # Configure hover effects for buttons
        style = ttk.Style()
        style.map("Accent.TButton",
            background=[('active', COLORS['accent_hover']), ('!active', COLORS['accent'])],
            foreground=[('active', 'white'), ('!active', 'white')])
        
        style.map("Success.TButton",
            background=[('active', COLORS['success_hover']), ('!active', COLORS['success'])],
            foreground=[('active', 'white'), ('!active', 'white')])
        
        # Configure tooltips
        self.tooltips = {}

        # Add debugging flag
        self.debug_trace = True

        # GUI setup
        self.setup_gui()
        
        # Bind mouse wheel and touchpad events for all scrollable widgets
        self.bind_scroll_events()

    def bind_scroll_events(self):
        """Bind scroll events for Windows touchpad two-finger scrolling"""
        def _on_vertical_scroll(event, widget):
            # Windows touchpad vertical scroll
            delta = -int(event.delta/120)
            try:
                widget.yview_scroll(delta, "units")
            except:
                # If the widget doesn't have yview_scroll, try to find a parent that does
                parent = widget.master
                while parent:
                    try:
                        parent.yview_scroll(delta, "units")
                        break
                    except:
                        parent = parent.master
            return "break"  # Prevent default scrolling
            
        def _on_horizontal_scroll(event, widget):
            # Windows touchpad horizontal scroll
            delta = int(event.delta/120)
            try:
                widget.xview_scroll(-delta, "units")
            except:
                # If the widget doesn't have xview_scroll, try to find a parent that does
                parent = widget.master
                while parent:
                    try:
                        parent.xview_scroll(-delta, "units")
                        break
                    except:
                        parent = parent.master
            return "break"  # Prevent default scrolling
        
        # List of all scrollable widgets and their containers
        scrollable_widgets = [
            (self.program_text, self.program_text),
            (self.memory_text, self.memory_text),
            (self.rs_tree, self.rs_tree.master),  # Bind to both tree and its container
            (self.reg_tree, self.reg_tree.master),
            (self.mem_tree, self.mem_tree.master),
            (self.instr_tree, self.instr_tree.master)
        ]
        
        # Bind scrolling events for each widget and its container
        for widget, container in scrollable_widgets:
            # Bind to the widget itself
            widget.bind('<MouseWheel>', lambda e, w=widget: _on_vertical_scroll(e, w))
            widget.bind('<Shift-MouseWheel>', lambda e, w=widget: _on_horizontal_scroll(e, w))
            
            # Bind to the container as well
            if container != widget:
                container.bind('<MouseWheel>', lambda e, w=widget: _on_vertical_scroll(e, w))
                container.bind('<Shift-MouseWheel>', lambda e, w=widget: _on_horizontal_scroll(e, w))
                
            # Bind to all child widgets to ensure event propagation
            for child in widget.winfo_children():
                child.bind('<MouseWheel>', lambda e, w=widget: _on_vertical_scroll(e, w))
                child.bind('<Shift-MouseWheel>', lambda e, w=widget: _on_horizontal_scroll(e, w))

    def create_tooltip(self, widget, text):
        """Create a tooltip for a widget"""
        def enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            
            label = ttk.Label(tooltip, text=text, justify='left',
                            background="#ffffe0", relief='solid', borderwidth=1)
            label.pack()
            
            self.tooltips[widget] = tooltip
            
        def leave(event):
            if widget in self.tooltips:
                self.tooltips[widget].destroy()
                del self.tooltips[widget]
                
        widget.bind('<Enter>', enter)
        widget.bind('<Leave>', leave)

    def setup_gui(self):
        # Configure root window background
        self.root.configure(bg=COLORS['bg'])
        
        # Make the main window scrollable
        main_canvas = tk.Canvas(self.root, bg=COLORS['bg'], highlightthickness=0)
        main_canvas.grid(row=0, column=0, sticky="nsew")
        
        # Add scrollbars with custom styling
        main_scrollbar_y = ttk.Scrollbar(self.root, orient="vertical", command=main_canvas.yview)
        main_scrollbar_y.grid(row=0, column=1, sticky="ns")
        main_scrollbar_x = ttk.Scrollbar(self.root, orient="horizontal", command=main_canvas.xview)
        main_scrollbar_x.grid(row=1, column=0, sticky="ew")
        
        # Configure the canvas
        main_canvas.configure(yscrollcommand=main_scrollbar_y.set, xscrollcommand=main_scrollbar_x.set)
        
        # Create a frame inside the canvas for all content
        main_frame = ttk.Frame(main_canvas)
        canvas_window = main_canvas.create_window((0, 0), window=main_frame, anchor="nw")
        
        # Configure canvas scrolling
        def configure_scroll_region(event):
            main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        main_frame.bind('<Configure>', configure_scroll_region)
        
        # Bind canvas resizing
        def on_canvas_configure(event):
            main_canvas.itemconfig(canvas_window, width=event.width)
        main_canvas.bind('<Configure>', on_canvas_configure)

        # Hardware Configuration Frame with improved styling
        hw_config_frame = ttk.LabelFrame(main_frame, text="Hardware Configuration", padding="10")
        hw_config_frame.pack(fill=tk.X, expand=False, padx=10, pady=10)
        
        # Create a modern style for the hardware configuration
        style = ttk.Style()
        style.configure("Config.TFrame", padding=5, relief="solid")
        
        # Create frames for each instruction type
        instruction_types = [
            ('LOAD', 'Load/Store'),
            ('STORE', 'Load/Store'),
            ('BEQ', 'Branch'),
            ('CALL_RET', 'Call/Return'),
            ('ADD_SUB', 'Add/Subtract'),
            ('NOR', 'NOR'),
            ('MUL', 'Multiply')
        ]

        # Dictionary to store the entry widgets
        self.hw_config_entries = {}

        # Create a frame for each row of configuration
        for i, (op_type, display_name) in enumerate(instruction_types):
            row_frame = ttk.Frame(hw_config_frame)
            row_frame.pack(fill=tk.X, pady=2)

            # Label for instruction type
            ttk.Label(row_frame, text=f"{display_name}:").pack(side=tk.LEFT, padx=5)

            # Number of reservation stations
            ttk.Label(row_frame, text="RS Count:").pack(side=tk.LEFT, padx=5)
            rs_entry = ttk.Entry(row_frame, width=5)
            rs_entry.pack(side=tk.LEFT, padx=5)
            # Set default number of reservation stations
            default_rs = {
                'LOAD': '2',
                'STORE': '2',
                'BEQ': '2',
                'CALL_RET': '1',
                'ADD_SUB': '4',
                'NOR': '2',
                'MUL': '2'
            }
            rs_entry.insert(0, default_rs[op_type])

            # Execution cycles
            ttk.Label(row_frame, text="Exec Cycles:").pack(side=tk.LEFT, padx=5)
            cycles_entry = ttk.Entry(row_frame, width=5)
            cycles_entry.pack(side=tk.LEFT, padx=5)
            # Set default execution cycles
            default_cycles = {
                'LOAD': '6',  # 2 (compute address) + 4 (read from memory)
                'STORE': '6',  # 2 (compute address) + 4 (writing to memory)
                'BEQ': '1',  # 1 (compute target and compare operands)
                'CALL_RET': '1',  # 1 (compute target and return address)
                'ADD_SUB': '2',
                'NOR': '1',
                'MUL': '10'
            }
            cycles_entry.insert(0, default_cycles[op_type])

            # Store the entries in the dictionary
            self.hw_config_entries[op_type] = (rs_entry, cycles_entry)

        # Input frame
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

        # Instructions display right after input
        instr_frame = ttk.LabelFrame(main_frame, text="Instructions")
        instr_frame.pack(fill=tk.X, expand=False, padx=10, pady=10)
        
        # Create scrollbars for instructions
        instr_scroll_frame = ttk.Frame(instr_frame)
        instr_scroll_frame.pack(fill=tk.BOTH, expand=True)
        
        instr_h_scroll = ttk.Scrollbar(instr_scroll_frame, orient="horizontal")
        instr_h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        
        instr_v_scroll = ttk.Scrollbar(instr_scroll_frame, orient="vertical")
        instr_v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create instructions Treeview
        self.instr_tree = ttk.Treeview(instr_scroll_frame, 
                                      columns=("PC", "Instruction", "Issue", "StartExec", "EndExec", "Write"),
                                      xscrollcommand=instr_h_scroll.set, yscrollcommand=instr_v_scroll.set)
        self.instr_tree.pack(fill=tk.BOTH, expand=True)
        
        # Configure the scrollbars
        instr_h_scroll.config(command=self.instr_tree.xview)
        instr_v_scroll.config(command=self.instr_tree.yview)
        
        # Configure the treeview columns
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
        
        # Create buttons with improved styling and tooltips
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        load_btn = ttk.Button(button_frame, text="Load Program", 
                            style="Accent.TButton", 
                            command=self.load_program)
        load_btn.pack(side=tk.LEFT, padx=(0, 5))
        self.create_tooltip(load_btn, "Load and initialize the program with current configuration")
        
        step_btn = ttk.Button(button_frame, text="Step",
                           style="Accent.TButton",
                           command=self.step)
        step_btn.pack(side=tk.LEFT, padx=5)
        self.create_tooltip(step_btn, "Execute one cycle of the simulation")
        
        run_btn = ttk.Button(button_frame, text="Run to End",
                          style="Success.TButton",
                          command=self.run_to_end)
        run_btn.pack(side=tk.LEFT, padx=5)
        self.create_tooltip(run_btn, "Run the simulation until completion")
        
        # Add tooltips to other important widgets
        self.create_tooltip(self.program_text, 
            "Enter your assembly program here.\nOne instruction per line.")
        self.create_tooltip(self.memory_text,
            "Enter initial memory values here.\nFormat: address:value")
        
        # Status frame
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Simulator status
        status_bar = ttk.Frame(status_frame)
        status_bar.pack(fill=tk.X, pady=(0, 10))
        self.cycle_label = ttk.Label(status_bar, text="Cycle: 1")
        self.cycle_label.pack(side=tk.LEFT, padx=(0, 20))
        self.pc_label = ttk.Label(status_bar, text="Current PC: 0")
        self.pc_label.pack(side=tk.LEFT)
        
        # Reservation stations display (using Treeview)
        rs_frame = ttk.LabelFrame(status_frame, text="Reservation Stations")
        rs_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Create a frame with scrollbars for the reservation stations
        rs_scroll_frame = ttk.Frame(rs_frame)
        rs_scroll_frame.pack(fill=tk.BOTH, expand=True)
        
        # Add horizontal and vertical scrollbars
        rs_h_scroll = ttk.Scrollbar(rs_scroll_frame, orient="horizontal")
        rs_h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        
        rs_v_scroll = ttk.Scrollbar(rs_scroll_frame, orient="vertical")
        rs_v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create the Treeview
        self.rs_tree = ttk.Treeview(rs_scroll_frame, columns=("Name", "Busy", "Op", "Vj", "Vk", "Qj", "Qk", "A", "Status", "Cycles"),
                                   xscrollcommand=rs_h_scroll.set, yscrollcommand=rs_v_scroll.set)
        self.rs_tree.pack(fill=tk.BOTH, expand=True)
        
        # Configure the scrollbars
        rs_h_scroll.config(command=self.rs_tree.xview)
        rs_v_scroll.config(command=self.rs_tree.yview)
        
        # Configure the treeview columns
        self.rs_tree.heading("#0", text="Type")
        self.rs_tree.heading("Name", text="Name")
        self.rs_tree.heading("Busy", text="Busy")
        self.rs_tree.heading("Op", text="Op")
        self.rs_tree.heading("Vj", text="Vj")
        self.rs_tree.heading("Vk", text="Vk")
        self.rs_tree.heading("Qj", text="Qj")
        self.rs_tree.heading("Qk", text="Qk")
        self.rs_tree.heading("A", text="A")
        self.rs_tree.heading("Status", text="Status")
        self.rs_tree.heading("Cycles", text="Cycles Left")
        
        self.rs_tree.column("#0", width=100, stretch=tk.NO)
        self.rs_tree.column("Name", width=80, stretch=tk.NO)
        self.rs_tree.column("Busy", width=50, stretch=tk.NO)
        self.rs_tree.column("Op", width=60, stretch=tk.NO)
        self.rs_tree.column("Vj", width=60, stretch=tk.NO)
        self.rs_tree.column("Vk", width=60, stretch=tk.NO)
        self.rs_tree.column("Qj", width=60, stretch=tk.NO)
        self.rs_tree.column("Qk", width=60, stretch=tk.NO)
        self.rs_tree.column("A", width=60, stretch=tk.NO)
        self.rs_tree.column("Status", width=80, stretch=tk.NO)
        self.rs_tree.column("Cycles", width=80, stretch=tk.NO)
        
        # Bottom frame with two columns
        bottom_frame = ttk.Frame(status_frame)
        bottom_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left column for registers
        reg_frame = ttk.LabelFrame(bottom_frame, text="Registers")
        reg_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Create scrollbars for registers
        reg_scroll_frame = ttk.Frame(reg_frame)
        reg_scroll_frame.pack(fill=tk.BOTH, expand=True)
        
        reg_h_scroll = ttk.Scrollbar(reg_scroll_frame, orient="horizontal")
        reg_h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        
        reg_v_scroll = ttk.Scrollbar(reg_scroll_frame, orient="vertical")
        reg_v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create register Treeview
        self.reg_tree = ttk.Treeview(reg_scroll_frame, columns=("Value", "Qi"), 
                                    xscrollcommand=reg_h_scroll.set, yscrollcommand=reg_v_scroll.set)
        self.reg_tree.pack(fill=tk.BOTH, expand=True)
        
        # Configure the scrollbars
        reg_h_scroll.config(command=self.reg_tree.xview)
        reg_v_scroll.config(command=self.reg_tree.yview)
        
        # Configure the treeview columns
        self.reg_tree.heading("#0", text="Register")
        self.reg_tree.heading("Value", text="Value")
        self.reg_tree.heading("Qi", text="Qi")
        
        self.reg_tree.column("#0", width=80, stretch=tk.NO)
        self.reg_tree.column("Value", width=80, stretch=tk.YES)
        self.reg_tree.column("Qi", width=80, stretch=tk.YES)
        
        # Right column for memory
        mem_frame = ttk.LabelFrame(bottom_frame, text="Memory (non-zero)")
        mem_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # Create scrollbars for memory
        mem_scroll_frame = ttk.Frame(mem_frame)
        mem_scroll_frame.pack(fill=tk.BOTH, expand=True)
        
        mem_h_scroll = ttk.Scrollbar(mem_scroll_frame, orient="horizontal")
        mem_h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        
        mem_v_scroll = ttk.Scrollbar(mem_scroll_frame, orient="vertical")
        mem_v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create memory Treeview
        self.mem_tree = ttk.Treeview(mem_scroll_frame, columns=("Value",),
                                    xscrollcommand=mem_h_scroll.set, yscrollcommand=mem_v_scroll.set)
        self.mem_tree.pack(fill=tk.BOTH, expand=True)
        
        # Configure the scrollbars
        mem_h_scroll.config(command=self.mem_tree.xview)
        mem_v_scroll.config(command=self.mem_tree.yview)
        
        # Configure the treeview columns
        self.mem_tree.heading("#0", text="Address")
        self.mem_tree.heading("Value", text="Value")
        
        self.mem_tree.column("#0", width=100, stretch=tk.NO)
        self.mem_tree.column("Value", width=100, stretch=tk.YES)
        
        # Improve treeview alternating row colors
        style = ttk.Style()
        style.map('Treeview',
            background=[('selected', COLORS['accent'])],
            foreground=[('selected', 'white')])
        
        def fixed_map(option):
            return [elm for elm in style.map('Treeview', query_opt=option)
                   if elm[:2] != ('!disabled', '!selected')]
            
        style.map('Treeview', 
            background=fixed_map('background'),
            foreground=fixed_map('foreground'))
        
        # Add visual feedback for hover in treeviews
        def on_enter(event):
            tree = event.widget
            item = tree.identify_row(event.y)
            if item:
                tree.set_tag_configure('hover', background='#e6f3ff')
                tree.item(item, tags=('hover',))
                
        def on_leave(event):
            tree = event.widget
            item = tree.identify_row(event.y)
            if item:
                tree.item(item, tags=())
        
        for tree in [self.rs_tree, self.reg_tree, self.mem_tree, self.instr_tree]:
            tree.bind('<Motion>', on_enter)
            tree.bind('<Leave>', on_leave)
        
        # Configure the root window to allow resizing
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)

    def parse_instruction(self, line, pc):
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
            # Validate 7-bit signed constant
            if not -64 <= label <= 63:  # 7-bit signed range: -64 to 63
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
        # Clear existing reservation stations
        self.res_stations.clear()

        # Create new reservation stations based on user configuration
        for op_type, (rs_entry, cycles_entry) in self.hw_config_entries.items():
            try:
                num_rs = int(rs_entry.get())
                exec_cycles = int(cycles_entry.get())
                if num_rs < 1 or exec_cycles < 1:
                    raise ValueError("Values must be positive integers")
                
                # For LOAD and STORE, use one less cycle than specified
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
        try:
            # Initialize reservation stations with user configuration
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
                    # Convert to signed 16-bit integer
                    if value < 0:
                        value = value & 0xFFFF  # Keep only 16 bits
                        if value & 0x8000:  # If highest bit is set
                            value = value - 0x10000  # Convert to negative
                    else:
                        value = value & 0xFFFF  # Keep only 16 bits
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
        if not self.instructions and all(not rs.busy for rs_list in self.res_stations.values() for rs in rs_list):
            self.show_results()
            return
        self.simulate_cycle()
        self.cycle += 1
        self.update_display()

    def run_to_end(self):
        while self.instructions or any(rs.busy for rs_list in self.res_stations.values() for rs in rs_list):
            self.simulate_cycle()
            self.cycle += 1
        self.update_display()
        self.show_results()

    def simulate_cycle(self):
        # Check for maximum cycle limit
        if self.cycle > self.max_cycles:
            messagebox.showerror("Error", f"Simulation stopped: Maximum cycle limit ({self.max_cycles}) reached. This may indicate an infinite loop or a very long-running program.")
            # Reset simulator state
            self.instructions.clear()
            self.pending_control_flow = False
            # Clear all reservation stations
            for rs_list in self.res_stations.values():
                for rs in rs_list:
                    rs.clear()
            return

        # First, clear any reservation stations that wrote results in the previous cycle
        for rs_list in self.res_stations.values():
            for rs in rs_list:
                if rs.wrote_result:
                    rs.clear()

        # Write stage: broadcast results on CDB
        completed = []
        for rs_list in self.res_stations.values():
            for rs in rs_list:
                # Fixed condition: ensure we only consider stations that have finished executing but haven't written yet
                if rs.busy and rs.executing and rs.cycles_left <= 0 and not rs.wrote_result:
                    completed.append(rs)

        if completed:
            for rs in completed:
                instr = rs.instruction
                instr.write_cycle = self.cycle
                result = None
                dest_reg = None

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
                elif instr.opcode == 'CALL':
                    result = instr.pc + 1
                    dest_reg = 1  # R1
                    self.current_pc = instr.operands[0]  # Branch directly to label address
                    
                    # Clear instruction queue and reload instructions from new PC
                    self.instructions.clear()
                    # Find the instruction with the target PC and add all subsequent instructions
                    found_target = False
                    for prog_instr in self.program:
                        if prog_instr.pc == instr.operands[0]:
                            found_target = True
                        if found_target:
                            self.instructions.append(prog_instr)
                    self.pending_control_flow = False
                elif instr.opcode == 'RET':
                    return_address = rs.vj  # Branch to address in R1
                    self.current_pc = return_address
                    
                    if self.debug_trace:
                        print(f"\nRET instruction: Return address = {return_address}")
                    
                    # Clear instruction queue and reload instructions from new PC
                    self.instructions.clear()
                    # Find the instruction with the target PC and add all subsequent instructions
                    found_target = False
                    for prog_instr in self.program:
                        if prog_instr.pc == return_address:
                            found_target = True
                            if self.debug_trace:
                                print(f"Found return target at PC={prog_instr.pc}: {prog_instr.opcode}")
                        if found_target:
                            self.instructions.append(prog_instr)
                            if self.debug_trace:
                                print(f"Adding to queue: PC={prog_instr.pc} {prog_instr.opcode} {prog_instr.operands}")
                    
                    if self.debug_trace:
                        print(f"Instruction queue after RET has {len(self.instructions)} instructions")
                        if len(self.instructions) == 0:
                            print("WARNING: Empty instruction queue after RET!")
                            for i, prog_instr in enumerate(self.program):
                                print(f"Program[{i}]: PC={prog_instr.pc} {prog_instr.opcode}")
                    
                    self.pending_control_flow = False
                elif instr.opcode == 'STORE':
                    addr = rs.vj + rs.a
                    self.memory[addr] = rs.vk

                # Broadcast on CDB
                if result is not None and dest_reg is not None:
                    if self.register_status[dest_reg] == rs.name:
                        self.registers[dest_reg] = result
                        self.register_status[dest_reg] = None
                    for rs_list in self.res_stations.values():
                        for other_rs in rs_list:
                            if other_rs.qj == rs.name:
                                other_rs.vj = result
                                other_rs.qj = None
                                other_rs.just_wrote = True  # Mark that this RS just received a result
                            if other_rs.qk == rs.name:
                                other_rs.vk = result
                                other_rs.qk = None
                                other_rs.just_wrote = True  # Mark that this RS just received a result

                # Handle control flow
                if instr.opcode == 'BEQ':
                    rA, rB = rs.vj, rs.vk
                    self.branch_count += 1
                    target_pc = instr.pc + 1 + (instr.operands[2] - 1)  # Subtract 1 from the offset
                    if target_pc < 0:  # Check for negative PC
                        messagebox.showerror("Error", f"Invalid branch target: PC cannot be negative (attempted to branch to {target_pc})")
                        # Reset simulator state
                        self.instructions.clear()
                        self.pending_control_flow = False
                        # Clear all reservation stations
                        for rs_list in self.res_stations.values():
                            for rs in rs_list:
                                rs.clear()
                        return
                    
                    if rA == rB:  # Taken
                        self.mispredictions += 1  # Always not taken predictor
                        self.current_pc = target_pc
                        # Clear instruction queue and reload instructions from new PC
                        self.instructions.clear()
                        # Find the instruction with the target PC and add all subsequent instructions
                        found_target = False
                        for instr in self.program:
                            if instr.pc == target_pc:
                                found_target = True
                            if found_target:
                                self.instructions.append(instr)
                    else:
                        self.current_pc = instr.pc + 1
                    self.pending_control_flow = False
                elif instr.opcode == 'STORE':
                    addr = rs.vj + rs.a
                    self.memory[addr] = rs.vk

                # Mark completion for all instruction types
                instr.completed = True
                self.completed_instructions += 1
                
                # Mark the RS as having written its result, but don't clear it yet
                rs.wrote_result = True

        # Execute stage
        for rs_list in self.res_stations.values():
            for rs in rs_list:
                # Only start execution if not just wrote in this cycle
                if rs.busy and not rs.executing and rs.qj is None and rs.qk is None and not rs.just_wrote:
                    rs.executing = True
                    rs.cycles_left = rs.exec_cycles
                    rs.instruction.start_exec_cycle = self.cycle
                elif rs.executing and rs.cycles_left > 0:
                    rs.cycles_left -= 1
                    if rs.cycles_left == 0:
                        rs.instruction.end_exec_cycle = self.cycle
                # Reset just_wrote flag at the end of the cycle
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

                # Set up reservation station
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
                    # STORE should not block subsequent instructions from issuing
                    # self.pending_control_flow = True
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
                elif instr.opcode == 'CALL':
                    free_rs.a = instr.operands[0]
                    self.register_status[1] = free_rs.name
                    self.pending_control_flow = True
                elif instr.opcode == 'RET':
                    if self.register_status[1]:
                        free_rs.qj = self.register_status[1]
                    else:
                        free_rs.vj = self.registers[1]
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
        # Update cycle and PC labels with color coding
        self.cycle_label.configure(
            text=f"Cycle: {self.cycle}",
            foreground=COLORS['accent']
        )
        self.pc_label.configure(
            text=f"Current PC: {self.current_pc}",
            foreground=COLORS['accent']
        )

        # Clear all Treeviews
        for tree in [self.rs_tree, self.reg_tree, self.mem_tree, self.instr_tree]:
            for item in tree.get_children():
                tree.delete(item)

        # Update Reservation Stations Treeview
        rs_parents = {}
        for rs_type, rs_list in self.res_stations.items():
            rs_parents[rs_type] = self.rs_tree.insert("", "end", text=rs_type, open=True)
            for rs in rs_list:
                if rs.busy:
                    op = rs.instruction.opcode if rs.instruction else ""
                else:
                    op = ""
                    
                status = "Wrote" if rs.wrote_result else "Executing" if rs.executing else "Waiting" if rs.busy else ""
                    
                values = [
                    rs.name,
                    "Yes" if rs.busy else "No",
                    op,
                    rs.vj if rs.vj is not None else "",
                    rs.vk if rs.vk is not None else "",
                    rs.qj if rs.qj is not None else "",
                    rs.qk if rs.qk is not None else "",
                    rs.a if rs.a is not None else "",
                    status,
                    rs.cycles_left if rs.busy else ""
                ]
                self.rs_tree.insert(rs_parents[rs_type], "end", values=values)

        # Update Registers Treeview
        for i, (val, qi) in enumerate(zip(self.registers, self.register_status)):
            self.reg_tree.insert("", "end", text=f"R{i}", values=(val, qi or "-"))

        # Update Memory Treeview (non-zero locations)
        for addr, val in sorted(self.memory.items()):
            if val != 0:
                self.mem_tree.insert("", "end", text=str(addr), values=(val,))

        # Update Instructions Treeview
        for i, instr in enumerate(self.program):
            values = (
                instr.pc,
                f"{instr.opcode} {' '.join(map(str, instr.operands))}",
                instr.issue_cycle or "-",
                instr.start_exec_cycle or "-",
                instr.end_exec_cycle or "-",
                instr.write_cycle or "-"
            )
            self.instr_tree.insert("", "end", text="", values=values)

    def show_results(self):
        total_cycles = self.cycle
        ipc = self.completed_instructions / total_cycles if total_cycles > 0 else 0
        mispred_pct = (self.mispredictions / self.branch_count * 100) if self.branch_count > 0 else 0

        # Create a new top-level window for results with improved styling
        result_window = tk.Toplevel(self.root)
        result_window.title("Simulation Results")
        result_window.geometry("800x600")
        result_window.configure(bg=COLORS['bg'])
        
        # Apply modern styling to the results window
        style = ttk.Style()
        style.configure("Results.TFrame",
            background=COLORS['bg'],
            padding=10)
        
        style.configure("Results.TLabel",
            font=("Arial", 11),
            background=COLORS['bg'],
            foreground=COLORS['fg'])
        
        style.configure("ResultsHeader.TLabel",
            font=("Arial", 12, "bold"),
            background=COLORS['bg'],
            foreground=COLORS['accent'])
        
        # Create custom styles for statistics
        style.configure("Stats.TLabel",
            font=("Arial", 11),
            padding=5,
            background=COLORS['bg'])
        
        style.configure("StatsValue.TLabel",
            font=("Arial", 11, "bold"),
            padding=5,
            foreground=COLORS['accent'],
            background=COLORS['bg'])
        
        # Summary tab
        summary_frame = ttk.Frame(result_window)
        notebook = ttk.Notebook(result_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Summary frame
        summary_frame = ttk.Frame(notebook)
        notebook.add(summary_frame, text="Summary")
        
        # Statistics display
        stats_frame = ttk.LabelFrame(summary_frame, text="Performance Statistics")
        stats_frame.pack(fill=tk.X, padx=10, pady=10)
        
        stats = [
            ("Total Cycles:", str(total_cycles)),
            ("Instructions Completed:", str(self.completed_instructions)),
            ("IPC:", f"{ipc:.2f}"),
            ("Conditional Branches:", str(self.branch_count)),
            ("Branch Mispredictions:", str(self.mispredictions)),
            ("Misprediction Percentage:", f"{mispred_pct:.2f}%")
        ]
        
        for i, (label, value) in enumerate(stats):
            ttk.Label(stats_frame, text=label, font=("Arial", 10, "bold")).grid(row=i, column=0, sticky="w", padx=20, pady=5)
            ttk.Label(stats_frame, text=value).grid(row=i, column=1, sticky="w", padx=20, pady=5)
        
        # Instruction timing tab
        timing_frame = ttk.Frame(notebook)
        notebook.add(timing_frame, text="Instruction Timing")
        
        # Create a scrollable frame for the timing table
        timing_scroll_frame = ttk.Frame(timing_frame)
        timing_scroll_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Add scrollbars
        timing_h_scroll = ttk.Scrollbar(timing_scroll_frame, orient="horizontal")
        timing_h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        
        timing_v_scroll = ttk.Scrollbar(timing_scroll_frame, orient="vertical")
        timing_v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create a treeview for instruction timing
        timing_tree = ttk.Treeview(timing_scroll_frame, columns=("PC", "Instruction", "Issue", "StartExec", "EndExec", "Write"),
                                  xscrollcommand=timing_h_scroll.set, yscrollcommand=timing_v_scroll.set)
        timing_tree.pack(fill=tk.BOTH, expand=True)
        
        # Configure scrollbars
        timing_h_scroll.config(command=timing_tree.xview)
        timing_v_scroll.config(command=timing_tree.yview)
        
        timing_tree.heading("#0", text="")
        timing_tree.heading("PC", text="PC")
        timing_tree.heading("Instruction", text="Instruction")
        timing_tree.heading("Issue", text="Issue")
        timing_tree.heading("StartExec", text="Start Exec")
        timing_tree.heading("EndExec", text="End Exec")
        timing_tree.heading("Write", text="Write")
        
        timing_tree.column("#0", width=20, stretch=tk.NO)
        timing_tree.column("PC", width=60, stretch=tk.NO)
        timing_tree.column("Instruction", width=200, stretch=tk.YES)
        timing_tree.column("Issue", width=80, stretch=tk.NO)
        timing_tree.column("StartExec", width=80, stretch=tk.NO)
        timing_tree.column("EndExec", width=80, stretch=tk.NO)
        timing_tree.column("Write", width=80, stretch=tk.NO)
        
        # Add instruction timing data
        for instr in self.program:
            values = (
                instr.pc,
                f"{instr.opcode} {' '.join(map(str, instr.operands))}",
                instr.issue_cycle or "-",
                instr.start_exec_cycle or "-",
                instr.end_exec_cycle or "-",
                instr.write_cycle or "-"
            )
            timing_tree.insert("", "end", text="", values=values)

        # Add a close button with hover effect
        close_btn = ttk.Button(result_window, text="Close",
                             style="Accent.TButton",
                             command=result_window.destroy)
        close_btn.pack(side=tk.BOTTOM, pady=10)
        
        # Make the results window modal
        result_window.transient(self.root)
        result_window.grab_set()
        
        # Center the window on screen
        result_window.update_idletasks()
        width = result_window.winfo_width()
        height = result_window.winfo_height()
        x = (result_window.winfo_screenwidth() // 2) - (width // 2)
        y = (result_window.winfo_screenheight() // 2) - (height // 2)
        result_window.geometry(f'{width}x{height}+{x}+{y}')

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Tomasulo Simulator - femTomas")
    root.geometry("1200x800")  # Set initial window size
    
    # Configure row and column weights for proper resizing
    root.rowconfigure(0, weight=1)
    root.rowconfigure(1, weight=1)
    root.columnconfigure(0, weight=1)
    
    app = TomasuloSimulator(root)
    root.mainloop()
