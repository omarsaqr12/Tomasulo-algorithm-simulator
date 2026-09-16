# Example input for the GUI

These are **two-section reference snippets**, not files that the GUI can import directly. Paste instruction lines (before the blank separator) into **Assembly Program** and `address:value` pairs into **Memory**. The parser does not robustly strip semicolon comments, so remove comments before pasting, especially from memory entries. The program's starting PC defaults to zero.

| File | Observed content / caveat |
| --- | --- |
| [`t1.txt`](t1.txt) | LOAD → ADD dependency, BEQ, MUL, STORE; memory at addresses 0 and 1 |
| [`t2.txt`](t2.txt) | Multiple LOADs, dependent arithmetic, BEQ and CALL; may loop depending on state |
| [`t3.txt`](t3.txt) | Backward BEQ; useful for exploring control-flow and repeated-instruction limitations |
| [`t4.txt`](t4.txt) | `CALL -2`; deliberately out-of-program target, **not** a successful call/return demo |
| [`t5.txt`](t5.txt) | `BEQ ... -10`; invalid negative branch target from PC 2, **not** a runnable loop |
| [`t6.txt`](t6.txt) | Annotated multi-step call/return scenario; remove `; ...` comments before entering memory, and review branch comments against actual conditions |
| [`t7.txt`](t7.txt) | High initial memory value `60000`; useful for investigating the inconsistent 16-bit signed display |

None of these files constitute an independently checked golden-output regression suite. The automated headless tests are under [`../tests/`](../tests/).
