import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser

import numpy as np
import sounddevice as sd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


def calculate_555():
    try:
        ra = float(entry_ra.get())
        rb = float(entry_rb.get())
        c = float(entry_c.get())
        freq = 1.44 / ((ra + 2 * rb) * c)
        duty = (ra + rb) / (ra + 2 * rb) * 100
        result_555.config(text=f"Freq: {freq:.2f} Hz\nDuty: {duty:.1f}%")
    except ValueError:
        messagebox.showerror("Error", "Invalid input")


def calculate_40106():
    try:
        r = float(entry_r_40106.get())
        c = float(entry_c_40106.get())
        freq = 1 / (1.4 * r * c)
        result_40106.config(text=f"Freq: {freq:.2f} Hz")
    except ValueError:
        messagebox.showerror("Error", "Invalid input")


def calculate_led_res():
    try:
        v_supply = float(entry_led_supply.get())
        v_f = float(entry_led_forward.get())
        i_f = float(entry_led_current.get())
        r = (v_supply - v_f) / (i_f / 1000)
        result_led.config(text=f"R = {r:.0f} Ω")
    except ValueError:
        messagebox.showerror("Error", "Invalid input")


def calculate_opamp_gain():
    try:
        rf = float(entry_rf.get())
        ri = float(entry_ri.get())
        gain = 1 + rf / ri
        result_opamp.config(text=f"Gain = {gain:.2f}")
    except ValueError:
        messagebox.showerror("Error", "Invalid input")


def calculate_bias():
    try:
        vcc = float(entry_vcc.get())
        rc = float(entry_rc.get())
        re = float(entry_re.get())
        beta = float(entry_beta.get())
        vbe = 0.7
        ie = vcc / (rc + re)
        ib = ie / beta
        rb = (vcc - vbe - ie * re) / ib
        result_bias.config(text=f"RB ≈ {rb:.0f} Ω\nIC ≈ {ie:.3f} A")
    except ValueError:
        messagebox.showerror("Error", "Invalid input")


def open_datasheet():
    part = entry_part.get()
    if part:
        url = f"https://www.google.com/search?q={part}+datasheet"
        webbrowser.open(url)
    else:
        messagebox.showinfo("Info", "Enter part number")


def start_oscope():
    duration = 0.1
    try:
        data = sd.rec(int(duration * 44100), samplerate=44100, channels=1)
        sd.wait()
        data = data.flatten()
        line.set_ydata(data)
        canvas.draw()
    except Exception as e:
        messagebox.showerror("Error", str(e))


# GUI setup
root = tk.Tk()
root.title("Audio Electronics Assistant")

notebook = ttk.Notebook(root)
notebook.pack(fill="both", expand=True)

# 555 timer
frame_555 = ttk.Frame(notebook)
notebook.add(frame_555, text="555")

entry_ra = ttk.Entry(frame_555, width=10)
entry_rb = ttk.Entry(frame_555, width=10)
entry_c = ttk.Entry(frame_555, width=10)

for i, text in enumerate(["RA (Ω)", "RB (Ω)", "C (F)"]):
    ttk.Label(frame_555, text=text).grid(row=i, column=0, sticky="e")
entry_ra.grid(row=0, column=1)
entry_rb.grid(row=1, column=1)
entry_c.grid(row=2, column=1)

ttktimer = ttk.Button(frame_555, text="Calculate", command=calculate_555)
ttktimer.grid(row=3, columnspan=2, pady=5)
result_555 = ttk.Label(frame_555, text="")
result_555.grid(row=4, columnspan=2)

# 40106
frame_40106 = ttk.Frame(notebook)
notebook.add(frame_40106, text="40106")

entry_r_40106 = ttk.Entry(frame_40106, width=10)
entry_c_40106 = ttk.Entry(frame_40106, width=10)
for i, text in enumerate(["R (Ω)", "C (F)"]):
    ttk.Label(frame_40106, text=text).grid(row=i, column=0, sticky="e")
entry_r_40106.grid(row=0, column=1)
entry_c_40106.grid(row=1, column=1)

ttk.Button(frame_40106, text="Calculate", command=calculate_40106).grid(row=2, columnspan=2, pady=5)
result_40106 = ttk.Label(frame_40106, text="")
result_40106.grid(row=3, columnspan=2)

# LED resistor
frame_led = ttk.Frame(notebook)
notebook.add(frame_led, text="LED")

labels = ["Supply V", "Forward V", "Current mA"]
entries = []
for i, text in enumerate(labels):
    ttk.Label(frame_led, text=text).grid(row=i, column=0, sticky="e")
    e = ttk.Entry(frame_led, width=10)
    e.grid(row=i, column=1)
    entries.append(e)
entry_led_supply, entry_led_forward, entry_led_current = entries

ttk.Button(frame_led, text="Calculate", command=calculate_led_res).grid(row=3, columnspan=2, pady=5)
result_led = ttk.Label(frame_led, text="")
result_led.grid(row=4, columnspan=2)

# Op-amp
frame_opamp = ttk.Frame(notebook)
notebook.add(frame_opamp, text="OpAmp")

labels = ["Rin (Ω)", "Rf (Ω)"]
entries = []
for i, text in enumerate(labels):
    ttk.Label(frame_opamp, text=text).grid(row=i, column=0, sticky="e")
    e = ttk.Entry(frame_opamp, width=10)
    e.grid(row=i, column=1)
    entries.append(e)
entry_ri, entry_rf = entries

ttk.Button(frame_opamp, text="Calculate", command=calculate_opamp_gain).grid(row=2, columnspan=2, pady=5)
result_opamp = ttk.Label(frame_opamp, text="")
result_opamp.grid(row=3, columnspan=2)

# Transistor bias
frame_bias = ttk.Frame(notebook)
notebook.add(frame_bias, text="Bias")

labels = ["Vcc", "Rc", "Re", "Beta"]
entries = []
for i, text in enumerate(labels):
    ttk.Label(frame_bias, text=text).grid(row=i, column=0, sticky="e")
    e = ttk.Entry(frame_bias, width=10)
    e.grid(row=i, column=1)
    entries.append(e)
entry_vcc, entry_rc, entry_re, entry_beta = entries

ttk.Button(frame_bias, text="Calculate", command=calculate_bias).grid(row=4, columnspan=2, pady=5)
result_bias = ttk.Label(frame_bias, text="")
result_bias.grid(row=5, columnspan=2)

# Datasheet
frame_data = ttk.Frame(notebook)
notebook.add(frame_data, text="Datasheet")

entry_part = ttk.Entry(frame_data, width=15)
entry_part.grid(row=0, column=1)
ttk.Label(frame_data, text="Part Number").grid(row=0, column=0, sticky="e")

ttk.Button(frame_data, text="Search", command=open_datasheet).grid(row=1, columnspan=2, pady=5)

# Oscilloscope
frame_scope = ttk.Frame(notebook)
notebook.add(frame_scope, text="Scope")

fig, ax = plt.subplots(figsize=(4, 2))
line, = ax.plot(np.zeros(4410))
ax.set_ylim(-1, 1)
canvas = FigureCanvasTkAgg(fig, master=frame_scope)
canvas_widget = canvas.get_tk_widget()
canvas_widget.pack()

ttk.Button(frame_scope, text="Capture", command=start_oscope).pack(pady=5)

root.mainloop()
