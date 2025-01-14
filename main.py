import geopandas as gpd
import pandas as pd
import folium
from folium.plugins import HeatMap
import branca
import os
import plotly.graph_objs as go
import plotly.express as px
import plotly.io as pio

# Load GeoJSON file
geo_data = gpd.read_file("provinces.geojson")

# Load financial data
finance_data = pd.read_csv("finance_data.csv")

# Merge datasets
geo_data = geo_data.merge(finance_data, left_on="name", right_on="Region")  # Adjust "name" to match your GeoJSON

# Ensure all columns are JSON-serializable

# Create a base map centered on Canada
m = folium.Map(location=[56.1304, -106.3468], zoom_start=4)

# Create a color scale for choropleth
colormap = branca.colormap.linear.YlGnBu_09.scale(geo_data["Investment"].min(), geo_data["Investment"].max())

# Add a choropleth map for investments
choropleth = folium.Choropleth(
    geo_data=geo_data,
    data=geo_data,
    columns=["Region", "Investment"],
    key_on="feature.properties.name",  # Adjust if your GeoJSON key differs
    fill_color="YlGnBu",
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name="Investment Levels ($)",
    highlight=True,
    nan_fill_color="white"
).add_to(m)

# Apply the color scale to style regions dynamically
def style_function(feature):
    investment = feature["properties"]["Investment"]
    return {
        "fillColor": colormap(investment),
        "color": "black",
        "weight": 1,
        "dashArray": "5, 5",
        "fillOpacity": 0.6,
    }

folium.GeoJson(
    geo_data,
    style_function=style_function,
    tooltip=folium.GeoJsonTooltip(fields=["Region"], aliases=["Province:"]),
).add_to(m)

# Add heatmap for dense investment regions
heat_data = [
    [row.geometry.centroid.y, row.geometry.centroid.x, row["Investment"]]
    for _, row in geo_data.iterrows()
    if not pd.isnull(row["Investment"])
]
HeatMap(heat_data, radius=15).add_to(m)

# Define the generate_chart function to create a Plotly chart for each region
def generate_chart(region_name):
    # Filter the data for the given region
    region_data = finance_data[finance_data["Region"] == region_name]

    # Create an interactive plotly chart for the region's investment over time
    fig = go.Figure()

    fig.add_trace(go.Scatter(x=region_data['Year'], y=region_data['Investment'], mode='lines+markers', name='Investment'))

    # Add labels and title
    fig.update_layout(
        title=f"Investment Over Time: {region_name}",
        xaxis_title='Year',
        yaxis_title='Investment ($)',
        template='plotly_dark',
    )

    # Convert the figure to an HTML string to embed in the popup
    chart_html = pio.to_html(fig, full_html=False)

    # Return the HTML for the chart
    return chart_html

# Add markers with popups and dynamic HTML
for _, row in geo_data.iterrows():
    # Generate the chart for each region
    chart_html = generate_chart(row['Region'])
    
    # Create HTML content for each popup with the generated chart
    popup_content = f"""
    <div>
        <b>{row['Region']}</b><br>
        Investment: ${row['Investment']}<br>
        Income: ${row['Income']}<br>
        {chart_html}<br>
    </div>
    """
    
    # Create the popup with dynamic content
    popup = folium.Popup(popup_content, max_width="100%")
    
    # Add the marker and bind the popup
    folium.Marker(
        location=[row.geometry.centroid.y, row.geometry.centroid.x],
        popup=popup
    ).add_to(m)

# Save the map to an HTML file
m.save("interactive_geospatial_finance_map_with_charts.html")
print("Interactive map saved as interactive_geospatial_finance_map_with_charts.html")
