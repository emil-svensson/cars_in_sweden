import pandas as pd
import numpy as np
import time
import streamlit as st
from streamlit_folium import st_folium # https://github.com/randyzwitch/streamlit-folium

import altair as alt
from altair import datum
import folium
from folium.features import DivIcon



st.set_page_config(layout="wide")



## Import files
df_county = pd.read_csv('./data/county_registrations_yearly.csv')
df_popu = pd.read_csv('./data/county_population_yearly.csv')
df_fuel = pd.read_csv('./data/fuel_type_monthly.csv')


df_county['Date'] = pd.to_datetime(df_county['Date'])
df_popu['Date'] = pd.to_datetime(df_popu['Date'])
df_fuel['Date'] = pd.to_datetime(df_fuel['Date'])


# filter out data from 2022
df_fuel = df_fuel[df_fuel['Date']<='2021-12-31']


# join population numbers to df_county
df_popu = df_popu.set_index(['County code', 'Date']).drop(columns=['County', 'Region'])
df_county = df_county.join(df_popu, on = ['County code', 'Date'], how='left')

# Add rows to df_county with all fuel types summed
gpby_list = list(df_county.columns)
gpby_list.remove('Fuel type')
gpby_list.remove('Count')
gpby_list.remove('County population')

df_county_all = pd.DataFrame(df_county.groupby(gpby_list,
                             as_index=False).agg({'Count':'sum', 'County population':'max'}))
df_county_all['Fuel type'] = 'All'
df_county = pd.concat([df_county, df_county_all], axis=0).sort_values(by=['County code', 'Date'])

# add column 'Per1000'
df_county['Per1000'] = 1000* df_county['Count']/df_county['County population']





st.sidebar.markdown("**Select one year or a range:**")



year_list = df_county['Date'].dt.year.sort_values().unique()

# def modify_year_labels(x):
#     x = "’"+ str(x)[-2:]    
#     return x

c_year = st.sidebar.select_slider('Select one year or a range:', year_list, value=[2013, 2021], 
                                help='Drag the limits on top of each other for a single year', label_visibility='collapsed')

st.sidebar.write(" ")
st.sidebar.write(" ")

c_fuel = st.sidebar.selectbox('Filter on fuel type:', ['All'] + list(df_county['Fuel type'].unique()))

st.sidebar.write(" ")
st.sidebar.write(" ")

dict_show_data_how = {'Per 1000 people':'Per1000', 'Actual':'Count'} # values are column names
ytypes = list(dict_show_data_how.keys()) # putting the key values in a list because they will be used several times later
actual_or_scaled = st.sidebar.radio('Choose how to show the data:', ytypes, index=0)
col = dict_show_data_how[actual_or_scaled]




# colorscale = px.colors.sequential.algae
colorscale = ['#bed8ec', '#a8cee5', '#8fc1de', '#74b2d7', '#5ba3cf', '#4592c6', '#3181bd', '#206fb2', '#125ca4'] # altair "blues"

def add_color(df, col, colorscale):
    colors_n = len(colorscale)

    lqval = 0.1
    uq = df[col].quantile(0.99)


    while True:
        lq = df[col].quantile(lqval)
        bin_limits = list(np.linspace(lq, uq, colors_n-1))    
        bin_limits = [0] + bin_limits[:-1] + [uq-1e-4] +[df[col].max()]

        if bin_limits[1] == 0:
            lqval += 0.01
        else:
            break
    
    df['temp'] = df[col]
    df['temp'] = df['temp'].apply(lambda x: x if x > lq else lq )
    df['temp'] = df['temp'].apply(lambda x: x if x < uq else uq )

    df['bin'] = pd.cut(df['temp'], bin_limits, labels=False)
    df['color'] = df['bin'].apply(lambda x: colorscale[x])

    df.drop(columns=['temp', 'bin'], inplace=True)

    return df, lq, uq




col1, col2 = st.columns(2)

with col1:
    # st.title("Initial car registrations in Sweden")
    st.markdown("# Initial car registrations in Sweden")

    # filter and aggregate data according to the user selected range

    sample_county = df_county.loc[(df_county['Date'].dt.year >= c_year[0]) &
                                  (df_county['Date'].dt.year <= c_year[1]) & 
                                  (df_county['Fuel type'] == c_fuel)].drop(columns='Per1000')

    sample_county_agg = sample_county.groupby('County', as_index=False
                                ).agg({'Count':'sum', 'County population':'sum'}
                                ).astype({'Count':'int32', 'County population':'int32'})

    sample_county = sample_county.drop(columns=['Count', 'County population', 'Date']
                    ).join(sample_county_agg.set_index('County'), on='County', how='left'
                    ).drop_duplicates(subset='County', ignore_index=True, keep='last')



    if c_year[1]-c_year[0] >0:
        sample_county['Year'] = str(c_year[0])+'-'+str(c_year[1])
    else:
        sample_county['Year'] = str(c_year[0])

    sample_county['Per1000'] = 1000* sample_county['Count']/sample_county['County population']
    # st.write(len(sample_county))
    # st.write(sample_county)




    sample_county, lq, uq = add_color(sample_county, col, colorscale)
    sample_county.sort_values(by=col, inplace=True)
    center_map = pd.read_csv('./data/_temp_center_map.csv', header=None) # load last position of the map center so it's not reset


    map = folium.Map(location=[center_map.iloc[0,0], 
                            center_map.iloc[0,1]],
                            zoom_start=center_map.iloc[0,2], 
                            control_scale=True,
                            tiles="cartodbpositron")
                            # tiles="cartodbdark_matter")
    

    

    text_position = [65.5, 3.7]
    folium.map.Marker(
        text_position,
        icon=DivIcon(
            icon_size=(150,36),
            icon_anchor=(0,0),
            html='<div style="font-size: 9pt"><b>Update the top right chart by selecting a county</b></div>',
            )
    ).add_to(map)



    for index, rowdata in sample_county.iterrows():
        folium.CircleMarker(
        [rowdata["County Latitude"], rowdata["County Longitude"]],
        radius=6,
        fill=True,
        tooltip = rowdata["County"] +' '+ str(round(rowdata[col],1)),
        color= rowdata['color']
        ).add_to(map)


    #
    # Print to screen
    #

    if actual_or_scaled == ytypes[0]:
        st.markdown('##### Yearly registrations per 1000 people by county', unsafe_allow_html=False)
    elif actual_or_scaled == ytypes[1]:
        st.markdown('##### Cummulative registrations by county', unsafe_allow_html=False)


    if c_fuel == 'All':
        st.markdown(f"All fuel types ({sample_county['Year'][0]}) $~~~~$ Minimum: **{round(sample_county[col].min(),1)} - {round(lq,1)}** $~~~~$ Maximum: **{round(uq,1)} - {round(sample_county[col].max(),1)}**", unsafe_allow_html=False)
    else:
        st.markdown(f"{c_fuel} ({sample_county['Year'][0]}) $~~~~$ Minimum: **{round(sample_county[col].min(),1)} - {round(lq,1)}** $~~~~$ Maximum: **{round(uq,1)} - {round(sample_county[col].max(),1)}**", unsafe_allow_html=False)

    county_selected = None
    map_selection = st_folium(map, width=650, height=520)




    # st.write(map_selection)
    st.write("""Inital car registration rates are especially high in the large city regions
    (Stockholm, Göteborg & Malmö), all located in the southern half of the country""")
    


with col2:

    df_selected_county = pd.read_csv('./data/_temp_county_data.csv')
    county_selected = df_selected_county.iloc[0]['County']


    if map_selection != None:
        if map_selection["last_object_clicked"] != None:
            lat_selected = map_selection["last_object_clicked"]["lat"]
            lng_selected = map_selection["last_object_clicked"]["lng"]
            county_selected = sample_county[(sample_county['County Latitude'] == lat_selected) & (sample_county['County Longitude'] == lng_selected)].iloc[0]['County']

            df_selected_county = df_county[df_county['County']==county_selected]
            df_selected_county.to_csv('./data/_temp_county_data.csv', index=False)
            
            center_map.iloc[0,0] = lat_selected
            center_map.iloc[0,1] = lng_selected
            zoom_level = map_selection["zoom"]
            center_map.iloc[0,2] = zoom_level
            center_map.to_csv('./data/_temp_center_map.csv', index=False, header=False)

    
    if actual_or_scaled == ytypes[0]:
        yval = 'Per1000:Q'
        yaxistitle = ytypes[0]
    elif actual_or_scaled == ytypes[1]:
        yval = 'Count:Q'
        yaxistitle = ytypes[1]
     
    linechart_one_county = alt.Chart(df_selected_county , height=250).mark_line().encode(
        alt.X('year(Date):T', axis = alt.Axis(title='')), alt.Y(yval, axis=alt.Axis(title=yaxistitle)), color='Fuel type').transform_filter(
        alt.FieldOneOfPredicate(field='Fuel type', oneOf=['Electricty', 'Electric hybrids', 'Plug-in hybrids', 'Gas', 'Diesel', 'NG', 'Ethanol']))

    st.write(" ")
    st.write(" ")
    st.markdown(f'**{county_selected}**: Yearly registrations', unsafe_allow_html=False)
    st.altair_chart(linechart_one_county.interactive(), use_container_width=True)


# Create new column with groups of fueltypes
fuel_cat = {'Diesel':'Fossil',
            'Gas':'Fossil',
            'Electricity':'Electrified',
            'Electric hybrids':'Electrified',
            'Plug-in hybrids':'Electrified',
            'Ethanol':'Other',
            'NG':'Other',
            'Others':'Other'}

df_fuel['Category'] = df_fuel['Fuel type'].apply(lambda x: fuel_cat[x])

# Add rows with all fuel types summed
df_fuel_all = pd.DataFrame(df_fuel.groupby('Date', as_index=False).agg({'Count':'sum'}))
df_fuel_all['Fuel type'] = 'All'
df_fuel_all['Category'] = 'All'
df_fuel = pd.concat([df_fuel, df_fuel_all], axis=0).sort_values(by='Date')

# pre-aggregate per category and date
df_fuel_agg = df_fuel.groupby(['Date', 'Category'], as_index=False).agg({'Count':'sum'})





# define variable yearrange based on the selected year range in the sidebar and filter data
if c_year[0] == 2013:
    yearrange = c_year[1]-2005
    df_fuel_agg = df_fuel_agg[df_fuel_agg['Date'].dt.year <= c_year[1]]
else:
    yearrange = c_year[1]-c_year[0]
    df_fuel_agg = df_fuel_agg[(df_fuel_agg['Date'].dt.year >= c_year[0]) & (df_fuel_agg['Date'].dt.year <= c_year[1])]


# change the altair x-axis aggregation based on yearrange
if yearrange >=4:
    agg_x = 'year(Date):T' # sum over years
elif (yearrange < 4) & (yearrange >=1):
    agg_x = 'yearquarter(Date):T'# sum over years and quarter
else:
    agg_x = 'Date:T' # no aggregation





with col2:

    all_categories_lines = alt.Chart(df_fuel_agg, height=250).mark_line(
    opacity=1).encode(
        alt.X(agg_x, axis = alt.Axis(title='')), alt.Y('mean(Count):Q'), color='Category').transform_filter(
        alt.FieldOneOfPredicate(field='Category', oneOf=['Electrified', 'Fossil', 'Other']))

    electrified_points = alt.Chart(df_fuel_agg).transform_filter((datum.Category =='Electrified')).mark_point(
        filled=True, size=40).encode(
        alt.X(agg_x, axis=alt.Axis(title='')), alt.Y('mean(Count):Q', axis=alt.Axis(title='Average per month')))

    grandtotal_area = alt.Chart(df_fuel_agg).transform_filter((datum.Category =='All')).mark_area(
        color='lightgray', opacity=0.2).encode(
        alt.X(agg_x, axis=alt.Axis(title='')), alt.Y('mean(Count):Q', axis=alt.Axis(title='Average per month')))

    grandtotal_line = alt.Chart(df_fuel_agg).transform_filter((datum.Category =='All')).mark_line(
    color='lightgray', opacity=0.5).encode(
    alt.X(agg_x, axis=alt.Axis(title='')), alt.Y('mean(Count):Q', axis=alt.Axis(title='Average per month')))

    fuelcategories_chart = all_categories_lines + electrified_points + grandtotal_area + grandtotal_line


    st.markdown('##### Monthly national averages (smoothed)', unsafe_allow_html=False)
    st.write("""2021 was the first year electrified cars (pure EVs, electric & plug-in hybrids) 
surpassed gas and diesel powered vehicles in terms of initial registrations. 
Over the shown 16 years, the total number of registrations per year is fluctuating significantly. 
The low in 2008 & 2009 coincides with effects of the global finacial crisis fully unravelling in Sweden.""")
    st.write(' ')
    st.write(' ')
    st.altair_chart(fuelcategories_chart.interactive(), use_container_width=True)
    st.write(' ')
