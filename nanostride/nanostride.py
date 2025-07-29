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
        desired_positions = {}
        desired_positions['X'] = x_entry.get()
        desired_positions['Y'] = y_entry.get()
        desired_positions['Z'] = z_entry.get()
        desired_positions['U'] = u_entry.get()
        desired_positions['V'] = v_entry.get()
        desired_positions['W'] = w_entry.get()
        return desired_positions
    hexapod.move_hexapod(get_desired_positions())
#########################################################################
#########################################################################

# GUI SETUP
root = Tk()
root.title("Motion Control")

#########################################################################
# Motion control frame
#########################################################################

mc_frame = ttk.Frame(root, padding=10)
mc_frame.grid(column=0, row=0,sticky=W)
ttk.Label(mc_frame, text="Motion Control").grid(row=0, column=0, columnspan=2)

#########################################################################
# Stage connection frame
#########################################################################
sc_frame = ttk.Frame(mc_frame, padding=10)
sc_frame.grid(row=1, column=0)
ttk.Label(sc_frame, text="Stage Connection").grid(row=0, column=0, sticky=W)
stage_port = ttk.Combobox(sc_frame, values=gui_utils.list_com_ports())
stage_port.grid(row=1, column=0)
stage_light = Canvas(sc_frame, width=20, height=20, highlightthickness=0)
stage_light.grid(row=1, column=1, padx=5)
stage_light.create_oval(2, 2, 18, 18, fill="", tags="light")
ttk.Button(sc_frame, text='Connect', command=connect_stages).grid(row=2, column=0, pady=2, sticky=W)
ttk.Button(sc_frame, text='Initialize', command=initialize_stages).grid(row=3, column=0, pady=2, sticky=W)

#########################################################################
# Stage movement frame ### root/mc_frame/sm_frame
#########################################################################
sm_frame = ttk.Frame(mc_frame, padding=10)
sm_frame.grid(row=2, column=0)
ttk.Label(sm_frame, text='Stage Movement').grid(row=0, column=0, sticky=W)
stage_position_label = ttk.Label(sm_frame, text="X: ---, Y: ---")
stage_position_label.grid(row=1, column=0, sticky=W, pady=(5, 0))
ttk.Label(sm_frame, text="Move Stage to Position").grid(row=2, column=0, sticky=W)
ttk.Label(sm_frame, text='X:').grid(row=3, column=0)
stage_x_entry = ttk.Entry(sm_frame, width=5)
stage_x_entry.grid(row=3, column=1)
stage_x_entry.insert(0, "0")
ttk.Label(sm_frame, text='Y:').grid(row=4, column=0)
stage_y_entry = ttk.Entry(sm_frame, width=5)
stage_y_entry.grid(row=4, column=1)
stage_y_entry.insert(0, "0")
ttk.Button(sm_frame, command=move_stage, text='Move Stage').grid(row=5, column=1, columnspan=2)
#########################################################################
# Hexapod connection frame ### root/mc_frame/hp_frame
#########################################################################
hp_frame = ttk.Frame(mc_frame, padding=10)
hp_frame.grid(row=1, column=1)
ttk.Label(hp_frame, text="Hexapod Connection").grid(row=0, column=0, sticky=W)
hexapod_port = ttk.Combobox(hp_frame, values=gui_utils.list_com_ports())
hexapod_port.grid(row=1, column=0)
hexapod_light = Canvas(hp_frame, width=20, height=20, highlightthickness=0)
hexapod_light.grid(row=1, column=1, padx=5)
hexapod_light.create_oval(2, 2, 18, 18, fill="", tags="light")
ttk.Button(hp_frame, text='Connect', command=connect_hexapod).grid(row=2, column=0, pady=2, sticky=W)
ttk.Button(hp_frame, text='Initialize', command=initialize_hexapod).grid(row=3, column=0, pady=2, sticky=W)

#########################################################################
# Hexapod movement frame ### root/mc_frame/hm_frame
#########################################################################
hm_frame = ttk.Frame(mc_frame, padding=10)
hm_frame.grid(row=2, column=1)
ttk.Label(hm_frame, text='Hexapod Movement').grid(row=0, column=0, sticky=W)
hexapod_position_label = ttk.Label(hm_frame, text="X: ---, Y: ---, Z: ---\nU: ---, V: ---, W: ---")
hexapod_position_label.grid(row=1, column=0, sticky=W, pady=(5,0))
ttk.Label(hm_frame, text='Move to Position').grid(row=2, column=0, sticky=W)
# X Entry
x_entry_label = ttk.Label(hm_frame, text='X:')
x_entry_label.grid(row=3, column=0, sticky='w')
x_entry = ttk.Entry(hm_frame, width=5)
x_entry.grid(row=3, column=1, sticky='w')
x_entry.insert(0, "0")

# Y Entry
y_entry_label = ttk.Label(hm_frame, text='Y:')
y_entry_label.grid(row=4, column=0, sticky='w')
y_entry = ttk.Entry(hm_frame, width=5)
y_entry.grid(row=4, column=1, sticky='w')
y_entry.insert(0, "0")

# Z Entry
z_entry_label = ttk.Label(hm_frame, text='Z:')
z_entry_label.grid(row=5, column=0, sticky='w')
z_entry = ttk.Entry(hm_frame, width=5)
z_entry.grid(row=5, column=1, sticky='w')
z_entry.insert(0, "0")

# U Entry
u_entry_label = ttk.Label(hm_frame, text='U:')
u_entry_label.grid(row=6, column=0, sticky='w')
u_entry = ttk.Entry(hm_frame, width=5) # 'show='0.0'' is likely not what you want. It's for password-like entries.
u_entry.grid(row=6, column=1, sticky='w')
u_entry.insert(0, "0")

# V Entry
v_entry_label = ttk.Label(hm_frame, text='V:')
v_entry_label.grid(row=7, column=0, sticky='w')
v_entry = ttk.Entry(hm_frame, width=5)
v_entry.grid(row=7, column=1, sticky='w')
v_entry.insert(0, "0")

# W Entry
w_entry_label = ttk.Label(hm_frame, text='W:')
w_entry_label.grid(row=8, column=0, sticky='w')
w_entry = ttk.Entry(hm_frame, width=5)
w_entry.grid(row=8, column=1, sticky='w')
w_entry.insert(0, "0")

# Move Button
move_button = ttk.Button(hm_frame, text='Move', command=move_hexapod)
move_button.grid(row=9, columnspan=2)

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
                                         facecolors='lightblue',
                                         edgecolors='gray',
                                         linewidths=0.2,
                                         alpha=0.9))
    scale = your_mesh.points.flatten()
    ax.auto_scale_xyz(scale, scale, scale)
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    canvas = FigureCanvasTkAgg(fig, plot_frame)
    canvas.draw()
    canvas.get_tk_widget().grid(row=0, column=0)
plot_button = ttk.Button(plot_frame, command=plot, text="plot")
plot_button.grid(row=5, column=0)

# Disconnect all and close
ttk.Button(mc_frame, text="Close and Kill", command=close_and_kill).grid(row=3, column=0, columnspan=2, pady=10)

update_stage_position()
update_hexapod_position()

root.mainloop()
