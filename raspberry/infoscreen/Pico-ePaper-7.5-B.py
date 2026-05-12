# -*- coding: utf-8 -*-
# *****************************************************************************
"""
Waveshare 7.5 inch e-Paper display driver for Raspberry Pi Pico.
This module provides a driver class for controlling the Waveshare 7.5 inch 
three-color (Black/White/Red) e-Paper display module using MicroPython on 
Raspberry Pi Pico.
Classes:
    EPD_7in5_B: Main driver class for the 7.5 inch e-Paper display.
Constants:
    EPD_WIDTH: Display width in pixels (800)
    EPD_HEIGHT: Display height in pixels (480)
    RST_PIN: GPIO pin number for reset (12)
    DC_PIN: GPIO pin number for data/command selection (8)
    CS_PIN: GPIO pin number for SPI chip select (9)
    BUSY_PIN: GPIO pin number for busy status (13)
The EPD_7in5_B class provides methods for:
    - Hardware initialization and reset
    - Full display updates (black and red layers)
    - Partial display updates for faster refresh
    - Display clearing (white, black, or red)
    - Drawing text and graphics using framebuf
    - Low power sleep mode
Example usage:
    epd.imageblack.text("Hello", 5, 10, 0x00)
    epd.imagered.text("World", 5, 40, 0xff)
Note: This driver uses SPI communication and requires proper wiring of the
display module to the Raspberry Pi Pico according to the pin definitions.
License: MIT License
Author: Waveshare team
Version: V1.0
Date: 2021-05-27
"""
# * | File        :	  Pico_ePaper-7.5-B.py
# * | Author      :   Waveshare team
# * | Function    :   Electronic paper driver
# * | Info        :
# *----------------
# * | This version:   V1.0
# * | Date        :   2021-05-27
# # | Info        :   python demo
# -----------------------------------------------------------------------------
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documnetation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to  whom the Software is
# furished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS OR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#

from machine import Pin, SPI
# import framebuf
import utime
# import framebuf2 as fb2
import framebuf2 as framebuf

# Unicode (ä/ö) support via peterhinch's writer
# https://github.com/peterhinch/micropython-font-to-py/blob/master/writer/writer_tests.py
from writer import Writer
import font10_fi as fifont10  # Use Finnish charset font
import font20_fi as fifont20  # Use Finnish charset font20

def draw_scaled_text(writer, text, scale=2):
    """
    Draw text with font scaled by multiplier (e.g., 2 = double size).
    Returns the width of the rendered text in pixels.
    """
    if scale == 1:
        writer.printstring(text)
        return writer.stringlen(text)
    
    # Get the starting position
    row, col = Writer.set_textpos(writer.device, row=None, col=None)
    
    # Create a small temporary framebuf for one char at a time
    max_w = writer.font.max_width()
    max_h = writer.font.height()
    temp_buf = bytearray((max_w * max_h + 7) // 8)
    temp_fb = framebuf.FrameBuffer(temp_buf, max_w, max_h, framebuf.MONO_HLSB)
    
    total_width = 0
    for char in text:
        glyph, char_h, char_w = writer.font.get_ch(char)
        
        # Clear temp buffer
        temp_fb.fill(writer.bgcolor)
        
        # Draw single character to temp buffer
        div, mod = divmod(char_w, 8)
        gbytes = div + 1 if mod else div
        
        for y in range(char_h):
            for x in range(char_w):
                byte_idx = (x // 8) + y * gbytes
                bit_idx = 7 - (x % 8) if writer.font.reverse() else x % 8
                if byte_idx < len(glyph):
                    pixel_val = (glyph[byte_idx] >> bit_idx) & 1
                    if pixel_val:
                        temp_fb.pixel(x, y, writer.fgcolor)
        
        # Scale and blit to device
        for y in range(char_h):
            for x in range(char_w):
                if temp_fb.pixel(x, y) == writer.fgcolor:
                    # Draw scaled pixel as scale x scale rectangle
                    writer.device.fill_rect(col + total_width + x * scale, 
                                          row + y * scale, 
                                          scale, scale, 
                                          writer.fgcolor)
        
        total_width += char_w * scale
    
    # Update writer position
    Writer.set_textpos(writer.device, row=row, col=col + total_width)
    return total_width

# Optional: sync RTC from NTP (requires Wi‑Fi connection)
def try_ntp_sync():
    try:
        import ntptime
        ntptime.settime()  # sets RTC to UTC
        print("NTP-aika synkronoitu (UTC)")
    except Exception as e:
        # No Wi‑Fi or NTP unavailable — continue with current RTC
        print("NTP-synkronointi epäonnistui:", e)

# Display resolution
EPD_WIDTH       = 800
EPD_HEIGHT      = 480

EPD_WIDTH_WIN1  = 160
EPD_HEIGHT_WIN1 = 80

RST_PIN         = 12
DC_PIN          = 8
CS_PIN          = 9
BUSY_PIN        = 13

# EPD command cheat sheet (7.5" B, practical mapping used in this driver)
# Source references:
# - Waveshare wiki: https://www.waveshare.com/wiki/Pico-ePaper-7.5-B
# - 7.5inch e-Paper B specification PDF (register/command details)
# - Waveshare Pico_ePaper_Code reference drivers
#
# 0x00 : PANEL SETTING
#        Valitsee paneelin ajotilan (tässä 3-väri/full- ja partial-sekvensseille).
# 0x04 : POWER ON
#        Kytkee panelin sisäiset HV-jännitteet päälle (BUSY pitää odottaa).
# 0x06 : BOOSTER SOFT START
#        Boosterin pehmeä käynnistys (jännitenoston ajoitus/profiili).
#        Tämän ajurin datat: 0x17, 0x17, 0x28, 0x17.
#        3. tavu (0x28) vaikuttaa käynnistysprofiiliin; Wavesharella vaihtoehto 0x38.
# 0x10 : WRITE RAM
#        Kirjoittaa 1. kuvatason RAMiin (tässä ajurissa black/white-puskuri).
# 0x12 : DISPLAY REFRESH
#        Käynnistää varsinaisen päivitysaallon (vasta tämä tuo RAM-sisällön näkyviin).
# 0x13 : WRITE RAM
#        Kirjoittaa 2. kuvatason RAMiin (tässä ajurissa red/white-puskuri).
# 0x15 : VCOM-tilaan liittyvä ohjaus
#        Vendor-sekvenssissä 0x00; jätetään ennalleen yhteensopivuuden vuoksi.
# 0x50 : VCOM AND DATA INTERVAL SETTING
#        Säätää VCOM/data-aikaväliä sekä border-käyttäytymistä.
# 0x60 : TCON SETTING
#        Ohjaimen sisäinen timing-asetus gate/source-ohjaukselle.
# 0x61 : RESOLUTION SETTING
#        Asettaa paneelin resoluution (800 x 480).
# 0x65 : Resolution related vendor setting
#        Lisäresoluutio-/offset-asetus (Waveshare init-sekvenssin osa).
# 0x90 : PARTIAL WINDOW
#        Määrittää osapäivityksen ikkunan rajat.
# 0x91 : PARTIAL IN
#        Siirtää ohjaimen partial-tilaan.
# 0x02 : POWER OFF
#        Sammuttaa HV-ajot turvallisesti.
# 0x07 : DEEP SLEEP
#        Syväuni; herätys vaatii reset+init.

class FrameWindow:
    def __init__(self, epd, Xstart, Ystart, Xend, Yend):
        if (Xend > EPD_WIDTH or Yend > EPD_HEIGHT):
            raise ValueError("FrameWindow exceeds display dimensions")

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
        print("FrameWindow display")
        # self.epd.display_Partial_Both(self.buffer_black, self.buffer_red, self.Xstart, self.Ystart, self.Xend, self.Yend)
        # self.epd.display_Partial(self.buffer_black, self.Xstart, self.Ystart, self.Xend, self.Yend)
        self.epd.blit(self.imageblack, self.imagered, self.Xstart, self.Ystart)
        self.epd.display()



class TempereratureWindow(FrameWindow):
    # Top-right quarter of the full display

    WIDTH = EPD_WIDTH // 2
    HEIGHT = EPD_HEIGHT // 2
    XSTART = EPD_WIDTH // 2
    YSTART = 0
    XEND = EPD_WIDTH
    YEND = EPD_HEIGHT // 2

    def __init__(self, epd):
        # Use class defaults for the top-right quarter
        Xstart = self.XSTART
        Ystart = self.YSTART
        Xend = self.XEND
        Yend = self.YEND

        super().__init__(epd, Xstart, Ystart, Xend, Yend)
        # Initialize window contents (labels)
        self.init()

    def init(self):
        # Prepare window: white background on both layers
        self.imageblack.fill(0xff)
        self.imagered.fill(0x00)

        # Header in red at 2x size using framebuf2
        # fb2_red = fb2.FrameBuffer(self.buffer_red, self.width, self.height, framebuf.MONO_HLSB)

        w_red20 = Writer(self.imagered, fifont20)
        Writer.set_textpos(self.imagered, 10, 10)
        w_red20.printstring("Lämpötilat")

        # self.imagered.large_text("Lämpötilat", 10, 10, 2, 1)
        self.imageblack.text("ulkona lämpö", 10, 40, 0x00)
        self.imagered.text("ulkorakennus", 10, 70, 0x00)
        self.imageblack.text("autotalli", 10, 100, 0x00)

        w_blk = Writer(self.imageblack, fifont10, verbose=True)
        Writer.set_textpos(self.imageblack, 140, 10)
        # Testaa kaikki suomen erikoismerkit: ä ö Ä Ö å Å
        w_blk.printstring("äöÄÖåÅ — ääkköset")
        # Writer.set_textpos(self.imageblack, 10, 70)
        # w_blk.printstring("ulkorakennus")
        # Writer.set_textpos(self.imageblack, 10, 100)
        # w_blk.printstring("autotalli")
        # Header in red using Writer (supports Unicode)
        w_red = Writer(self.imagered, fifont10)
        Writer.set_textpos(self.imagered, 140, 200)
        w_red.printstring("Lämpötilat")

    # def display(self):
    #     print("TempereratureWindow display")
    #     self.epd.display_Partial_Both(self.buffer_black, self.buffer_red, self.Xstart, self.Ystart, self.Xend, self.Yend)
    #     # self.epd.display_Partial(self.buffer_black, self.Xstart, self.Ystart, self.Xend, self.Yend)

class ElectricityWindow(FrameWindow):
    # Bottom-right quarter of the full display

    WIDTH = EPD_WIDTH // 2
    HEIGHT = EPD_HEIGHT // 2
    XSTART = EPD_WIDTH // 2
    YSTART = EPD_HEIGHT // 2
    XEND = EPD_WIDTH
    YEND = EPD_HEIGHT

    BAR_COUNT = 20
    PRICE_RED_THRESHOLD = 20.0

    def __init__(self, epd, current_price=0.0, prices=None, price_red_threshold=None):
        self.current_price = current_price
        if prices is None:
            self.prices = [0] * self.BAR_COUNT
        else:
            self.prices = self._normalize_prices(prices)

        if price_red_threshold is None:
            self.price_red_threshold = self.PRICE_RED_THRESHOLD
        else:
            self.price_red_threshold = float(price_red_threshold)

        # super().__init__(epd, self.XSTART, self.YSTART, self.XEND, self.YEND)

        Xstart = self.XSTART
        Ystart = self.YSTART
        Xend = self.XEND
        Yend = self.YEND

        # print("ElectricityWindow init")
        # print("Xstart:", Xstart, "Xend:", Xend, "Ystart:", Ystart, "Yend:", Yend)
        super().__init__(epd, Xstart, Ystart, Xend, Yend)
        self.init()

    def _extract_price_value(self, value):
        if isinstance(value, (int, float)):
            return float(value)

        text = str(value).replace(',', '.')
        numeric = []
        dot_seen = False

        for ch in text:
            if ch.isdigit() or (ch == '-' and not numeric):
                numeric.append(ch)
            elif ch == '.' and not dot_seen:
                numeric.append(ch)
                dot_seen = True

        try:
            if numeric:
                return float(''.join(numeric))
        except ValueError:
            pass

        return None

    def _normalize_prices(self, prices):
        values = list(prices[:self.BAR_COUNT])
        if len(values) < self.BAR_COUNT:
            values.extend([0] * (self.BAR_COUNT - len(values)))
        return values

    def _format_current_price_text(self):
        text = str(self.current_price)
        if "c/kWh" in text:
            return text

        price_value = self._extract_price_value(self.current_price)
        if price_value is None:
            return text

        if int(price_value) == price_value:
            return "%d c/kWh" % int(price_value)

        return "%s c/kWh" % price_value

    def set_current_price(self, current_price):
        self.current_price = current_price

    def set_prices(self, prices):
        self.prices = self._normalize_prices(prices)

    def init(self):

        self.imageblack.fill(0xff)
        self.imagered.fill(0x00)

        price_value = self._extract_price_value(self.current_price)
        show_price_red = (price_value is not None and price_value > self.price_red_threshold)
        current_price_text = self._format_current_price_text()

        self.imageblack.text("Hinta nyt", 10, 10, 0x00)

        self.imageblack.fill_rect(10, 32, 20, 80, 0xff)
        # Writer jättää partial päivityksen kanssa haamuja
        Writer.set_textpos(self.imageblack, 32, 10)

        if show_price_red:
            w_black = Writer(self.imageblack, fifont20, verbose=False)
            w_black.printstring(current_price_text, invert=True)
            # self.imageblack.text(str(current_price_text), 10, 32, 0x00)
        else:
            w_black = Writer(self.imageblack, fifont20, verbose=False)
            w_black.printstring(current_price_text, invert=True)

            # self.imageblack.text(str(current_price_text), 10, 32, 0x00)

        graph_left = self.width - 190
        graph_top = 20
        graph_bottom = self.height - 20
        graph_height = graph_bottom - graph_top

        bar_width = 6
        gap = 2

        max_price = 1
        for price in self.prices:
            if price > max_price:
                max_price = price

        self.imageblack.hline(graph_left - 4, graph_bottom, self.BAR_COUNT * (bar_width + gap) + 4, 0x00)

        for i in range(self.BAR_COUNT):
            price = self.prices[i]
            if price < 0:
                price = 0

            bar_height = int((price / max_price) * graph_height)
            if bar_height < 1 and price > 0:
                bar_height = 1

            x = graph_left + i * (bar_width + gap)
            y = graph_bottom - bar_height

            if bar_height > 0:
                self.imageblack.fill_rect(x, y, bar_width, bar_height, 0x00)

    def display(self):
        print("ElectricityWindow display")
        # self.epd.display_Base_color(0xFF)  # set base to white
        # self.epd.display_Partial_Both(self.buffer_black, self.buffer_red, self.Xstart, self.Ystart, self.Xend, self.Yend)
        # self.epd.display_Partial(self.buffer_black, self.Xstart, self.Ystart, self.Xend, self.Yend)
        # self.epd.display_red()

        self.epd.blit(self.imageblack, self.imagered, self.Xstart, self.Ystart)        
        # self.epd.display()

        # self.epd.display_Base_color(0xFF)
        self.epd.init_part()
        self.epd.display_Partial(self.buffer_black, self.Xstart, self.Ystart, self.Xend, self.Yend)

class EPD_7in5_B:
    def __init__(self):
        self.reset_pin = Pin(RST_PIN, Pin.OUT)
        
        self.busy_pin = Pin(BUSY_PIN, Pin.IN, Pin.PULL_UP)
        self.cs_pin = Pin(CS_PIN, Pin.OUT)
        self.width = EPD_WIDTH
        self.height = EPD_HEIGHT
        self.partFlag=1
        self.red_full_refresh_interval_ms = 120000
        self.last_red_full_refresh_ms = utime.ticks_ms() - self.red_full_refresh_interval_ms
        self.pending_red_full_refresh = False
        
        self.spi = SPI(1)
        self.spi.init(baudrate=4000_000)
        self.dc_pin = Pin(DC_PIN, Pin.OUT)
        

        self.buffer_black = bytearray(self.height * self.width // 8)
        self.buffer_red = bytearray(self.height * self.width // 8)
        self.imageblack = framebuf.FrameBuffer(self.buffer_black, self.width, self.height, framebuf.MONO_HLSB)
        self.imagered = framebuf.FrameBuffer(self.buffer_red, self.width, self.height, framebuf.MONO_HLSB)

        self.width_win1 = EPD_WIDTH_WIN1
        self.height_win1 = EPD_HEIGHT_WIN1

        self.buffer_black_win1 = bytearray(self.height_win1 * self.width_win1 // 8)
        self.buffer_red_win1 = bytearray(self.height_win1 * self.width_win1 // 8)
        self.imageblack_win1 = framebuf.FrameBuffer(self.buffer_black_win1, self.width_win1, self.height_win1, framebuf.MONO_HLSB )
        self.imagered_win1 = framebuf.FrameBuffer(self.buffer_red_win1, self.width_win1, self.height_win1, framebuf.MONO_HLSB )


        # d = props_as_dict(self.imageblack_win1)
        # print(json.dumps(d)) 
        # print(self.imageblack_win1.height)

        self.init()

    def digital_write(self, pin, value):
        pin.value(value)

    def digital_read(self, pin):
        return pin.value()

    def delay_ms(self, delaytime):
        utime.sleep(delaytime / 1000.0)

    def spi_writebyte(self, data):
        self.spi.write(bytearray(data))

    def module_exit(self):
        self.digital_write(self.reset_pin, 0)

    # Hardware reset
    def reset(self):
        self.digital_write(self.reset_pin, 1)
        self.delay_ms(200) 
        self.digital_write(self.reset_pin, 0)
        self.delay_ms(2)
        self.digital_write(self.reset_pin, 1)
        self.delay_ms(200)   

    def send_command(self, command):
        self.digital_write(self.dc_pin, 0)
        self.digital_write(self.cs_pin, 0)
        self.spi_writebyte([command])
        self.digital_write(self.cs_pin, 1)

    def send_data(self, data):
        self.digital_write(self.dc_pin, 1)
        self.digital_write(self.cs_pin, 0)
        self.spi_writebyte([data])
        self.digital_write(self.cs_pin, 1)
        
    def send_data1(self, buf):
        self.digital_write(self.dc_pin, 1)
        self.digital_write(self.cs_pin, 0)
        self.spi.write(bytearray(buf))
        self.digital_write(self.cs_pin, 1)

    def WaitUntilIdle(self):
        print("e-Paper busy")
        while(self.digital_read(self.busy_pin) == 0):   # Wait until the busy_pin goes LOW
            self.delay_ms(20)
        self.delay_ms(20) 
        print("e-Paper busy release")  

    def TurnOnDisplay(self):
        self.send_command(0x12) # DISPLAY REFRESH
        self.delay_ms(100)      #!!!The delay here is necessary, 200uS at least!!!
        self.WaitUntilIdle()
        
    def init(self):
        # EPD hardware init start     
        self.reset()
        
        self.send_command(0x06)     # BOOSTER SOFT START
        self.send_data(0x17)        # booster param 1 (vendor profile)
        self.send_data(0x17)        # booster param 2 (vendor profile)
        self.send_data(0x28)        # booster param 3; try 0x38 if panel behaves abnormally
        self.send_data(0x17)        # booster param 4 (vendor profile)
        
#         self.send_command(0x01)  # POWER SETTING
#         self.send_data(0x07)
#         self.send_data(0x07)     # VGH=20V,VGL=-20V
#         self.send_data(0x3f)     # VDH=15V
#         self.send_data(0x3f)     # VDL=-15V
        
        self.send_command(0x04)  # POWER ON
        self.delay_ms(100)
        self.WaitUntilIdle()

        self.send_command(0X00)   # PANNEL SETTING
        self.send_data(0x0F)      # KW-3f   KWR-2F	BWROTP 0f	BWOTP 1f

        self.send_command(0x61)     # tres
        self.send_data(0x03)     # source 800
        self.send_data(0x20)
        self.send_data(0x01)     # gate 480
        self.send_data(0xE0)

        self.send_command(0X15)
        self.send_data(0x00)

        self.send_command(0X50)     # VCOM AND DATA INTERVAL SETTING
        self.send_data(0x11)
        self.send_data(0x07)

        self.send_command(0X60)     # TCON SETTING
        self.send_data(0x22)

        self.send_command(0x65)     # Resolution setting
        self.send_data(0x00)
        self.send_data(0x00)     # 800*480
        self.send_data(0x00)
        self.send_data(0x00)
        
        return 0;
    
    def init_Fast(self):
        # EPD hardware init start
        self.reset()

        self.send_command(0X00)
        self.send_data(0x0F)

        self.send_command(0x04)
        self.delay_ms(100)
        self.WaitUntilIdle()

        self.send_command(0x06)
        self.send_data(0x27)
        self.send_data(0x27) 
        self.send_data(0x18)		
        self.send_data(0x17)		

        self.send_command(0xE0)
        self.send_data(0x02)
        self.send_command(0xE5)
        self.send_data(0x5A)

        self.send_command(0X50)
        self.send_data(0x11)
        self.send_data(0x07)
        
        return 0
    
    def init_part(self):
        # EPD hardware init start
        self.reset()

        self.send_command(0X00)
        self.send_data(0x1F)  # Partial support only BW refresh

        self.send_command(0x04)
        self.delay_ms(100)
        self.WaitUntilIdle()

        self.send_command(0xE0)
        self.send_data(0x02)
        self.send_command(0xE5)
        self.send_data(0x6E)

        self.send_command(0X50)
        self.send_data(0xA9)
        self.send_data(0x07)

        # EPD hardware init end
        return 0
    
    
    def Clear(self):
        high = self.height
        if( self.width % 8 == 0) :
            wide =  self.width // 8
        else :
            wide =  self.width // 8 + 1
        
        self.send_command(0x10)
        for i in range(0, wide):
            self.send_data1([0xff] * high)
                
        self.send_command(0x13) 
        for i in range(0, wide):
            self.send_data1([0x00] * high)
                
        self.TurnOnDisplay()
        
    def ClearRed(self):
        
        high = self.height
        if( self.width % 8 == 0) :
            wide =  self.width // 8
        else :
            wide =  self.width // 8 + 1
        
        self.send_command(0x10) 
        for i in range(0, wide):
            self.send_data1([0xff] * high)
                
        self.send_command(0x13) 
        for i in range(0, wide):
            self.send_data1([0xff] * high)
                
        self.TurnOnDisplay()
        
    def ClearBlack(self):
        
        high = self.height
        if( self.width % 8 == 0) :
            wide =  self.width // 8
        else :
            wide =  self.width // 8 + 1
        
        self.send_command(0x10) 
        for i in range(0, wide):
            self.send_data1([0x00] * high)
                
        self.send_command(0x13) 
        for i in range(0, wide):
            self.send_data1([0x00] * high)
                
        self.TurnOnDisplay()
        
    def display(self):
        
        high = self.height
        if( self.width % 8 == 0) :
            wide =  self.width // 8
        else :
            wide =  self.width // 8 + 1
        print("dispaly, wide:", wide, "high:", high)
        # send black data
        self.send_command(0x10) 
        for i in range(0, wide):
            self.send_data1(self.buffer_black[(i * high) : ((i+1) * high)])
            
        print("and red")
        # send red data
        self.send_command(0x13) 
        for i in range(0, wide):
            self.send_data1(self.buffer_red[(i * high) : ((i+1) * high)])
            
        self.TurnOnDisplay()
        
    def display_Base_color(self, color):
        if(self.width % 8 == 0):
            Width = self.width // 8
        else:
            Width = self.width // 8 +1
        Height = self.height
        self.send_command(0x10)   #Write Black and White image to RAM
        for j in range(Height):
            for i in range(Width):
                self.send_data(color)
                
        self.send_command(0x13)  #Write Black and White image to RAM
        for j in range(Height):
            for i in range(Width):
                self.send_data(~color)

        # self.send_command(0x12)
        # self.delay_ms(100)
        # self.WaitUntilIdle()
        
        
    def display_Partial(self, Buffer, Xstart, Ystart, Xend, Yend):
        if((Xstart % 8 + Xend % 8 == 8 & Xstart % 8 > Xend % 8) | Xstart % 8 + Xend % 8 == 0 | (Xend - Xstart)%8 == 0):
            Xstart = Xstart // 8 * 8
            Xend = Xend // 8 * 8
        else:
            Xstart = Xstart // 8 * 8
            if Xend % 8 == 0:
                Xend = Xend // 8 * 8
            else:
                Xend = Xend // 8 * 8 + 1
                
        Width = (Xend - Xstart) // 8
        Height = Yend - Ystart

        print("Xstart:", Xstart, "Xend:", Xend, "Ystart:", Ystart, "Yend:", Yend)
        print("Width:", Width, "Height:", Height)
        # self.send_command(0x50)
        # self.send_data(0xA9)
        # self.send_data(0x07)

        self.send_command(0x91)		#This command makes the display enter partial mode
        self.send_command(0x90)		#resolution setting
        self.send_data (Xstart//256)
        self.send_data (Xstart%256)   #x-start    

        self.send_data ((Xend -1)//256)		
        self.send_data ((Xend -1)%256)  #x-end	

        self.send_data (Ystart//256)  #
        self.send_data (Ystart%256)   #y-start    

        self.send_data ((Yend -1)//256)		
        self.send_data ((Yend -1)%256)  #y-end
        self.send_data (0x01)

        if self.partFlag == 1:
            self.partFlag = 0
            self.send_command(0x10)
            for i in range(0, Width):
                self.send_data1([0xFF] * Height)

        self.send_command(0x13)   #Write Black and White image to RAM
        for i in range(0, Width):
            # self.send_data1(Image[(i * Height) : ((i+1) * Height)])
            self.send_data1(Buffer[(i * Height) : ((i+1) * Height)])

        self.send_command(0x12)
        self.delay_ms(100)
        self.WaitUntilIdle()

# lokista
# dispaly, wide: 100 high: 480
# partial loop
# Xstart: 8 Xend: 169 Ystart: 10 Yend: 90
# Width: 20 Height: 80

    def display_Partial_Both(self, BufferBlack, BufferRed, Xstart, Ystart, Xend, Yend):
        print("display_Partial_Both")
        print("Xstart:", Xstart, "Xend:", Xend, "Ystart:", Ystart, "Yend:", Yend)
        if((Xstart % 8 + Xend % 8 == 8 & Xstart % 8 > Xend % 8) | Xstart % 8 + Xend % 8 == 0 | (Xend - Xstart)%8 == 0):
            Xstart = Xstart // 8 * 8
            Xend = Xend // 8 * 8
        else:
            Xstart = Xstart // 8 * 8
            if Xend % 8 == 0:
                Xend = Xend // 8 * 8
            else:
                Xend = Xend // 8 * 8 + 1
                
        Width = (Xend - Xstart) // 8
        Height = Yend - Ystart

        red_has_data = False
        for i in range(0, Width):
            chunk = BufferRed[(i * Height) : ((i+1) * Height)]
            for b in chunk:
                if b != 0x00:
                    red_has_data = True
                    break
            if red_has_data:
                break

        if red_has_data:
            # win_width = Xend - Xstart
            # win_height = Yend - Ystart
            # win_black = framebuf.FrameBuffer(BufferBlack, win_width, win_height, framebuf.MONO_HLSB)
            # win_red = framebuf.FrameBuffer(BufferRed, win_width, win_height, framebuf.MONO_HLSB)
            # self.imageblack.blit(win_black, Xstart, Ystart)
            # self.imagered.blit(win_red, Xstart, Ystart)
            self.pending_red_full_refresh = True

        # if self.pending_red_full_refresh:
        #     now = utime.ticks_ms()
        #     if utime.ticks_diff(now, self.last_red_full_refresh_ms) >= self.red_full_refresh_interval_ms:
        #         print("Deferred red full refresh")
        #         # self.init()
        #         self.init_Fast()
        #         self.display()
        #         self.init_part()
        #         self.partFlag = 1
        #         self.last_red_full_refresh_ms = now
        #         self.pending_red_full_refresh = False
        #         return

        self.send_command(0x91)     # enter partial mode
        self.send_command(0x90)     # window setting
        self.send_data (Xstart//256)
        self.send_data (Xstart%256)
        self.send_data ((Xend-1)//256)
        self.send_data ((Xend-1)%256)
        self.send_data (Ystart//256)
        self.send_data (Ystart%256)
        self.send_data ((Yend-1)//256)
        self.send_data ((Yend-1)%256)
        self.send_data (0x01)

        if self.partFlag == 1:
            self.partFlag = 0
            self.send_command(0x10)
            for i in range(0, Width):
                self.send_data1([0xFF] * Height)

        # write black layer
        self.send_command(0x13)
        for i in range(0, Width):
            self.send_data1(BufferBlack[(i * Height) : ((i+1) * Height)])

        # no red writes in partial path; red is deferred to timed full refresh

        # single refresh for both layers
        # self.send_command(0x12)
        # self.delay_ms(100)
        # self.WaitUntilIdle()
        self.TurnOnDisplay()

    def display_red(self):
        print("display red")
        if self.pending_red_full_refresh:
            print("display red refresh")
            # self.init()
            self.init_Fast()
            # self.init_part()

            self.display()
            # self.partFlag = 0
            self.last_red_full_refresh_ms = utime.ticks_ms()
            self.pending_red_full_refresh = False       

    def blit(self, imageBlack, imageRed, x, y):
        self.imageblack.blit(imageBlack, x, y)
        self.imagered.blit(imageRed, x, y)

    def sleep(self):
        self.send_command(0x02) # power off
        self.WaitUntilIdle()
        self.send_command(0x07) # deep sleep
        self.send_data(0xa5)


def show_finnish_test_page(epd):
    print("show_finnish_test_page start")

    # Full-screen Finnish glyph verification for both layers
    # epd.init()
    epd.init_Fast()
    epd.imageblack.fill(0xff)
    epd.imagered.fill(0x00)

    w_black = Writer(epd.imageblack, fifont10, verbose=False)
    w_red = Writer(epd.imagered, fifont10, verbose=False)

    # Title in red
    Writer.set_textpos(epd.imagered, 10, 10)
    w_red.printstring("Suomi-testisivu: äöÄÖåÅ — äkköset")

    # Black layer lines
    Writer.set_textpos(epd.imageblack, 40, 10)
    w_black.printstring("Perus: abcdefghijklmnopqrstuvwxyz åäö", invert=True)
    Writer.set_textpos(epd.imageblack, 60, 10)
    w_black.printstring("Kapiteelit: ABCDEFGHIJKLMNOPQRSTUVWXYZ ÅÄÖ")
    Writer.set_textpos(epd.imageblack, 80, 10)
    w_black.printstring("Numerot: 0123456789")
    Writer.set_textpos(epd.imageblack, 100, 10)
    w_black.printstring("Välimerkit: .,:;!?()[]{}-–— ‘’ “” @&%#")

    # Red layer lines
    Writer.set_textpos(epd.imagered, 130, 10)
    w_red.printstring("Lause: Pöllö söi äyriäisiä yössä.")
    Writer.set_textpos(epd.imagered, 150, 10)
    w_red.printstring("Paikkakunta: Åland ja Örebro")

    print("show_finnish_test_page display")
    epd.display()
    print("show_finnish_test_page done")

def show_temperature_window(temperature_window):
    temperature_window.display()

def show_electricity_window(electricity_window, current_price=0.0, prices=None, price_red_threshold=None):
    if prices is None:
        prices = [
            12.3, 11.8, 10.6, 9.9, 10.1,
            11.7, 13.2, 15.4, 18.6, 21.1,
            24.6, 26.2, 23.7, 19.9, 17.1,
            16.0, 14.8, 13.9, 12.7, 11.5,
        ]

    electricity_window.set_current_price(current_price)
    electricity_window.set_prices(prices)
    electricity_window.init()

    electricity_window.display()

if __name__=='__main__':
    # Try to sync time from NTP, then print UTC and Finland time (UTC+2 winter)
    # try_ntp_sync()
    _utc = utime.localtime()
    print("Local-aika: %04d-%02d-%02d %02d:%02d:%02d" % (_utc[0], _utc[1], _utc[2], _utc[3], _utc[4], _utc[5]))
    # _fi = utime.localtime(utime.time() + 2*3600)
    # print("Nykyinen aika (UTC+2): %04d-%02d-%02d %02d:%02d:%02d" % (_fi[0], _fi[1], _fi[2], _fi[3], _fi[4], _fi[5]))

    epd = EPD_7in5_B()
    epd.init()
    epd.Clear()
    epd.delay_ms(5000)
    print("remove cable")
    epd.display_Base_color(0xFF)  # set base to white
    epd.TurnOnDisplay()
    epd.delay_ms(2000)




    # partial update
    print("partial start")
    # epd.init_part()

    # Optional: show full Finnish test page to verify glyphs
# test page toimii
    show_finnish_test_page(epd)
    epd.imageblack_win1.fill(0xff)
    # epd.imageblack.fill(0xff)
    # epd.imagered.fill(0x00)

    win_temp = TempereratureWindow(epd)
    # Demo: top-right temperature window
    show_temperature_window(win_temp)

    win_electricity = ElectricityWindow(epd)

    # Demo: bottom-right electricity window
    for current_price in [24, 5, 20]:
        show_electricity_window(win_electricity, current_price=current_price)
        epd.delay_ms(1000)

    # win2 = FrameWindow(epd, 400, 240, 800, 480)
    # epd.imageblack.fill(0xff)
    epd.display_Base_color(0xFF)
    epd.init_part()

    for i in range(0, 4):
        print("partial loop")

        epd.imageblack_win1.fill(0xff)
        epd.imageblack_win1.fill_rect(0, 0, 10, 20, 0xff)
        epd.imageblack_win1.fill_rect(0, 30, 10, 20, 0x00)

        epd.imageblack_win1.fill_rect(40, 40, 10, 20, 0xff)
        epd.imageblack_win1.text(str(i), 41, 41, 0x00)


        epd.display_Partial(epd.buffer_black_win1, 0, 200, 160, 280)

        print("partial loop end")
        epd.delay_ms(2000)
            

    epd.init_Fast()
    epd.display()

    print("shutdown")
    epd.init()       
    epd.Clear()
    epd.delay_ms(2000)
    print("sleep")
    epd.sleep()

