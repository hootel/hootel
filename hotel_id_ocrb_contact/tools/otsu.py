# Image binarization - Otsu algorithm
#
# Author: Bostjan Cigan (http://zerocool.is-a-geek.net)
# Port to Python: Alexandre Díaz
from PIL import Image


class OtsuBinarize(object):

    def __init__(self):
        self.original = None
        self.grayscale = None
        self.binarized = None

    def run(self, inputImage):
        original = inputImage
        grayscale = self._toGray(original)
        binarized = self._binarize(grayscale)
        return binarized

    # Return histogram of grayscale image
    def imageHistogram(self, input):
        histogram = [0] * 256

        for i in range(input.getWidth()):
            for j in range(input.getHeight()):
                r, g, b = input.getPixel((i, j))
                histogram[r] += 1

        return histogram

    # The luminance method
    def _toGray(sefl, original):
        lum = Image.new('RGB', (original.getWidth(), original.getHeight()))

        for i in range(original.getWidth()):
            for j in range(original.getHeight()):
                # Get pixels by R, G, B
                r, g, b = original.getPixel((i, j))
                r = 0.21 * r + 0.71 * g + 0.07 * b

                # Write pixels into image
                lum[i][j] = (r, r, r)

        return lum

    # Get binary treshold using Otsu's method
    def _otsuTreshold(self, original):
        histogram = self._imageHistogram(original)
        total = original.getHeight() * original.getWidth()

        sum = 0.0
        for i in range(256):
            sum += i * histogram[i]

        sumB = 0.0
        wB = 0
        wF = 0

        varMax = 0.0
        threshold = 0

        for i in range(256):
            wB += histogram[i]
            if wB == 0:
                continue

            wF = total - wB
            if wF == 0:
                break

            sumB += i * histogram[i]
            mB = sumB / wB
            mF = (sum - sumB) / wF

            varBetween = wB * wF * (mB - mF) * (mB - mF)

            if varBetween > varMax:
                varMax = varBetween
                threshold = i

        return threshold

    def _binarize(self, original):
        threshold = self._otsuTreshold(original)
        binarized = Image.new('RGB',
                              (original.getWidth(), original.getHeight()))

        for i in range(original.getWidth()):
            for j in range(original.getHeight()):
                # Get pixels
                r, g, b = original.getPixel((i, j))
                newPixel = 255 if r > threshold else 0

                binarized[i][j] = (newPixel, newPixel, newPixel)

        return binarized
