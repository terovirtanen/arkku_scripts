from writer import Writer
import font10_fi as fifont10
import font20_fi as fifont20

import config
from window_base import WindowBase


class WindowSpotPrices(WindowBase):
    WIDTH = config.EPD_WIDTH // 2
    HEIGHT = config.EPD_HEIGHT // 2
    XSTART = config.EPD_WIDTH // 2
    YSTART = config.EPD_HEIGHT // 2
    XEND = config.EPD_WIDTH
    YEND = config.EPD_HEIGHT

    title = "Pörssisähkö"
    scale_min = -5
    scale_max = 30
    max_bars = 20

    def __init__(self, epd):
        self.current_price = None
        self.price_points = []
        super().__init__(epd, self.XSTART, self.YSTART, self.XEND, self.YEND)

    def _write_title(self):
        writer = Writer(self.imagered, fifont20)
        Writer.set_textpos(self.imagered, 10, 10)
        writer.printstring(self.title)

    def _format_price(self, value):
        if value is None:
            return "--.-"
        return "%.1f" % value

    def _draw_text(self, text, y, x, font_module=fifont10):
        writer = Writer(self.imageblack, font_module)
        Writer.set_textpos(self.imageblack, y, x)
        writer.printstring(text, invert=True)

    def _draw_current_price(self):
        self._draw_text("Nyt", 70, 18, fifont10)
        self._draw_text(self._format_price(self.current_price), 98, 18, fifont20)
        self._draw_text("c/kWh", 126, 18, fifont10)

    def _value_to_y(self, value, graph_top, graph_height):
        clipped = value
        if clipped < self.scale_min:
            clipped = self.scale_min
        if clipped > self.scale_max:
            clipped = self.scale_max
        scaled = self.scale_max - clipped
        return graph_top + int((scaled * graph_height) / (self.scale_max - self.scale_min))

    def _draw_graph(self):
        graph_top = 58
        graph_height = 132
        graph_bottom = graph_top + graph_height
        graph_left = 170
        graph_width = self.width - graph_left - 10
        zero_y = self._value_to_y(0, graph_top, graph_height)

        self.imageblack.vline(graph_left, graph_top, graph_height + 1, 0x00)
        self.imageblack.hline(graph_left, zero_y, graph_width, 0x00)

        self._draw_text("30", graph_top - 5, 138, fifont10)
        self._draw_text("0", zero_y - 5, 145, fifont10)
        self._draw_text("-5", graph_bottom - 10, 138, fifont10)

        points = self.price_points[:self.max_bars]
        if not points:
            self._draw_text("Ei dataa", 110, 220, fifont10)
            return

        bar_gap = 2
        bar_width = graph_width // len(points) - bar_gap
        if bar_width < 2:
            bar_width = 2

        x = graph_left + 4
        last_hour_label = None
        for hour, quarter, value in points:
            bar_top_y = self._value_to_y(value, graph_top, graph_height)
            if value >= 0:
                self.imageblack.fill_rect(x, bar_top_y, bar_width, zero_y - bar_top_y, 0x00)
            else:
                self.imageblack.fill_rect(x, zero_y, bar_width, bar_top_y - zero_y, 0x00)

            if quarter == 0 and hour != last_hour_label:
                label = "%02d" % hour
                self._draw_text(label, graph_bottom + 8, x - 2, fifont10)
                last_hour_label = hour

            x += bar_width + bar_gap
            if x >= graph_left + graph_width:
                break

    def _redraw_black(self):
        self.imageblack.fill(0xff)
        self._draw_current_price()
        self._draw_graph()

    def _refresh(self, refresh=True):        
        self._redraw_black()
        if refresh:
            self.displayPartialBlack()

    def init(self):
        self.imageblack.fill(0xff)
        self.imagered.fill(0x00)
        self._write_title()
        self._redraw_black()

    def update_prices(self, current_price, price_points, refresh=True):
        if price_points is None:
            price_points = []

        if refresh and current_price == self.current_price and price_points == self.price_points:
            return

        self.current_price = current_price
        self.price_points = price_points
        
        self._refresh(refresh)