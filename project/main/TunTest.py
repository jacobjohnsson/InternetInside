import os 
import fcntl
import struct
import pytun
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

tun = pytun.TunTapDevice(name="LongG")
tun.addr = "192.168.2.107"
tun.netmask = "255.255.255.0"
tun.dstaddr = "192.168.2.108"
tun.mtu = 1500
tun.up()

station = TunStation(receiver, transmitter, ADDRESS, tun)

print("TunTest is up")

x = []
y = []
pack_count = 0
t0 = time.time()
while True:
    packet = tun.read(tun.mtu)
    print("Packet in tun: \n" + str(packet))
    station.send(packet, DESTINATION)

tun.down()
tun.close()
station.shutdown()

print("TunTest is down")