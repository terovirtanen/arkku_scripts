# WindowTemperature class for managing a rectangular area on the ePaper display with separate black and red buffers.

# import framebuf2 as fb2
import framebuf2 as framebuf

# Unicode (ä/ö) support via peterhinch's writer
# https://github.com/peterhinch/micropython-font-to-py/blob/master/writer/writer_tests.py
from writer import Writer
import font10_fi as fifont10  # Use Finnish charset font
import font20_fi as fifont20  # Use Finnish charset font20

import config
import EPD_7in5_B
from window_base import WindowBase

class WindowTemperature(WindowBase):
    # Top-right quarter of the full display

    WIDTH = config.EPD_WIDTH // 2
    HEIGHT = config.EPD_HEIGHT // 2
    XSTART = config.EPD_WIDTH // 2
    YSTART = 0
    XEND = config.EPD_WIDTH
    YEND = config.EPD_HEIGHT // 2

    leftMargin = 10
    topMargin = 10
    lineSpacing = 30
    columnSpacing = 150
    valueWidth = 140
    valueHeight = 24

    title = "Lämpötilat"

    temperature_labels = [
        "Ulkolämpötila",
        "Ulkorakennus",
        "Autotalli",
    ]

    def __init__(self, epd):
        # Use class defaults for the top-right quarter
        Xstart = self.XSTART
        Ystart = self.YSTART
        Xend = self.XEND
        Yend = self.YEND

        self.temperature_values = [None] * len(self.temperature_labels)

        super().__init__(epd, Xstart, Ystart, Xend, Yend)
        # Initialize window contents (labels)
        self.init()

    def _writeTitle(self):
        # Header in red at 2x size using framebuf2
        w_red20 = Writer(self.imagered, fifont20)
        Writer.set_textpos(self.imagered, self.leftMargin, self.topMargin)
        w_red20.printstring(self.title)

    def _writeLabels(self):
        # Labels in black, one per row in list order
        w_black = Writer(self.imageblack, fifont20)
        for index, label in enumerate(self.temperature_labels):
            row_y = self.topMargin + (index + 1) * self.lineSpacing
            Writer.set_textpos(self.imageblack, row_y, self.leftMargin)
            w_black.printstring(label, invert=True)

    def _format_temperature(self, value):
        if value is None:
            return "--.- °C"
        return "%s °C" % value

    def _clearValueRows(self):
        # Clear value area for all rows before rewriting values.
        for index in range(len(self.temperature_labels)):
            row_y = self.topMargin + (index + 1) * self.lineSpacing
            self.imageblack.fill_rect(self.columnSpacing, row_y, self.valueWidth, self.valueHeight, 0xff)

    def _writeValues(self):
        # Values are written in the same order as labels, row by row.
        w_black = Writer(self.imageblack, fifont20)
        for index, value in enumerate(self.temperature_values):
            row_y = self.topMargin + (index + 1) * self.lineSpacing
            Writer.set_textpos(self.imageblack, row_y, self.columnSpacing)
            w_black.printstring(self._format_temperature(value), invert=True)

    def _update_temperature(self, index, temperature):
        self.temperature_values[index] = temperature
        self._clearValueRows()
        self._writeValues()
        self.displayPartialBlack()

    def init(self):
        # Prepare window: white background on both layers
        self.imageblack.fill(0xff)
        self.imagered.fill(0x00)

        self._writeTitle()
        self._writeLabels()
        self._writeValues()

    def update_outdoor_temperature(self, temperature):
        self._update_temperature(0, temperature)

    def update_outbuilding_temperature(self, temperature):
        self._update_temperature(1, temperature)
    
    def update_garage_temperature(self, temperature):
        self._update_temperature(2, temperature)

    def update_temperatures(self, temperatures):
        # Update all temperatures by list order and redraw all value rows.
        count = min(len(self.temperature_values), len(temperatures))
        for index in range(count):
            self.temperature_values[index] = temperatures[index]
        self._clearValueRows()
        self._writeValues()
        self.displayPartialBlack()