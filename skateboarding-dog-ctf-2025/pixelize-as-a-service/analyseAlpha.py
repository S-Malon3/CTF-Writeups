from PIL import Image
import numpy as np

img = Image.open('flag_pixelised.png')
img_array = np.array(img)

# Analyze the alpha channel (transparency values)
alpha_channel = img_array[:,:,3]
print("Alpha channel shape:", alpha_channel.shape)
print("Alpha value range:", np.min(alpha_channel), np.max(alpha_channel))
print("Unique alpha values:", np.unique(alpha_channel))

# The alpha values themselves might encode the flag
# Common encodings: ASCII, binary, or image data
