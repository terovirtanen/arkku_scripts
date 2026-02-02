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
import font10 as tempfont  # Adjust to your generated font module

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

try:
    import ujson as json
except ImportError:
    import json

def props_as_dict(obj, include_private=True):
    out = {}
    names = getattr(obj, "__dict__", None)
    names = list(names.keys()) if names else dir(obj)
    for n in names:
        if not include_private and str(n).startswith('_'):
            continue
        try:
            v = getattr(obj, n)
            if callable(v):
                out[n] = "<callable>"
            elif isinstance(v, (bytes, bytearray)):
                out[n] = "<%s len=%d>" % (type(v).__name__, len(v))
            else:
                # yritä tehdä JSON-kelpoinen, muuten repr
                try:
                    json.dumps(v)
                    out[n] = v
                except Exception:
                    out[n] = repr(v)
        except Exception as e:
            out[n] = "<error: %s>" % e
    return out

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

    def display(self):
        print("FrameWindow display")
        # self.epd.display_Partial_Both(self.buffer_black, self.buffer_red, self.Xstart, self.Ystart, self.Xend, self.Yend)
        self.epd.display_Partial(self.buffer_black, self.Xstart, self.Ystart, self.Xend, self.Yend)


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
        self.imagered.large_text("Lämpötilat", 10, 10, 2, 1)
        self.imageblack.text("ulkona lämpö", 10, 40, 0x00)
        self.imageblack.text("ulkorakennus", 10, 70, 0x00)
        self.imageblack.text("autotalli", 10, 100, 0x00)

        w_blk = Writer(self.imageblack, tempfont, verbose=False)
        Writer.set_textpos(self.imageblack, 10, 140)
        w_blk.printstring("ääkköset")
        # Writer.set_textpos(self.imageblack, 10, 70)
        # w_blk.printstring("ulkorakennus")
        # Writer.set_textpos(self.imageblack, 10, 100)
        # w_blk.printstring("autotalli")

    def display(self):
        print("TempereratureWindow display")
        self.epd.display_Partial_Both(self.buffer_black, self.buffer_red, self.Xstart, self.Ystart, self.Xend, self.Yend)
        # self.epd.display_Partial(self.buffer_black, self.Xstart, self.Ystart, self.Xend, self.Yend)

class EPD_7in5_B:
    def __init__(self):
        self.reset_pin = Pin(RST_PIN, Pin.OUT)
        
        self.busy_pin = Pin(BUSY_PIN, Pin.IN, Pin.PULL_UP)
        self.cs_pin = Pin(CS_PIN, Pin.OUT)
        self.width = EPD_WIDTH
        self.height = EPD_HEIGHT
        self.partFlag=1
        
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


        d = props_as_dict(self.imageblack_win1)
        print(json.dumps(d)) 
        print(self.imageblack_win1.height)

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
        
        self.send_command(0x06)     # btst
        self.send_data(0x17)
        self.send_data(0x17)
        self.send_data(0x28)        # If an exception is displayed, try using 0x38
        self.send_data(0x17)
        
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
        self.send_data(0x1F)

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
        self.send_command(0x10)
        for i in range(0, Width):
            self.send_data1(BufferBlack[(i * Height) : ((i+1) * Height)])

        # write red layer
        self.send_command(0x13)
        for i in range(0, Width):
            self.send_data1(BufferRed[(i * Height) : ((i+1) * Height)])

        # single refresh for both layers
        self.send_command(0x12)
        self.delay_ms(100)
        self.WaitUntilIdle()

    def sleep(self):
        self.send_command(0x02) # power off
        self.WaitUntilIdle()
        self.send_command(0x07) # deep sleep
        self.send_data(0xa5)

if __name__=='__main__':
    # Try to sync time from NTP, then print UTC and Finland time (UTC+2 winter)
    # try_ntp_sync()
    _utc = utime.localtime()
    print("Local-aika: %04d-%02d-%02d %02d:%02d:%02d" % (_utc[0], _utc[1], _utc[2], _utc[3], _utc[4], _utc[5]))
    # _fi = utime.localtime(utime.time() + 2*3600)
    # print("Nykyinen aika (UTC+2): %04d-%02d-%02d %02d:%02d:%02d" % (_fi[0], _fi[1], _fi[2], _fi[3], _fi[4], _fi[5]))

    epd = EPD_7in5_B()
    epd.Clear()
    
    epd.imageblack.fill(0xff)
    print("fill black")
    epd.imagered.fill(0x00)
    print("fill red")
    
    epd.imageblack.text("Waveshare", 5, 10, 0x00)
    print("draw text 1")
    epd.imagered.text("Pico_ePaper-7.5-B", 5, 40, 0xff)
    print("draw text 2")
    epd.imageblack.text("Raspberry Pico", 5, 70, 0x00)
    print("draw text 3")
    epd.display()
    print("display")

    # epd.delay_ms(5000)

    # Base color examples: full white, then full red
    # print("base color examples")
    # epd.init()
    # epd.display_Base_color(0xFF)  # set base to white
    # epd.TurnOnDisplay()
    # epd.delay_ms(2000)
    # epd.display_Base_color(0x00)  # set base to red
    # epd.TurnOnDisplay()
    # epd.delay_ms(2000)
    
    # epd.imageblack.vline(10, 90, 60, 0x00)
    # epd.imageblack.vline(120, 90, 60, 0x00)
    # epd.imagered.hline(10, 90, 110, 0xff)
    # epd.imagered.hline(10, 150, 110, 0xff)
    # epd.imagered.line(10, 90, 120, 150, 0xff)
    # epd.imagered.line(120, 90, 10, 150, 0xff)
    # epd.display()
    # epd.delay_ms(5000)
    
    # epd.imageblack.rect(10, 180, 50, 80, 0x00 )
    # epd.imageblack.fill_rect(70, 180, 50, 80,0x00 )
    # epd.imagered.rect(10, 300, 50, 80, 0xff )
    # epd.imagered.fill_rect(70, 300, 50, 80,0xff )
    # epd.display()
    # epd.delay_ms(5000)

    # for k in range(0, 3):
    #     for j in range(0, 3):
    #         for i in range(0, 5):
    #             epd.imageblack.fill_rect(200+100+j*200, i*20+k*200, 100, 10, 0x00)
    #         for i in range(0, 5):
    #             epd.imagered.fill_rect(200+0+j*200, i*20+100+k*200, 100, 10, 0xff)
    # epd.display()
    # epd.delay_ms(5000)

    # partial update
    print("partial start")


    
    epd.init()
    epd.imageblack_win1.fill(0xff)
    # epd.imageblack.fill(0xff)
    # epd.imagered.fill(0x00)
    epd.display_Base_color(0xFF)
    epd.init_part()

    # Demo: top-right temperature window
    win_temp = TempereratureWindow(epd)
    win_temp.display()

    win2 = FrameWindow(epd, 400, 240, 800, 480)

    for i in range(0, 4):
        print("partial loop")
        win2.imageblack.fill(0xff)
        win2.imageblack.fill_rect(40, 40, 10, 20, 0xff)
        win2.imageblack.text(str(i), 41, 41, 0x00)
        win2.imagered.text("win 2", 200, 100, 0x00)
        win2.display()

        epd.imageblack_win1.fill_rect(0, 0, 10, 20, 0xff)
        epd.imageblack_win1.fill_rect(0, 30, 10, 20, 0x00)

        epd.imageblack_win1.fill_rect(40, 40, 10, 20, 0xff)
        epd.imageblack_win1.text(str(i), 41, 41, 0x00)

        # epd.imageblack_win1.text(str(i), 20, 80, 0x00)
        # epd.imageblack_win1.text(str(i+20), 2, 2, 0x00)
        # epd.imageblack_win1.pixel(30, 30, 0xff)
        # epd.imageblack_win1.pixel(31, 30, 0xff)
        # epd.imageblack_win1.pixel(30, 31, 0xff)
        # epd.imageblack_win1.pixel(31, 31, 0x00)
        # epd.display_Partial(epd.buffer_black, 0, 0, 800, 480)
        # epd.display_Partial(epd.buffer_black_win1, 10, 10, 170, 90)
        epd.display_Partial(epd.buffer_black_win1, 0, 200, 160, 280)

        # epd.imageblack.fill_rect(175, 105, 100, 20, 0xff)
        # epd.imageblack.text(str(i), 177, 106, 0x00)
        # epd.imageblack.text(str(i+20), 2, 2, 0x00)
        # # epd.display_Partial(epd.buffer_black, 0, 0, 800, 480)
        # epd.display_Partial(epd.buffer_black, 10, 10, 200, 200)

        # epd.imagered.fill_rect(375, 105, 100, 20, 0x00)
        # epd.imagered.text("pidempi teksti", 386, 116, 0xff) # tämähän ei toimi ?
        # epd.display_Partial(epd.buffer_red, 0, 0, 800, 480)
        # Päivitä vain uudet alueet (pyöristetty 8 pikselin tarkkuuteen)
        # Musta alue (rect + teksti)
        # epd.display_Partial_Both(epd.buffer_black, epd.buffer_red, 168, 96, 280, 132)
        # Punainen alue (rect + teksti)
        # epd.display_Partial_Both(epd.buffer_black, epd.buffer_red, 0, 0, 800, 480)
        print("partial loop end")
        epd.delay_ms(5000)
            
    print("shutdown")
    epd.init()       
    epd.Clear()
    epd.delay_ms(2000)
    print("sleep")
    epd.sleep()

