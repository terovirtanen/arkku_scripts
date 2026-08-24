from writer import Writer
import font10_fi as fifont10
import font20_fi as fifont20
import time

import config
import helsinki_time
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
        self.spot_prices_long = None
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

    def _parse_spot_day_key(self, day_key):
        parts = day_key.split('-')
        if len(parts) != 3:
            raise ValueError('Invalid day key: %s' % day_key)
        return (int(parts[0]), int(parts[1]), int(parts[2]))

    def _parse_spot_timestamp_key(self, timestamp_key):
        date_and_time = timestamp_key.split('T')
        if len(date_and_time) != 2:
            raise ValueError('Invalid timestamp key: %s' % timestamp_key)

        year, month, day = self._parse_spot_day_key(date_and_time[0])

        time_parts = date_and_time[1].split(':')
        if len(time_parts) < 2:
            raise ValueError('Invalid timestamp key: %s' % timestamp_key)

        hour = int(time_parts[0])
        minute = int(time_parts[1])
        quarter = minute // 15
        if quarter > 3:
            quarter = 3

        return (year, month, day, hour, quarter)

    def _build_spot_price_points(self):
        if not isinstance(self.spot_prices_long, dict):
            return []

        points = []
        for day_key, hours in self.spot_prices_long.items():
            # Support flat format, e.g. {'2026-3-30T18:1:25': 2.7}
            if isinstance(hours, (int, float)):
                try:
                    year, month, day, hour, quarter = self._parse_spot_timestamp_key(day_key)
                except ValueError:
                    continue

                points.append((year, month, day, hour, quarter, hours))
                continue

            try:
                year, month, day = self._parse_spot_day_key(day_key)
            except ValueError:
                continue

            if not isinstance(hours, dict):
                continue

            for hour_key, quarters in hours.items():
                try:
                    hour = int(hour_key)
                except ValueError:
                    continue

                if not isinstance(quarters, list):
                    continue

                for quarter, value in enumerate(quarters):
                    if quarter > 3:
                        break
                    if isinstance(value, (int, float)):
                        points.append((year, month, day, hour, quarter, value))

        points.sort()
        return points

# ('spot_prices_long', {'2026-4-5': {'22': [0, 0, 0, 0], '23': [0, 0, 0, 0], '18': [0, 0, 0, 0], '19': [0, 1, 1, 0], '21': [0, 1, 0, 0], '20': [1, 1, 1, 1]}})
    def _resolve_spot_prices(self):
        config.debug_print('_resolve_spot_prices')
        points = self._build_spot_price_points()
        if not points:
            return (None, [])

        now = helsinki_time.localtime()
        current_marker = (now[0], now[1], now[2], now[3], now[4] // 15)

        current_price = None
        future_points = []
        for year, month, day, hour, quarter, value in points:
            marker = (year, month, day, hour, quarter)
            if marker == current_marker and current_price is None:
                current_price = value
            if marker >= current_marker:
                future_points.append((hour, quarter, value))

        if current_price is None:
            if future_points:
                current_price = future_points[0][2]
            else:
                current_price = points[-1][5]

        returnValue = True
        if (self.current_price == current_price and self.price_points == future_points):
            returnValue = False

        self.current_price = current_price
        self.price_points = future_points

        return returnValue


    def init(self):
        self.imageblack.fill(0xff)
        self.imagered.fill(0x00)
        self._write_title()
        self._redraw_black()

    def update_prices(self, spot_prices_long = None, refresh=True):
        if spot_prices_long is not None:
            self.spot_prices_long = spot_prices_long

        update = self._resolve_spot_prices()

        if refresh or update:
            self._refresh(refresh)