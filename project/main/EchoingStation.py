import digitalio, board, busio, adafruit_rfm9x
import time

RADIO_FREQ_MHZ = 868.

CS = digitalio.DigitalInOut( board.CE1)
RESET = digitalio.DigitalInOut( board.D25)
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)

radio = adafruit_rfm9x.RFM9x( spi, CS, RESET, RADIO_FREQ_MHZ)
radio.destination = 7
radio.node = 8

class EchoingStation:

    def __init__(self):
        pass

    def do(self):
        packet = radio.receive(with_header=True, timeout = 5.0)
        if packet != None:
            data = packet[4:]
            src = packet[1]
            dest = packet[0]
            print("Echoing: \t" + str(data) + 
            "\n\t\tFrom:\t" + str(src) + 
            "\n\t\tTo:\t" + str(dest))
            #time.sleep(0.2)
            radio.send(data)

def main():
    station = EchoingStation()
    while True:
        station.do()


if __name__ == "__main__":
    main()
