import board

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