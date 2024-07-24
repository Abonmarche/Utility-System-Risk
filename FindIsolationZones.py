import arcpy

# Set the workspace - change this to your actual workspace
arcpy.env.workspace = r"Place Feature Database Path Here"
trace_network = r"Place Trace Network Path Here"
water_mains_fc = "Place Water Main Layer Name Here"
water_valves_fc = "Place Water Valve Layer Name Here"

#This function will create individual in memory points in the center of each of the features
#Inputs: The feature line (An individual feature), The point name or objectid for the point
#Returns: The given point feature for the line
def create_in_memory_point(input_line_layer, point_name):
    #Generate a point at the center of the input line layer
    in_memory_point = arcpy.management.FeatureToPoint(input_line_layer, f"in_memory/{point_name}", "INSIDE")
    return in_memory_point

#This function will run the trace function for the program for the given input parameters
#Input: The starting point for the trace, The layer that has all water mains stored within it (I.E water_mains_fc)
#Returns a trace feature layer that stores the geometry for the traced item
def perform_trace(start_point_feature, barrier_layer):
    #Will generate a trace line that is multi-point.
    arcpy.tn.Trace(
        in_trace_network=trace_network,
        trace_type="CONNECTED",
        starting_points=start_point_feature,
        barriers=barrier_layer,
        path_direction="NO_DIRECTION",
        shortest_path_network_attribute_name="",
        include_barriers="INCLUDE_BARRIERS",
        validate_consistency="VALIDATE_CONSISTENCY",
        ignore_barriers_at_starting_points="DO_NOT_IGNORE_BARRIERS_AT_STARTING_POINTS",
        allow_indeterminate_flow="IGNORE_INDETERMINATE_FLOW",
        condition_barriers=None,
        function_barriers=None,
        traversability_scope="BOTH_JUNCTIONS_AND_EDGES",
        functions=None,
        output_conditions=None,
        result_types="AGGREGATED_GEOMETRY",
        selection_type="NEW_SELECTION",
        clear_all_previous_trace_results="CLEAR_ALL_PREVIOUS_TRACE_RESULTS",
        trace_name="trace",
        aggregated_points="Trace_Points",
        aggregated_lines="Trace_Lines",
        out_network_layer=None,
        use_trace_config="DO_NOT_USE_TRACE_CONFIGURATION",
        trace_config_name="",
        out_json_file=None
    )

def main():
    #Creates the spatial reference of a layer because the created layer require that information
    spatial_ref = arcpy.Describe(water_mains_fc).spatialReference
    #This will create an Isolation Zone Layer and will store all of the data into this layer once the program ends
    iso_zone_fc = "IsoZone"
    arcpy.CreateFeatureclass_management(arcpy.env.workspace, iso_zone_fc, "POLYLINE", spatial_reference=spatial_ref)
    arcpy.env.overwriteOutput = True

    # add a text field called zone to the iso zone feature class
    arcpy.AddField_management(iso_zone_fc, "zone", "TEXT")
    #Will create a centroid layer that will have the center of each of the lines such that we can start traces
    centroids = arcpy.FeatureVerticesToPoints_management(water_mains_fc, "Water_Centroids","MID")

    #Creates a storage layer so that we can only test points that are un-used
    UsedPoints = []
    count = 0
    #Will run through every point in the centroid layer that was created
    with arcpy.da.SearchCursor(centroids, ["OID@", "SHAPE@"]) as centroid:
        for row in centroid:
            #Will check to see if the point had been checked already
            if row[0] not in UsedPoints:
                count = count + 1
                #Will preform a trace on the point
                perform_trace(row[1], water_valves_fc)
                #Will place the feature in the feature storage
                arcpy.Append_management("Trace_Lines", iso_zone_fc, "NO_TEST")\
                #Will identify all points that are on the trace
                Storage_Values = arcpy.management.SelectLayerByLocation("Water_Centroids", "INTERSECT", "Trace_Lines", 0, "NEW_SELECTION")
                #Will place all points in the used points list to ensure that none of them are checked again
                with arcpy.da.SearchCursor(Storage_Values, ["OID@", "SHAPE@"]) as removePoint:
                    for row in removePoint:
                        UsedPoints.append(row[0])
    arcpy.Delete_management("memory")
    print(count)

if __name__ == "__main__":
    main()