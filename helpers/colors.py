import binascii
import numpy as np
import scipy.cluster
from PIL import Image
import requests

MONOTONE_THRESHOLD = 50
DARK_THRESHOLD = 70
BRIGHT_THRESHOLD = 650
DEFAULT_COLORS = ((148, 74, 255), (43, 255, 169))
NUM_CLUSTERS = 3


class Color:
    def __init__(self, rgb, count):
        self.rgb = rgb
        self.count = count

    def is_dark(self):
        return sum(self.rgb) < DARK_THRESHOLD

    def is_bright(self):
        return sum(self.rgb) > BRIGHT_THRESHOLD

    # Makes the color's rgb maximally bright without losing proportions
    def brighten(self):
        scale = 255 / (max(self.rgb) + 1)
        bright = tuple(round(i * scale) for i in self.rgb)
        self.rgb = bright

    def difference(self, another):
        return sum(list(np.absolute(np.subtract(self.rgb, another.rgb))))

    def toned(self):
        # Return an rgb that doesn't go over the brightness threshold
        if not self.is_bright():
            return self.rgb
        # Returns a toned down rgb of the color that stays below the brightness threshold
        scale = BRIGHT_THRESHOLD/sum(self.rgb)
        toned = tuple(round(i * scale) for i in self.rgb)
        return toned

# Downloads an image from url and returns two most distinguishable of n dominant colors
def gradient_from_url(url):
    im = Image.open(requests.get(url, stream=True).raw)
    im = im.resize((50, 50))  # resize image to save (a lot of) time
    ar = np.asarray(im)
    shape = ar.shape
    ar = ar.reshape(np.product(shape[:2]), shape[2]).astype(float)

    codes = scipy.cluster.vq.kmeans(ar, NUM_CLUSTERS)[0]  # find clusters
    vecs = scipy.cluster.vq.vq(ar, codes)[0]  # assign codes
    counts = np.histogram(vecs, len(codes))[0]  # count occurrences
    contains_black = False

    # Get rgb colors from the clusters
    colors = []
    for i in range(len(codes)):
        color = binascii.hexlify(bytearray(int(c) for c in codes[i])).decode('ascii')
        rgb = tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))  # convert hex to rgb
        colors.append(Color(rgb, counts[i]))  # save color along with it's cluster size

    # Check if the dominant color is too dark
    dominant_color = max(colors, key=lambda c: c.count)
    dark_image = dominant_color.is_dark()

    bright_colors = []
    for color in colors:
        if not color.is_dark():
            color.brighten()
            bright_colors.append(color)
    bright_colors.sort(key=lambda c: c.count, reverse=True)

    if len(bright_colors) < 2:
        # In case there are no bright colors, return the default gradient with dominant for background
        return DEFAULT_COLORS

    if len(bright_colors) == 2:
        # If there are only two bright colors left, use them as the gradient
        gradient_colors = bright_colors

    if len(bright_colors) > 2:
        # Compares pairs of colors and returns the most distinguishable one
        # Note this will not work exactly for more than three clusters
        pairs = []
        for i in range(len(colors)):
            color1 = colors[i]
            color2 = colors[(i + 1) % len(colors)]
            # Create a pair with the more dominant color first
            sorted_pair = sorted([color1, color2], key=lambda c: c.count, reverse=True)
            pairs.append(sorted_pair)
        # Select the pair with the highest difference
        gradient_colors = max(pairs, key=lambda pair: pair[0].difference(pair[1]))

    if gradient_colors[0].difference(gradient_colors[1]) < MONOTONE_THRESHOLD:
        # The image is too monotone to make a gradient,but the leading color can be used for a background
        return DEFAULT_COLORS[0], DEFAULT_COLORS[1], dominant_color.rgb

    # If the image is dark don't include a background color, it will be black instead
    gradient_rgb = [gradient_colors[0].rgb, gradient_colors[1].rgb]
    if not dark_image:
        gradient_rgb.append(gradient_colors[0].toned())
    return gradient_rgb

    # sorted_pair = sorted([color1, color2], key=lambda c: c['counts'], reverse=True)  # always keep the more dominant color first
    # print(f"BIGGEST DIFFERENCE: {gradient_colors[1]}")
    # if gradient_colors[1] < 20:
    #    raise Exception("Colors too similar")
    # if contains_black:
    #    gradient_colors.append((0, 0, 0))
