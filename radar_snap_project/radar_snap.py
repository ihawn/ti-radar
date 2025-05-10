import serial
import time
import subprocess
import numpy as np
import os
import socket

PORT = '/dev/ttyUSB0'
BAUD = 115200
CFG_FILE = 'one_frame.cfg'

BIN_FILE = 'adc_raw.bin'
TXT_FILE = 'output.txt'
NCAT_TIMEOUT = 5 
UDP_PORT = 4098

NUM_RX = 4
SAMPLES_PER_CHIRP = 256
NUM_CHIRPS = 1

def send_cfg():
    print(f"[INFO] Sending config to radar on {PORT}...")
    with serial.Serial(PORT, BAUD, timeout=1) as ser:
        with open(CFG_FILE, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('%'):
                    continue
                ser.write((line + '\n').encode())
                print(f'> {line}')
                time.sleep(0.1)


def capture_udp_data():
    print(f"[INFO] Listening for UDP packets on port {UDP_PORT} for {NCAT_TIMEOUT}s...")

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("", UDP_PORT))
    sock.settimeout(NCAT_TIMEOUT)

    start_time = time.time()
    with open(BIN_FILE, "wb") as f:
        try:
            while time.time() - start_time < NCAT_TIMEOUT:
                data, addr = sock.recvfrom(4096)
                f.write(data)
        except socket.timeout:
            pass
        except Exception as e:
            print(f"[ERROR] UDP capture failed: {e}")
        finally:
            sock.close()

    print(f"[INFO] Saved raw binary to {BIN_FILE}")


def convert_binary_to_txt():
    print(f"[INFO] Converting {BIN_FILE} to {TXT_FILE}...")
    raw = np.fromfile(BIN_FILE, dtype=np.int16)
    expected_len = NUM_RX * SAMPLES_PER_CHIRP * NUM_CHIRPS
    if len(raw) != expected_len:
        print(f"[WARN] Expected {expected_len} samples but got {len(raw)}")

    try:
        reshaped = raw.reshape((NUM_CHIRPS, SAMPLES_PER_CHIRP, NUM_RX))
    except ValueError:
        print("[ERROR] Cannot reshape raw data — check radar config and capture.")
        return

    with open(TXT_FILE, 'w') as f:
        for chirp in reshaped:
            for sample in chirp:
                f.write(' '.join(map(str, sample)) + '\n')

    print(f"[INFO] Saved readable data to {TXT_FILE}")

if __name__ == '__main__':
    send_cfg()
    capture_udp_data()
    convert_binary_to_txt()
