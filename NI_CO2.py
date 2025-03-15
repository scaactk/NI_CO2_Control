import time
import serial
import nidaqmx
from nidaqmx.constants import TerminalConfiguration

# Serial port configuration
ser = serial.Serial(
    port='COM4',
    baudrate=9600,
    bytesize=serial.EIGHTBITS,
    stopbits=serial.STOPBITS_ONE,
    parity=serial.PARITY_NONE,
    timeout=0
)

# CO2 concentration threshold, 10% corresponds to this sensor value
CO2_THRESHOLD = 10000  # 10% = 10000 ppm

# NI device output configuration
VALVE_CONTROL_CHANNEL = "Dev1/ao1"  # NI device AO0 channel, depends on which channel you are going to use
VALVE_ON_VOLTAGE = 5.0  # Output voltage when valve is open
VALVE_OFF_VOLTAGE = 0.0  # Output voltage when valve is closed


def read_co2_value():
    """Read and parse CO2 sensor value"""
    query = 'Z\r\n'.encode('ascii')
    ser.write(query)
    time.sleep(0.1)  # Give sensor some response time

    buffer_size = ser.inWaiting()
    if buffer_size:
        data = ser.read(buffer_size).decode('utf-8')
        print(f"Raw data: {data}")

        # Parse data, extract value portion
        try:
            # Assuming data format is "Z 00018", we need to extract "00018" and convert to integer
            parts = data.strip().split(' ')
            if len(parts) >= 2 and parts[0] == 'Z':
                co2_value = int(parts[1])
                print(f"CO2 concentration: {co2_value}")
                return co2_value
        except Exception as e:
            print(f"Data parsing error: {e}")

    return None


def control_valve(open_valve):
    """Control the solenoid valve"""
    with nidaqmx.Task() as task:
        task.ao_channels.add_ao_voltage_chan(
            VALVE_CONTROL_CHANNEL,
            min_val=0.0,
            max_val=5.0
        )

        if open_valve:
            task.write(VALVE_ON_VOLTAGE)
            print("Valve opened - Releasing CO2")
        else:
            task.write(VALVE_OFF_VOLTAGE)
            print("Valve closed - Stopping CO2 release")


# Main loop
try:
    print("CO2 concentration monitoring and control system started...")

    # Initialize by closing the valve
    control_valve(False)

    while True:
        # Read CO2 concentration
        co2_value = read_co2_value()

        if co2_value is not None:
            # Check if CO2 concentration is below threshold
            if co2_value < CO2_THRESHOLD:
                # CO2 concentration below 10%, open valve
                control_valve(True)
            else:
                # CO2 concentration at or above 10%, close valve
                control_valve(False)

        # Wait 1 second before next detection
        time.sleep(1)

except KeyboardInterrupt:
    print("Program interrupted by user")
    # Ensure valve is closed before exiting
    control_valve(False)

except Exception as e:
    print(f"Error occurred: {e}")
    # Ensure valve is closed in case of error
    control_valve(False)

finally:
    # Clean up resources
    ser.close()
    print("Program has exited")