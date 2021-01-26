import digitalio, board, busio, adafruit_rfm9x
import time

from station.Station import *

RADIO_FREQ_MHZ = 868.

CS = digitalio.DigitalInOut(board.CE1)
RESET = digitalio.DigitalInOut(board.D25)
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
transmitter = adafruit_rfm9x.RFM9x( spi, CS, RESET, RADIO_FREQ_MHZ)
transmitter.tx_power = 5

CS = digitalio.DigitalInOut(board.D17)
RESET = digitalio.DigitalInOut(board.D4)
spi = busio.SPI(board.D21, MOSI=board.D20, MISO=board.D19)
receiver = adafruit_rfm9x.RFM9x( spi, CS, RESET, RADIO_FREQ_MHZ)

station = ThreadedStation(receiver, transmitter, 0)
#station.setStrategy(BasicStrategy(receiver, transmitter))

counter = 0
received = 0
i = 0
t0 = time.perf_counter()

while (time.perf_counter() - t0 < 1800):
    msg = "Hello world!"
    b = bytearray()
    b.extend(map(ord, msg))
    station.send(b)
    response = station.receive()
    if response != None:
        received += 1
        print("Response: " + str(response))
        if (b == response):
	        counter += 1
    i += 1

print("Messages sent: " + str(i) + 
    "\nReceived : " + str(received) + 
    "\nCorrect: " + str(counter))
