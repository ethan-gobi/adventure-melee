"""Read the emulated GameCube memory of a running Dolphin process (Windows).

Finds the 32 MB region that starts with the game ID and reads big-endian values by GameCube address.
"""
import ctypes
import ctypes.wintypes as wt
import struct

PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_READ = 0x0010
MEM_COMMIT = 0x1000
k32 = ctypes.WinDLL("kernel32", use_last_error=True)


class MBI(ctypes.Structure):
    _fields_ = [("BaseAddress", ctypes.c_void_p), ("AllocationBase", ctypes.c_void_p), ("AllocationProtect", wt.DWORD),
                ("PartitionId", wt.WORD), ("RegionSize", ctypes.c_size_t), ("State", wt.DWORD), ("Protect", wt.DWORD), ("Type", wt.DWORD)]


k32.OpenProcess.restype = wt.HANDLE
k32.VirtualQueryEx.argtypes = [wt.HANDLE, ctypes.c_void_p, ctypes.POINTER(MBI), ctypes.c_size_t]
k32.VirtualQueryEx.restype = ctypes.c_size_t
k32.ReadProcessMemory.argtypes = [wt.HANDLE, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]


class GameMemory:
    def __init__(self, pid, game_id=b"GALE01"):
        self.h = k32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
        if not self.h:
            raise OSError("OpenProcess failed")
        self.game_id = game_id
        self.base = None

    def _raw(self, addr, n):
        buf = ctypes.create_string_buffer(n)
        got = ctypes.c_size_t(0)
        if not k32.ReadProcessMemory(self.h, ctypes.c_void_p(addr), buf, n, ctypes.byref(got)) or got.value != n:
            return None
        return buf.raw

    def find(self):
        """Locate emulated RAM. Returns True once the game ID is visible at its start."""
        addr = 0
        mbi = MBI()
        while k32.VirtualQueryEx(self.h, ctypes.c_void_p(addr), ctypes.byref(mbi), ctypes.sizeof(mbi)):
            size = mbi.RegionSize
            if mbi.State == MEM_COMMIT and size >= 0x1800000 and size <= 0x4000000:
                head = self._raw(mbi.BaseAddress, 6)
                if head == self.game_id:
                    self.base = mbi.BaseAddress
                    return True
            addr = (mbi.BaseAddress or 0) + size
            if addr >= 0x7FFFFFFFFFFF:
                break
        return False

    def valid(self, gc_addr, n=4):
        return 0x80000000 <= gc_addr and gc_addr + n <= 0x81800000

    def read(self, gc_addr, n):
        if not self.valid(gc_addr, n):
            return None
        return self._raw(self.base + (gc_addr - 0x80000000), n)

    def u8(self, a):
        d = self.read(a, 1); return None if d is None else d[0]

    def u16(self, a):
        d = self.read(a, 2); return None if d is None else struct.unpack(">H", d)[0]

    def u32(self, a):
        d = self.read(a, 4); return None if d is None else struct.unpack(">I", d)[0]

    def f32(self, a):
        d = self.read(a, 4); return None if d is None else struct.unpack(">f", d)[0]
