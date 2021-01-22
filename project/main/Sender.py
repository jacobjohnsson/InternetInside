import array
import digitalio, board, busio, adafruit_rfm9x
import numpy as np
import time

RADIO_FREQ_MHZ = 868.

CS = digitalio.DigitalInOut(board.CE1)
RESET = digitalio.DigitalInOut(board.D25)
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)

radio = adafruit_rfm9x.RFM9x( spi, CS, RESET, RADIO_FREQ_MHZ)
radio.tx_power = 5
b = bytearray()
b.extend(map(ord, "Hello World"))

counter = 0
t0 = time.perf_counter()

while (time.perf_counter() - t0 < 595):
	result = radio.send(b)
	counter += 1;

print(counter)
