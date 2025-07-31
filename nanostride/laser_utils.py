import nidaqmx

def toggle_shutter(shutter_state):
    device = 'PXI1Slot2'
    ao_channel = "ao1"
    with nidaqmx.Task() as ao_task:
        ao_task.ao_channels.add_ao_voltage_chan(f"{device}/{ao_channel}")
        if shutter_state == "ON":
            ao_task.write(5.0)
            ao_task.stop()
        elif shutter_state == "OFF":
            ao_task.write(0.0)
            ao_task.stop()

def toggle_resonance_scanner(scanner_state):
    device = 'PXI1Slot2'
    ao_channel = "ao0"
    with nidaqmx.Task() as ao_task:
        ao_task.ao_channels.add_ao_voltage_chan(f"{device}/{ao_channel}")
        if scanner_state == "ON":
            ao_task.write(4.0)
            ao_task.stop()
        elif scanner_state == "OFF":
            ao_task.write(0.0)
            ao_task.stop()
    