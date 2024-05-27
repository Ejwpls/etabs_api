import tkinter as tk
from tkinter import ttk
import Lateral_Plots as lp
import time
import threading


def on_selection(event):
    """ Function to call when an item is selected """
    # This function can be used if you want to perform an action immediately upon selection
    pass

def start_progress():
    """ Function to start and update the progress bar """
    progress_bar['value'] = 0
    root.update_idletasks()
    for i in range(1, 11):
        time.sleep(0.5)  # Simulating a task
        progress_bar['value'] = i * 10
        root.update_idletasks()

def on_button_click():

    design_wind = combo_box_windult.get()
    drift_wind = combo_box_winddrift.get()
    design_EQ = combo_box_eqult.get()
    drift_EQ = combo_box_eqdrift.get()

    #Define the load combinations and cases
    loadcombos_to_run = [design_wind,drift_wind]
    loadcase_to_run = ['WTs','WT',design_EQ,drift_EQ]

    # Get data from ETABS
    df_story_Drift, df_story_Shear, df_story_AvgDisp, df_story_COMDisp, df_story_Def, e_name, model_path = lp.get_etabs_dataframes(loadcombos_to_run, loadcase_to_run)

    # Plot data wind
    lp.plot_etabs_data(df_story_Drift, df_story_Shear, df_story_AvgDisp, df_story_COMDisp, df_story_Def, e_name, model_path, design_wind, drift_wind,'Wind')
    # Plot data EQ
    lp.plot_etabs_data(df_story_Drift, df_story_Shear, df_story_AvgDisp, df_story_COMDisp, df_story_Def, e_name, model_path, design_EQ, drift_EQ,'EQ')

    threading.Thread(target=start_progress).start()

# Get List Loads from ETABS 
loadcases = []
loadcombos = []

# Define the values for the combobox
loadcases,loadcombos = lp.GetLoadNames(loadcases,loadcombos)

# Create the main window
root = tk.Tk()
root.geometry("500x340")
root.title("Lateral Plot Exporters")

# Create label
label = tk.Label(root, text="Select Loads", font=("Helvetica", 12))
label.pack(pady=5)

# Create label
label_eqult = tk.Label(root, text="Select your EQ-ULT Case", font=("Helvetica", 8))
label_eqdrift = tk.Label(root, text="Select your EQ-Drift Case", font=("Helvetica", 8))
label_windult = tk.Label(root, text="Select your Wind Only-ULT Combo", font=("Helvetica", 8))
label_winddrift = tk.Label(root, text="Select your Wind Only-SERV Combo", font=("Helvetica", 8))

# Create a ttk combobox
combo_box_eqult = ttk.Combobox(root, width=50)
combo_box_eqdrift = ttk.Combobox(root, width=50)
combo_box_windult = ttk.Combobox(root, width=50)
combo_box_winddrift = ttk.Combobox(root, width=50)

combo_box_eqult['values'] = loadcases
combo_box_eqdrift['values'] = loadcases

combo_box_windult['values'] = loadcombos
combo_box_winddrift['values'] = loadcombos

# Set the function to call when an item is selected
#combo_box_case.bind("<<ComboboxSelected>>", on_selection)
#combo_box_combo.bind("<<ComboboxSelected>>", on_selection)

# Create a progress bar
progress_bar = ttk.Progressbar(root, orient='horizontal', length=300, mode='determinate')

# Create a button
button = tk.Button(root, text="Run Selected", command=on_button_click)

# Set the default value
#combo_box_case.current(0)
combo_box_eqult.set("SPEC XY-DUCT1")
combo_box_eqdrift.set("SPEC XY-DRIFT")
combo_box_windult.set('ENV WIND ONLY ULT 500Y')
combo_box_winddrift.set('ENV WIND ONLY SERV 25Y')

# Add the combobox to the main window
label_eqult.pack(pady=0)
combo_box_eqult.pack(pady=0)
label_eqdrift.pack(pady=0)
combo_box_eqdrift.pack(pady=0)

label_windult.pack(pady=0)
combo_box_windult.pack(pady=0)
label_winddrift.pack(pady=0)
combo_box_winddrift.pack(pady=0)

button.pack(pady=10)

progress_bar.pack(pady=20)

# Start the GUI event loop
root.mainloop()