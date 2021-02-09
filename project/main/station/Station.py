import board
import time
import threading
import pytun

from multiprocessing import Queue, Process

terminate_station = False

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
                print("Printing " + str(message) + " to tun.\n")

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