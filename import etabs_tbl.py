import etabs_obj 
import find_etabs
import pandas as pd
import xlwings as xw

# Load up ETABS Model
etabs = find_etabs.find_etabs()
e = etabs_obj.EtabsModel(etabs)
model_path =  e.get_filepath()
print(f"Model path: {model_path}")

file_path = "C:/Users/edbert/OneDrive - Hera Engineering/Desktop/ETABS_WALL_DESIGN_REV2.2.xlsx"
wb = xw.Book(file_path)

# Read Story Definitions from ETABS
df_tbl_StoryDefinition = e.database.read(table_key='Story Definitions', to_dataframe=True)

# Rename columns as required
df_tbl_StoryDefinition.rename(columns={
    'Story': 'Name',
    'IsMaster': 'Master Story',
    'SimilarTo': 'Similar To',
    'IsSpliced': 'Splice Height'
}, inplace=True)

# Update 'ETABS' column
df_tbl_StoryDefinition['ETABS'] = df_tbl_StoryDefinition['Name'].shift(1).fillna('Base')
df_tbl_StoryDefinition.at[df_tbl_StoryDefinition.index[-1], 'ETABS'] = 'Base'

# Access Excel sheet and table
sheet = wb.sheets['Story Definitions']
excel_table = sheet.tables['tbl_storydef']

# Get headers from the Excel table
excel_headers = [cell.value for cell in excel_table.header_row_range]

# Reorder DataFrame columns to match Excel table headers
matching_columns = [col for col in excel_headers if col in df_tbl_StoryDefinition.columns]
df_filtered = df_tbl_StoryDefinition[matching_columns]

# Find the index of the 'Height' column in the DataFrame
height_column_index = df_filtered.columns.tolist().index('Height')

# Insert a placeholder column after the 'Height' column
# We'll call this placeholder column 'Placeholder' for alignment
df_filtered.insert(height_column_index + 1, 'Placeholder', '')

# Clear existing data in the Excel table
data_range = excel_table.data_body_range
if data_range is not None:  # Check if the table has data
    data_range.clear_contents()

# Write new data from DataFrame to Excel table
if not df_filtered.empty:  # Check if the DataFrame is not empty
    # Access the first cell of the data body range
    starting_cell = excel_table.data_body_range[0, 0]

    # Write the data
    sheet.range(starting_cell.address).options(index=False, header=False).value = df_filtered

    # Calculate the number of rows and columns for the new data
    num_rows = len(df_filtered)
    num_columns = len(df_filtered.columns)

    # Calculate the last cell address for the new data range
    last_cell_row = starting_cell.row + num_rows
    last_cell_column = starting_cell.column + num_columns - 1
    last_cell_address = sheet.range(last_cell_row, last_cell_column).address

    # Define the new table range including the header
    new_table_range = excel_table.range.resize(row_size=num_rows + 1, column_size=num_columns)

    # Resize the table to fit the new data
    excel_table.resize(new_table_range)

