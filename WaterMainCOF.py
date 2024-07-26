import arcpy
import pandas as pd
from arcgis.features import GeoAccessor, GeoSeriesAccessor
import os
from datetime import datetime
import numpy as np
from sklearn.cluster import KMeans
from arcgis.gis import GIS
import yaml

# sign into arcgis online with user credentials
# Load credentials from CityLogins.yaml
with open("../CityLogins.yaml", "r") as file:
    config = yaml.safe_load(file)

# Function to get GIS object from city name
def get_gis(city_name):
    city_config = config['cities'][city_name]
    url = city_config['url']
    username = city_config['username']
    password = city_config['password']
    gis = GIS(url, username, password)
    return gis

# Define your User
user = 'Abonmarche'

# Connect to GIS
user_gis = get_gis(user)

# variables
dir_path = os.getcwd()
workspace = r"memory"
arcpy.env.workspace = workspace
arcpy.env.overwriteOutput = True
arcpy.env.maintainAttachments = False
dir_path = os.getcwd()

# User Variables *keep them in this order*
results_folder = r"C:\Users\ggarcia\OneDrive - Abonmarche\Documents\GitHub\Utility-System-Risk\AlleganResults"
feature_services = [
    ("WaterMain", "https://services6.arcgis.com/o5a9nldztUcivksS/arcgis/rest/services/Allegan_Water/FeatureServer/6"),
    ("WaterLaterals", "https://services6.arcgis.com/o5a9nldztUcivksS/arcgis/rest/services/Allegan_Water/FeatureServer/4"),
    ("CriticalCustomers", "https://services6.arcgis.com/o5a9nldztUcivksS/arcgis/rest/services/Allegan_2024_Working_Analysis2/FeatureServer/1"),
    ("SchoolChildcare", "https://services6.arcgis.com/o5a9nldztUcivksS/arcgis/rest/services/Allegan_2024_Working_Analysis2/FeatureServer/2"),
    ("Healthcare", "https://services6.arcgis.com/o5a9nldztUcivksS/arcgis/rest/services/Allegan_2024_Working_Analysis2/FeatureServer/3"),
    ("Roadway", "https://services6.arcgis.com/o5a9nldztUcivksS/arcgis/rest/services/Allegan_2024_Working_Analysis2/FeatureServer/4"),
    ("Buildings", "https://services6.arcgis.com/o5a9nldztUcivksS/arcgis/rest/services/Allegan_2024_Working_Analysis2/FeatureServer/5"),
    ("WaterLines", "https://services6.arcgis.com/o5a9nldztUcivksS/arcgis/rest/services/Allegan_2024_Working_Analysis2/FeatureServer/6"),
    ("WaterAreas", "https://services6.arcgis.com/o5a9nldztUcivksS/arcgis/rest/services/Allegan_2024_Working_Analysis2/FeatureServer/7"),
    ("ROW", "https://services6.arcgis.com/o5a9nldztUcivksS/arcgis/rest/services/Allegan_2024_Working_Analysis2/FeatureServer/8"),
    ("Parcels", "https://services6.arcgis.com/o5a9nldztUcivksS/arcgis/rest/services/Allegan_2024_Working_Analysis2/FeatureServer/9"),
    ("isozones", "https://services6.arcgis.com/o5a9nldztUcivksS/arcgis/rest/services/Allegan_IsoZone/FeatureServer/0")
]

# New variable to store a list of static features to analyze
features_to_analyze = ["Buildings", "ROW", "WaterAreas", "WaterLines"]

# water main fields
UniqueID = "FACILITYID"
InstallDate = "PLACEDINSE"
Material = "MATERIAL"
Diameter = "DIAMETER"

# roadway values
RoadwayType = "Road"
MajorRoad = "Major Road"
MinorRoad = "Minor Road"
MajorIntersection = "Major Intersection"
MinorIntersection = "Minor Intersection"

# Export each feature service to a feature class
for fc_name, url in feature_services:
    arcpy.conversion.ExportFeatures(url, fc_name)

# list feature classes
# feature_classes = arcpy.ListFeatureClasses()
# feature_classes

# split the Roadway feature class by the RoadwayType field
arcpy.analysis.SplitByAttributes(feature_services[5][0], workspace, RoadwayType)

# Function to replace spaces with underscores
def format_feature_class_name(name):
    return name.replace(" ", "_")

# List of road feature classes to use in near analysis
near_feature_classes = [
    format_feature_class_name(MajorRoad),
    format_feature_class_name(MajorIntersection),
    format_feature_class_name(MinorIntersection),
    format_feature_class_name(MinorRoad)
]

# Add other static feature classes
near_feature_classes.extend(features_to_analyze)

water_main = feature_services[0][0]
columns = ["OBJECTID", UniqueID, InstallDate, Material, Diameter]
# make a water main dataframe with just the columns
water_main_df = pd.DataFrame.spatial.from_featureclass(water_main)
# drop any column not in columns
water_main_df = water_main_df.drop(columns=[col for col in water_main_df.columns if col not in columns])
# water_main_df.head()

# function to generate near table with distances from each main to the analysis features
# water main is the main feature class to analyze, near_feature_classes is a list of feature classes to analyze, and results_folder is the folder path to save the results
def generate_near_table(water_main, near_feature_classes, results_folder):
    # Dictionary to store the dataframes
    dfs = {}
    # Iterate over the feature classes
    for fc in near_feature_classes:
        # Create the output path
        output_path = os.path.join(results_folder, "near_" + fc + ".csv")
        # Near analysis
        near_table = arcpy.analysis.GenerateNearTable(
            in_features=water_main,
            near_features=fc,
            out_table=output_path,
            search_radius="10000 Feet",
            location="NO_LOCATION",
            angle="NO_ANGLE",
            closest="CLOSEST",
            closest_count="0",
            method="PLANAR",
            distance_unit="Feet")

        # Convert near table csv to dataframe
        near_df = pd.read_csv(output_path)

        # remove the out_table
        os.remove(output_path)
        # remove the .xml, .ini, and .csv.xml files the geoprocess also created
        for file in os.listdir(results_folder):
            if file.endswith(".xml") or file.endswith(".ini"):
                os.remove(os.path.join(results_folder, file))

        # rename the column in the near_df from NEAR_DIST to the name of the feature class
        near_df.rename(columns={'NEAR_DIST': fc}, inplace=True)
        # drop the columns OBJECTID and NEAR_FID
        near_df = near_df.drop(columns=['NEAR_FID'])

        # Add the dataframe to the dictionary
        dfs[fc] = near_df

    # Initialize Near_results_df with the first dataframe in dfs
    Near_results_df = next(iter(dfs.values()))

    # Merge the dataframes with the Near_results_df removing the IN_FID column each time
    for key, value in list(dfs.items())[1:]:
        Near_results_df = pd.merge(Near_results_df, value, left_on='IN_FID', right_on='IN_FID', how='left')

    return Near_results_df

# run the generate_near_table function and merge the water_main_df with the Near_results_df
Near_results_df = generate_near_table(water_main, near_feature_classes, results_folder)
# merge the water_main_df with the Near_results_df
Near_results_df = pd.merge(water_main_df, Near_results_df, left_on='OBJECTID', right_on='IN_FID', how='left')
# Drop the IN_FID column after the merge
Near_results_df = Near_results_df.drop(columns=['IN_FID'])

# Save the Near_results_df to a csv file using dir_path
# Near_results_df.to_csv(os.path.join(results_folder, "NearResults.csv"), index=False)

# Affected customer analysis
def affected_customer_analysis(isolation_zones_fc, lateral_lines_fc, results_folder):
    # Spatial join laterals to isozones one to many so there is a row for each lateral in the iso zone
    zones_lats_join = "zones_lats_join"
    arcpy.analysis.SpatialJoin(
        target_features=isolation_zones_fc,
        join_features=lateral_lines_fc,
        out_feature_class=zones_lats_join,
        join_operation="JOIN_ONE_TO_MANY",
        join_type="KEEP_COMMON",
        match_option="INTERSECT",
    )

    # Summarize the join results
    summary_output = os.path.join(results_folder, "zone_lat_summary.csv")
    arcpy.analysis.Statistics(
        in_table=zones_lats_join,
        out_table=summary_output,
        statistics_fields="OBJECTID COUNT",
        case_field="zone",
    )

    # Convert the summary table to a dataframe
    summary_df = pd.read_csv(summary_output)

    # remove the out_table
    os.remove(summary_output)

    # Remove the .xml, .ini, and .csv.xml files the geoprocess also created
    for file in os.listdir(results_folder):
        if file.endswith(".xml") or file.endswith(".ini"):
            os.remove(os.path.join(results_folder, file))
    
    return summary_df

isolation_zones_fc = feature_services[-1][0]
lateral_lines_fc = feature_services[1][0]
summary_df = affected_customer_analysis(isolation_zones_fc, lateral_lines_fc, results_folder)

# add a spatial join to the water main feature class to get the isolation zones into the water mains
main_iso_join = "main_iso_join"
arcpy.analysis.SpatialJoin(
    target_features=water_main,
    join_features=isolation_zones_fc,
    out_feature_class=main_iso_join,
    join_operation="JOIN_ONE_TO_ONE",
    join_type="KEEP_ALL",
    match_option="LARGEST_OVERLAP"
)
# Convert the feature class to a dataframe
mains_iso_df = pd.DataFrame.spatial.from_featureclass(main_iso_join)
# keep only fields zone and the unique id variable field
mains_iso_df = mains_iso_df[[UniqueID, "zone"]]
#  use the summary df as a key to add a column to the mains_iso_df for affected laterals and fill it with the count of laterals in the isolation zone
mains_iso_df['affected_lats'] = mains_iso_df['zone'].map(summary_df.set_index('zone')['FREQUENCY'])
# merge the mains_iso_df with the Near_results_df
mains_iso_df = pd.merge(Near_results_df, mains_iso_df, left_on=UniqueID, right_on=UniqueID, how='left')

# affected critical customers