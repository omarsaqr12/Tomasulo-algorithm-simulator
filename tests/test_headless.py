"""Headless smoke tests; avoid creating Tk windows. Not ISA conformance tests."""
import unittest
from collections import defaultdict, deque
from tomasulo_simulator import Instruction, ReservationStation, TomasuloSimulator


class SimulatorTests(unittest.TestCase):
    def build(self, lines, memory=None, registers=None):
        sim = TomasuloSimulator.__new__(TomasuloSimulator)
        sim.cycle = 1
        sim.max_cycles = 100
        sim.program = [sim.parse_instruction(line, pc) for pc, line in enumerate(lines)]
        sim.instructions = deque(sim.program)
        sim.current_pc = 0
        sim.pending_control_flow = False
        sim.registers = list(registers or [0] * 8)
        sim.register_status = [None] * 8
        sim.memory = defaultdict(int, memory or {})
        sim.completed_instructions = sim.branch_count = sim.mispredictions = 0
        sim.debug_trace = False
        kinds = {'LOAD': 2, 'STORE': 2, 'BEQ': 1, 'CALL_RET': 1,
                 'ADD_SUB': 2, 'NOR': 1, 'MUL': 2}
        sim.res_stations = {kind: [ReservationStation(kind + str(i), kind, cycles)
                                   for i in range(1, 4)]
                            for kind, cycles in kinds.items()}
        sim.op_to_rs = {'LOAD': 'LOAD', 'STORE': 'STORE', 'BEQ': 'BEQ',
                        'CALL': 'CALL_RET', 'RET': 'CALL_RET',
                        'ADD': 'ADD_SUB', 'SUB': 'ADD_SUB', 'NOR': 'NOR', 'MUL': 'MUL'}
        return sim

    def finish(self, sim):
        for _ in range(80):
            if not sim.instructions and all(not s.busy for stations in sim.res_stations.values()
                                             for s in stations):
                return
            sim.simulate_cycle()
            sim.cycle += 1
        self.fail('Simulator did not drain within the test cycle budget')

    def test_parse_load_and_call_range(self):
        sim = self.build([])
        self.assertEqual(sim.parse_instruction('LOAD R2, -3(R1)', 4).operands,
                         ['R2', 'R1', -3])
        self.assertEqual(sim.parse_instruction('CALL 63', 0).operands, [63])
        with self.assertRaises(ValueError):
            sim.parse_instruction('CALL 64', 0)

    def test_load_to_add_raw_forwarding(self):
        sim = self.build(['LOAD R1, 0(R0)', 'ADD R2, R1, R1'], memory={0: 7})
        self.finish(sim)
        self.assertEqual(sim.registers[2], 14)
        self.assertEqual(sim.completed_instructions, 2)
        self.assertLess(sim.program[0].issue_cycle, sim.program[0].write_cycle)
        self.assertGreater(sim.program[1].write_cycle, sim.program[0].write_cycle)

    @unittest.expectedFailure
    def test_known_gap_r0_is_hardwired(self):
        sim = self.build(['ADD R0, R1, R1'], registers=[0, 2, 0, 0, 0, 0, 0, 0])
        self.finish(sim)
        self.assertEqual(sim.registers[0], 0)
        self.assertIsNone(sim.register_status[0])

    @unittest.expectedFailure
    def test_known_gap_single_cdb_result_per_cycle(self):
        sim = self.build(['ADD R2, R1, R1', 'NOR R3, R1, R1'],
                         registers=[0, 2, 0, 0, 0, 0, 0, 0])
        self.finish(sim)
        self.assertNotEqual(sim.program[0].write_cycle, sim.program[1].write_cycle)


if __name__ == '__main__':
    unittest.main()
