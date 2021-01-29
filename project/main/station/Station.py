import board
import time
import threading

from multiprocessing import Queue, Process

terminate_station = False

class Station:

    def __init__(self, receiver: board, transmitter: board):
        self.strategy = NoStrategy()
        self.receiver = receiver
        self.transmitter = transmitter

    def setStrategy(self, strategy):
        self.strategy = strategy
        self.strategy.setReceiver(self.receiver)
        self.strategy.setTransmitter(self.transmitter)

    def send(self, message):
        self.strategy.send(message)

    def receive(self) -> str:
        return self.strategy.receive()

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
        terminate_station = True
        self.rx_process.join()
        self.tx_process.join()

    def send(self, message, dest):
        self.tx_queue.put((message, dest))
        #print("SendQueue size: " + tx_queue.qsize())

    def blocking_send(self, queue):
        while True:
            message = self.tx_queue.get()
            data = message[0]
            dest = message[1]
            self.transmitter.send(data, destination=dest)
            if terminate_station:       # A horrendous way to stop a thread...
                break;

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
            if terminate_station:       # A horrendous way to stop a thread...
                break;


class NoStrategy:

    def __init__(self):
        pass

    def send(self, message):
        pass

    def receive(self):
        pass

    def setReceiver(self, receiver: board):
        pass

    def setTransmitter(self, transmitter: board):
        pass

class BasicStrategy(NoStrategy):

    def __init__(self, receiver: board, transmitter: board):
        self.receiver = receiver
        self.transmitter = transmitter

    def send(self, message):
        b = bytearray()
        b.extend(map(ord, message))
        self.transmitter.send(b)

    def receive(self) -> bytearray:
        return self.receiver.receive()

    def setReceiver(self, receiver: board):
        self.receiver = receiver

    def setTransmitter(self, transmitter: board):
        self.transmitter = transmitter
