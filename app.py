import pandas as pd
import numpy as np

import dash
import plotly.express as px
from dash import Dash, html, dcc, Input, Output
from dash.exceptions import PreventUpdate

# get data
df1 = pd.read_csv('all_month.csv')
df1 = df1[df1['type'] == 'earthquake']
df1.time = pd.to_datetime(df1.time, utc=True)
df1 = df1[['time', 'latitude', 'longitude', 'mag']]
df1 = df1.sample(1000)
df1 = df1.reset_index(drop=True)
df1.head()

# main code
app1 = dash.Dash(__name__)

app1.layout = html.Div([
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
    df1_ = df1.copy()
    
    # magnitude selection
    if selectedDataMag and 'points' in selectedDataMag:
        mags = [point['x'] for point in selectedDataMag['points']]
        min_mag, max_mag = min(mags), max(mags)
        filter_mag = np.array([1 if min_mag <= mag <= max_mag else 0 for mag in df1_['mag']])
    else:
        filter_mag = np.zeros(len(df1_['mag']))
    # date selection
    if selectedDataDate and 'points' in selectedDataDate:
        dates = pd.to_datetime([point['x'] for point in selectedDataDate['points']], utc=True)
        min_date, max_date = min(dates), max(dates)
        filter_date = np.array([1 if min_date <= time <= max_date else 0 for time in df1_['time']])
    else:
        filter_date = np.zeros(len(df1_['mag']))
    filter_ = filter_mag + filter_date
    if sum(filter_) > 0:
        df1_['selection'] = filter_
        df1_['selection'] =  df1_['selection'].apply(lambda x: 'selected' if x>=1 else 'unselected')
    else:
        df1_['selection'] = 'selected'
        
    fig = px.scatter_mapbox(df1_[df1_['selection'] == 'selected'], lat="latitude", lon="longitude", color="mag",
                            color_continuous_scale=px.colors.cyclical.IceFire,
                            size_max=10, zoom=0.1, mapbox_style="carto-positron",
                            title="Earthquake Map")
    fig.add_scattermapbox(lat=df1_[df1_['selection'] == 'unselected']['latitude'],
                          lon=df1_[df1_['selection'] == 'unselected']['longitude'],
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
    df1_ = df1.copy()
    df1_['selection'] = 'unselected'
    
    # map selection
    if selectedDataMap and 'points' in selectedDataMap:
        indexes_map = [point['pointNumber'] for point in selectedDataMap['points']]
    else:
        indexes_map = []
    
    # date selection
    if selectedDataDate and 'points' in selectedDataDate:
        dates = pd.to_datetime([point['x'] for point in selectedDataDate['points']], utc=True)
        min_date, max_date = min(dates), max(dates)
        indexes_date = df1_[(min_date <= df1_['time']) & (df1_['time'] <= max_date)].index.to_list()
    else:
        indexes_date = []
    
    indexes = list(set(indexes_map).union(set(indexes_date)))
    if len(indexes):
        df1_.loc[indexes, 'selection'] = 'selected'
    
    fig = px.histogram(df1_, x='mag', color='selection',
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
    df1_ = df1.copy()
    df1_['selection'] = 'unselected'
    
    # map selection
    if selectedDataMap and 'points' in selectedDataMap:
        indexes_map = [point['pointNumber'] for point in selectedDataMap['points']]
    else:
        indexes_map = []
    
    # magnitude selection
    if selectedDataMag and 'points' in selectedDataMag:
        mags = [point['x'] for point in selectedDataMag['points']]
        min_mag, max_mag = min(mags), max(mags)
        indexes_mag = df1_[(min_mag <= df1_['mag']) & (df1_['mag'] <= max_mag)].index.to_list()
    else:
        indexes_mag = []
    
    indexes = list(set(indexes_map).union(set(indexes_mag)))
    if len(indexes):
        df1_.loc[indexes, 'selection'] = 'selected'
    
    fig = px.histogram(df1_, x='time', color='selection',
                       color_discrete_map={'unselected': 'gray', 'selected': 'red'},
                       nbins=100, title="Distribution of Earthquake Dates")
    for trace in fig.data:
        if trace.name == "selected":
            trace.marker.opacity = 0.5
        else:
            trace.marker.opacity = 0.3
            
    fig.update_layout(dragmode='select')
    return fig



regions = [
    'Тернопільська', 'Харківська', 'Вінницька', 'Івано-Франківська',
    'Дніпропетровська', 'Миколаївська', 'Сумська', 'Полтавська',
    'Черкаська', 'Чернігівська', 'Одеська', 'Запорізька', 'Київська',
    'Хмельницька', 'Закарпатська', 'Херсонська', 'Львівська',
    'Кіровоградська', 'Рівненська', 'Чернівецька', 'Житомирська',
    'Волинська', 'Автономна Республіка Крим', 'Донецька', 'Луганська'
]
df_regions = pd.DataFrame({
    'name': regions,
    'value': [0] * len(regions)
})

import plotly.express as px
import plotly.graph_objects as go
import dash
from dash import Dash, html, dcc, Input, Output
from dash.exceptions import PreventUpdate

# read data: geojson
filepath = 'data/ukraine.geojson'
with open(filepath) as f:
    geojson_data = json.load(f)
# read data: main dataframe
df = pd.read_csv('data/submissions.csv')
df = df[['submission_date', 'submission_status', 'initiator_region', 'item_amount', 'item_classification']]
df.columns = ['date', 'status', 'region', 'amount', 'classification']
df['index'] = df.index
df.head(3)

# some colors
category_order = ['approval', 'active', 'pending', 'withdrawn', 'unsuccessful', 'declined']
colors = ['#34eb4f', '#4f81eb', '#ebcd34', '#eb5834', '#9634eb', '#707070']
color_map = {status: color for status, color in zip(category_order, colors)}
reversed_color_map = {color: status for status, color in zip(category_order, colors)}
class_color_discrete_map = {'kitchen': 'red', 'shelter': 'blue'}

app2 = dash.Dash(__name__)
app2.layout = html.Div([
    dcc.Graph(id='map', style={'width': '100%', 'display': 'inline-block'}),
    dcc.Graph(id='barchart', style={'width': '50%', 'display': 'inline-block'}),
    dcc.Graph(id='money_distribution', style={'width': '50%', 'display': 'inline-block'})  # New histogram
])

# Map count
@app.callback(
    Output('map', 'figure'),
    [Input('barchart', 'selectedData'),
     Input('money_distribution', 'selectedData')]
)
def update_map(selectedStatus, selectedMoney):
    df_ = df.copy()
    if selectedStatus is None:
        pass
    else:
        colors = [point['marker.color'] for point in selectedStatus['points']]
        status_list = [reversed_color_map[color] for color in colors]
        df_ = df_[df_['status'].isin(status_list)]
        
    # group
    df_ = df_.groupby('region').agg({'amount': 'count'}).reset_index()
    df_.columns = ['name', 'value']
    # add empty regions
    missing_regions = ~df_regions['name'].isin(df_['name'])
    missing_df = df_regions[missing_regions]
    df_ = pd.concat([df_, missing_df], ignore_index=True)
    # plot map
    map_color_scale = [
        (0.0, 'white'),    # Zero values as grey
        (0.01, '#0d0887'),  # Start of Plasma, deep purple
        (0.25, '#7e03a8'),  # Purple
        (0.5, '#cb4679'),   # Pinkish
        (0.75, '#f89441'),  # Orange
        (1.0, '#f0f921')    # Bright yellow
    ]
    fig = px.choropleth(
        df_,
        locations='name',
        color='value',
        geojson=geojson_data,
        featureidkey="properties.name",
        color_continuous_scale=map_color_scale,
        title='Applications Distribution',
    )
    fig.update_geos(fitbounds="locations",
                    projection_type="mercator",
                    visible=False)
    
    fig.update_layout(title_x=0.5)
    fig.update_layout(
        autosize=False,
        margin = dict(
                l=0,
                r=0,
                b=0,
                t=25,
                autoexpand=True
            ),
            width=800,
        #     height=400,
    )
    fig.update_layout(dragmode='select')
    
    return fig



# Status chart
@app.callback(
    Output('barchart', 'figure'),
    [Input('map', 'selectedData')])
def update_mag_chart(selectedMap):
    # filter by regions
    df_ = df.copy()
    if selectedMap is None:
        pass
    else:
        regions = [point['location'] for point in selectedMap['points']]
        df_ = df_[df_['region'].isin(regions)]
    category_order = ['approval', 'active', 'pending', 'withdrawn', 'unsuccessful', 'declined']
    colors = ['#34eb4f', '#4f81eb', '#ebcd34', '#eb5834', '#9634eb', '#707070']
    
    df_ = df_.value_counts("status").reset_index()
    df_.columns = ['status', 'count']
    df_['status'] = pd.Categorical(df_['status'], categories=category_order, ordered=True)
    df_ = df_.sort_values('status')

    # plot
    fig = go.Figure(data=[
        go.Bar(
            x=df_['status'],
            y=df_['count'],
            marker_color=[color_map[status] for status in df_['status']]
        )
    ])

    # Setting up the layout
    fig.update_layout(
        title='Applications Status Counts',
        xaxis_title='Status',
        yaxis_title='Count',
        yaxis=dict(range=[0, 300]),
        title_x=0.5,  # centers the title
    )
    fig.update_layout(dragmode='select')
    
    
    return fig

@app.callback(
    Output('money_distribution', 'figure'),
    [Input('map', 'selectedData'), Input('barchart', 'selectedData')]
)
def update_money_distribution(selectedMap, selectedStatus):
    df_ = df.copy()
    
    # Filter by regions if any selected on the map
    if selectedMap is not None:
        regions = [point['location'] for point in selectedMap['points']]
        df_ = df_[df_['region'].isin(regions)]
    
    # Filter by statuses if any selected on the barchart
    if selectedStatus is not None:
        colors = [point['marker.color'] for point in selectedStatus['points']]
        status_list = [reversed_color_map[color] for color in colors]
        df_ = df_[df_['status'].isin(status_list)]
    
    # Plot histogram
    fig = px.histogram(
        df_,
        x='amount',  # Switch x to y for horizontal layout
        color='classification',
        barmode='group',
        color_discrete_map=class_color_discrete_map,
        nbins=30,  # Number of bins set to 30
        title='Monetary Distribution by Classification',
    )
    # Update layout for better view
    fig.update_layout(
        yaxis_title='Monetary Amount',  # Now y-axis is the monetary amount
        xaxis_title='Count',  # x-axis now represents the count
        legend_title='Classification',
        title_x=0.5,  # centers the title
    )
    return fig
