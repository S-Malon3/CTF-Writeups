from PIL import Image
import numpy as np

img = Image.open('flag_pixelised.png')
img_array = np.array(img)

# Check if ALL RGB values are exactly 255
print("Are all RGB values 255?", np.all(img_array[:,:,:3] == 255))

# Check if there are slight variations from pure white
print("RGB value range:", np.min(img_array[:,:,:3]), np.max(img_array[:,:,:3]))

# Check if there's pattern in the least significant bits
lsb = img_array[:,:,:3] & 1  # Extract LSB of each color channel
print("LSB pattern unique values:", np.unique(lsb))
