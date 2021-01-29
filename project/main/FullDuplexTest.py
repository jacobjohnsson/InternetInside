import digitalio, board, busio, adafruit_rfm9x
import time

from station.Station import *

ADDRESS = 7
DESTINATION = 8

RADIO_FREQ_MHZ_1 = 866.
RADIO_FREQ_MHZ_2 = 867.

CS = digitalio.DigitalInOut(board.CE1)
RESET = digitalio.DigitalInOut(board.D25)
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
transmitter = adafruit_rfm9x.RFM9x( spi, CS, RESET, RADIO_FREQ_MHZ_1)
transmitter.tx_power = 5

CS = digitalio.DigitalInOut(board.D17)
RESET = digitalio.DigitalInOut(board.D4)
spi = busio.SPI(board.D21, MOSI=board.D20, MISO=board.D19)
receiver = adafruit_rfm9x.RFM9x( spi, CS, RESET, RADIO_FREQ_MHZ_2)
receiver.tx_power = 5

station = ThreadedStation(receiver, transmitter, 7)

counter = 0
received = 0
i = 0
t0 = time.perf_counter()

messages = [("Hello from " + str(ADDRESS) + "! " + str(i)).encode("utf-8") for i in range(100)]

while (counter < 100):

    station.send(messages[counter], DESTINATION)
    print("Sent: " + str(messages[counter]))
    counter += 1
    time.sleep(0.1)

print("Sending is done, now receiving.")

responses = [print(str(station.receive_timeout(0.1))) for i in range(counter)]

#print("Messages sent: " + str(i) + 
#    "\nReceived : " + str(received) + 
#    "\nCorrect: " + str(counter))

station.shutdown()
