## Initial Analysis
This was an RSA Challenge where the goal was to decrypt a 6-digit PIN.  The modulus, public exponent and ciphertext were randomised but provided.  The catch was you "gotta go fast" and solve it on a Netcat server within a 30 second time limit.

The code for the challenge was provided with a fake flag, allowing me to see the validation logic for the pin, and since a 6 digit only has 1,000,000 possible values, brute force seemed like the easiest way to solve this.

## Solve
I wrote a Python script with `validatePin(pin, n, e, c)` that replicated the servers encryption process by:
 - Encrypting the candidate PIN using the provided `n` and `e`
 - Compared the resulting ciphertext to `c`
I then iterated this function over all possible 6-digit PINS.  The brute-force executed well under the time limit, allowing me to find the correct PIN and retrieve the flag from the server.
