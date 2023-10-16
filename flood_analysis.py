import arcpy
import os
import time
import rasterio
import matplotlib.pyplot as plt

#SET VARIABLES BEFORE RUNNING
project_path = r"D:\OneDrive - VEI\portfolio_projects\arcpy"
output_path = r"D:\OneDrive - VEI\portfolio_projects\arcpy\outputfiles"
geodatabase_name = "geodatabase1"
aoi_path = r"D:\OneDrive - VEI\portfolio_projects\arcpy\files\study_area.shp"
dem_path = r"D:\OneDrive - VEI\portfolio_projects\arcpy\files\full_dem.tif"
land_cover_path = r"D:\OneDrive - VEI\portfolio_projects\arcpy\files\land_cover.tif"

start_time = time.time()

#CREATE A GEODATABASE
try:
    arcpy.management.CreateFileGDB(f"{project_path}", f"{geodatabase_name}", "CURRENT")
    geodatabase_path = f"{project_path}\\{geodatabase_name}.gdb"
    print(geodatabase_path)
    print(f"{geodatabase_name} created")
except:
    print("Failed to create geodatabase")

def save_tif(input_path, output_name):
    arcpy.management.CopyRaster(input_path, f"{output_path}//{output_name}.tif", '', None, "0", 
        "NONE", "NONE", '', "NONE", "NONE", "TIFF", "NONE", "CURRENT_SLICE", "NO_TRANSPOSE")

def display_raster(file_name, color):
    path = r"D:\OneDrive - VEI\portfolio_projects\arcpy\outputfiles"
    path = f"{path}\\{file_name}.tif"
    data = rasterio.open(path).read(1)
    cmap = plt.cm.get_cmap(color, 10)
    # Display the data using matplotlib
    plt.figure(figsize=(8, 8))
    plt.imshow(data, cmap=cmap)
    plt.title(file_name)
    plt.colorbar()
    plt.show()

#DEM EXTRACTION
try:
    out_raster = arcpy.sa.ExtractByMask(dem_path, aoi_path, "INSIDE"); 
    out_raster.save(f"{geodatabase_path}\\dem_aoi")
    dem_aoi_path = f"{geodatabase_path}\\dem_aoi"
    print("DEM extraction completed")

except:
    print("Failed to extract DEM")

#LAND COVER EXTRACTION
try:
    out_raster = arcpy.sa.ExtractByMask(land_cover_path, aoi_path, "INSIDE"); 
    out_raster.save(f"{geodatabase_path}\\land_cover_aoi")
    land_cover_aoi_path = f"{geodatabase_path}\\land_cover_aoi"
    print("Land Cover extraction completed")

    save_tif(land_cover_aoi_path, "land_cover_aoi")
    print("Land cover file has been saved")
    print("Displaying raster image of Land Cover")
    try:
        display_raster("land_cover_aoi","turbo")
    except:
        print("Failed to display Land Cover")
except:
    print("Failed to extract Land Cover")

#SLOPE ANALYSIS
try:
    out_raster = arcpy.sa.Slope(dem_aoi_path, "DEGREE", 1, "PLANAR", "METER"); 
    out_raster.save(f"{geodatabase_path}\\slope_aoi")
    slope_aoi_path = f"{geodatabase_path}\\slope_aoi"
    print("Slope analysis completed")

    save_tif(slope_aoi_path, "slope_aoi")
    print("Slope analysis file has been saved")
    print("Displaying raster image of Slope analysis")
    try:
        display_raster("slope_aoi","rainbow")
    except:
        print("Failed to display slope analysis")
except:
    print("Slope analysis failed")

#DEM FILL(DEPRESSION LESS DEM)
try:
    out_surface_raster = arcpy.sa.Fill(dem_aoi_path, None); 
    out_surface_raster.save(f"{geodatabase_path}\\dem_aoi_fill")
    dem_aoi_fill_path = f"{geodatabase_path}\\dem_aoi_fill"
    print("Depression less DEM has been created")
except:
    print("DEM fill process failed")

#FLOW DIRECTION
try:
    out_flow_direction_raster = arcpy.sa.FlowDirection(dem_aoi_fill_path, "NORMAL", None, "D8"); 
    out_flow_direction_raster.save(f"{geodatabase_path}\\flow_direction")
    flow_direction_path = f"{geodatabase_path}\\flow_direction"
    print("Flow direction has been calculated")
except:
    print("Flow direction calculation failed")

#FLOW ACCUMULATION
try:
    out_accumulation_raster = arcpy.sa.FlowAccumulation(flow_direction_path, None, "FLOAT", "D8"); 
    out_accumulation_raster.save(f"{geodatabase_path}\\flow_accumulation")
    flow_accumulation_path = f"{geodatabase_path}\\flow_accumulation"
    print("Flow accumulation has been calculated")
except:
    print("Failed to calculated flow accumulation")

#STREAMS DELINEATION
try:
    max = arcpy.GetRasterProperties_management(flow_accumulation_path, "MAXIMUM")
    max = float(max.getOutput(0))
    threshold = max * .1

    range = f"0 {threshold} NODATA;{threshold} {max} 1"

    out_raster = arcpy.sa.Reclassify(flow_accumulation_path, "VALUE", range, "NODATA"); 
    out_raster.save(f"{geodatabase_path}\\streams")
    streams_path = f"{geodatabase_path}\\streams"
    print("Streams have been extracted")

    save_tif(streams_path, "streams")
    print("Stream file has been saved")
    print("Displaying raster image of Streams")
    try:
        display_raster("streams","turbo")
    except:
        print("Failed to display streams")
except:
    print("Stream extraction failed")

#EUCLIDEAN DISTANCE
try:
    with arcpy.EnvManager(mask=aoi_path):
        out_distance_raster = arcpy.sa.EucDistance(streams_path, None, 0.000277777777777786, None, "GEODESIC", None, None); 
        out_distance_raster.save(f"{geodatabase_path}\\euclidean")
        euclidean_path = f"{geodatabase_path}\\euclidean"
        print("Euclidean distances from streams have been calculated")

        save_tif(euclidean_path, "euclidean")
        print("Euclidean distance file has been saved")
        print("Displaying raster image of Euclidean distance")
        try:
            display_raster("euclidean","turbo")
        except:
            print("Failed to display euclidean distance raster")
except:
    print("Euclidean distance calculation failed")

#PERFORM RECLASSIFICATION ACCORDING TO YOUR AOI
#DEM RECLASSIFICATION
try:
    out_raster = arcpy.sa.Reclassify(dem_aoi_path, "Value", "-46 6 10;6 9 8;9 13 6;13 17 4;17 55 2", "NODATA"); 
    out_raster.save(f"{geodatabase_path}\\reclass_dem_aoi")
    reclass_dem_aoi_path = f"{geodatabase_path}\\reclass_dem_aoi"
    print("DEM has been reclassified")

    save_tif(reclass_dem_aoi_path, "reclass_dem_aoi")
    print("Reclassified DEM file has been saved")
    print("Displaying Reclassified DEM")
    try:
        display_raster("reclass_dem_aoi","turbo")
    except:
        print("Failed to display Reclassified DEM")
except:
    print("DEM Reclassification failed")

#SLOPE RECLASSIFICATION
try:
    out_raster = arcpy.sa.Reclassify(slope_aoi_path, "VALUE", "0 2 10;2 5 8;5 10 6;10 20 4;20 39.750427 2", "NODATA"); 
    out_raster.save(f"{geodatabase_path}\\reclass_slope_aoi")
    reclass_slope_aoi_path = f"{geodatabase_path}\\reclass_slope_aoi"
    print("Slope analysis has been reclassified")

    save_tif(reclass_slope_aoi_path, "reclass_slope_aoi")
    print("Reclassified Slope file has been saved")
    print("Displaying Reclassified Slope")
    try:
        display_raster("reclass_slope_aoi","turbo")
    except:
        print("Failed to display Reclassified Slope")
except:
    print("Slope Reclassification failed")


#LAND COVER RECLASSIFICATION
try:
    out_raster = arcpy.sa.Reclassify(land_cover_aoi_path, "N_L2", "'Mine, Dump and Construction Sites' 4;'Industrial, Commercial, Public, Military, Private and Transport Units' 2;'Urban Fabric' 2;'Other Natural and Semi-natural Areas (Savannah, Grassland)' 8;'Agricultural Area' 8;'Artificial non-agricultural vegetated areas' 6;'Inland Water' 10", "NODATA"); 
    out_raster.save(f"{geodatabase_path}\\reclass_land_cover_aoi")
    reclass_land_cover_aoi_path = f"{geodatabase_path}\\reclass_land_cover_aoi"
    print("Land cover has been reclassified")

    save_tif(reclass_land_cover_aoi_path, "reclass_land_cover_aoi")
    print("Reclassified Land Cover has been saved")
    print("Displaying reclassified Land Cover")
    try:
        display_raster("reclass_land_cover_aoi","turbo")
    except:
        print("Failed to display Reclassified Land Cover")
except:
    print("Land Cover Reclassification failed")

#EUCLIDEAN DISTANCE RECLASSIFICATION
try:
    out_raster = arcpy.sa.Reclassify(euclidean_path, "VALUE", "0 744.653872 10;744.653872 1557.003550 8;1557.003550 2369.353228 6;2369.353228 3429.920864 4;3429.920864 5754.143555 2", "NODATA"); 
    out_raster.save(f"{geodatabase_path}\\reclass_euclidean_aoi")
    reclass_euclidean_aoi_path = f"{geodatabase_path}\\reclass_euclidean_aoi"
    print("Euclidean Distances have been reclassified")

    save_tif(reclass_euclidean_aoi_path, "reclass_euclidean_aoi")
    print("Reclassified Euclidean Distances have been saved")
    print("Displaying Reclassified Euclidean Distance")
    try:
        display_raster("reclass_euclidean_aoi","turbo")
    except:
        print("Failed to display Reclassified Euclidean Distance")
except:
    print("Euclidean Distance Reclassification failed")

#WEIGHTED SUM
try:
    out_raster = arcpy.ia.WeightedSum(f"{reclass_dem_aoi_path} Value 0.3;{reclass_slope_aoi_path} Value 0.2;{reclass_euclidean_aoi_path} Value 0.3;{reclass_land_cover_aoi_path} Value 0.2"); 
    out_raster.save(f"{geodatabase_path}\\weighted_sum")
    weighted_sum_path = f"{geodatabase_path}\\weighted_sum"
    print("Weighted Sum calculation completed")

    save_tif(weighted_sum_path, "weighted_sum")
    print("Weighted Sum file has been saved")
    print("Displaying raster image Weighted Sum")
    try:
        display_raster("weighted_sum","turbo")
    except:
        print("Failed to display Weighted Sum")
except:
    print("Weighted Sum calculation has been failed")

#RECLASSIFY WEIGHTED SUM 
try:
    out_raster = arcpy.sa.Reclassify(weighted_sum_path, "VALUE", "2.800000 4.804706 1;4.804706 5.792941 2;5.792941 6.809412 3;6.809412 8.192941 4;8.192941 10 5", "DATA"); 
    out_raster.save(f"{geodatabase_path}\\reclass_weighted_sum")
    reclass_weighted_sum_path = f"{geodatabase_path}\\reclass_weighted_sum"
    print("Weighted Sum has been reclassfied")

    save_tif(reclass_weighted_sum_path, "reclass_weighted_sum")
    print("Reclassified Weighted Sum file has been saved")
    print("Displaying Reclassified Weighted Sum")
    try:
        display_raster("reclass_weighted_sum","turbo")
    except:
        print("Failed to display Reclassified Weighted Sum")

except:
    print("Weighted sum reclassification failed")

#ATTRIBUTE FILL
try:
    arcpy.management.AddField(reclass_weighted_sum_path, "risk", "TEXT")
    print("Risk field added to attribute table")
    try:
        value_to_risk = {
            1: 'Low Risk',
            2: 'Moderate Risk',
            3: 'High Risk',
            4: 'Very High Risk',
            5: 'Extreme Risk'
        }
        with arcpy.da.UpdateCursor(reclass_weighted_sum_path, ['Value', 'risk']) as cursor:
            for row in cursor:
                value = row[0]
                risk = value_to_risk.get(value)
                if risk:
                    row[1] = risk
                    cursor.updateRow(row)
        del cursor
        print ("Risk values have been added to attribute table")
    except:
        print("Failed to add risk values to attribute table")
except:
    print("Failed to add risk field to attribute table")

print("Flood analysis completed!")
print(f"Time elapsed: {time.time()-start_time}")





    
    





