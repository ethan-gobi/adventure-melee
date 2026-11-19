/* Stand-in for powerpc-eabi-gcc: logs its arguments next to itself and fails, so nothing is compiled silently. */
#include <stdio.h>
int main(int argc, char **argv) {
    FILE *f = fopen("C:\adventure-melee\tools\ppc-shim\calls.log", "a");
    if (f) { for (int i = 0; i < argc; i++) fprintf(f, "%s ", argv[i]); fprintf(f, "\n"); fclose(f); }
    fprintf(stderr, "ppc-shim: not a compiler; use precompiled .o inputs\n");
    return 1;
}
