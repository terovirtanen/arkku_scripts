from writer import Writer
import font10_fi as fifont10
import font20_fi as fifont20

import config
from window_base import WindowBase


class WindowHeating(WindowBase):
    WIDTH = config.EPD_WIDTH // 2
    HEIGHT = config.EPD_HEIGHT // 2
    XSTART = 0
    YSTART = config.EPD_HEIGHT // 2
    XEND = config.EPD_WIDTH // 2
    YEND = config.EPD_HEIGHT

    title = "Lämmitys"
    left_margin = 10
    top_margin = 10

    tank_left = 40
    tank_top = 70
    tank_width = 110
    tank_height = 125

    boiler_left = 255
    boiler_top = 82
    boiler_width = 82
    boiler_height = 98

    connector_top_y = 100
    connector_bottom_y = 165

    tank_top_text_y = tank_top + 14
    tank_bottom_text_y = tank_top + tank_height - 28
    boiler_text_y = boiler_top + 12

    def __init__(self, epd):
        self.tank_down_temperature = None
        self.tank_up_temperature = None
        self.tank_resistance_running = False
        self.boiler_temperature = None
        self.boiler_running = False
        super().__init__(epd, self.XSTART, self.YSTART, self.XEND, self.YEND)

    def _write_title(self):
        writer = Writer(self.imagered, fifont20)
        Writer.set_textpos(self.imagered, self.top_margin, self.left_margin)
        writer.printstring(self.title)

    def _format_temperature(self, value):
        if value is None:
            return "--.-C"
        return "%sC" % value

    def _centered_text_x(self, text, area_left, area_width, font_module):
        text_width = len(text) * font_module.max_width()
        x = area_left + (area_width - text_width) // 2
        if x < area_left:
            return area_left
        return x

    def _draw_text(self, text, y, x, font_module=fifont10):
        writer = Writer(self.imageblack, font_module)
        Writer.set_textpos(self.imageblack, y, x)
        writer.printstring(text, invert=True)

    def _draw_cylinder_outline(self, left, top, width, height):
        right = left + width - 1
        bottom = top + height - 1
        cap_height = 16
        inset_outer = 14
        inset_inner = 7

        self.imageblack.hline(left + inset_outer, top, width - 2 * inset_outer, 0x00)
        self.imageblack.line(left + inset_inner, top + cap_height // 2, left + inset_outer, top, 0x00)
        self.imageblack.line(left, top + cap_height, left + inset_inner, top + cap_height // 2, 0x00)
        self.imageblack.line(right - inset_outer, top, right - inset_inner, top + cap_height // 2, 0x00)
        self.imageblack.line(right - inset_inner, top + cap_height // 2, right, top + cap_height, 0x00)

        self.imageblack.vline(left, top + cap_height, height - 2 * cap_height, 0x00)
        self.imageblack.vline(right, top + cap_height, height - 2 * cap_height, 0x00)

        self.imageblack.line(left, bottom - cap_height, left + inset_inner, bottom - cap_height // 2, 0x00)
        self.imageblack.line(left + inset_inner, bottom - cap_height // 2, left + inset_outer, bottom, 0x00)
        self.imageblack.hline(left + inset_outer, bottom, width - 2 * inset_outer, 0x00)
        self.imageblack.line(right - inset_outer, bottom, right - inset_inner, bottom - cap_height // 2, 0x00)
        self.imageblack.line(right - inset_inner, bottom - cap_height // 2, right, bottom - cap_height, 0x00)

    def _draw_boiler_outline(self, left, top, width, height):
        self.imageblack.rect(left, top, width, height, 0x00)

    def _draw_connectors(self):
        tank_right = self.tank_left + self.tank_width - 1
        boiler_left = self.boiler_left
        self.imageblack.hline(tank_right, self.connector_top_y, boiler_left - tank_right + 1, 0x00)
        self.imageblack.hline(tank_right, self.connector_bottom_y, boiler_left - tank_right + 1, 0x00)

    def _draw_resistance_icon(self):
        if not self.tank_resistance_running:
            return

        center_x = self.tank_left + self.tank_width // 2
        start_y = self.tank_top + 38
        self.imageblack.vline(center_x, start_y - 12, 10, 0x00)
        self.imageblack.line(center_x, start_y, center_x - 14, start_y + 10, 0x00)
        self.imageblack.line(center_x - 14, start_y + 10, center_x + 14, start_y + 22, 0x00)
        self.imageblack.line(center_x + 14, start_y + 22, center_x - 14, start_y + 34, 0x00)
        self.imageblack.line(center_x - 14, start_y + 34, center_x + 14, start_y + 46, 0x00)
        self.imageblack.line(center_x + 14, start_y + 46, center_x, start_y + 56, 0x00)
        self.imageblack.vline(center_x, start_y + 56, 10, 0x00)

    def _draw_flame_icon(self):
        if not self.boiler_running:
            return

        center_x = self.boiler_left + self.boiler_width // 2
        base_y = self.boiler_top + self.boiler_height - 16
        self.imageblack.line(center_x, base_y - 24, center_x - 16, base_y, 0x00)
        self.imageblack.line(center_x - 16, base_y, center_x, base_y + 10, 0x00)
        self.imageblack.line(center_x, base_y + 10, center_x + 16, base_y, 0x00)
        self.imageblack.line(center_x + 16, base_y, center_x, base_y - 24, 0x00)
        self.imageblack.line(center_x, base_y - 13, center_x - 7, base_y + 2, 0x00)
        self.imageblack.line(center_x - 7, base_y + 2, center_x + 2, base_y - 4, 0x00)
        self.imageblack.line(center_x + 2, base_y - 4, center_x, base_y - 13, 0x00)

    def _clear_tank_top_temperature(self):
        self.imageblack.fill_rect(self.tank_left + 4, self.tank_top_text_y - 1, self.tank_width - 8, 14, 0xff)

    def _clear_tank_bottom_temperature(self):
        self.imageblack.fill_rect(self.tank_left + 4, self.tank_bottom_text_y - 1, self.tank_width - 8, 14, 0xff)

    def _clear_boiler_temperature(self):
        self.imageblack.fill_rect(self.boiler_left + 3, self.boiler_text_y - 1, self.boiler_width - 6, 14, 0xff)

    def _clear_resistance_icon(self):
        center_x = self.tank_left + self.tank_width // 2
        start_y = self.tank_top + 38
        self.imageblack.fill_rect(center_x - 16, start_y - 14, 33, 78, 0xff)

    def _clear_flame_icon(self):
        center_x = self.boiler_left + self.boiler_width // 2
        base_y = self.boiler_top + self.boiler_height - 16
        self.imageblack.fill_rect(center_x - 18, base_y - 26, 37, 40, 0xff)

    def _draw_tank_top_temperature(self):
        text = self._format_temperature(self.tank_up_temperature)
        text_left = self.tank_left + 8
        text_width = self.tank_width - 16
        self._draw_text(
            text,
            self.tank_top_text_y,
            self._centered_text_x(text, text_left, text_width, fifont10),
        )

    def _draw_tank_bottom_temperature(self):
        text = self._format_temperature(self.tank_down_temperature)
        text_left = self.tank_left + 8
        text_width = self.tank_width - 16
        self._draw_text(
            text,
            self.tank_bottom_text_y,
            self._centered_text_x(text, text_left, text_width, fifont10),
        )

    def _draw_boiler_temperature(self):
        text = self._format_temperature(self.boiler_temperature)
        text_left = self.boiler_left + 6
        text_width = self.boiler_width - 12
        self._draw_text(
            text,
            self.boiler_text_y,
            self._centered_text_x(text, text_left, text_width, fifont10),
        )

    def _draw_all_dynamic(self):
        self._draw_tank_top_temperature()
        self._draw_tank_bottom_temperature()
        self._draw_boiler_temperature()
        self._draw_resistance_icon()
        self._draw_flame_icon()

    def _draw_static(self):
        self._draw_cylinder_outline(self.tank_left, self.tank_top, self.tank_width, self.tank_height)
        self._draw_boiler_outline(self.boiler_left, self.boiler_top, self.boiler_width, self.boiler_height)
        self._draw_connectors()

    def _refresh(self):
        self.displayPartialBlack()

    def init(self):
        self.imageblack.fill(0xff)
        self.imagered.fill(0x00)
        self._write_title()
        self._draw_static()
        self._draw_all_dynamic()

    def update_tank_down_temperature(self, temperature, refresh=True):
        if temperature == self.tank_down_temperature:
            return
        self.tank_down_temperature = temperature
        self._clear_tank_bottom_temperature()
        self._draw_tank_bottom_temperature()
        if refresh:
            self._refresh()

    def update_tank_up_temperature(self, temperature, refresh=True):
        if temperature == self.tank_up_temperature:
            return
        self.tank_up_temperature = temperature
        self._clear_tank_top_temperature()
        self._draw_tank_top_temperature()
        if refresh:
            self._refresh()

    def update_tank_resistance_running(self, running, refresh=True):
        new_running = bool(running)
        if new_running == self.tank_resistance_running:
            return
        self.tank_resistance_running = new_running
        self._clear_resistance_icon()
        self._draw_resistance_icon()
        if refresh:
            self._refresh()

    def update_boiler_temperature(self, temperature, refresh=True):
        if temperature == self.boiler_temperature:
            return
        self.boiler_temperature = temperature
        self._clear_boiler_temperature()
        self._draw_boiler_temperature()
        if refresh:
            self._refresh()

    def update_boiler_running(self, running, refresh=True):
        new_running = bool(running)
        if new_running == self.boiler_running:
            return
        self.boiler_running = new_running
        self._clear_flame_icon()
        self._draw_flame_icon()
        if refresh:
            self._refresh()

    def update_values(
        self,
        tank_down_temperature=None,
        tank_up_temperature=None,
        tank_resistance_running=None,
        boiler_temperature=None,
        boiler_running=None,
        refresh=True,
    ):
        changed = False

        if tank_down_temperature != self.tank_down_temperature:
            self.tank_down_temperature = tank_down_temperature
            self._clear_tank_bottom_temperature()
            self._draw_tank_bottom_temperature()
            changed = True

        if tank_up_temperature != self.tank_up_temperature:
            self.tank_up_temperature = tank_up_temperature
            self._clear_tank_top_temperature()
            self._draw_tank_top_temperature()
            changed = True

        if boiler_temperature != self.boiler_temperature:
            self.boiler_temperature = boiler_temperature
            self._clear_boiler_temperature()
            self._draw_boiler_temperature()
            changed = True

        if tank_resistance_running is not None:
            new_running = bool(tank_resistance_running)
            if new_running != self.tank_resistance_running:
                self.tank_resistance_running = new_running
                self._clear_resistance_icon()
                self._draw_resistance_icon()
                changed = True

        if boiler_running is not None:
            new_running = bool(boiler_running)
            if new_running != self.boiler_running:
                self.boiler_running = new_running
                self._clear_flame_icon()
                self._draw_flame_icon()
                changed = True

        if changed and refresh:
            self._refresh()