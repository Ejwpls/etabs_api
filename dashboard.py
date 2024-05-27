import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import pandas as pd
import base64
import io

# Initialize the Dash app
app = dash.Dash(__name__)

# Define the app layout
app.layout = html.Div([
    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select Files')
        ]),
        style={
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        },
        multiple=False
    ),
    dcc.Dropdown(id='output_case_dropdown'),
    dcc.Graph(id='graph')
])

# Define the callback to update the dropdown after file upload
@app.callback(
    Output('output_case_dropdown', 'options'),
    [Input('upload-data', 'contents')],
    [State('upload-data', 'filename')]
)
def update_dropdown(contents, filename):
    if contents is not None:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        xls = pd.ExcelFile(io.BytesIO(decoded))
        story_forces = pd.read_excel(xls, 'Story Forces')
        story_forces.columns = story_forces.iloc[0]
        story_forces = story_forces[2:]
        story_forces.reset_index(drop=True, inplace=True)
        return [{'label': i, 'value': i} for i in story_forces['Output Case'].unique()]
    return []

# Define the callback to update the graph
@app.callback(
    Output('graph', 'figure'),
    [Input('output_case_dropdown', 'value'),
     Input('upload-data', 'contents')],
    [State('upload-data', 'filename')]
)
def update_graph(selected_output_case, contents, filename):
    if contents is not None:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        xls = pd.ExcelFile(io.BytesIO(decoded))
        story_forces = pd.read_excel(xls, 'Story Forces')
        story_forces.columns = story_forces.iloc[0]
        story_forces = story_forces[2:]
        story_forces.reset_index(drop=True, inplace=True)
        filtered_df = story_forces[story_forces['Output Case'] == selected_output_case]
        figure = {
            'data': [
                {'x': filtered_df['VX'], 'y': filtered_df['Story'], 'mode': 'markers', 'name': 'VX'},
                {'x': filtered_df['VY'], 'y': filtered_df['Story'], 'mode': 'markers', 'name': 'VY'},
            ],
            'layout': {
                'title': 'Story Forces',
                'xaxis': {'title': 'Values'},
                'yaxis': {'title': 'Story'}
            }
        }
        return figure
    return {}

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8050)