import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import dash_table

import base64
import datetime
import io


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([
    html.H6("RRH FIT Plot Builder"), 
    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Drag and Drop a "working set" KPI report in csv\
            or xlsx format from NetAct, or ',
            html.A('Select a File')
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
        # 
        multiple=False
    ),
    html.Div(id='output-data-upload'),
    
    dcc.DatePickerRange(
        id='date-picker-range',
        #start_date=dt(1997, 5, 3),
    ),
    
    html.Div(id='output-data-KPI_process'), # Add an html.Div for app output
]) #style={'columnCount': 2}


# Build the KPIs figures
def list_of_fig_divs(df):

    # num_of_KPIs = df.columns[2:].size
    kpi_list = df.columns[2:]

    fig_list = []
    
    # Append the table to fig_list
    prepared_table = prepare_stats_table(df)
    table_figure = create_plotly_table (prepared_table)
    fig_list.append(table_figure)
    
    for KPI in kpi_list:
        fig = px.line(df, x='Period start time',
                      y=KPI, line_group='ws', color='ws')
        fig.update_layout(legend_orientation="h")
        fig_list.append(fig)
    
    return [dcc.Graph(figure=fig) for fig in fig_list]


def parse_contents(contents, filename, date):
    global df
    content_type, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(
                io.StringIO(decoded.decode('utf-8')), sep=';')
        elif 'xls' in filename:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(decoded))
            df.drop(0, inplace=True)
    except Exception as e:
        print(e)
        return html.Div([
            'There was an error processing this file.'
        ])

    upload_table_div =  html.Div([
        html.H5(filename),
        html.H6(datetime.datetime.fromtimestamp(date)),

        dash_table.DataTable(
            data=df.head().to_dict('records'), # modified to show head only
            columns=[{'name': i, 'id': i} for i in df.columns]
        ),
        html.Hr()
    ])
    
    
    return upload_table_div

# ===== Table functions ========

def prepare_stats_table(df):
    #Creates a summary table
    df2 = df[df.columns[2:]].astype('float')
    df3 = df[df.columns[:2]]
    df4 = pd.concat([df3, df2], axis=1)
    df5 = df4.groupby('ws').mean().T
    df5 = df5.round(2)
    df5.reset_index(inplace=True)
    return df5

def create_plotly_table (summ_table):
    # receives
    fig = go.Figure(data=[go.Table(
        header=dict(values=list(summ_table.columns),
                    fill_color='paleturquoise',
                    align='left'),
        cells=dict(values=summ_table.values.T,
                   fill_color='lavender',
                   align='left'))
    ])
    fig.update_layout(legend_orientation="h")
    return fig



@app.callback([Output('output-data-upload', 'children'),
               #Output('date-picker-range','min_date_allowed'),
               #Output('date-picker-range','max_date_allowed'),
               Output('output-data-KPI_process','children'),
               Output('date-picker-range','style')],
               [Input('date-picker-range', 'start_date'),
                Input('date-picker-range', 'end_date'),
                Input('upload-data', 'contents')],
              [State('upload-data', 'filename'),
               State('upload-data', 'last_modified')])
def update_database(start_date, end_date, content, name, date):
    upload_tb_list, kpi_div_list, new_df = [], [], []
    show_date_picker = {'display': 'none'}
    #start_date = pd.to_datetime(start_date, infer_datetime_format=True)
    #end_date = pd.to_datetime(end_date, infer_datetime_format=True)
    #min_date, max_date = datetime.datetime(2019,1,1), datetime.datetime(2019,1,2)
    if content is not None:
        #for c, n, d in zip(list_of_contents, list_of_names, list_of_dates):
        upload_tb_div = parse_contents(content, name, date)
        kpi_div_list = list_of_fig_divs(df)
        
        upload_tb_list.append(upload_tb_div)

        show_date_picker = {'display': 'block'}
        #min_date = df['Period start time'].min()
        #max_date = df['Period start time'].max()

    if start_date and end_date is not None:
        print(start_date,'\n')
        print(end_date)

        new_df = df[(df['Period start time'] >= start_date) & (df['Period start time'] <= end_date)]

        kpi_div_list = list_of_fig_divs(new_df)
        

    return upload_tb_list, kpi_div_list, show_date_picker

'''
@app.callback(
    dash.dependencies.Output('output-data-KPI_process','children'),
    [dash.dependencies.Input('date-picker-range', 'start_date'),
     dash.dependencies.Input('date-picker-range', 'end_date')])
def update_with_new_dates(start_date, end_date):
    new_df, new_div_list = df, []
    if start_date and end_date is not None:
        new_df = df[df['Period start time'] >= start_date & df['Period start time'] <= end_date]
        new_div_list = list_of_fig_divs(new_df)
    return new_div_list
'''

if __name__ == '__main__':
    app.run_server(debug=True)
