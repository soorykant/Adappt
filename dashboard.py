import pandas as pd
import dash
from dash import dcc
from dash import html
import plotly.graph_objects as go

# data cleaning and preprocessing
data = pd.read_csv("data.csv")
details = pd.read_csv("details.csv")

data['Datetime'] = pd.to_datetime(data['Datetime'])

data.drop_duplicates(inplace=True)

details["timezoneOffset"] = pd.to_timedelta(details["timezoneOffset"])
offset = details["timezoneOffset"][0]
data['Datetime'] = data['Datetime'] + offset

data_resampled = data.groupby(
    [pd.Grouper(key='Datetime', freq='10T'), 'sensorId']).agg({
        'peopleCount':
        'sum'
    }).fillna(0).reset_index()

df = pd.merge(data_resampled, details, on="sensorId", how="inner")

# a) Average people Count and Peak People Count of both floors in a chart
avg_people_count = df.groupby('floor')['peopleCount'].mean().round(2)
peak_people_count = df.groupby('floor')['peopleCount'].max().round(2)

fig_a = go.Figure()
fig_a.add_trace(
    go.Bar(x=avg_people_count.index,
           y=avg_people_count.values,
           text=avg_people_count.values,
           name='Average People Count'))
fig_a.add_trace(
    go.Bar(x=peak_people_count.index,
           y=peak_people_count.values,
           text=peak_people_count.values,
           name='Peak People Count'))

fig_a.update_layout(title='Average and Peak People Count by Floor',
                    xaxis_title='Floor',
                    yaxis_title='People Count',
                    barmode='group')

# b) Display department-wise people count statistics in a chart.
department_stats = df.groupby('department')['peopleCount'].agg(
    ['mean', 'max', 'min']).round(2)

fig_b = go.Figure()
fig_b.add_trace(
    go.Bar(x=department_stats.index,
           y=department_stats['mean'],
           text=department_stats['mean'],
           name='Average People Count'))
fig_b.add_trace(
    go.Bar(x=department_stats.index,
           y=department_stats['max'],
           text=department_stats['max'],
           name='Max People Count'))
fig_b.add_trace(
    go.Bar(x=department_stats.index,
           y=department_stats['min'],
           text=department_stats['min'],
           name='Min People Count'))

fig_b.update_layout(title='People Count Statistics by Department',
                    xaxis_title='Department',
                    yaxis_title='People Count',
                    barmode='group')

# c) Show the top 5 desks with the most consistent occupancy in a table or chart.
df1 = df.groupby('name').agg({"peopleCount": "sum", "capacity": "sum"})
df1["occupancy_rate"] = df1["peopleCount"] / df1["capacity"] * 100
top5_occupancy_rate = df1.sort_values(
    by="occupancy_rate", ascending=False).reset_index().head(5).round(2)

fig_c = go.Figure(data=go.Bar(x=top5_occupancy_rate['name'],
                              y=top5_occupancy_rate['occupancy_rate'],
                              text=top5_occupancy_rate['occupancy_rate']))

fig_c.update_layout(title='Top 5 Desks with Highest Average Occupancy Rate',
                    xaxis_title='Desk ID',
                    yaxis_title='Occupancy Rate (%)')

# d) Show overall people count trends over day of week in a line chart.
df['DayOfWeek'] = df['Datetime'].dt.day_name()
weekday_order = [
    'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday',
    'Sunday'
]
people_count_trends = df.groupby('DayOfWeek')['peopleCount'].mean().reindex(
    weekday_order).round(2)

fig_d = go.Figure(data=[
    go.Scatter(x=people_count_trends.index,
               y=people_count_trends.values,
               mode='lines+markers')
])

fig_d.update_layout(title='People Count Trends by Day of Week',
                    xaxis_title='Day of Week',
                    yaxis_title='Average People Count')

# e) Show people count trends over time in a day in a line chart.
df['Hour'] = df['Datetime'].dt.hour
people_count_trends = df.groupby('Hour')['peopleCount'].mean().round(2)

fig_e = go.Figure(data=go.Scatter(x=people_count_trends.index,
                                  y=people_count_trends.values,
                                  mode='lines+markers'))

fig_e.update_layout(title='Overall People Count Trends over Time in a Day',
                    xaxis_title='Hour',
                    yaxis_title='Average People Count')

# f) Show overall people count trends over time in a line chart.
fig_f = go.Figure(
    data=[go.Scatter(x=df["Datetime"], y=df["peopleCount"], mode='lines')])

fig_f.update_layout(title='People Count Trends Over Time',
                    xaxis_title='Time',
                    yaxis_title='People Count')

# g) Highlight and plot outliers in a chart or table.
df['zscore'] = (df['peopleCount'] -
                df['peopleCount'].mean()) / df['peopleCount'].std()

threshold = 3
outliers = df[df['zscore'].abs() > threshold]

fig_g = go.Figure()
fig_g.add_trace(
    go.Scatter(x=df['Datetime'],
               y=df['peopleCount'],
               mode='lines',
               name='People Count'))
fig_g.add_trace(
    go.Scatter(x=outliers['Datetime'],
               y=outliers['peopleCount'],
               mode='markers',
               name='Outliers',
               marker=dict(color='red', size=8)))

fig_g.update_layout(title='Overall People Count Trends with Outliers',
                    xaxis_title='Time',
                    yaxis_title='People Count')

# Dashboard part
app = dash.Dash(__name__)

# Define the layout
app.layout = html.Div(children=[
    html.H1('Adappt Intelligence Dashboard'),
    dcc.Graph(id='people-count-chart', figure=fig_a),
    dcc.Graph(id='department-wise-chart', figure=fig_b),
    dcc.Graph(id='occupancy-rate-chart', figure=fig_c),
    dcc.Graph(id='people-count-trends-chart-day', figure=fig_d),
    dcc.Graph(id='people-count-trends-chart-hour', figure=fig_e),
    dcc.Graph(id='people-count-trends-chart-over-time', figure=fig_f),
    dcc.Graph(id='outlier-chart', figure=fig_g)
])

if __name__ == '__main__':
    app.run_server(debug=True)
