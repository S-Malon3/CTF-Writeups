import hashlib

files = ['flag_pixelised.png', 'flag_pixelised2.png', 'flag_pixelised4.png']
for f in files:
    with open(f, 'rb') as file:
        data = file.read()
        md5 = hashlib.md5(data).hexdigest()
        print(f"{f}: MD5 = {md5}")

# If they have different hashes, they contain different data despite looking the same
# Returned the same hashes, therefore the same image was being returned despite the inputted scale
