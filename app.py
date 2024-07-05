import pandas as pd
import numpy as np

import dash
import plotly.express as px
from dash import Dash, html, dcc, Input, Output
from dash.exceptions import PreventUpdate

# get data
df = pd.read_csv('all_month.csv')
df = df[df['type'] == 'earthquake']
df.time = pd.to_datetime(df.time, utc=True)
df = df[['time', 'latitude', 'longitude', 'mag']]
df = df.sample(1000)
df = df.reset_index(drop=True)
df.head()


# main code
app = dash.Dash(__name__)

app.layout = html.Div([
    dcc.Graph(id='earthquake-map', style={'width': '100%', 'display': 'inline-block'}),
    dcc.Graph(id='magnitude-chart', style={'width': '50%', 'display': 'inline-block'}),
    dcc.Graph(id='date-chart', style={'width': '50%', 'display': 'inline-block'}),
])

# MAP
@app.callback(
    Output('earthquake-map', 'figure'),
    [Input('magnitude-chart', 'selectedData'),
     Input('date-chart', 'selectedData')]
)
def update_map(selectedDataMag, selectedDataDate):
    df_ = df.copy()
    
    # magnitude selection
    if selectedDataMag and 'points' in selectedDataMag:
        mags = [point['x'] for point in selectedDataMag['points']]
        min_mag, max_mag = min(mags), max(mags)
        filter_mag = np.array([1 if min_mag <= mag <= max_mag else 0 for mag in df_['mag']])
    else:
        filter_mag = np.zeros(len(df_['mag']))
    # date selection
    if selectedDataDate and 'points' in selectedDataDate:
        dates = pd.to_datetime([point['x'] for point in selectedDataDate['points']], utc=True)
        min_date, max_date = min(dates), max(dates)
        filter_date = np.array([1 if min_date <= time <= max_date else 0 for time in df_['time']])
    else:
        filter_date = np.zeros(len(df_['mag']))
    filter_ = filter_mag + filter_date
    if sum(filter_) > 0:
        df_['selection'] = filter_
        df_['selection'] =  df_['selection'].apply(lambda x: 'selected' if x>=1 else 'unselected')
    else:
        df_['selection'] = 'selected'
        
    fig = px.scatter_mapbox(df_[df_['selection'] == 'selected'], lat="latitude", lon="longitude", color="mag",
                            color_continuous_scale=px.colors.cyclical.IceFire,
                            size_max=10, zoom=0.1, mapbox_style="carto-positron",
                            title="Earthquake Map")
    fig.add_scattermapbox(lat=df_[df_['selection'] == 'unselected']['latitude'],
                          lon=df_[df_['selection'] == 'unselected']['longitude'],
                          mode='markers',
                          marker=dict(size=10, color='grey', opacity=0.5),
                          name='Unselected')
    
    fig.update_layout(dragmode='lasso')
    return fig


# MAG CHART
@app.callback(
    Output('magnitude-chart', 'figure'),
    [Input('earthquake-map', 'selectedData'),
     Input('date-chart', 'selectedData')]
)
def update_mag_chart(selectedDataMap, selectedDataDate):
    df_ = df.copy()
    df_['selection'] = 'unselected'
    
    # map selection
    if selectedDataMap and 'points' in selectedDataMap:
        indexes_map = [point['pointNumber'] for point in selectedDataMap['points']]
    else:
        indexes_map = []
    
    # date selection
    if selectedDataDate and 'points' in selectedDataDate:
        dates = pd.to_datetime([point['x'] for point in selectedDataDate['points']], utc=True)
        min_date, max_date = min(dates), max(dates)
        indexes_date = df_[(min_date <= df_['time']) & (df_['time'] <= max_date)].index.to_list()
    else:
        indexes_date = []
    
    indexes = list(set(indexes_map).union(set(indexes_date)))
    if len(indexes):
        df_.loc[indexes, 'selection'] = 'selected'
    
    fig = px.histogram(df_, x='mag', color='selection',
                       color_discrete_map={'unselected': 'gray', 'selected': 'red'},
                       nbins=100, title="Distribution of Earthquake Magnitudes")
    for trace in fig.data:
        if trace.name == "selected":
            trace.marker.opacity = 0.5
        else:
            trace.marker.opacity = 0.3
            
    fig.update_layout(dragmode='select')
    return fig


# DATE CHART
@app.callback(
    Output('date-chart', 'figure'),
    [Input('earthquake-map', 'selectedData'),
     Input('magnitude-chart', 'selectedData')]
)
def update_date_chart(selectedDataMap, selectedDataMag):
    df_ = df.copy()
    df_['selection'] = 'unselected'
    
    # map selection
    if selectedDataMap and 'points' in selectedDataMap:
        indexes_map = [point['pointNumber'] for point in selectedDataMap['points']]
    else:
        indexes_map = []
    
    # magnitude selection
    if selectedDataMag and 'points' in selectedDataMag:
        mags = [point['x'] for point in selectedDataMag['points']]
        min_mag, max_mag = min(mags), max(mags)
        indexes_mag = df_[(min_mag <= df_['mag']) & (df_['mag'] <= max_mag)].index.to_list()
    else:
        indexes_mag = []
    
    indexes = list(set(indexes_map).union(set(indexes_mag)))
    if len(indexes):
        df_.loc[indexes, 'selection'] = 'selected'
    
    fig = px.histogram(df_, x='time', color='selection',
                       color_discrete_map={'unselected': 'gray', 'selected': 'red'},
                       nbins=100, title="Distribution of Earthquake Dates")
    for trace in fig.data:
        if trace.name == "selected":
            trace.marker.opacity = 0.5
        else:
            trace.marker.opacity = 0.3
            
    fig.update_layout(dragmode='select')
    return fig

