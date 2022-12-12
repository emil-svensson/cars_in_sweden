# Inital car registrations in sweden
This repo contains the python code for a [streamlit app](https://emil-svensson-cars-in-sweden-app-5h4066.streamlit.app) with dynamic visualizations. 
The data was collected from: www.trafa.se (car registrations), www.scb.se (population numbers) & www.geonames.org (geographical data)


### Interacting with the app
The main visualisation is the map showing the average number of car registrations in each county by color. This is **yearly data**.  Lighter blue -> fewer registrations, darker blue -> more registrations. In the left sidebar the user can choose a range of years (or a single year). A specific fuel type can be chosen or the default setting "All" can be kept. The map connects to the top right chart which shows registrations by fuel type for all years for one selected county. 

The third chart (bottom right) uses a different data source with **monthly** data. However, it is filtered based on the user selected year range and it aggregates the monthly data differently based on how long the selected range is. All different fuel types have been binned into 3 categories: fossil, electrified and other.


### to-do list
- The map update behavior is not working as intended. More experimentation/thought has to go into making it be persistent as the user interacts with the app.
- The note on the map should always be visible, not referencing a static lat. & lng.
- Annotations on the right hand side charts could be useful and allow for a more consistent color-scheme
- Axis labels are too numerous. Fixing this in altair doesn't seem possible since string values cannot be set manually (my understanding).
- Additional filters could be introduced to show only a subset of counties based on user specified values
- The map should be changed to choropleth style, this requires cleaning of geojson files with polygons
- The user should have the option to show aggregated data on a region level too
