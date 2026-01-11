import time

import serial

from projects import append_action


def main() -> None:
    serial_port_no = 14340
    SERIAL_PORT = f"/dev/cu.wchusbserial{serial_port_no}"

    BAUD_RATE = 115200  # must match the ESP baud rate
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    time.sleep(2)  # wait for ESP to initialize

    try:
        while True:
            face_expression = ser.readline().decode().strip()
            append_action(tag=face_expression)
    except KeyboardInterrupt:
        print("\nClosing connection.")
        ser.close()


if __name__ == "__main__":
    main()
