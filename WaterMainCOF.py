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

# User Variables
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
    #("isozones", "https://services6.arcgis.com")
]

# water main fields
UniqueID = "FACILITYID"
InstallDate = "PLACEDINSE"
Material = "MATERIAL"

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
#feature_classes = arcpy.ListFeatureClasses()
#feature_classes

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
near_feature_classes.extend(["Buildings", "ROW", "WaterAreas", "WaterLines"])

water_main = feature_services[0][0]
columns = [UniqueID, InstallDate, Material]

# Dictionary to store the dataframes
dfs = {}
# Iterate over the feature classes
for fc in near_feature_classes:
    # Create the output path
    output_path = os.path.join(results_folder, "near_" + fc + ".csv")
    # Near analysis
    near_table = arcpy.GenerateNearTable_analysis(
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

    # remove the .xml, .ini, and .csv.xml files the geoprocess also created
    for file in os.listdir(results_folder):
        if file.endswith(".xml") or file.endswith(".ini"):
            os.remove(os.path.join(results_folder, file))

    # rename the column in the near_df from NEAR_DIST to the name of the feature class
    near_df.rename(columns = {'NEAR_DIST': fc}, inplace = True)
    # drop the columns OBJECTID and NEAR_FID
    near_df = near_df.drop(columns=['NEAR_FID'])

    # Add the dataframe to the dictionary
    dfs[fc] = near_df

# Merge the dataframes with the Near_results_df removing the IN_FID column each time
for key, value in dfs.items():
    Near_results_df = pd.merge(Near_results_df, value, left_on='OBJECTID', right_on='IN_FID', how='left')
    Near_results_df = Near_results_df.drop(columns=['IN_FID'])

Near_results_df.head()
# save the Near_results_df to a csv file using dir_path
Near_results_df.to_csv(os.path.join(dir_path, "Results", "NearResults.csv"), index=False)