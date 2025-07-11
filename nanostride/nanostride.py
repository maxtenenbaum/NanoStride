from tkinter import *
from tkinter import messagebox
from tkinter import ttk
import gui_utils
import motion_utils

# HELPER FUNCTION
def set_light(canvas, color):
    canvas.itemconfig("light", fill=color)

# FUNCTIONS 

# Stages
def connect_stages():
    selected_port = stage_port.get()
    if selected_port:
        port_num = int(selected_port.split(':')[0][3:])
        set_light(stage_light, 'yellow')  # show connecting
        root.update_idletasks()  # refresh UI immediately
        global stages
        try:
            stages = motion_utils.StageController(port_num)
            if stages.hc >= 0:
                print('Connection success')
                set_light(stage_light, 'green')
            else:
                print("Connection failure. Maybe wrong port?")
                set_light(stage_light, 'red')
        except Exception as e:
            print(f"Stage connection error: {e}")
            set_light(stage_light, 'red')
    else:
        gui_utils.show_error("No port selected.")
def initialize_stages():
    try:
        stages.zero_stage()
        print("Stages initialized.")
    except NameError:
        gui_utils.show_error("Stages not connected yet.")
    except Exception as e:
        gui_utils.show_error(f"Initialization failed: {str(e)}")
def update_stage_position():
    try:
        if 'stages' in globals() and stages is not None:
            x_pos, y_pos = stages.get_stage_pos()  # your function
            stage_position_label.config(text=f"X: {x_pos:.2f}, Y: {y_pos:.2f}")
    except Exception as e:
        stage_position_label.config(text="X: ---, Y: ---")
    root.after(200, update_stage_position)  # repeat every 200 ms

# Hexapod Control
def connect_hexapod():
    selected = hexapod_port.get()
    if selected:
        port_num = int(selected.split(':')[0][3:])
        set_light(hexapod_light, 'yellow')  # show connecting
        root.update_idletasks()  # refresh UI immediately
        global hexapod
        try:
            hexapod = motion_utils.HexapodController(port_num)
            if hexapod.connected:
                print("Connection success")
                set_light(hexapod_light, 'green')
            else:
                gui_utils.show_error("Connection failed. Maybe wrong port?")
                set_light(hexapod_light, 'red')
        except Exception as e:
            print(f"Hexapod connection error: {e}")
            set_light(hexapod_light, 'red')
    else:
        gui_utils.show_error("No port selected.")
def initialize_hexapod():
    try:
        if not hexapod.connected:
            gui_utils.show_error("Hexapod not connected yet.")
            return
        hexapod.zero_hexapod()
        print("Hexapod initialized.")
    except NameError:
        gui_utils.show_error("Hexapod not connected yet.")
    except Exception as e:
        gui_utils.show_error(f"Initialization failed: {str(e)}")

def close_and_kill():
    if 'hexapod' in globals():
        hexapod.close()
    if 'stages' in globals():
        stages.close_stage()
    root.quit()

# GUI SETUP
root = Tk()
root.title("Motion Control")

# Motion control frame
mc_frame = ttk.Frame(root, padding=10)
mc_frame.grid()

ttk.Label(mc_frame, text="Motion Control").grid(row=0, column=0, columnspan=2)

# Stage connection frame
sc_frame = ttk.Frame(mc_frame, padding=10)
sc_frame.grid(row=1, column=0)
ttk.Label(sc_frame, text="Stage Connection").grid(row=0, column=0, sticky=W)

stage_port = ttk.Combobox(sc_frame, values=gui_utils.list_com_ports())
stage_port.grid(row=1, column=0)

# Stage light
stage_light = Canvas(sc_frame, width=20, height=20, highlightthickness=0)
stage_light.grid(row=1, column=1, padx=5)
stage_light.create_oval(2, 2, 18, 18, fill="", tags="light")

ttk.Button(sc_frame, text='Connect', command=connect_stages).grid(row=2, column=0, pady=2, sticky=W)
ttk.Button(sc_frame, text='Initialize', command=initialize_stages).grid(row=3, column=0, pady=2, sticky=W)

# Hexapod connection frame
hp_frame = ttk.Frame(mc_frame, padding=10)
hp_frame.grid(row=1, column=1)
ttk.Label(hp_frame, text="Hexapod Connection").grid(row=0, column=0, sticky=W)

hexapod_port = ttk.Combobox(hp_frame, values=gui_utils.list_com_ports())
hexapod_port.grid(row=1, column=0)

# Hexapod light
hexapod_light = Canvas(hp_frame, width=20, height=20, highlightthickness=0)
hexapod_light.grid(row=1, column=1, padx=5)
hexapod_light.create_oval(2, 2, 18, 18, fill="", tags="light")

ttk.Button(hp_frame, text='Connect Hexapod', command=connect_hexapod).grid(row=2, column=0, pady=2, sticky=W)
ttk.Button(hp_frame, text='Initialize Hexapod', command=initialize_hexapod).grid(row=3, column=0, pady=2, sticky=W)

# Stage movement frame
sm_frame = ttk.Frame(mc_frame, padding=10)
sm_frame.grid(row=2, column=0)
ttk.Label(sm_frame, text='Stage Movement').grid(row=0, column=0, sticky=W)
# Live position label
stage_position_label = ttk.Label(sm_frame, text="X: ---, Y: ---")
stage_position_label.grid(row=1, column=0, sticky=W, pady=(5, 0))


# Disconnect all and close
ttk.Button(mc_frame, text="Close and Kill", command=close_and_kill).grid(row=3, column=0, columnspan=2, pady=10)

update_stage_position()
root.mainloop()
