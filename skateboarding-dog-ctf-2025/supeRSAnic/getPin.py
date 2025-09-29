import argparse
from Crypto.Util.number import bytes_to_long

# Encrypt pin in same way as original code, compare pin to provided
# Ciphertext to validate
def validatePin(pin, n, e, c):
    pinBytes = pin.encode()
    longPin = bytes_to_long(pinBytes)
    encryptedGuess = pow(longPin, e, n)

    return (c == encryptedGuess)

# Use argparser to quickly parse in values
parser = argparse.ArgumentParser()

parser.add_argument("n", type=int)
parser.add_argument("e", type=int)
parser.add_argument("c", type=int)

args = parser.parse_args()

n = args.n
e = args.e
c = args.c
    
print(n, e, c)

# Brute force all pins
for i in range(999999):
    # Prepend all pins with 0s so "1" becomes "000001"
    pin_str = str(i).zfill(6)
    print("Trying pin ", pin_str, "\r", end="", flush=True)
    if (validatePin(pin_str, n, e, c)):
        print()
        print("PIN: ", i)
        break
