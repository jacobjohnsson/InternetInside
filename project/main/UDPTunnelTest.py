import os 
import fcntl
import struct
import pytun
import digitalio, board, busio, adafruit_rfm9x
import time
import socket
import matplotlib.pyplot as plt
import signal
import sys

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

t0 = time.perf_counter()
print("UDPTest is up")

RECEIVER_IP = "192.168.1.3" # Inuti08
MY_IP = "192.168.1.2"       # Inuti07
UDP_PORT = 4000

tx_sock = socket.socket( socket.AF_INET,    # Internet
                         socket.SOCK_DGRAM) # UDP

rx_sock = socket.socket( socket.AF_INET,    # Internet
                         socket.SOCK_DGRAM) # UDP

rx_sock.bind((MY_IP, UDP_PORT)) # Bind to local network

station = UDPStation(tun, tx_sock, rx_sock, RECEIVER_IP, UDP_PORT)

x = []
y = []

def graceful_exit(sig, frame):
    global x, y, station
    print("Graceful exit.")
    station.shutdown()
    tun.down()
    tun.close()

    plt.plot(x, y)
    plt.savefig("tmp.png")
    print("UDPTest is down")
    sys.exit(0)

signal.signal(signal.SIGINT, graceful_exit)

pack_count = 0
t0 = time.time()
while pack_count < 500:
    packet = tun.read(tun.mtu)
    print("Packet in tun: \n" + str(packet))
    station.send(packet, 8)
    pack_count += 1
    y.append(pack_count)
    x.append(time.time() - t0)

tun.down()
tun.close()
station.shutdown()

plt.plot(x, y)
plt.savefig("tmp.png")
print("UDPTest is down")


