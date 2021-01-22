import digitalio, board, busio, adafruit_rfm9x

RADIO_FREQ_MHZ = 868.

CS = digitalio.DigitalInOut( board.CE1)
RESET = digitalio.DigitalInOut( board.D25)
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)

radio = adafruit_rfm9x.RFM9x( spi, CS, RESET, RADIO_FREQ_MHZ)

def main():
    while True:
        fpacket = radio.receive()
        if packet != None:
            print("Echoing " + str(packet))
            radio.send(packet)

if __name__ == "__main__":
    main()
