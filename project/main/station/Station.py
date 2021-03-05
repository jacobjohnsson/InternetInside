import board
import time
import threading
import pytun
import socket
from functools import reduce

from multiprocessing import Queue, Process, Lock

ACK = '1'
DATA = '0'
TIMEOUT = 1.0       # seconds
MAX_WINDOW_SIZE = 4
window = Queue()
window_lock = Lock()
last_ack = -1

RADIO_DST = 8
RADIO_MTU = 100

class UDPACKStation:

    tx_queue = Queue(200)
    rx_queue = Queue(400)
    IP_ID = 0

    def __init__(self, tun, tx_sock, rx_sock, RECEIVER_IP, UDP_PORT):
        self.tun = tun
        self.tx_sock = tx_sock
        self.rx_sock = rx_sock
        self.rx_sock.settimeout(TIMEOUT)
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
        global ACK, DATA, TIMEOUT, MAX_WINDOW_SIZE, window, last_ack

        while True:
            message = self.tx_queue.get()
            # print("message[0]: " + str(message[0]))
            # print("message[0][0]: " + str(message[0][0]))
            # print("chr(message[0][0]): " + str(chr(message[0][0])))
            if chr(message[0][0]) == ACK: 
                print("Sending an ACK: " + str(message[0]))
                self.tx_sock.sendto(message[0], (self.RECEIVER_IP, self.UDP_PORT))
                continue
            else:
                # print("Sending DATA: " + str(message[0]))
                # print("message[0][2] = " + chr(message[0][2]))
                if message[0][2] == 134: # only ICMP plz
                    continue
            print("\t - - - - Sending Message - - - - \n\n" + str(message[0]) + "\n")

            # Empty the window
            window_lock.acquire()
            while not window.empty():
                window.get()
            print("Windows size: " + str(window.qsize()))
            window_lock.release()

            ip_data = message[0]
            dest = message[1]
            print("\nIP packet length: " + str(len(ip_data)))

            radio_payloads = []
            i = 0
            while (i + 1 < len(ip_data) / RADIO_MTU):
                radio_payloads.append(ip_data[i * RADIO_MTU : (i + 1) * RADIO_MTU])
                i += 1
            radio_payloads.append(ip_data[i * RADIO_MTU : len(ip_data)])
            

            #radio_message = (str(0) + str(0) + str(bytes(self.IP_ID))).encode("utf-8") + ip_data    

            radio_messages = []     # including new fragment header
            current_id = 0
            last_id = len(radio_payloads) - 1
            for payload in radio_payloads:
                radio_messages.append((DATA + str(current_id) + str(last_id) + str(self.IP_ID)).encode("utf-8") + payload)
                # self.tx_sock.sendto(radio_message, (self.RECEIVER_IP, self.UDP_PORT))
                current_id += 1
                # print("\n   RADIO_MESSAGE SENT:\n" + str(radio_message) + "\n")

            print("NBR OF PAYLOADS: " + str(len(radio_messages)))
            for payload in radio_messages:
                print("HEADER + PAYLOAD: " + str(payload[0:20]) + "...")

            last_sent_pack = -1
            last_sent_pack_time = time.time()
            
            
            while last_sent_pack < last_id:
                while (window.qsize() < min(len(radio_messages), MAX_WINDOW_SIZE)) and last_sent_pack < last_id:

                    print("SENDING: " + str(radio_messages[last_sent_pack + 1][0:20]) + "...")
                    self.tx_sock.sendto(radio_messages[last_sent_pack + 1], (self.RECEIVER_IP, self.UDP_PORT))
                    last_sent_pack_time = time.time()
                    last_sent_pack += 1
                    window_lock.acquire()
                    window.put(last_sent_pack)
                    window_lock.release()

                # print("Window Complete, windows size: " + str(window.qsize()))


                # time.sleep(0.1)

                if last_sent_pack >= last_id and last_ack == last_id:
                    print("last_ack: " + str(last_ack))
                    print("loop broken")
                    last_ack = -1
                    window_lock.acquire()
                    while not window.empty():
                        window.get()
                    window_lock.release()
                    break

            print("\t - - - - Message Sent - - - - \n\n")


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
        global ACK, DATA, TIMEOUT, MAX_WINDOW_SIZE, window, last_ack

        while True:
            try:
                message, addr = self.rx_sock.recvfrom(1024)
            except socket.timeout:
                continue
            
            if message == None:
                continue

            print("\t - - - - Incoming Message - - - - \n\n")
            print("Size of tx_queue: " + str(self.tx_queue.qsize()))
            print("Size of rx_queue: " + str(self.rx_queue.qsize()))
            # print("Message[0]: " + str(chr(message[0])))
            # print("Received message: " + message.decode("utf-8"))
            print("int(chr(message[0])) = " + str(int(chr(message[0]))))

            if int(chr(message[0])) == int(ACK):
                print("Got an ACK: " + str(message))
                ack_number = message[1]

                last_ack = ack_number

                # Remove all messages with IDs lower than ack_number from window
                print("Discarding from window:")
                window_lock.acquire()
                for i in range(int(chr(ack_number)) + 1):
                    if not window.empty():
                        frag_number = window.get(0)
                        print(frag_number)
                window_lock.release()
                
                continue

            elif int(chr(message[2])) == 0:     # No Fragments
                message = message[4:]
                ack = (ACK + str(0)).encode("utf-8")
                print("Sending ACK!")
                print("ACK: " + str(ack))
                self.send(ack, RADIO_DST)
                # self.tx_sock.sendto((ACK + str(0)).encode("utf-8"), (self.RECEIVER_IP, self.UDP_PORT))

            elif int(chr(message[2])) != 0:     # FRAGMENTS!
                t0 = time.time()
                last_correct_pack = 0           # Read from message, like line directly below?

                fragment_nbr = int(chr(message[1]))
                nbr_of_fragments = int(chr(message[2])) + 1
                print("Total fragments: " + str(nbr_of_fragments))
                print("Fragment nbr: " + str(fragment_nbr))
                print("Fragment: " + str(message) + "\n")
                fragments = [None] * nbr_of_fragments
                fragments[fragment_nbr] = message[4: ]

                i = 1
                acked = False
                message_received = False
                while (not message_received) or (not acked):
                    print("outer loop")
                    acked = False
                    t0 = time.time()
                    #time.sleep(0.2)
                    while i < nbr_of_fragments and time.time() < (t0 + TIMEOUT):

                        try:
                            message, addr = self.rx_sock.recvfrom(1024)
                        except socket.timeout:
                            continue

                        fragment_nbr = int(chr(message[1]))
                        print("Fragment nbr: " + str(fragment_nbr))

                        if fragment_nbr == last_correct_pack + 1:
                            t0 = time.time()
                            print("Correctly received fragment!")
                            last_correct_pack += 1
                        
                        print("Fragment: " + str(message) + "\n")
                        fragments[fragment_nbr] = message[4 : ]
                        i += 1

                    if time.time() > (t0 + TIMEOUT):
                        ack = (ACK + str(last_correct_pack)).encode("utf-8")
                        print("Sending ACK!")
                        print("ACK: " + str(ack))
                        self.send(ack, RADIO_DST)
                        #self.tx_sock.sendto((ACK + str(last_correct_pack)).encode("utf-8"), (self.RECEIVER_IP, self.UDP_PORT))
                        acked = True
                    
                    if i == nbr_of_fragments: # Last fragment
                        ack = (ACK + str(last_correct_pack)).encode("utf-8")
                        print("Sending ACK!")
                        print("ACK: " + str(ack))
                        self.send(ack, RADIO_DST)
                        # self.tx_sock.sendto((ACK + str(last_correct_pack)).encode("utf-8"), (self.RECEIVER_IP, self.UDP_PORT))
                        acked = True
                        print("Message fully received cuz: " + str(i) + "==" + str(nbr_of_fragments))
                        message_received = True

                print(fragments)
                message = reduce(lambda x, y: x + y, fragments)

            print("Printing \t" + str(message) + " to tun.\n")
            self.rx_queue.put(bytes(message))
            self.tun.write(bytes(message))
                
    def tx_queue_size(self):
        return self.tx_queue.qsize()



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