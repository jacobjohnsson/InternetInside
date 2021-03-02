import os 
import fcntl
import struct
import digitalio, board, busio, adafruit_rfm9x
import time
import pytun
import socket
import signal
import sys

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

tun = pytun.TunTapDevice(name="LongG")
tun.addr = "192.168.2.108"
tun.netmask = "255.255.255.0"
tun.dstaddr = "192.168.2.107"
tun.mtu = 1500

tun.up()
t0 = time.perf_counter()
print("UDPEcho is up")

RECEIVER_IP = "192.168.1.6" # Inuti07
MY_IP = "192.168.1.3"       # Inuti08
UDP_PORT = 4000

tx_sock = socket.socket( socket.AF_INET,    # Internet
                         socket.SOCK_DGRAM) # UDP

rx_sock = socket.socket( socket.AF_INET,    # Internet
                         socket.SOCK_DGRAM) # UDP

rx_sock.bind((MY_IP, UDP_PORT))             # Bind to local network

station = UDPStation(tun, tx_sock, rx_sock, RECEIVER_IP, UDP_PORT)

def graceful_exit(sig, frame):
    global station
    print("Graceful exit.")
    station.shutdown()
    tun.down()
    tun.close()

    print("UDPEcho is down")
    sys.exit(0)

signal.signal(signal.SIGINT, graceful_exit)

while True:
    message = station.receive()
    
    print("Received: \n" + str(bytes(message)) + "\n")
    
    response = tun.read(tun.mtu)
    print("Message has been read..")
    station.send(response, 7)
    print("Sent a response : \n" + str(bytes(response)) + "\n")

tun.down()
tun.close()
station.shutdown()

print("UDPEcho is down")