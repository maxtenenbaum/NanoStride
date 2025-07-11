def list_com_ports():
    import serial.tools.list_ports
    ports = serial.tools.list_ports.comports()
    ports_list = []
    for port, desc, other in sorted(ports):
        ports_list.append("{}: {}".format(port, desc))
    return ports_list

# Error handling
def show_error(msg):
    from tkinter import messagebox
    messagebox.showerror("Error", msg)
