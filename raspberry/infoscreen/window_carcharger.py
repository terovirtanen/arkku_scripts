# WindowCarCharger class for managing the top-left quarter of the ePaper display for car charging status and schedule bar.

from writer import Writer
import font10_fi as fifont10
import font20_fi as fifont20
import config
import EPD_7in5_B
from window_base import WindowBase

class WindowCarCharger(WindowBase):
    # Top-left quarter of the full display
    WIDTH = config.EPD_WIDTH // 2
    HEIGHT = config.EPD_HEIGHT // 2
    XSTART = 0
    YSTART = 0
    XEND = config.EPD_WIDTH // 2
    YEND = config.EPD_HEIGHT // 2

    leftMargin = 10
    topMargin = 10
    lineSpacing = 30
    title = "Auton lataus"
    bar_top = 100
    bar_height = 24
    bar_left = 10
    bar_right = XEND - 10
    slot_minutes = 10
    start_hour = 10
    end_hour = 20

    status = "ei yhteyttä"  # "käynnissä" or "lepotila"
    slots = []  # List of bools indicating scheduled charging slots

    def __init__(self, epd):
        super().__init__(epd, self.XSTART, self.YSTART, self.XEND, self.YEND)
        self.status = "lepotila"  # "käynnissä" or "lepotila"
        self.slots = [False] * self._slot_count()  # False = not scheduled, True = scheduled
        self.init()

    def _slot_count(self):
        return ((self.end_hour - self.start_hour) * 60) // self.slot_minutes

    def _writeTitle(self):
        w_red20 = Writer(self.imagered, fifont20)
        Writer.set_textpos(self.imagered, self.topMargin, self.leftMargin)
        w_red20.printstring(self.title)

    def _writeStatus(self):
        w_black = Writer(self.imageblack, fifont20)
        Writer.set_textpos(self.imageblack, self.topMargin + self.lineSpacing, self.leftMargin)
        w_black.printstring(f"Tila: {self.status}", invert=True)

    def _writeBar(self):
        # Draw the time bar with slots
        slot_count = self._slot_count()
        bar_width = self.bar_right - self.bar_left
        slot_width = bar_width // slot_count
        y = self.bar_top
        for i in range(slot_count):
            x = self.bar_left + i * slot_width
            # Jos self.slots-listassa ei ole arvoa tälle indeksille, piirretään valkoinen (0xff)
            if i < len(self.slots):
                color = 0x00 if self.slots[i] else 0xff  # black if scheduled, white if not
            else:
                color = 0xff  # white (empty)
            self.imageblack.fill_rect(x, y, slot_width - 1, self.bar_height, color)
        # Draw start and end times
        w_black = Writer(self.imageblack, fifont10)
        text_y = y + self.bar_height + 5
        # Arvioidaan fontin korkeus (esim. 10)
        font_height = 10
        if text_y > self.HEIGHT - font_height:
            text_y = self.HEIGHT - font_height
            if text_y < 0:
                text_y = 0
        Writer.set_textpos(self.imageblack, text_y, self.bar_left)
        w_black.printstring(f"{self.start_hour:02d}:00")
        Writer.set_textpos(self.imageblack, text_y, self.bar_right - 40 )
        w_black.printstring(f"{self.end_hour:02d}:00")

    def init(self):
        self.imageblack.fill(0xff)
        self.imagered.fill(0x00)
        self._writeTitle()
        self._writeStatus()
        self._writeBar()

    def update_status(self, status):
        self.status = status
        self._writeStatus()

    def update_slots(self, slots):
        # slots: list of bools, len = slot_count
        self.slots = slots[:self._slot_count()]
        self._writeBar()
