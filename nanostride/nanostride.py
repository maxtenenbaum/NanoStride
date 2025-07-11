from tkinter import *
from tkinter import messagebox
from tkinter import ttk
import gui_utils
import motion_utils

# Error handling
def show_error(msg):
    messagebox.showerror("Error", msg)
############

def connect_stages():
    selected_port = stage_port.get().split(':')[0]
    if len(selected_port) > 0:
        global stages
        stages = motion_utils.StageController(selected_port)
    else:
        show_error("No port selected.") 

root = Tk()

# Motion control frame
mc_frame = ttk.Frame(root, padding=10)
mc_frame.grid()

ttk.Label(mc_frame, text="Motion Control").grid(row=0, column=0)

# Stage connection frame
sc_frame = ttk.Frame(mc_frame, padding=10)
sc_frame.grid(row=1, column=0)
ttk.Label(sc_frame, text="Stage Connection").grid(row=0, column=0)
stage_port = ttk.Combobox(sc_frame, values=gui_utils.list_com_ports())
stage_port.grid(row=1, column=0)

ttk.Button(sc_frame, text='Connect Stages', command=connect_stages).grid(row=2, column=0)

# Hexapod connection frame
hp_frame = ttk.Frame(mc_frame, padding=10)
hp_frame.grid(row=1, column=1)
ttk.Label(hp_frame, text="Hexapod Connection").grid(row=0, column=0)
ttk.Combobox(hp_frame, values=gui_utils.list_com_ports()).grid(row=1, column=0)

root.mainloop()
