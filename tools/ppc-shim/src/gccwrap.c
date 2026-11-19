/* powerpc-eabi-gcc stand-in for MexTK: forwards to Zig's clang (compile) or lld (partial link -r).
   GCC-only flags that clang rejects are dropped; the GameCube CPU target is added. */
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
/* Zig location: set ZIG_EXE (e.g. the zig.exe from "pip install ziglang"); otherwise zig.exe must be on PATH. */
static const char *ZIG = "zig.exe";
static const char *DROP[] = {"-mogc", "-meabi", "-mhard-float", "-fpermissive", "-mcpu=750", NULL};
static int dropped(const char *a) { for (int i = 0; DROP[i]; i++) if (!strcmp(a, DROP[i])) return 1; return 0; }
static void add(char *cmd, const char *a) { strcat(cmd, " \""); strcat(cmd, a); strcat(cmd, "\""); }
int main(int argc, char **argv) {
    static char cmd[65536];
    int link = 0;
    for (int i = 1; i < argc; i++) if (!strcmp(argv[i], "-r")) link = 1;
    const char *zig = getenv("ZIG_EXE");
    snprintf(cmd, sizeof cmd, "\"%s\"", zig && *zig ? zig : ZIG);
    if (link) {
        strcat(cmd, " ld.lld");
        for (int i = 1; i < argc; i++) add(cmd, argv[i]);
    } else {
        strcat(cmd, " cc -target powerpc-freestanding-eabihf -mcpu=750 -fno-builtin -ffreestanding -fno-stack-protector"
                    " -fno-exceptions -fno-asynchronous-unwind-tables -ffunction-sections -fdata-sections -Wno-int-conversion -Wno-incompatible-pointer-types"
                    " -Wno-incompatible-function-pointer-types -Wno-implicit-function-declaration -Wno-return-type");
        for (int i = 1; i < argc; i++) if (!dropped(argv[i])) add(cmd, argv[i]);
    }
    FILE *log = fopen("C:\\adventure-melee\\tools\\ppc-shim\\calls.log", "a");
    if (log) { fprintf(log, "%s\n", cmd); fclose(log); }
    STARTUPINFOA si = {sizeof si}; PROCESS_INFORMATION pi;
    if (!CreateProcessA(NULL, cmd, NULL, NULL, TRUE, 0, NULL, NULL, &si, &pi)) { fprintf(stderr, "gccwrap: cannot start zig\n"); return 1; }
    WaitForSingleObject(pi.hProcess, INFINITE);
    DWORD code = 1; GetExitCodeProcess(pi.hProcess, &code);
    return (int)code;
}
