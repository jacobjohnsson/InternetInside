import board
import queue
import time
import threading

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

    tx_queue = queue.Queue(64)
    rx_queue = queue.Queue(128)

    def __init__(self, receiver: board, transmitter: board, address: int):
        self.address = address
        self.receiver = receiver
        self.receiver.node = address
        self.rx_process = threading.Thread(target=self.blocking_receive, kwargs={'queue':self.rx_queue})
        self.rx_process.start()

        self.transmitter = transmitter
        self.transmitter.node = address
        self.tx_process = threading.Thread(target=self.blocking_send, kwargs={'queue':self.tx_queue})
        self.tx_process.start()

    def send(self, message):
        print("Adding \"" + str(message) + "\" to the tx_queue.")
        self.tx_queue.put(message)
        # print("Size of queue: " + str(self.tx_queue.qsize()))

    def receive(self) -> str:
        return self.rx_queue.get()

    def receive_timeout(self, timeout) -> str:
        return self.rx_queue.get(timeout=timeout)

    def blocking_send(self, queue):
        while True:
            print("[TX] Size of tx_queue: " + str(queue.qsize()))
            message = self.tx_queue.get()
            print("[TX] Sending " + str(message))
            self.transmitter.send(message)

    def blocking_receive(self, queue):
        while True:
            print("[RX] Size of rx_queue: " + str(queue.qsize()))
            message = self.receiver.receive(with_header=True)
            print("[RX] Received: " + str(message))
            self.rx_queue.put(message)

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
