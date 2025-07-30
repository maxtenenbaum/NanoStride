from tkinter import *
from tkinter import messagebox
from tkinter import ttk
import gui_utils
import motion_utils
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk


# HELPER FUNCTIONS
def set_light(canvas, color):
    canvas.itemconfig("light", fill=color)
def close_and_kill():
    if 'hexapod' in globals():
        hexapod.close()
    if 'stages' in globals():
        stages.close_stage()
    root.quit()

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
            stage_position_label.config(text=f"X: {x_pos:.4f}, Y: {y_pos:.4f}")
    except Exception as e:
        stage_position_label.config(text="X: ---, Y: ---")
    root.after(20, update_stage_position)  # repeat every 200 ms

def move_stage():
    desired_stage_x = stage_x_entry.get()
    desired_stage_y = stage_y_entry.get()
    stages.move_stage_to_point(desired_stage_x, desired_stage_y)

def relative_move_stage(axis):
    x_pos, y_pos = stages.get_stage_pos()
    step = float(stage_step_entry.get())
    if axis == "+Y":
        stages.move_stage_to_point(x_pos, y_pos+step)
    if axis == "-Y":
        stages.move_stage_to_point(x_pos, y_pos-step)
    if axis == "+X":
        stages.move_stage_to_point(x_pos+step, y_pos)
    if axis == '-X':
        stages.move_stage_to_point(x_pos-step, y_pos)

# Hexapod
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
def update_hexapod_position():
    try:
        if 'hexapod' in globals() and hexapod is not None:
            hexapod_positions = hexapod.get_hexapod_pos()
            hexapod_position_label.config(text=f"X: {hexapod_positions['X']:.4f}, Y: {hexapod_positions['Y']:.4f}, Z: {hexapod_positions['Z']:.4f}\nU: {hexapod_positions['U']:.4f}, V: {hexapod_positions['V']:.4f}, W: {hexapod_positions['W']:.4f}")
    except Exception as e:
        hexapod_position_label.config(text=e)
    root.after(20, update_hexapod_position)
def move_hexapod():
    def get_desired_positions():
        return {
            axis: float(entry_vars[axis].get())
            for axis in entry_vars
        }
    hexapod.move_hexapod(get_desired_positions())

#########################################################################
#########################################################################

# GUI SETUP
root = Tk()
root.title("NanoStride")

#########################################################################
# Motion control frame
#########################################################################

mc_frame = ttk.Frame(root, padding=10)
mc_frame.grid(column=0, row=0,sticky=W)
ttk.Label(mc_frame, text="Device Selection").grid(row=0, column=0, sticky=W)
#########################################################################
# Connection frame
#########################################################################
connection_frame = ttk.Frame(mc_frame, padding=10, relief="solid", borderwidth=1)
connection_frame.grid(row=1, column=0)
ttk.Label(connection_frame, text='Stages: ').grid(row=1, column=0, sticky=W)
stage_port = ttk.Combobox(connection_frame, values=gui_utils.list_com_ports())
stage_port.grid(row=1, column=1, sticky=W, pady=2)
stage_light = Canvas(connection_frame, width=20, height=20, highlightthickness=0)
stage_light.grid(row=1, column=3, padx=5)
stage_light.create_oval(2, 2, 18, 18, fill="", tags="light")

ttk.Label(connection_frame, text="Hexapod: ").grid(row=2, column=0, sticky=W)
hexapod_port = ttk.Combobox(connection_frame, values=gui_utils.list_com_ports())
hexapod_port.grid(row=2, column=1, sticky=W, pady=2)
hexapod_light = Canvas(connection_frame, width=20, height=20, highlightthickness=0)
hexapod_light.grid(row=2, column=3, padx=5)
hexapod_light.create_oval(2, 2, 18, 18, fill="", tags="light")
ttk.Button(connection_frame, text='Connect', command=connect_stages).grid(row=1, column=2, sticky=W)
ttk.Button(connection_frame, text='Connect', command=connect_hexapod).grid(row=2, column=2, sticky=W)

#########################################################################
# Movement frame, with two frames inside, one for each
#########################################################################
movement_frame = ttk.Frame(mc_frame, padding=10, relief="solid", borderwidth=1)
movement_frame.grid(row=2, column=0)

sm_frame = ttk.Frame(movement_frame, relief="solid", borderwidth=1)
sm_frame.grid(row=1, column=0)

hm_frame = ttk.Frame(movement_frame, relief="solid", borderwidth=1)
hm_frame.grid(row=3, column=0)

# Absolute Stage Movements
ttk.Label(movement_frame, text='Stage Movement').grid(row=0, column=0, sticky=W, pady=(0, 5))

ttk.Label(sm_frame, text='Position:').grid(row=0, column=0, sticky=W, padx=(0, 5))
stage_position_label = ttk.Label(sm_frame, text="X: ---, Y: ---")
stage_position_label.grid(row=0, column=1, sticky=W, columnspan=2)

ttk.Label(sm_frame, text='X:').grid(row=1, column=0, sticky=E, padx=(0, 5))
stage_x_entry = ttk.Entry(sm_frame, width=5)
stage_x_entry.grid(row=1, column=1, sticky=W)
stage_x_entry.insert(0, "0")

ttk.Label(sm_frame, text='Y:').grid(row=2, column=0, sticky=E, padx=(0, 5))
stage_y_entry = ttk.Entry(sm_frame, width=5)
stage_y_entry.grid(row=2, column=1, sticky=W)
stage_y_entry.insert(0, "0")

ttk.Button(sm_frame, command=move_stage, text='Absolute Move').grid(
    row=3, column=0, columnspan=2, pady=(5, 0), sticky=EW
)

# Relative Stage Movements
rsm_frame = ttk.Frame(sm_frame)
rsm_frame.grid(row=1, column=2, rowspan=4, padx=(10, 0), sticky="n")

# Directional Buttons
stage_y_up = ttk.Button(rsm_frame, text='↑', width=3, command=lambda: relative_move_stage("+Y"))
stage_y_up.grid(row=0, column=1, padx=1, pady=1)
stage_y_left = ttk.Button(rsm_frame, text='←', width=3, command=lambda: relative_move_stage("-X"))
stage_y_left.grid(row=1, column=0, padx=1, pady=1)
stage_zero = ttk.Button(rsm_frame, text='●', width=3, command=initialize_stages)
stage_zero.grid(row=1, column=1, padx=1, pady=1)
stage_y_right = ttk.Button(rsm_frame, text='→', width=3, command=lambda:relative_move_stage("+X"))
stage_y_right.grid(row=1, column=2, padx=1, pady=1)
stage_y_down = ttk.Button(rsm_frame, text='↓', width=3, command= lambda: relative_move_stage("-Y"))
stage_y_down.grid(row=2, column=1, padx=1, pady=1)
# Step Size Entry
ttk.Label(rsm_frame, text="Step (mm)").grid(row=3, column=0, columnspan=3, pady=(5, 2))
stage_step_entry = ttk.Entry(rsm_frame, width=5, justify="center")
stage_step_entry.grid(row=4, column=0, columnspan=3)
stage_step_entry.insert(0, "1")  # Default increment

# Hexapod movements
ttk.Label(movement_frame, text='Hexapod Movement').grid(row=2, column=0, sticky=W, pady=(10, 5))

ttk.Label(hm_frame, text='Position').grid(row=0, column=0, sticky=W)
hexapod_position_label = ttk.Label(hm_frame, text="X: ---, Y: ---, Z: ---\nU: ---, V: ---, W: ---")
hexapod_position_label.grid(row=0, column=1, sticky=W, columnspan=2)

ttk.Label(hm_frame, text='Move to Position').grid(row=2, column=0, sticky=W)

# Absolute Position Entries
entries = [
    ('X:', 3), ('Y:', 4), ('Z:', 5),
    ('U:', 6), ('V:', 7), ('W:', 8)
]
entry_vars = {}
for label, row in entries:
    ttk.Label(hm_frame, text=label).grid(row=row, column=0, sticky=W, padx=(0, 5))
    e = ttk.Entry(hm_frame, width=5)
    e.grid(row=row, column=1, sticky=W)
    e.insert(0, "0")
    entry_vars[label.strip(':')] = e

# Move & Home Buttons
move_button = ttk.Button(hm_frame, text='Absolute Move', command=move_hexapod)
move_button.grid(row=9, column=0, columnspan=2, pady=(5, 0), sticky=EW)
ttk.Button(hm_frame, text='Home Hexapod', command=initialize_hexapod).grid(row=10, column=0, columnspan=2, sticky=EW)

# ------------------------------
# Relative Movement Control Pad
# ------------------------------
rhm_frame = ttk.Frame(hm_frame)
rhm_frame.grid(row=3, column=2, rowspan=8, padx=(15, 0), sticky="n")

# Translational Movement (X/Y/Z)
ttk.Button(rhm_frame, text='↑', width=3).grid(row=0, column=1, padx=1, pady=1)        # Y+
ttk.Button(rhm_frame, text='←', width=3).grid(row=1, column=0, padx=1, pady=1)        # X-
ttk.Button(rhm_frame, text='●', width=3).grid(row=1, column=1, padx=1, pady=1)        # Center/Stop
ttk.Button(rhm_frame, text='→', width=3).grid(row=1, column=2, padx=1, pady=1)        # X+
ttk.Button(rhm_frame, text='↓', width=3).grid(row=2, column=1, padx=1, pady=1)        # Y-
ttk.Button(rhm_frame, text='Z↑', width=3).grid(row=0, column=3, padx=(6, 1), pady=1)  # Z+
ttk.Button(rhm_frame, text='Z↓', width=3).grid(row=2, column=3, padx=(6, 1), pady=1)  # Z-

# Spacer
ttk.Label(rhm_frame, text='').grid(row=3, column=0)

# Rotational Movement (U/V/W)
ttk.Label(rhm_frame, text='Tilt').grid(row=4, column=0, columnspan=4, pady=(5, 2))

rot_width = 8
ttk.Button(rhm_frame, text='↺ Left', width=rot_width).grid(row=5, column=0, padx=1, pady=1, columnspan=2, sticky="ew")
ttk.Button(rhm_frame, text='Right ↻', width=rot_width).grid(row=5, column=2, padx=1, pady=1, columnspan=2, sticky="ew")
ttk.Button(rhm_frame, text='Back ⤴', width=rot_width).grid(row=6, column=0, padx=1, pady=1, columnspan=2, sticky="ew")
ttk.Button(rhm_frame, text='Front ⤵', width=rot_width).grid(row=6, column=2, padx=1, pady=1, columnspan=2, sticky="ew")
ttk.Button(rhm_frame, text='θ CCW', width=rot_width).grid(row=7, column=0, padx=1, pady=1, columnspan=2, sticky="ew")
ttk.Button(rhm_frame, text='θ CW', width=rot_width).grid(row=7, column=2, padx=1, pady=1, columnspan=2, sticky="ew")

# ------------------------------
# Step Size Entry (Translation Increment)
# ------------------------------
ttk.Label(rhm_frame, text="Step (mm)").grid(row=8, column=0, columnspan=4, pady=(6, 2))
hexapod_step_entry = ttk.Entry(rhm_frame, width=6, justify="center")
hexapod_step_entry.grid(row=9, column=0, columnspan=4)
hexapod_step_entry.insert(0, "1")  # Default increment

# Force equal column weight for alignment
for col in range(4):
    rhm_frame.grid_columnconfigure(col, weight=1)


#########################################################################
#########################################################################
# PLOTTING FRAME ### root/plot_frame
#########################################################################
#########################################################################
plot_frame = ttk.Frame(root, padding=10)
plot_frame.grid(column=1, row=0, sticky=E)
ttk.Label(plot_frame, text="Viewing").grid(row=0, column=0)

from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from stl import mesh
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

def plot():
    your_mesh = mesh.Mesh.from_file(r"C:\Users\max\Desktop\NanoStride\test_files\cube.stl")
    fig = Figure(figsize=(5, 5), dpi=100)
    ax = fig.add_subplot(111, projection='3d')
    ax.add_collection3d(Poly3DCollection(your_mesh.vectors, 
                                         facecolors='lightgreen',
                                         edgecolors='black',
                                         linewidths=0.2,
                                         alpha=0.9))
    scale = your_mesh.points.flatten()
    ax.auto_scale_xyz(scale, scale, scale)
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    canvas = FigureCanvasTkAgg(fig, plot_frame)
    canvas.draw()
    canvas.get_tk_widget().grid(row=1, column=0)
plot_button = ttk.Button(plot_frame, command=plot, text="plot")
plot_button.grid(row=5, column=0)

# Disconnect all and close
ttk.Button(mc_frame, text="Close and Kill", command=close_and_kill).grid(row=3, column=0, columnspan=2, pady=10)

update_stage_position()
update_hexapod_position()

root.mainloop()
