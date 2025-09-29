#include <stdio.h>
#include <unistd.h>
#include <stdint.h>
#include <sys/syscall.h>
#include <time.h>

int main() {
    //the main loop iterates over each of these data values, adding them together
    //to get different ASCII values to print
    int8_t data[] = {
        116,
        -7, -8, 3, 4, 21, -12, 2, 6,
        -20, 9, 9, 0, 1, -12, -1, 20, -12,
        -3, 3, 6, -8, 15, 13, -25, 22, -14,
        8, -6, 12, -7, 8, 0, -8, -67, 1, 1, 93,
        127
    };

    int r4 = 0;
    int r7 = data[0];  // Start with first value

    while (1) {
        int r0 = r4 + 1;
        int r1 = r7 - r0;

        uint8_t val = (uint8_t)r1;
        syscall(SYS_write, 1, &val, 1);

        struct timespec req = {0, 0};  // Change to {3600, 0} for original sleep
        struct timespec rem = {0, 0};
        syscall(SYS_nanosleep, &req, &rem);

        r4++;
        int8_t next_val = data[r4];
        if (next_val == 127) {
            break;
        }
        r7 += next_val;  // Add the next data value to running sum
    }

    syscall(SYS_exit, 0);
    return 0;
}
