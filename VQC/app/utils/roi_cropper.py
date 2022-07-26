import numpy as np
import cv2 as cv
import logging
from app.utils import Util

logger = logging.getLogger("app")


class ROI_cropper(Util):
    """
        Class being able to crop region from image that we are interested in based either on edge detecion or color sampling
        Currently not used but may be usefull
    """

    def __init__(
        self,
        x1_i=0,
        x2_i=-1,
        y1_i=3,
        y2_i=-1,
        method="edge",
        canny_thresh_low=0,
        canny_thresh_top=255,
        thresh_border=677,
        low_color="#004000",
        high_color="#ffffff",
    ):
        """
            Args:
                x1_i, x2_i, y1_i, y2_i (int): indices which edge from the right, left, top, bottom should be considered as the edge of the region
                if background is not smooth it may be necessery to tune either those hyperparameters or different

                method (string): edge - using edge detection, color - using color segmentation. For Grayscale images only edge method will work properly

                canny_thresh_low, canny_thresh_top (int): Only for method 0! what threshold means here - Pixels above threshold top are considered
                as edges pixels below threshold low are discarded and pixels between those values are considered as edges iff they're connected to
                pixels that are above upper threshold it should be selected carefully as to big thresh_top may lead to not detecting those
                edges that we want and vice versa to low may detect edges that should be rejected

                thresh_border (int): again this value should be selected according to the new data this threshold basically means
                how many white pixels should be there to conider some row as an edge. I empirically made it 28k but probably it should be different

                low_color (string): hexadecimal value of the color from which we start building a thresholding range, USED IN METHOD 1
                high_color (string): hexadecimal value of the color at which we stop  building a thresholding range, USED IN METHOD 1
        """
        self.x1_i = x1_i
        self.x2_i = x2_i
        self.y1_i = y1_i
        self.y2_i = y2_i
        self.method = method
        self.canny_thresh_low = canny_thresh_low
        self.canny_thresh_top = canny_thresh_top
        self.thresh_border = thresh_border
        self.low_color = low_color
        self.high_color = high_color

    def set_params(
        self,
        x1_i=0,
        x2_i=-1,
        y1_i=0,
        y2_i=-1,
        method="edge",
        canny_thresh_low=51,
        canny_thresh_top=221,
        thresh_border=8200,
        low_color="#004000",
        high_color="#ffffff",
    ):
        self.x1_i = x1_i
        self.x2_i = x2_i
        self.y1_i = y1_i
        self.y2_i = y2_i
        self.method = method
        self.canny_thresh_low = canny_thresh_low
        self.canny_thresh_top = canny_thresh_top
        self.thresh_border = thresh_border
        self.low_color = low_color
        self.high_color = high_color

    def hex_to_rgb(self, value):
        value = value.lstrip("#")
        lv = len(value)
        return tuple(int(value[i : i + 2], 16) for i in range(0, lv, lv // 3))

    def apply(self, img):
        """
            Function that crop and return our ROI. It work as follows:
            based on method it either prepare image of edges or binary mask based on some color range
            -> if calulates sums along x and y axis and select first indives that are above some threshold from
            right, top, left and bottom those indices create rectangle of ROI
            -> crop ROI and return it

            Args:
                img (np.ndarray with shape (H,W,C) C=3): image to be cropped
            
            Returns:
                cropped (np.ndarray with shape (H,W,C): cropped image
        """
        if self.method == "edge":
            # canny edge detector in open cv takes both color images as well as grayscale and I wonder if I should change pixels to grayscale before.
            mask = cv.Canny(
                image=img,
                threshold1=self.canny_thresh_low,
                threshold2=self.canny_thresh_top,
            )
        elif self.method == "color":
            blur = cv.blur(img, (5, 5))
            blur = cv.medianBlur(blur, 5)
            blur = cv.GaussianBlur(blur, (5, 5), 0)

            rgb = cv.cvtColor(blur, cv.COLOR_BGR2RGB)

            low_color = self.hex_to_rgb(self.low_color)
            high_color = self.hex_to_rgb(self.high_color)

            mask = cv.inRange(rgb, low_color, high_color)

        else:
            print("Wrong method")
            return None

        sumX = np.sum(
            mask, axis=0
        )  # collapsing rows, values of pixels from columns are summed
        indicesX = np.argwhere(sumX > self.thresh_border)
        x1 = indicesX[self.x1_i][
            0
        ]  # getting x1_i-th value from the left as a top left x coordinate
        x2 = indicesX[self.x2_i][0]

        sumY = np.sum(mask, axis=1)  # collapsing columns, rowss are summed
        indicesY = np.argwhere(sumY > self.thresh_border)  # the same story as above
        y1 = indicesY[self.y1_i][0]
        y2 = indicesY[self.y2_i][0]

        cropped = img[y1 : y2 + 1, x1 : x2 + 1]  # cropping the image

        return cropped

