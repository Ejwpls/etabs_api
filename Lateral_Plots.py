import etabs_obj 
import find_etabs
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from tqdm import tqdm
import webbrowser
import os
import logging

logging.basicConfig(filename='error_log.log', filemode='w', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def get_etabs_dataframes(loadcombos_to_run, loadcase_to_run):
    try:
        # Load up ETABS Model
        etabs = find_etabs.find_etabs()
        e = etabs_obj.EtabsModel(etabs)
        e_name = e.get_file_name_without_suffix()
        model_path = e.get_filepath()

        # Initialize tqdm loading bar
        tasks = tqdm(total=8, desc="Fetching Data", leave=False)

        # Set up load combinations
        e.set_current_unit('kN', 'm')
        e.load_combinations.select_load_combinations(loadcombos_to_run, True)
        e.SapModel.DatabaseTables.SetLoadCasesSelectedForDisplay(loadcase_to_run)
        #e.load_cases.select_load_cases(loadcase_to_run)
        tasks.update(1)  # Update loading bar

        # Get Tables from ETABS
        df_story_Drift = e.database.read(table_key='Story Drifts', to_dataframe=True)
        tasks.update(1)  # Update loading bar
        df_story_Shear = e.database.read(table_key='Story Forces', to_dataframe=True)
        tasks.update(1)  # Update loading bar
        df_story_AvgDisp = e.database.read(table_key='Story Max Over Avg Displacements', to_dataframe=True)
        tasks.update(1)  # Update loading bar
        df_story_COMDisp = e.database.read(table_key='Diaphragm Center Of Mass Displacements', to_dataframe=True)
        tasks.update(1)  # Update loading bar
        df_story_Def = e.database.read(table_key='Story Definitions', to_dataframe=True)
        tasks.update(1)  # Update loading bar

        # Process the Story Definitions DataFrame
        df_story_Def = df_story_Def[['Story', 'Height']]
        df_story_Def['Elevation'] = df_story_Def['Height'].astype(float)
        df_story_Def['Height'] = df_story_Def['Height'].astype(float)

        if 'Base' not in df_story_Def['Story'].values:
            df_story_Def.loc[len(df_story_Def)] = ['Base', 0, 0]

        total_height = df_story_Def['Height'].sum()
        df_story_Def.at[0, 'Elevation'] = total_height
        tasks.update(1)  # Update loading bar

        for i in range(1, len(df_story_Def)):
            df_story_Def.at[i, 'Elevation'] = round((df_story_Def.at[i-1, 'Elevation'] - df_story_Def.at[i-1, 'Height']), 2)
        tasks.update(1)  # Update loading bar


        # Join story drift dataframes with story definition dataframe on story name
        df_story_Drift = df_story_Drift.merge(df_story_Def, on='Story', how='left')
        df_story_Shear = df_story_Shear.merge(df_story_Def, on='Story', how='left')
        df_story_COMDisp = df_story_COMDisp.merge(df_story_Def, on='Story', how='left')
        df_story_AvgDisp = df_story_AvgDisp.merge(df_story_Def, on='Story', how='left')
        tasks.close()

        return df_story_Drift, df_story_Shear, df_story_AvgDisp, df_story_COMDisp, df_story_Def, e_name, model_path
    except Exception as e:
        logging.error("Error in get_etabs_dataframes: ", exc_info=True)

def plot_etabs_data(df_story_Drift, df_story_Shear, df_story_AvgDisp, df_story_COMDisp, df_story_Def, e_name, model_path, design, drift,lat):
    
    # Shear & Overturning Dataframe
    df_story_Shear['VX'] = df_story_Shear['VX'].astype(float)
    df_story_Shear['VY'] = df_story_Shear['VY'].astype(float)
    df_story_Shear['MX'] = df_story_Shear['MX'].astype(float)
    df_story_Shear['MY'] = df_story_Shear['MY'].astype(float)

    df_story_Shear1 = df_story_Shear[df_story_Shear['OutputCase'] == design].reset_index(drop=True)

    def update_elevation(df_in):
        for i in range(len(df_in)):
            if i == len(df_in) - 1:
                df_in.loc[i, 'Elevation'] = 0
            elif df_in.loc[i, 'Location'] == 'Bottom':
                df_in.loc[i, 'Elevation'] = df_in.loc[i + 1, 'Elevation']
        return df_in

    df_story_Shear_Max = update_elevation(df_story_Shear1[df_story_Shear1['StepType'] == 'Max'].reset_index(drop=True))
    df_story_Shear_Min = update_elevation(df_story_Shear1[df_story_Shear1['StepType'] == 'Min'].reset_index(drop=True))

    df_story_Ovt_Max = df_story_Shear_Max[df_story_Shear_Max['Location'] == 'Top']
    df_story_Ovt_Min = df_story_Shear_Min[df_story_Shear_Min['Location'] == 'Top']
    
    
    #Drift dataframes
    df_story_Drift = df_story_Drift[(df_story_Drift['OutputCase'] == drift)].reset_index(drop=True)

    df_story_Drift['Drift'] = df_story_Drift['Drift'].astype(float)
    df_story_Drift['Z'] = df_story_Drift['Z'].astype(float)

    df_story_Drift_x_Max = df_story_Drift[(df_story_Drift['Direction'] == 'X') & (df_story_Drift['StepType'] == 'Max')].reset_index(drop=True)
    df_story_Drift_y_Max = df_story_Drift[(df_story_Drift['Direction'] == 'Y') & (df_story_Drift['StepType'] == 'Max') ].reset_index(drop=True)

    df_story_Drift_x_Min = df_story_Drift[(df_story_Drift['Direction'] == 'X') & (df_story_Drift['StepType'] == 'Min')].reset_index(drop=True)
    df_story_Drift_y_Min = df_story_Drift[(df_story_Drift['Direction'] == 'Y') & (df_story_Drift['StepType'] == 'Min') ].reset_index(drop=True)

    #Displacement COM Dataframes
    df_story_COMDisp = df_story_COMDisp[(df_story_COMDisp['OutputCase'] == drift)].reset_index(drop=True)

    df_story_COMDisp['UX'] = df_story_COMDisp['UX'].astype(float) * 1000 # Change to 'mm'
    df_story_COMDisp['UY'] = df_story_COMDisp['UY'].astype(float) * 1000 # Change to 'mm'
    df_story_COMDisp['Z'] = df_story_COMDisp['Z'].astype(float)

    df_story_COMDisp_x_Max = df_story_COMDisp[(df_story_COMDisp['StepType'] == 'Max')].reset_index(drop=True)
    df_story_COMDisp_y_Max = df_story_COMDisp[(df_story_COMDisp['StepType'] == 'Max') ].reset_index(drop=True)

    df_story_COMDisp_x_Min = df_story_COMDisp[(df_story_COMDisp['StepType'] == 'Min')].reset_index(drop=True)
    df_story_COMDisp_y_Min = df_story_COMDisp[(df_story_COMDisp['StepType'] == 'Min') ].reset_index(drop=True)

    # Create subplots
    fig_ = make_subplots(
        rows=1, cols=4,
        start_cell="top-left",
        subplot_titles=(f"Story Shear<br><sub>{design}", f"Overturning Moment<br><sub>{design}", 
                        f"Story Drift<br><sub>{drift}", f"COM Displacement<br><sub>{drift}"))
    
    h1 = 'V: %{x:,.1f} kN<br>Elev: %{y:.1f} m<br>Story: %{text}'
    h2 = 'M: %{x:,.1f} kNm<br>Elev: %{y:.1f} m<br>Story: %{text}'
    h3 = 'Drift: %{x:.5f}<br>Elev: %{y:.1f} m<br>Story: %{text}'
    h4 = 'Disp: %{x:,.1f} mm<br>Elev: %{y:.1f} m<br>Story: %{text}'

    #Story Shear Min Max
    fig_.add_trace(go.Scatter(x=df_story_Shear_Max['VX'], y=df_story_Shear_Max['Elevation'],
                        mode='lines+markers',
                        name='Vx_Max',
                        hovertemplate= h1,
                        text= df_story_Shear_Max['Story']), 
                        row=1, col=1,) 
    fig_.add_trace(go.Scatter(x=df_story_Shear_Max['VY'], y=df_story_Shear_Max['Elevation'],
                        mode='lines+markers',
                        name='Vy_Max',
                        hovertemplate= h1,
                        text= df_story_Shear_Max['Story']), 
                        row=1, col=1) 
    fig_.add_trace(go.Scatter(x=df_story_Shear_Min['VX'], y=df_story_Shear_Min['Elevation'],
                        mode='lines+markers',
                        name='Vx_Min',
                        hovertemplate=h1,
                        text= df_story_Shear_Min['Story']), 
                        row=1, col=1) 
    fig_.add_trace(go.Scatter(x=df_story_Shear_Min['VY'], y=df_story_Shear_Min['Elevation'],
                        mode='lines+markers',
                        name='Vy_Min',
                        hovertemplate=h1,
                        text= df_story_Shear_Min['Story']), 
                        row=1, col=1) 


    #Overturning Moment Min/Max
    fig_.add_trace(go.Scatter(x=df_story_Ovt_Max['MX'], y=df_story_Ovt_Max['Elevation'],
                        mode='lines+markers',
                        name='Mx_Max',
                        hovertemplate= h2,
                        text= df_story_Ovt_Max['Story']),
                        row=1, col =2)
    fig_.add_trace(go.Scatter(x=df_story_Ovt_Max['MY'], y=df_story_Ovt_Max['Elevation'],
                        mode='lines+markers',
                        name='My_Max',
                        hovertemplate= h2,
                        text= df_story_Ovt_Max['Story']),
                        row=1, col =2)
    fig_.add_trace(go.Scatter(x=df_story_Ovt_Min['MX'], y=df_story_Ovt_Min['Elevation'],
                        mode='lines+markers',
                        name='Mx_Min',
                        hovertemplate= h2,
                        text= df_story_Ovt_Min['Story']),
                        row=1, col =2)
    fig_.add_trace(go.Scatter(x=df_story_Ovt_Min['MY'], y=df_story_Ovt_Min['Elevation'],
                        mode='lines+markers',
                        name='My_Min',
                        hovertemplate= h2,
                        text= df_story_Ovt_Min['Story']),
                        row=1, col =2)

    #Drift Max/Min
    fig_.add_trace(go.Scatter(x=df_story_Drift_x_Max['Drift'], y=df_story_Drift_x_Max['Z'],
                        mode='lines+markers',
                        name='Drift X_Max',
                        hovertemplate=h3,
                        text= df_story_Drift_x_Max['Story']),
                        row=1, col=3)
    fig_.add_trace(go.Scatter(x=df_story_Drift_y_Max['Drift'], y=df_story_Drift_y_Max['Z'],
                        mode='lines+markers',
                        name='Drift Y_Max',
                        hovertemplate=h3,
                        text= df_story_Drift_y_Max['Story']),row=1, col=3)
    fig_.add_trace(go.Scatter(x=df_story_Drift_x_Min['Drift'], y=df_story_Drift_x_Min['Z'],
                        mode='lines+markers',
                        name='Drift X_Min',
                        hovertemplate=h3,
                        text= df_story_Drift_x_Min['Story']),row=1, col=3)
    fig_.add_trace(go.Scatter(x=df_story_Drift_y_Min['Drift'], y=df_story_Drift_y_Min['Z'],
                        mode='lines+markers',
                        name='Drift Y_Min',
                        hovertemplate=h3,
                        text= df_story_Drift_y_Min['Story']),row=1, col=3)

    #Displacement
    fig_.add_trace(go.Scatter(x=df_story_COMDisp_x_Max['UX'], y=df_story_COMDisp_x_Max['Z'],
                        mode='lines+markers',
                        name='Displacement X_Max',
                        hovertemplate=h4,
                        text= df_story_COMDisp_x_Max['Story']),row=1, col=4)
    fig_.add_trace(go.Scatter(x=df_story_COMDisp_y_Max['UY'], y=df_story_COMDisp_y_Max['Z'],
                        mode='lines+markers',
                        name='Displacement Y_Max',
                        hovertemplate=h4,
                        text= df_story_COMDisp_y_Max['Story']),
                        row=1, col=4)
    fig_.add_trace(go.Scatter(x=df_story_COMDisp_x_Min['UX'], y=df_story_COMDisp_x_Min['Z'],
                        mode='lines+markers',
                        name='Displacement X_Min',
                        hovertemplate=h4,
                        text= df_story_COMDisp_x_Min['Story']),
                        row=1, col=4)
    fig_.add_trace(go.Scatter(x=df_story_COMDisp_y_Min['UY'], y=df_story_COMDisp_y_Min['Z'],
                        mode='lines+markers',
                        name='Displacement Y_Min',
                        hovertemplate=h4,
                        text= df_story_COMDisp_y_Min['Story']),
                        row=1, col=4)

    fig_.update_layout(height=900, width=1500,
                    title_text=f"<br>Wind Lateral Performance<br><sub>{e_name}",
                    title_automargin=True,
                    margin=dict(t=120)
                    )

    # Update layout and show plot
    fig_.update_layout(height=900, width=1500, title_text=f"Wind Lateral Performance<br><sub>{e_name}",
                    title_automargin=True,
                    margin=dict(t=120)
                  )
    
    # Create a new folder for saving the plots
    new_folder = "ETABS_Plots"
    plot_save_path = os.path.join(model_path, new_folder)
    if not os.path.exists(plot_save_path):
        os.makedirs(plot_save_path)
    
    #file_path = f"C:/Users/edbert/OneDrive - Hera Engineering/Desktop/plots/Wind_plot.html"
    file_path = f"{model_path}/Wind_plot_{e_name}.html"
    #fig_.show()
    file_path = os.path.join(plot_save_path, f"{lat}_plot_{e_name}.html")
    fig_.write_html(file_path)
    #fig_.write_html(file_path)
    
    return  webbrowser.open('file://' + file_path)


def GetLoadNames(loadcases,loadcombos):
    try:
        # Load up ETABS Model
        etabs = find_etabs.find_etabs()
        e = etabs_obj.EtabsModel(etabs)
        e_name = e.get_file_name_without_suffix()
        model_path =  e.get_filepath()

        # Get list of Loadcases & Combos 
        loadcases = list(e.load_cases.get_load_cases())
        loadcombos = list(e.load_combinations.get_load_combination_names())

        return loadcases,loadcombos
    
    except Exception as e:
            logging.error("Error in Get Loadname: ", exc_info=True)
    
#INPUTS
#design_wind = 'ENV WIND ONLY ULT 500Y'
#drift_wind = 'ENV WIND ONLY SERV 25Y'
#design_EQ = 'SPEC XY-DUCT1'
#drift_EQ = 'SPEC XY-DRIFT'

# Define the load combinations and cases
#loadcombos_to_run = [design_wind,drift_wind]
#loadcase_to_run = ['WTs','WT',design_EQ,drift_EQ]

# Get data from ETABS
#df_story_Drift, df_story_Shear, df_story_AvgDisp, df_story_COMDisp, df_story_Def, e_name, model_path = get_etabs_dataframes(loadcombos_to_run, loadcase_to_run)

#print(df_story_Drift.head())

# Plot data wind
#plot_etabs_data(df_story_Drift, df_story_Shear, df_story_AvgDisp, df_story_COMDisp, df_story_Def, e_name, model_path, design_wind, drift_wind,'Wind')
# Plot data EQ
#plot_etabs_data(df_story_Drift, df_story_Shear, df_story_AvgDisp, df_story_COMDisp, df_story_Def, e_name, model_path, design_EQ, drift_EQ,'EQ')
