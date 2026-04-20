# WindowTemperature class for managing a rectangular area on the ePaper display with separate black and red buffers.

# import framebuf2 as fb2

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

    def _row_y(self, index):
        # config.debug_print("row_y for index %d: %d" % (index, self.topMargin + (index + 1) * self.lineSpacing))
        return self.topMargin + (index + 1) * self.lineSpacing

    def _value_row_bounds(self, index):
        row_y = self._row_y(index)
        top = max(0, row_y - 2)
        bottom = min(self.height, row_y + fifont20.height() + 2)
        return (top, bottom)

    def _clearValueRow(self, index):
        top, bottom = self._value_row_bounds(index)
        config.debug_print("Clearing value row %d: top=%d, bottom=%d" % (index, top, bottom))
        self.imageblack.fill_rect(self.columnSpacing, top, self.valueWidth, bottom - top, 0xff)

    def _writeValue(self, index, framebuffer_obj=None, row_y=None, column_x=None):
        if framebuffer_obj is None:
            framebuffer_obj = self.imageblack
        if row_y is None:
            row_y = self._row_y(index)
        if column_x is None:
            column_x = self.columnSpacing

        config.debug_print("Writing value for index %d: %s at row_y=%d, column_x=%d" % (index, self._format_temperature(self.temperature_values[index]), row_y, column_x))
        w_black = Writer(framebuffer_obj, fifont20)
        Writer.set_textpos(framebuffer_obj, row_y, column_x)
        w_black.printstring(self._format_temperature(self.temperature_values[index]), invert=True)

    def _writeValues(self):
        # Values are written in the same order as labels, row by row.
        w_black = Writer(self.imageblack, fifont20)
        for index, value in enumerate(self.temperature_values):
            row_y = self._row_y(index)
            Writer.set_textpos(self.imageblack, row_y, self.columnSpacing)
            w_black.printstring(self._format_temperature(value), invert=True)

    def _value_partial_bounds(self):
        x_start = (self.columnSpacing // 8) * 8
        x_end = ((self.columnSpacing + self.valueWidth + 7) // 8) * 8
        return (x_start, x_end)

    def _displayValuePartialBlack(self, index):
        row_top, row_bottom = self._value_row_bounds(index)
        local_x_start, local_x_end = self._value_partial_bounds()
        config.debug_print("Displaying value subarea local_x_start=%d, local_x_end=%d, row_top=%d, row_bottom=%d" % (local_x_start, local_x_end, row_top, row_bottom))
        self.displayPartialBlackSubArea(local_x_start, row_top, local_x_end, row_bottom)

    def _update_temperature(self, index, temperature, refresh=True):
        self.temperature_values[index] = temperature
        self._clearValueRow(index)
        self._writeValue(index)
        if refresh:
            self._displayValuePartialBlack(index)

    def init(self):
        # Prepare window: white background on both layers
        self.imageblack.fill(0xff)
        self.imagered.fill(0x00)

        self._writeTitle()
        self._writeLabels()
        self._writeValues()

    def update_outdoor_temperature(self, temperature, refresh=True):
        self._update_temperature(0, temperature, refresh=refresh)

    def update_outbuilding_temperature(self, temperature, refresh=True):
        self._update_temperature(1, temperature, refresh=refresh)
    
    def update_garage_temperature(self, temperature, refresh=True):
        self._update_temperature(2, temperature, refresh=refresh)

    def update_temperatures(self, temperatures, refresh=True):
        # Update only changed rows by list order.
        count = min(len(self.temperature_values), len(temperatures))
        for index in range(count):
            if self.temperature_values[index] != temperatures[index]:
                self._update_temperature(index, temperatures[index], refresh=refresh)