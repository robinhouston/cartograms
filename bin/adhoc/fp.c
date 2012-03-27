/*  fp.c
 *
 *  Explore how decimal numbers are truncated by different machine representations.
 */
#include <stdio.h>
#include <stdlib.h>
#include <sysexits.h>

int main(int argc, char **argv)
{
    if (argc != 2) {
        fprintf(stderr, "Usage: %s number\n", argv[0]);
        return EX_USAGE;
    }
    float f = strtof(argv[1], 0);
    double d = strtod(argv[1], 0);
    long double l = strtold(argv[1], 0);

    printf("Float:  %.99g\n", f);
    printf("Double: %.99g\n", d);
    printf("Long:   %.99Lg\n", l);
}

