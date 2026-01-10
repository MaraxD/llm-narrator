import time

import serial


def main() -> None:
    serial_port_no = 1443440
    SERIAL_PORT = f"/dev/cu.usbserial-{serial_port_no}"

    BAUD_RATE = 115200  # must match the ESP baud rate
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    time.sleep(2)  # wait for ESP to initialize

    try:
        while True:
            with open("runtime/actions.txt", mode="r") as actions_file:
                # always read the final entry
                data = actions_file.readlines()
                if data:
                    last_entry = data[-1]
                    ser.write(last_entry.encode())  # send as bytes
    except KeyboardInterrupt:
        print("\nClosing connection.")
        ser.close()


if __name__ == "__main__":
    main()
