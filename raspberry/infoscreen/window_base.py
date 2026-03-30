# WindowBase class for managing a rectangular area on the ePaper display with separate black and red buffers.

# import framebuf2 as fb2
import framebuf2 as framebuf

# Unicode (ä/ö) support via peterhinch's writer
# https://github.com/peterhinch/micropython-font-to-py/blob/master/writer/writer_tests.py
from writer import Writer
import font10_fi as fifont10  # Use Finnish charset font
import font20_fi as fifont20  # Use Finnish charset font20

import config
import EPD_7in5_B

class WindowBase:
    def __init__(self, epd, Xstart, Ystart, Xend, Yend):
        if (Xend > config.EPD_WIDTH or Yend > config.EPD_HEIGHT):
            raise ValueError("WindowBase exceeds display dimensions")

        self.epd = epd
        self.Xstart = Xstart
        self.Ystart = Ystart
        self.Xend = Xend
        self.Yend = Yend

        self.width = Xend - Xstart
        self.height = Yend - Ystart

        if (self.width % 8 != 0):
            raise ValueError("width must be multiple of 8 for byte alignment!")

        self.buffer_black = bytearray(self.height * self.width // 8)
        self.buffer_red = bytearray(self.height * self.width // 8)
        self.imageblack = framebuf.FrameBuffer(self.buffer_black, self.width, self.height, framebuf.MONO_HLSB)
        self.imagered = framebuf.FrameBuffer(self.buffer_red, self.width, self.height, framebuf.MONO_HLSB)

        self.init()

    def init(self):
        # Prepare window: white background on both layers
        self.imageblack.fill(0xff)
        self.imagered.fill(0x00)

    def display(self):
        print("WindowBase display")
        self.epd.blit(self.imageblack, self.imagered, self.Xstart, self.Ystart)
        self.epd.display()

    def displayPartialBlack(self):
        print("WindowBase display partial black")
        self.epd.blit(self.imageblack, self.imagered, self.Xstart, self.Ystart)

        self.epd.init_part()
        self.epd.display_Partial(self.buffer_black, self.Xstart, self.Ystart, self.Xend, self.Yend)
