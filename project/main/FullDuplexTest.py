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
transmitter = adafruit_rfm9x.RFM9x( spi, CS, RESET, RADIO_FREQ_MHZ_2)
transmitter.tx_power = 5

CS = digitalio.DigitalInOut(board.D17)
RESET = digitalio.DigitalInOut(board.D4)
spi = busio.SPI(board.D21, MOSI=board.D20, MISO=board.D19)
receiver = adafruit_rfm9x.RFM9x( spi, CS, RESET, RADIO_FREQ_MHZ_1)
receiver.tx_power = 5

station = ThreadedStation(receiver, transmitter, ADDRESS)

counter = 0
received = 0
i = 0
t0 = time.perf_counter()

TEST_SIZE = 400  # In nbr of packages

messages = [("Hello from " + str(ADDRESS) + "! " + str(i) + " PADDINGPADDING") for i in range(TEST_SIZE)]
encoded_messages = [s.encode("utf-8") for s in messages]

time.sleep(3)

while (counter < TEST_SIZE):

    station.send(encoded_messages[counter], DESTINATION)
    #print("Sent: " + str(encoded_messages[counter]))
    counter += 1
    #time.sleep(0.1)

print("Sending is done, now receiving.")


#responses = [print(str(station.receive_timeout(2))) for i in range(counter)]
packet_responses = [station.receive_timeout(0.1) for i in range(counter)]
expected_responses = [("Hello from " + str(DESTINATION) + "! " + str(i) + " PADDINGPADDING") for i in range(TEST_SIZE)]
string_responses = [p[4:].decode("utf-8", 'backslashreplace') for p in packet_responses if p != None]

print('\n'.join(map(str, string_responses)))

cut = set(expected_responses).difference(set(string_responses))

# print("Expected messages: ")
# print('\n'.join(map(str, expected_responses)))

# print("Responses: ")
# print('\n'.join(map(str, string_responses)))

print("Missing stuff: \n")
print('\n'.join(map(str, cut)))


print("\nMessages sent: " + str(TEST_SIZE) + 
    "\nReceived : " + str(len(string_responses)) + 
    "\nCorrect: " + str(TEST_SIZE - len(cut)))

station.shutdown()