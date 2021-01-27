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
receiver.tx_power = 5

station = ThreadedStation(receiver, transmitter, 7)
#station.setStrategy(BasicStrategy(receiver, transmitter))

counter = 0
received = 0
i = 0
t0 = time.perf_counter()

while (time.perf_counter() - t0 < 60):
    msg = "Hello world!" + str(i)
    print("Sending: " + msg)
    b = bytearray()
    b.extend(map(ord, msg))

    station.send(b, 8)
    response = station.receive_timeout(5.0)

    if response != None:
        received += 1
        response_data = response[4:]
        print("Response: " + str(response_data))
        if (str(b) == str(response_data)):
            print("CORRECT!")
            counter += 1
    i += 1
    #time.sleep(1.0)

print("Messages sent: " + str(i) + 
    "\nReceived : " + str(received) + 
    "\nCorrect: " + str(counter))

station.shutdown()
