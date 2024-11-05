import pandas as pd
import altair as alt
import geopandas as gpd


def acled_base_data(acled):
    '''
    Imports the acled data from the local data file.

    Does a number of data-cleaning functions on the ACLED Data, including:
        - Removes non-violent events
        - adds a month indicator from date
        - Does a flip
    
    Returns a Pandas dataframe of the cleaned data.
    '''
    #acled = pd.read_csv("../data/acled_2023.csv")

    # Non-violent event removal from Event types and event subtypes
    acled = acled[acled["event_type"] != "Protests"]
    acled = acled[acled["sub_event_type"] != "Headquarters or base established"]
    acled = acled[acled["sub_event_type"] != "Other"]
    acled = acled[acled["sub_event_type"] != "Change to group/activity"]
    acled = acled[acled["sub_event_type"] != "Agreement"]
    acled = acled[acled["sub_event_type"] != "Non-violent transfer of territory"]

    #Datetime Conversion
    acled["date"] = pd.to_datetime(acled["event_date"])

    return acled

def small_big_split(df):
    '''
    Splits events data into the major media coverage ones (big) and the less covered ones (small)
    Returns both sets as pandas dataframes.
    '''
    small = df[df["country"] != "Ukraine"]
    small = small[small["country"] != "Palestine"]
    small = small[small["country"] != "Israel"]
    small = small[small["country"] != "Russia"]
    small = small[small["country"] != "Lebanon"]
    small["conflict_size"] = "Rest of the World" 

    ukr = df[df["country"] == "Ukraine"]
    pal = df[df["country"] == "Palestine"]
    isr = df[df["country"] == "Israel"]
    rus = df[df["country"] == "Russia"]
    leb = df[df["country"] == "Lebanon"]

    #Tagging Ukraine-related countries
    ukr_rus = pd.concat([ukr, rus])
    ukr_rus["conflict_size"] = "Ukraine/Russia"

    #Tagging Palestine-related countries
    isr_pal = pd.concat([isr, pal, leb])
    isr_pal["conflict_size"] = "Palestine"

    big = pd.concat([ukr_rus, isr_pal])

    rejoined_violence = pd.concat([small, big])

    return small, big, rejoined_violence

def top_k_countries(df, k):

    top_k = df["country"].value_counts()
    top_k = top_k.reset_index()
    top_country = top_k["country"][0:k]
    filtered_df = df[df["country"].isin(top_country)]

    return filtered_df

def top_k_countries_map(gdf, df, k):

    top_k = df["country"].value_counts()
    top_k = top_k.reset_index()
    top_country = top_k["country"][0:k]
    filtered_df = gdf[gdf["name"].isin(top_country)]

    return filtered_df

def map_merger(df):

    countries = gpd.read_file("../data/worldmap.geojson")
    country_counts = df["country"].value_counts()

    # Adds population numbers from a csv to the map data
    populations = pd.read_csv("../data/population.csv", encoding = "ISO-8859-1")
    add2 = countries.merge(populations, 'left',left_on='name',right_on='Country')
    add2['pop'] = add2['Population'].fillna(0)

    #Migration ###s insert
    migration = pd.read_csv("../data/migration.csv", encoding = "ISO-8859-1")
    migration["Country"] = migration["Country"].str[1:]
    add2 = add2.merge(migration, 'left',left_on='name',right_on='Country')
    add2['Net Migration'] = add2['Net Migration'].fillna(0)
    add2['NM per 1000'] = add2['NM per 1000'].fillna(0)

    # Adds count of civilans impacted
    civilian_series = df.groupby('country', as_index=False)['population_best'].sum()
    add2 = add2.merge(civilian_series, 'left',left_on='name',right_on='country')
    add2['population_best'] = add2['population_best'].fillna(0)

    # Adds the count of events in each country for the Choropleth map
    addup = add2.merge(country_counts, 'left',left_on='name',right_on='country')
    addup['count'] = addup['count'].fillna(0)

    #Makes a variable adjusting event count for population
    addup["vpcap100k"] = (addup['count'] * 100000)/addup["pop"]
    addup["vpcap100k"] = addup["vpcap100k"].fillna(0)

    return addup