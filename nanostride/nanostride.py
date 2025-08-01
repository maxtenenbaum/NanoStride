from tkinter import *
from tkinter import messagebox, filedialog
from tkinter import ttk
import gui_utils
import motion_utils
import laser_utils
import slicer_utils
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from stl import mesh
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.image as mpimg
import glob
import os

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
def relative_move_hexapod(axis):
    hexapod_positions = hexapod.get_hexapod_pos()
    step = float(hexapod_step_entry.get())
    if axis == "+X":
        hexapod_positions['X'] += step
    elif axis == "-X":
        hexapod_positions['X'] -= step
    elif axis == "+Y":
        hexapod_positions['Y'] += step
    elif axis == "-Y":
        hexapod_positions['Y'] -= step
    elif axis == "+Z":
        hexapod_positions['Z'] += step
    elif axis == "-Z":
        hexapod_positions['Z'] -= step
    elif axis == "+U":
        hexapod_positions['U'] += step
    elif axis == "-U":
        hexapod_positions['U'] -= step
    elif axis == "+V":
        hexapod_positions['V'] += step
    elif axis == "-V":
        hexapod_positions['V'] -= step
    elif axis == "+W":
        hexapod_positions['W'] += step
    elif axis == "-W":
        hexapod_positions['W'] -= step
    hexapod.move_hexapod(hexapod_positions)

# Laser
shutter_state = "OFF"
def update_shutter_indicator(state):
    def draw_star(x, y, size, color, tag):
        points = [
            x, y - size,
            x + size * 0.4, y - size * 0.4,
            x + size, y,
            x + size * 0.4, y + size * 0.4,
            x, y + size,
            x - size * 0.4, y + size * 0.4,
            x - size, y,
            x - size * 0.4, y - size * 0.4,
        ]
        shutter_light.create_polygon(points, fill=color, outline=color, tags=tag)
        radius = size * 0.3
        shutter_light.create_oval(
            x - radius, y - radius,
            x + radius, y + radius,
            fill="yellow" if color == "red" else "black",
            outline="yellow" if color == "red" else "black",
            width=1, tags=tag
        )

    shutter_light.delete("beam")  
    # Emitter box
    shutter_light.create_rectangle(2, 6, 10, 14, fill="gray20", tags="emitter")
    
    # Laser beam
    color = "red" if state == "ON" else "black"
    shutter_light.create_line(10, 10, 28, 10, fill=color, width=5, tags="beam")
    
    # Star at end of beam
    if state == "ON":
        draw_star(32, 10, 6, "red", "beam")
def toggle_shutter():
    global shutter_state
    shutter_state = "ON" if shutter_state == "OFF" else "OFF"
    update_shutter_indicator(shutter_state)
    laser_utils.toggle_shutter(shutter_state)

# Resonant mirror
rsm_state = "OFF"
scan_y, scan_direction = 2, 1
def update_rsm_indicator():
    global scan_y, scan_direction
    rsm_light.delete("all")
    color = "red" if rsm_state == "ON" else "black"
    rsm_light.create_line(0, 10, 15, 10, fill=color, width=3)
    rsm_light.create_rectangle(15, 7, 21, 13, fill="silver")
    end_y = scan_y if rsm_state == "ON" else 2
    rsm_light.create_line(18, 10, 40, end_y, fill=color, width=3)
    if rsm_state == "ON":
        scan_y += scan_direction * 2
        if scan_y >= 18 or scan_y <= 2:
            scan_direction *= -1
        rsm_light.after(50, update_rsm_indicator)
def toggle_rsm():
    global rsm_state
    rsm_state = "OFF" if rsm_state == "ON" else "ON"
    update_rsm_indicator()
    laser_utils.toggle_resonance_scanner(rsm_state)

# Galvo mirror
galvo_state = "OFF"
scan_x, scan_x_direction = 2, 1
def update_galvo_indicator():
    global scan_x, scan_x_direction
    galvo_light.delete("all")
    color = "red" if galvo_state == "ON" else "black"
    galvo_light.create_line(0, 10, 15, 10, fill=color, width=3)
    galvo_light.create_rectangle(15, 7, 21, 13, fill="silver")
    end_x = scan_x if galvo_state == "ON" else 2
    galvo_light.create_line(18, 10, 40, end_x, fill=color, width=3)
    if galvo_state == "ON":
        scan_x += scan_x_direction * 2
        if scan_x >= 18 or scan_x <= 2:
            scan_x_direction *= -1
        galvo_light.after(50, update_galvo_indicator)
def toggle_galvo():
    global galvo_state
    galvo_state = "OFF" if galvo_state == "ON" else "ON"
    update_galvo_indicator()

# File processing
file_path = None
def open_stl():
    global file_path
    file_path = filedialog.askopenfilename(title="Select a file", filetypes=[("STL files", "*.stl")])
    if file_path is not None:
        plot()

def plot():
    global ax
    if file_path is None:
        return

    try:
        # clear out the old contents
        ax.cla()

        # load and draw your mesh
        your_mesh = mesh.Mesh.from_file(file_path)
        ax.add_collection3d(Poly3DCollection(
            your_mesh.vectors,
            facecolors='lightgreen',
            edgecolors='black',
            linewidths=0.2,
            alpha=0.9
        ))

        # rescale & label
        scale = your_mesh.points.flatten()
        ax.auto_scale_xyz(scale, scale, scale)
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')

        # redraw the canvas
        canvas.draw()
    except Exception as e:
        print("Plot error:", e)


# SLICING

def slice():
    import slicer_finder
    try:
        slicer_path = slicer_finder.find_prusaslicer()
    except FileNotFoundError as e:
        print(e)

    slicer_utils.slice_and_extract(
        slicer_path=slicer_path,
        stl_path=file_path,
        config_path=r'C:\Users\max\Desktop\NanoStride\scripts\config.ini',
        output_dir='slices_script',
        extracted_image_dir='temp_slices'
    )

    show_slices()

image_files = None
def show_slices():
    global image_files
    extracted_image_dir = r"C:\Users\max\Desktop\NanoStride\temp_slices"
    image_files = sorted(glob.glob(os.path.join(extracted_image_dir, "*.png")))
    if not image_files:
        raise RuntimeError(f"No images found")
        # re-configure the slider to match new number of files
    max_idx = len(image_files) - 1
    slider.config(from_=max_idx, to=0)  # top of slider = last slice
    slider.set(0)                       # start at slice 0
    show_image(0)

def show_image(idx):
    if image_files:
        img = mpimg.imread(image_files[idx])
        axis.clear()
        axis.imshow(img)
        axis.axis("on")           
        slice_canvas.draw()

# --- slider callback ---
def on_slider_change(val):
    idx = int(float(val))
    show_image(idx)


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
ttk.Label(mc_frame, text="Device Selection", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky=W)
#########################################################################
# Connection frame
#########################################################################
connection_frame = ttk.Frame(mc_frame, padding=10, relief='groove')
connection_frame.grid(row=1, column=0, sticky=W)
ttk.Label(connection_frame, text='Stages: ').grid(row=1, column=0, sticky=W)
stage_port = ttk.Combobox(connection_frame, values=gui_utils.list_com_ports(), width=3)
stage_port.grid(row=1, column=1, sticky=W, pady=2)
stage_light = Canvas(connection_frame, width=20, height=20, highlightthickness=0)
stage_light.grid(row=1, column=3, padx=5)
stage_light.create_oval(2, 2, 18, 18, fill="", tags="light")

ttk.Label(connection_frame, text="Hexapod: ").grid(row=2, column=0, sticky=W)
hexapod_port = ttk.Combobox(connection_frame, values=gui_utils.list_com_ports(), width=3)
hexapod_port.grid(row=2, column=1, sticky=W, pady=2)
hexapod_light = Canvas(connection_frame, width=20, height=20, highlightthickness=0)
hexapod_light.grid(row=2, column=3, padx=5)
hexapod_light.create_oval(2, 2, 18, 18, fill="", tags="light")
ttk.Button(connection_frame, text='Connect', command=connect_stages).grid(row=1, column=2, sticky=W)
ttk.Button(connection_frame, text='Connect', command=connect_hexapod).grid(row=2, column=2, sticky=W)

#########################################################################
# Movement frame, with two frames inside, one for each
#########################################################################
movement_frame = ttk.Frame(mc_frame, padding=10)
movement_frame.grid(row=2, column=0, sticky=W)

sm_frame = ttk.Frame(movement_frame, relief='groove', padding=10)
sm_frame.grid(row=1, column=0, sticky=W)

hm_frame = ttk.Frame(movement_frame, relief='groove', padding=10)
hm_frame.grid(row=3, column=0, sticky=W)

# Absolute Stage Movements
ttk.Label(movement_frame, text='Stage Movement', font=("Arial", 10, "bold")).grid(row=0, column=0, sticky=W, pady=(0, 5))

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
ttk.Button(sm_frame, command=initialize_stages, text='Initialize').grid(
    row=4, column=0, columnspan=2, pady=(5, 0), sticky=EW
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
ttk.Label(movement_frame, text='Hexapod Movement', font=("Arial", 10, "bold")).grid(row=2, column=0, sticky=W, pady=(10, 5))

ttk.Label(hm_frame, text='Position').grid(row=0, column=0, sticky=W)
hexapod_position_label = ttk.Label(hm_frame, text="X: ---, Y: ---, Z: ---\nU: ---, V: ---, W: ---")
hexapod_position_label.grid(row=0, column=1, sticky=W, columnspan=2)

ttk.Label(hm_frame, text='Move to Position').grid(row=2, column=0, columnspan=3, sticky=W)

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
ttk.Button(rhm_frame, text='↑', width=3, command=lambda: relative_move_hexapod("-X")).grid(row=0, column=1, padx=1, pady=1)        # Y+
ttk.Button(rhm_frame, text='←', width=3, command=lambda: relative_move_hexapod("-Y")).grid(row=1, column=0, padx=1, pady=1)        # X-
ttk.Button(rhm_frame, text='●', width=3, command=lambda: hexapod.move_hexapod(hexapod.get_hexapod_pos())).grid(row=1, column=1, padx=1, pady=1)  # Center/Stop (no movement)
ttk.Button(rhm_frame, text='→', width=3, command=lambda: relative_move_hexapod("+Y")).grid(row=1, column=2, padx=1, pady=1)        # X+
ttk.Button(rhm_frame, text='↓', width=3, command=lambda: relative_move_hexapod("+X")).grid(row=2, column=1, padx=1, pady=1)        # Y-
ttk.Button(rhm_frame, text='Z↑', width=3, command=lambda: relative_move_hexapod("+Z")).grid(row=0, column=3, padx=(6, 1), pady=1)  # Z+
ttk.Button(rhm_frame, text='Z↓', width=3, command=lambda: relative_move_hexapod("-Z")).grid(row=2, column=3, padx=(6, 1), pady=1)  # Z-

# Spacer
ttk.Label(rhm_frame, text='').grid(row=3, column=0)

# Rotational Movement (U/V/W)
ttk.Label(rhm_frame, text='Tilt').grid(row=4, column=0, columnspan=4, pady=(5, 2))

rot_width = 8
ttk.Button(rhm_frame, text='↺ Left', width=rot_width, command=lambda: relative_move_hexapod("+U")).grid(row=5, column=0, padx=1, pady=1, columnspan=2, sticky="ew")
ttk.Button(rhm_frame, text='Right ↻', width=rot_width, command=lambda: relative_move_hexapod("-U")).grid(row=5, column=2, padx=1, pady=1, columnspan=2, sticky="ew")
ttk.Button(rhm_frame, text='Back ⤴', width=rot_width, command=lambda: relative_move_hexapod("-V")).grid(row=6, column=0, padx=1, pady=1, columnspan=2, sticky="ew")
ttk.Button(rhm_frame, text='Front ⤵', width=rot_width, command=lambda: relative_move_hexapod("+V")).grid(row=6, column=2, padx=1, pady=1, columnspan=2, sticky="ew")
ttk.Button(rhm_frame, text='θ CCW', width=rot_width, command=lambda: relative_move_hexapod("+W")).grid(row=7, column=0, padx=1, pady=1, columnspan=2, sticky="ew")
ttk.Button(rhm_frame, text='θ CW', width=rot_width, command=lambda: relative_move_hexapod("-W")).grid(row=7, column=2, padx=1, pady=1, columnspan=2, sticky="ew")

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
# Laser control
#########################################################################
laser_frame = ttk.Frame(root, padding=10)
laser_frame.grid(column=1, row=0, sticky=NW)
ttk.Label(laser_frame, text='Laser Control', font=("Arial", 10, "bold")).grid(row=0, column=0, sticky=W)

# Optics frame
optics_frame = ttk.Frame(laser_frame, relief='groove', padding=10)
optics_frame.grid(row=1, column=0, sticky=W)
# Shutter control
shutter_light = Canvas(optics_frame, width=50, height=20, highlightthickness=0)
shutter_light.grid(row=1, column=1, padx=5)
ttk.Button(optics_frame, text='Shutter', command=toggle_shutter, width=15).grid(row=1, column=0)
update_shutter_indicator(shutter_state)

# Mirror control
rsm_light = Canvas(optics_frame, width=50, height=20, highlightthickness=0)
rsm_light.grid(row=2, column=1, padx=5)
ttk.Button(optics_frame, text="Resonant Mirror", command=toggle_rsm, width=15).grid(row=2, column=0)
update_rsm_indicator()

# Slow scan control
galvo_light = Canvas(optics_frame, width=50, height=20, highlightthickness=0)
galvo_light.grid(row=3, column=1)
ttk.Button(optics_frame, text="Y Galvo", command=toggle_galvo, width=15).grid(row=3, column=0)
update_galvo_indicator()

# Placeholder for power settings and calibration
power_frame = ttk.Frame(laser_frame, padding=10, relief="groove")
power_frame.grid(row=3, column=0, columnspan=2, pady=5, sticky="ew")
ttk.Label(power_frame, text="Laser Power Settings", font=("Arial", 10, "bold")).grid(row=0, column=0, columnspan=2, pady=(0, 5))
ttk.Label(power_frame, text="Power (%)").grid(row=1, column=0, sticky="w")
ttk.Scale(power_frame, from_=0, to=100, orient="horizontal", length=120).grid(row=1, column=1, padx=5, pady=2)
ttk.Label(power_frame, text="Wavelength (nm)").grid(row=2, column=0, sticky="w")
ttk.Combobox(power_frame, values=["800", "850", "900", "950", "1000"], width=8).grid(row=2, column=1, padx=5, pady=2)
ttk.Button(power_frame, text="Calibrate").grid(row=3, column=0, columnspan=2, pady=(5, 0), sticky="ew")
Canvas(power_frame, width=20, height=20, highlightthickness=0, background="gray80").grid(row=4, column=0, padx=(0,5), pady=(5,0))
ttk.Label(power_frame, text="Ready").grid(row=4, column=1, sticky="w", pady=(5,0))

#########################################################################
# File processing
#########################################################################

file_processing_frame = ttk.Frame(root, padding=10)
file_processing_frame.grid(column=2, row=0, sticky=NW)

# Visualization
fig = Figure(figsize=(5, 5), dpi=100)
ax = fig.add_subplot(111, projection='3d')
canvas = FigureCanvasTkAgg(fig, master=file_processing_frame)
canvas.get_tk_widget().grid(row=0, column=0)


# Individual slice vizualising
slice_fig = Figure(figsize=(5,5), dpi=100, facecolor="#f0f0f0")
axis = slice_fig.add_subplot(111)
slice_canvas = FigureCanvasTkAgg(slice_fig, master=file_processing_frame)
slice_canvas.get_tk_widget().grid(row=0, column=1)

# --- create the slider ---
slider = ttk.Scale(
    file_processing_frame,
    from_=1,    # dummy
    to=0,       # dummy
    orient="vertical",
    command=lambda v: show_image(int(float(v))),
    length=400
)
slider.grid(row=0, column=2, padx=10)

# Slicing frame
ttk.Label(file_processing_frame, text='Voxelizing', font=("Arial", 10, "bold")).grid(row=1, column=0)
slicing_frame = ttk.Frame(file_processing_frame, relief='groove', borderwidth=1, padding=10)
slicing_frame.grid(row=2, column=0)
ttk.Label(slicing_frame, text="Upload File", font=("Arial", 10, "bold")).grid(row=0, column=0)
ttk.Button(slicing_frame, text="Open STL", command=open_stl).grid(row=1, column=0)

# Slicing
ttk.Label(slicing_frame, text="Number of layers").grid(row=0, column=1)
num_layers = ttk.Entry(slicing_frame).grid(row=1, column=1)

ttk.Label(slicing_frame, text="Layer height (um)").grid(row=0, column=2)
layer_thickness = ttk.Entry(slicing_frame).grid(row=1, column=2)

ttk.Button(slicing_frame, text="Slice", command=slice).grid(row=0, column=3)

# Disconnect all and close
ttk.Button(mc_frame, text="Close and Kill", command=close_and_kill).grid(row=3, column=0, columnspan=2, pady=10)

update_stage_position()
update_hexapod_position()

root.mainloop()
