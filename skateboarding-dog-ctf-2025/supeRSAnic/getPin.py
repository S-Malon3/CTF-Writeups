import argparse
from Crypto.Util.number import bytes_to_long

def validatePin(pin, n, e, c):
    pinBytes = pin.encode()
    longPin = bytes_to_long(pinBytes)
    encryptedGuess = pow(longPin, e, n)

    return (c == encryptedGuess)

parser = argparse.ArgumentParser()

parser.add_argument("n", type=int)
parser.add_argument("e", type=int)
parser.add_argument("c", type=int)

args = parser.parse_args()

n = args.n
e = args.e
c = args.c
    
print(n, e, c)

for i in range(999999):
    pin_str = str(i).zfill(6)
    print("Trying pin ", pin_str, "\r", end="", flush=True)
    if (validatePin(pin_str, n, e, c)):
        print()
        print("PIN: ", i)
        break
