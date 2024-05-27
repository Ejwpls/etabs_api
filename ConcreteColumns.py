import etabs_obj 
import find_etabs
import pandas as pd

# Load up ETABS Model
etabs = find_etabs.find_etabs()
e = etabs_obj.EtabsModel(etabs)
e_name = e.get_file_name_without_suffix()
model_path =  e.get_filepath()
print(f"API attached model: {e_name}")
print(f"Model path: {model_path}")

# Function to get selected ETABS object and put return as dataframe 
def GetSelectedObject(objtype):
    #From ETABS and put into tuples
    selected_output = e.SapModel.SelectObj.GetSelected()
    obj_type = selected_output[1]
    obj_names = selected_output[2]

    # Put into a dataframe
    df = pd.DataFrame({'objname': obj_names, 'objtype': obj_type})

    # Filter objtype 
    df = df[df['objtype'] == objtype].reset_index(drop=True)

    return df

# Function to get Frame Label from Name 
def GetLabelFromName(name):
    frame = e.SapModel.FrameObj.GetLabelFromName(name)
    return frame

# Function to get Section name from Name
def GetSectionFromName(name):
    section = e.SapModel.FrameObj.GetSection(name)
    return section

df_frames = GetSelectedObject(2)

# Get all Frames Section in ETABS model
allframeobj = e.SapModel.FrameObj.GetAllFrames()
fr_name = allframeobj[1]
fr_propname = allframeobj[2]
fr_storyname = allframeobj[3]
fr_PointName1 = allframeobj[4]
fr_PointName2 = allframeobj[5]
fr_Point1X = allframeobj[6]
fr_Point1Y = allframeobj[7]

df_allFrames = pd.DataFrame({'NAME': fr_name, 'PROPNAME': fr_propname,'STORY':fr_storyname, 'POINT 1X': fr_Point1X, 'POINT 1Y': fr_Point1Y})

# Filter All Frames with Selected Frames 
df_SelectedFrame = df_allFrames[df_allFrames['NAME'].isin(df_frames['objname'])].reset_index(drop=True)

df1 = df_SelectedFrame.copy()
b = df1['NAME'].apply(GetLabelFromName)

label = []
level = []
ret = []
section = []

i = 0
for bx in b:
    label.append(b[i][0])
    ret.append(b[i][2])
    section.append(b[i][0])
    i = i +1

df1['LABEL'] = label
df1['LABEL'] = df1['LABEL'].astype(str)

# Get all the Columns 
df_sel_column = df1[df1['LABEL'].str.startswith('C')| df1['LABEL'].str.startswith('D')]

print(df_sel_column.head())

def GetSelectedPiers():
    # Get Tables from ETABS
    df_Tables = e.database.read(table_key='Pier Section Properties', to_dataframe=True)
    df_PierSection = df_Tables[['Story','Pier','CGBotX','CGBotY']]
    #Give Name to each Pier
    df_PierSection['NAME'] = ['P' + str(index).zfill(5) for index in range(len(df_PierSection))]
    #Create PROPNAMING
    df_PierSection['PROPNAME'] = df_Tables.apply(lambda row: f"PIER_{int(float(row['WidthBot'])*1000)}x{int(float(row['ThickBot'])*1000)}_{row['Material']}", axis=1)
    #Formating 
    df_PierSection = df_PierSection.rename(columns={'Story':'STORY', 'Pier':'LABEL','CGBotX':'POINT 1X', 'CGBotY':'POINT 1Y'})

    return df_PierSection

df_sel_pier = GetSelectedPiers()

df_selected = df_sel_column.append(df_sel_pier)
# ALL PIER SEEMS TO BE IMPORTED


# Export values back to Excel
file_path = "C:/Users/edbert/OneDrive - Hera Engineering/Desktop/#####_HTK_COLUMN DESIGN_0.151_EW.xlsm"
df_excel = pd.read_excel(file_path, sheet_name='SCHEDULE')

common_cols = df_selected.intersection(df_excel.columns)