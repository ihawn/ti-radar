import serial

PORT = '/dev/ttyUSB1'
BAUD = 115200

with serial.Serial(PORT, BAUD, timeout=1) as ser:
    ser.write(b'echo "connected"\n')