import pandas as pd
import numpy as np
from dash import Dash, dcc, html, Input, Output, State, callback, Patch, clientside_callback, dash_table
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import plotly.io as pio
from dash.dependencies import Input, Output
from dash_bootstrap_templates import ThemeChangerAIO, template_from_url
import dash_ag_grid as dag

# stylesheet with the .dbc class to style  dcc, DataTable and AG Grid components with a Bootstrap theme
dbc_css = "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates/dbc.min.css"

# Load the data (assuming the code to load ratings and polls dataframes is already present)
ratings = pd.read_csv('pollster-ratings-combined.csv')
polls = pd.read_csv('raw_polls.csv')
polls['polldate'] = pd.to_datetime(polls['polldate'])
polls['methodology']=polls['methodology'].fillna("Unknown Method")
polls['year'] = polls['polldate'].dt.year
polls['margin_diff']=polls['margin_poll'].sub(polls['margin_actual'])
pollsters = polls['pollster'].unique()
locations = polls['location'].unique()
race_types = polls['type_simple'].unique()
methodologies = polls['methodology'].unique()
polldates = polls['polldate'].unique()
election_date = polls['electiondate'].unique()
time_to_election = polls['time_to_election'].unique()


# Initialize the Dash app
#dbc_css = "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates/dbc.min.css"
app = Dash(__name__, external_stylesheets=[dbc.themes.ZEPHYR])

# Define the layout
app.layout = dbc.Container(
    [
        dbc.Row(dbc.Col(html.H1("Understanding Pollster Ratings"),className="bg-dark bg-gradient text-white text-center rounded", width= 12)),

        dbc.Row(
            [
                dbc.Col(
                    html.Div([
                        dbc.Label("Select a Pollster:"),
                        dcc.Dropdown(
                            id='pollster-dropdown',
                            options=[{'label': i, 'value': i} for i in ratings['pollster'].unique()],
                            value=ratings['pollster'].unique()[0]
                        ),
                    ]),
                    width={"size": 6} 
                )
            ]
        ),
        dbc.Row(
            dbc.Col(
                html.Br()
            )
        ),
        dbc.Row(
            dbc.Col(
                html.H2("Pollster Ratings from 538"), className="bg-dark text-white text-center rounded",
                width= 12
                )
        ), 
        dbc.Row(
            dbc.Col(
                html.Div(id='pollster-info', className="info")
            )
        ),

        dbc.Row(
            dbc.Col(
                html.Br()
            )
        ),

        dbc.Row(
            dbc.Col(
                html.H2("Pollster Detail"),
                className="bg-dark text-center rounded-top text-white"
            )
        ),

        dbc.Row(
            children=[
                dbc.Col(
                        children=[
                            dbc.Row(
                                dbc.Col(
                                    html.Div([
                                        dbc.Label("Select Cycle:"),
                                        dcc.Dropdown(id='cycle-dropdown',className= "text-black"),
                                    ])
                                )
                            ),
                            dbc.Row(
                                dbc.Col(
                                    html.Div([
                                        dbc.Label("Select Race:"),
                                        dcc.Dropdown(id='race-dropdown', className= "text-black"),
                                    ])
                                )
                            ),
                            dbc.Row(
                                dbc.Col(
                                    html.Div([
                                        dbc.Label("Select Location:"),
                                        dcc.Dropdown(id='location-dropdown', className= "text-black"),
                                    ])
                                )
                            ),
                            dbc.Row(
                                dbc.Col(
                                    html.Div([
                                        dbc.Label("Select Methodology:"),
                                        dcc.Dropdown(id='methodology-dropdown',className= "text-black"),
                                    ])
                                )
                            )
                        ], 
                        width={"size": 4}
                    ),
                dbc.Col(
                    children=[
                        html.Div(id='pollster-details-output'),
                        dcc.Graph(id='margin-plot', className= "rounded"),
                        html.Br()

                    ], 
                    width={"size": 8},
                    className= "bg-dark text-white rounded-bottom"
                )
            ]    
        ,className= "bg-dark text-white rounded"
        )
    ]
)        




@app.callback(
    [Output('pollster-info', 'children'),
     Output('cycle-dropdown', 'options'),
     Output('race-dropdown', 'options'),
     Output('location-dropdown', 'options'),
     Output('methodology-dropdown', 'options')],
    [Input('pollster-dropdown', 'value')]
)

def update_table_and_dropdowns(selected_pollster):
    filtered_ratings = ratings[ratings['pollster'] == selected_pollster]
    new_order = ['rank', 'pollster','numeric_grade', 'POLLSCORE','wtd_avg_transparency','number_polls_pollster_total', 
                 'error_ppm', 'bias_ppm']
    filtered_ratings2 = filtered_ratings[new_order].rename(columns={'rank':'Rank', 'pollster':'Pollster', 
                                                           'numeric_grade':'Rating','POLLSCORE': 'Pollscore',
                                                             'wtd_avg_transparency':'Transparency', 
                                                             'number_polls_pollster_total': 'Number Polls',
                                                             'error_ppm':'+/- Error', 'bais_ppm': '+/- Bias'})
    table = dash_table.DataTable(filtered_ratings2.to_dict('records'), [{"name": i, "id": i} for i in filtered_ratings2.columns])
    filtered_polls = polls[polls['pollster'] == selected_pollster]
    cycle_options = [{'label': i, 'value': i} for i in filtered_polls['cycle'].unique()]
    race_options = [{'label': i, 'value': i} for i in filtered_polls['race'].unique()]
    location_options = [{'label': i, 'value': i} for i in filtered_polls['location'].unique()]
    methodology_options = [{'label': i, 'value': i} for i in filtered_polls['methodology'].unique()]

    return table, cycle_options, race_options, location_options, methodology_options

@app.callback(
    [Output('pollster-details-output', 'children'),
     Output('margin-plot', 'figure')],
    [Input('pollster-dropdown', 'value'),
     Input('cycle-dropdown', 'value'),
     Input('race-dropdown', 'value'),
     Input('location-dropdown', 'value'),
     Input('methodology-dropdown', 'value')]
)
def update_details(selected_pollster, selected_cycle, selected_race, selected_location, selected_methodology):
    filtered_polls = polls[polls['pollster'] == selected_pollster]
    filtered_polls['margin_diff']= filtered_polls['margin_poll'].sub(filtered_polls['margin_actual'])
    
    if selected_cycle:
        filtered_polls = filtered_polls[filtered_polls['cycle'] == selected_cycle]
    if selected_race:
        filtered_polls = filtered_polls[filtered_polls['race'] == selected_race]
    if selected_location:
        filtered_polls = filtered_polls[filtered_polls['location'] == selected_location]
    if selected_methodology:
        filtered_polls = filtered_polls[filtered_polls['methodology'] == selected_methodology]


    num_polls = filtered_polls['poll_id'].nunique()
    num_questions = filtered_polls['question_id'].nunique()
   
    details = html.H4(f"Number of Polls: {num_polls}.   Number of Questions: {num_questions}",className="bg-dark text-white text-center")

    
    
    fig = px.scatter(filtered_polls, x='polldate', y=['margin_poll', 'margin_actual'], size='samplesize',
                   title="Margin Over Time",
                   labels={'year':'Year', 'value':'Margin'},
                   color_discrete_map={'margin_poll':'blue', 'margin_actual':'green'})

    return details, fig

if __name__ == '__main__':
    app.run_server(debug=True)
