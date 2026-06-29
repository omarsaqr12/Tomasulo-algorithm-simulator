# Example Programs

Each `.txt` file contains a sample input for the simulator. The format is:

```
<assembly program, one instruction per line>

<initial memory, one `address:value` per line>
```

The two sections are separated by a blank line. When using the GUI, paste the
**program** lines into the *Assembly Program* box and the **memory** lines into
the *Memory* box.

## Files

| File     | Demonstrates                                                        |
| -------- | ------------------------------------------------------------------ |
| `t1.txt` | RAW dependency chain (`LOAD → ADD → MUL → STORE`) with a branch     |
| `t2.txt` | Multiple loads, a taken branch, and a `CALL`                        |
| `t3.txt` | —                                                                  |
| `t4.txt` | —                                                                  |
| `t5.txt` | Backward branch / loop behavior                                     |
| `t6.txt` | —                                                                  |
| `t7.txt` | —                                                                  |

### Example (`t1.txt`)

```
LOAD R1, 0(R2)
ADD R3, R1, R4
BEQ R3, R0, 2
MUL R5, R3, R1
STORE R5, 0(R2)
```

Memory:

```
0:10
1:20
```
