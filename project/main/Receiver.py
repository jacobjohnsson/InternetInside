import digitalio, board, busio, adafruit_rfm9x
import time

RADIO_FREQ_MHZ = 868.

CS = digitalio.DigitalInOut( board.CE1)
RESET = digitalio.DigitalInOut( board.D25)
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)

radio = adafruit_rfm9x.RFM9x( spi, CS, RESET, RADIO_FREQ_MHZ)

counter = 0;
t0 = time.perf_counter()

while(time.perf_counter() - t0 < 600):
	packet = radio.receive()
	#rssi = radio.last_rssi
	#print("Signal strength: " + str(rssi) + " dB")
	if (packet != None):
		counter += 1
	print(str(counter) + "\t[" + str(packet) + "]")

print("Received " + str(counter) + " packages")
