import digitalio, board, busio, adafruit_rfm9x
import time

RADIO_FREQ_MHZ_1 = 866.
RADIO_FREQ_MHZ_2 = 867.

CS = digitalio.DigitalInOut( board.CE1)
RESET = digitalio.DigitalInOut( board.D25)
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)

tranceiver = adafruit_rfm9x.RFM9x( spi, CS, RESET, RADIO_FREQ_MHZ_2)
tranceiver.destination = 7
tranceiver.node = 8

CS = digitalio.DigitalInOut(board.D17)
RESET = digitalio.DigitalInOut(board.D4)
spi = busio.SPI(board.D21, MOSI=board.D20, MISO=board.D19)
receiver = adafruit_rfm9x.RFM9x( spi, CS, RESET, RADIO_FREQ_MHZ_1)
receiver.tx_power = 5
receiver.node = 8

class EchoingStation:

    def __init__(self):
        pass

    def do(self):
        packet = receiver.receive(with_header=True, timeout = 5.0)
        if packet != None:
            data = packet[4:]
            src = packet[1]
            dest = packet[0]
            print("Echoing: \t" + str(data) + 
            "\n\t\tFrom:\t" + str(src) + 
            "\n\t\tTo:\t" + str(dest))
            #time.sleep(0.2)
            tranceiver.send(data)

def main():
    station = EchoingStation()
    while True:
        station.do()


if __name__ == "__main__":
    main()
