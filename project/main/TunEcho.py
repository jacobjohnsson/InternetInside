import os 
import fcntl
import struct
import digitalio, board, busio, adafruit_rfm9x
import time
import pytun

from station.Station import *

ADDRESS = 8
DESTINATION = 7

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

station = ThreadedStation(receiver, transmitter, ADDRESS)

tun = pytun.TunTapDevice(name="LongG")
tun.addr = "192.168.2.108"
tun.netmask = "255.255.255.0"
tun.dstaddr = "192.168.2.107"
tun.mtu = 1500

tun.up()
t0 = time.perf_counter()
print("TunEcho is up")

while True:
    packet = station.receive()
    print("Received a package : \n" + str(bytes(packet[4:])) + "\n")
    tun.write(bytes(packet[4:]))
    response = tun.read(tun.mtu)
    station.send(response, DESTINATION)
    print("Sent a response : \n" + str(response) + "\n")

tun.down()
tun.close()
station.shutdown()

print("TunEcho is down")