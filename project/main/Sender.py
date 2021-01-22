import PyLora
import time
PyLora.init()
PyLora.set_frequency(915000000)
PyLora.enable_crc()
while True:
    PyLora.send_packet('Hello')
    print('Packet sent...')
    time.sleep(2)