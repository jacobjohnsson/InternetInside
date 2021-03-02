import board
import time
import threading
import pytun
import socket
from functools import reduce

from multiprocessing import Queue, Process

RADIO_MTU = 200

class UDPStation:

    tx_queue = Queue(200)
    rx_queue = Queue(400)
    IP_ID = 0

    def __init__(self, tun, tx_sock, rx_sock, RECEIVER_IP, UDP_PORT):
        self.tun = tun
        self.tx_sock = tx_sock
        self.rx_sock = rx_sock
        self.RECEIVER_IP = RECEIVER_IP
        self.UDP_PORT = UDP_PORT

        self.rx_process = Process(target=self.blocking_receive, kwargs={'queue':self.rx_queue})
        self.rx_process.start()

        self.tx_process = Process(target=self.blocking_send, kwargs={'queue':self.tx_queue})
        self.tx_process.start()

    def shutdown(self):
        self.rx_process.terminate()
        self.tx_process.terminate()

    def send(self, message, dest):
        self.tx_queue.put((message, dest))
        #print("SendQueue size: " + tx_queue.qsize())

    def blocking_send(self, queue):
        while True:
            message = self.tx_queue.get()
            ip_data = message[0]
            dest = message[1]
            print("IP packet length: " + str(len(ip_data)))
            
            if len(ip_data) < RADIO_MTU:      # No fragmentation required, just add radio_header anyway ( package number 0 of 0)
                current_id = 0
                last_id = 0
                radio_message = (str(current_id) + str(last_id) + str(bytes(self.IP_ID))).encode("utf-8") + ip_data
                self.tx_sock.sendto(radio_message, (self.RECEIVER_IP, self.UDP_PORT))
                
            else:                               # Fragmentation required
                radio_payloads = []
                i = 0
                while (i + 1 < len(ip_data) / RADIO_MTU):
                    radio_payloads.append(ip_data[i * RADIO_MTU : (i + 1) * RADIO_MTU])
                    i += 1
                radio_payloads.append(ip_data[i * RADIO_MTU : len(ip_data)])

                print("NBR OF PAYLOADS: " + str(len(radio_payloads)))
                for payload in radio_payloads:
                    print("PAYLOAD: " + str(payload))

                current_id = 0
                last_id = len(radio_payloads) - 1
                for payload in radio_payloads:
                    radio_message = (str(current_id) + str(last_id) + str(self.IP_ID)).encode("utf-8") + payload
                    self.tx_sock.sendto(radio_message, (self.RECEIVER_IP, self.UDP_PORT))
                    current_id += 1
                    print("\n   RADIO_MESSAGE SENT:\n" + str(radio_message) + "\n")

            self.IP_ID += 1
            if self.IP_ID == 10:
                self.IP_ID = 0


    def receive(self) -> str:
        #print("Receive-Size: " + str(self.rx_queue.qsize()))
        return self.rx_queue.get()

    def receive_timeout(self, timeout) -> str:
        #print("Receive-Size: " + str(self.rx_queue.qsize()))
        try:
            return self.rx_queue.get(timeout=timeout)
        except:
            return None

    def blocking_receive(self, queue):
        while True:
            message, addr = self.rx_sock.recvfrom(1024)
            if message == None:
                continue
            
            print("Size of tx_queue: " + str(self.tx_queue.qsize()))
            print("Size of rx_queue: " + str(self.rx_queue.qsize()))
            # print("Message[0]: " + str(chr(message[0])))
            # print("Message: " + str(message))

            if int(chr(message[1])) != 0:     # FRAGMENTS!
                
                fragment_nbr = int(chr(message[0]))
                nbr_of_fragments = int(chr(message[1])) + 1
                print("Total fragments: " + str(nbr_of_fragments))
                print("Fragment nbr: " + str(fragment_nbr))
                print("Fragment: " + str(message) + "\n")
                fragments = [None] * nbr_of_fragments
                fragments[fragment_nbr] = message[3: ]

                i = 1
                while (i < nbr_of_fragments):
                    message, addr = self.rx_sock.recvfrom(1024)
                    fragment_nbr = int(chr(message[0]))
                    print("Fragment nbr: " + str(fragment_nbr))
                    print("Fragment: " + str(message) + "\n")
                    fragments[fragment_nbr] = message[3: ]
                    i += 1

                message = reduce((lambda x, y: x + y), fragments)

            print("Printing \t" + str(message) + " to tun.\n")
            self.rx_queue.put(bytes(message))
            self.tun.write(bytes(message))
                
    def tx_queue_size(self):
        return self.tx_queue.qsize()

class TunStation:

    tx_queue = Queue(200)
    rx_queue = Queue(400)

    def __init__(self, receiver: board, transmitter: board, address: int, tun):
        self.tun = tun
        self.address = address
        self.receiver = receiver
        self.receiver.node = address
        self.rx_process = Process(target=self.blocking_receive, kwargs={'queue':self.rx_queue})
        self.rx_process.start()

        self.transmitter = transmitter
        self.transmitter.node = address
        self.tx_process = Process(target=self.blocking_send, kwargs={'queue':self.tx_queue})
        self.tx_process.start()
        

    def shutdown(self):
        self.receiver.reset()
        self.transmitter.reset()
        self.rx_process.terminate()
        self.tx_process.terminate()

    def send(self, message, dest):
        self.tx_queue.put((message, dest))
        #print("SendQueue size: " + tx_queue.qsize())

    def blocking_send(self, queue):
        while True:
            message = self.tx_queue.get()
            data = message[0]
            dest = message[1]
            self.transmitter.send(data, destination=dest)

    def receive(self) -> str:
        #print("Receive-Size: " + str(self.rx_queue.qsize()))
        return self.rx_queue.get()

    def receive_timeout(self, timeout) -> str:
        #print("Receive-Size: " + str(self.rx_queue.qsize()))
        try:
            return self.rx_queue.get(timeout=timeout)
        except:
            return None

    def blocking_receive(self, queue):
        while True:
            message = self.receiver.receive(with_header=True)
            if message != None:
                self.rx_queue.put(message)
                self.tun.write(bytes(message[4:]))
                print("Printing \n" + str(bytes(message[4:])) + " to tun.\n")

    def tx_queue_size(self):
        return self.tx_queue.qsize()

class ThreadedStation:

    tx_queue = Queue(200)
    rx_queue = Queue(400)

    def __init__(self, receiver: board, transmitter: board, address: int):
        self.address = address
        self.receiver = receiver
        self.receiver.node = address
        self.rx_process = Process(target=self.blocking_receive, kwargs={'queue':self.rx_queue})
        self.rx_process.start()

        self.transmitter = transmitter
        self.transmitter.node = address
        self.tx_process = Process(target=self.blocking_send, kwargs={'queue':self.tx_queue})
        self.tx_process.start()

    def shutdown(self):
        self.receiver.reset()
        self.transmitter.reset()
        self.rx_process.terminate()
        self.tx_process.terminate()

    def send(self, message, dest):
        self.tx_queue.put((message, dest))
        #print("SendQueue size: " + tx_queue.qsize())

    def blocking_send(self, queue):
        while True:
            message = self.tx_queue.get()
            data = message[0]
            dest = message[1]
            self.transmitter.send(data, destination=dest)

    def receive(self) -> str:
        #print("Receive-Size: " + str(self.rx_queue.qsize()))
        return self.rx_queue.get()

    def receive_timeout(self, timeout) -> str:
        #print("Receive-Size: " + str(self.rx_queue.qsize()))
        try:
            return self.rx_queue.get(timeout=timeout)
        except:
            return None

    def blocking_receive(self, queue):
        while True:
            message = self.receiver.receive(with_header=True)
            if message != None:
                self.rx_queue.put(message)

    def tx_queue_size(self):
        return self.tx_queue.qsize()