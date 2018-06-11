#-------------------------------------------------------------------------------
# Name:        HabitatMask_batch.py
# Purpose:     Automate geoprocessing tools in order to create a non-suitable
#              habitat (vector) layer and use it to mask a set of rasters
# Author:      Francesco Tonini
#
# Created:     23/01/2013
# Copyright:   (c) ftonini 2013
# Licence:     Python Software Foundation License (PSF)
# Software:    Tested successfully using Python 2.7.2 (http://www.python.org)
#-------------------------------------------------------------------------------
#!/usr/bin/env python

#STEPS:
# 1) define workspace
# 2) define local variables + all layers that contribute to the overall
#    non-suitable habitat layer
# 3) create a reference clip simulation area
# 4) project all layers to the same coord. system
# 5) selection of sub-classes/areas within chosen layers
# 6) union of all desired features
# 7) use erase function to eliminate habitat (union) from reference clip
#    simulation area
# 8) LOOP through each raster:
#       -resample (near. neighbor) down to high resolution
#       -

# Import arcpy module
import arcpy, os, sys
from arcpy import env
from arcpy.sa import *

# Check out the ArcGIS Spatial Analyst extension license
arcpy.CheckOutExtension("Spatial")

def main():

    env.workspace = 'C:\\Temp'

    #create new folder (if it does not exist already) where to store all processed layers
    newFold = 'Layers'
    newpath = os.path.join(env.workspace, 'Layers')
    if not os.path.exists(newpath): os.makedirs(newpath)

    #or r'C:\Temp' if you use a single '\' do not forget to add 'r' before the string
    #or 'C:/Temp'

    # Allow output to overwrite
    arcpy.gp.overwriteOutput = True

    # Local variables:
    Target_lyr = 'water_Broward.shp'
    Termite_loc = 'PreTreat03_NoDup2003.shp'
    LULC_lyr = 'd4_lu_gen_2010.shp'
    Roads_lyr = 'navteq_broward_streets.shp'
    TA_Multinet_lyr = 'teleatlas_broward_land_use.shp'

    #------------------------------------------------------------------------------
    #A SpatialReference can be easily created from existing datasets and PRJ files:
    #
    #(1) Use a PRJ file as an argument to the SpatialReference class:
    #prjFile = os.path.join(arcpy.GetInstallInfo()["InstallDir"],
    #                     "Coordinate Systems/Geographic Coordinate Systems/North America/NAD 1983.prj")
    #spatialRef = arcpy.SpatialReference(prjFile)
    #
    #(2) Manually define a .prj string
    #prjFile = 'PROJCS[...]'
    #spatialRef = arcpy.SpatialReference(prjFile)
    #
    #(3) Describe a dataset and access its spatialReference property:
    #TargetCS = arcpy.Describe(Water_lyr).spatialReference
    #Geographic transformation -
    #transformation = 'NAD_1983_To_WGS_1984_1'
    #If ALL FEATURES need a datum transformation OR NONE of them needs one then
    #try:
    #    res = arcpy.BatchProject_management(arcpy.ListFeatureClasses('*'), env.workspace, TargetCS, '',
    #                                       transformation) OR '' instead of transformation
    #        print 'projection of all datasets successful'
    #    else:
    #        print 'failed to project one or more datasets'
    #except:
    #    print res.getMessages()
    #------------------------------------------------------------------------------

    try:

        # Define a common target coordinate system
        desc = arcpy.Describe(Target_lyr)
        TargetSR = desc.spatialReference

        # If target layer has no projection defined print a message and stop
        if TargetSR.Name == "Unknown":

            arcpy.AddError(Target_lyr + "is used as target layer but has Unknown Projection!")
            sys.exit('Target Layer Has Unknown Projection!')

        # Use ListFeatureClasses to generate a list of inputs
        for inputFC in arcpy.ListFeatureClasses('*'):

            if inputFC != Target_lyr:

                # Strip name and extension from a feature class
                # fileName, fileExtension = os.path.splitext(inputFC)

                # Input spatial reference
                inputFC_SR = arcpy.Describe(inputFC).spatialReference

                # Determine if the input has a defined coordinate system
                if inputFC_SR.Name == "Unknown":
                    print 'Projecting ' + inputFC + '...'
                    arcpy.DefineProjection_management(inputFC, TargetSR)
                    outFC = os.path.join(newpath, inputFC)
                    # Make a copy of the current layer into the new folder
                    arcpy.CopyFeatures_management(inputFC, outFC)
                    print 'Projected ' + inputFC + ' from Unknown ' + \
                        ' to ' + TargetSR.Name

                # Check if current layer and target layer are same TYPE
                #(i.e. projected and geographic or viceversa)
                if inputFC_SR.type == TargetSR.type:

                    #SAME TYPE...Check if same projection name:

                    #CASE (1) SAME NAME..create copy and continue
                    if inputFC_SR.Name == TargetSR.Name:
                        outFC = os.path.join(newpath, inputFC)
                        arcpy.CopyFeatures_management(inputFC, outFC)
                        continue

                    #CASE (2) DIFFERENT NAME..check if SAME DATUM OR NOT
                    else:
                        # if they have different names check their datum
                        # (GCS method new in 10.1)
                        if inputFC_SR.GCS.datumName == TargetSR.GCS.datumName:
                            print 'Projecting ' + inputFC + '...'
                            # if datum are the same just project without any transformation
                            outFC = os.path.join(newpath, inputFC)
                            arcpy.Project_management(inputFC, outFC, TargetSR)
                            print 'Projected ' + inputFC + ' from ' + inputFC_SR.Name + \
                                    ' to ' + TargetSR.Name
                        else:
                            # if datum are NOT the same then get transformations
                            # available for your specific study area (based on extent)
                            print 'Projecting ' + inputFC + '...'
                            outlist = arcpy.ListTransformations(inputFC_SR, TargetSR, arcpy.Describe(inputFC).extent)
                            transformation = outlist[0]
                            outFC = os.path.join(newpath, inputFC)
                            arcpy.Project_management(inputFC, outFC, TargetSR, transformation)
                            print 'Projected ' + inputFC + ' from ' + inputFC_SR.Name + \
                                    ' to ' + TargetSR.Name + '\nDatum Transformation: ' + transformation

                else:

                    #DIFFERENT TYPE...Check if same projection name:
                    #...check if SAME DATUM OR NOT
                    #(GCS method new in 10.1)
                    if inputFC_SR.GCS.datumName == TargetSR.GCS.datumName:
                        print 'Projecting ' + inputFC + '...'
                        #if datum are the same just project without any transformation
                        outFC = os.path.join(newpath, inputFC)
                        arcpy.Project_management(inputFC, outFC, TargetSR)
                        print 'Projected ' + inputFC + ' from ' + inputFC_SR.Name + \
                                ' to ' + TargetSR.Name
                    else:
                        # if datum are NOT the same then get transformations
                        # available for your specific study area (based on extent)
                        print 'Projecting ' + inputFC + '...'
                        outlist = arcpy.ListTransformations(inputFC_SR, TargetSR, arcpy.Describe(inputFC).extent)
                        transformation = outlist[0]
                        outFC = os.path.join(newpath, inputFC)
                        arcpy.Project_management(inputFC, outFC, TargetSR, transformation)
                        print 'Projected ' + inputFC + ' from ' + inputFC_SR.Name + \
                             ' to ' + TargetSR.Name + '\nDatum Transformation: ' + transformation

            else:
                # if current layer is the same as target layer make a copy and
                #skip to next iteration
                outFC = os.path.join(newpath, inputFC)
                arcpy.CopyFeatures_management(inputFC, outFC)
                continue

            print '\n'

        #------------
        #END OF LOOP!
        #------------

        # CALCULATE CENTROID OF POINTS AND CREATE A SQUARE/RECTANGULAR CLIPPING EXTENT
        # AROUND THAT POINT
        print 'Calculating centroid of point cloud...'

        fc = os.path.join(newpath, Termite_loc)
        shapefieldname = arcpy.Describe(fc).ShapeFieldName
        # Create search cursor
        Rows = arcpy.SearchCursor(Termite_loc)

        # Initialize local variables
        X_temp = 0.0
        Y_temp = 0.0
        counter = 0

        # Enter for loop for each feature/row
        for row in Rows:
            counter = counter + 1
            # Create the geometry object 'feat'. Identify the geometry field.
            feat = row.getValue(shapefieldname)
            # Use getPart() to return an array of point objects for a particular part of the geometry
            pnt = feat.getPart()
            X_temp = X_temp + pnt.X
            Y_temp = Y_temp + pnt.Y

        # Calculate centroid of point cloud
        X_centroid = X_temp/counter
        Y_centroid = Y_temp/counter

        # Create an empty feature class from point coords
        # Set local variables
        Centroid_pnt = arcpy.Point(X_centroid, Y_centroid)
        Centroid_pntGeometry = arcpy.PointGeometry(Centroid_pnt, TargetSR)
        out_name1 = os.path.join(newpath,'Centroid_buffer.shp')
        out_name2 = os.path.join(newpath,'Centroid_buffer_sq.shp')
        # Specify desired distance
        distance = '10000 Meters'
        # Create round buffer
        print 'Creating round buffer around centroid...'
        Centroid_buffer = arcpy.Buffer_analysis(Centroid_pntGeometry, out_name1, distance)
        # Create square buffer
        print 'Creating square buffer around centroid...'
        Centroid_buffer_sq = arcpy.FeatureEnvelopeToPolygon_management(Centroid_buffer, out_name2)
        # Delete the circle buffer...no need to keep it anymore
        arcpy.Delete_management(Centroid_buffer, '')
        print '\n'

        # CLIP ALL FEATURES with the squared buffer area

        env.workspace = newpath
        # Loop through a list of feature classes in the desired folder
        for fc in arcpy.ListFeatureClasses('*'):
            if fc == 'Centroid_buffer_sq.shp' or fc == Termite_loc: continue
            # Strip name and extension from a feature class
            fileName, fileExtension = os.path.splitext(fc)
            outFC = os.path.join(newpath, fileName + '_Clip' + fileExtension)
            #Clip each input feature class in the list
            print 'Clipping ' + fc + ' to square buffer area...'
            fc_clipped = arcpy.Clip_analysis(fc, Centroid_buffer_sq, outFC, 0.01)
            #delete original...just keep clipped one
            arcpy.Delete_management(fc, '')
            # Rename the clipped file to standard name
            arcpy.Rename_management(fc_clipped, fc)

        #END OF LOOP!
        print '\n'

        #SELECT FEATURES WITH CERTAIN ATTRIBUTES OF INTEREST

        # Make a layer from the feature class (temporary layer)
        arcpy.MakeFeatureLayer_management(LULC_lyr,'LC_Agric')
        arcpy.MakeFeatureLayer_management(TA_Multinet_lyr,'TA_Airport')
        arcpy.MakeFeatureLayer_management(Roads_lyr,'NAVTEQ_buff')

        # Select only those attributes with class agricultural fields (i.e. DESCRIPT = 'AGRICULTURAL')
        print 'Selecting agricultural features from ' + LULC_lyr
        arcpy.SelectLayerByAttribute_management('LC_Agric', "NEW_SELECTION", " \"DESCRIPT\" = 'AGRICULTURAL' ")

        # Select only those attributes with feature type Airport Ground (9732) OR Airport Runway (9776)
        print 'Selecting airport ground & runway features from ' + TA_Multinet_lyr
        arcpy.SelectLayerByAttribute_management('TA_Airport', "NEW_SELECTION", " \"FEATTYP\" in (9732,9776) ")

        # Write the selected features to a new featureclass
        # Strip name and extension from a feature class
        fileName, fileExtension = os.path.splitext(LULC_lyr)
        LC_Agric = arcpy.CopyFeatures_management('LC_Agric', os.path.join(fileName + '_temp' + fileExtension))

        fileName, fileExtension = os.path.splitext(TA_Multinet_lyr)
        TA_Airport = arcpy.CopyFeatures_management('TA_Airport', os.path.join(fileName + '_temp' + fileExtension))

        # Make buffer around streets (10 m)
        fileName, fileExtension = os.path.splitext(Roads_lyr)
        linearDist = '10 Meters'
        print 'Creating buffer of ' + linearDist + ' for layer ' + Roads_lyr
        NAVTEQ_buff10 = arcpy.Buffer_analysis(Roads_lyr, os.path.join(fileName + '_temp' + fileExtension),
                                              linearDist, 'FULL', 'ROUND', 'ALL', '')

        arcpy.Delete_management(LULC_lyr, '')
        arcpy.Delete_management(TA_Multinet_lyr, '')
        arcpy.Delete_management(Roads_lyr, '')

        # Rename the clipped file to standard name
        LC_out = 'LC_Agric.shp'
        TA_out = 'TA_Airport.shp'
        NAVTQ_out = 'NAVTEQ_buff10.shp'
        Water_out = 'water_Broward.shp'
        arcpy.Rename_management(LC_Agric, 'LC_Agric.shp')
        arcpy.Rename_management(TA_Airport, 'TA_Airport.shp')
        arcpy.Rename_management(NAVTEQ_buff10, 'NAVTEQ_buff10.shp')
        print '\n'

        #UNION OF ALL SELECTED FEATURES
        print 'Creating Union of unsuitable habitat layers...'
        inFeatures = [LC_out, TA_out, NAVTQ_out, Water_out]
        outFeatures = 'UnsuitHab_Union'
        clusterTol = 0.001
        UnsuitHab_Union = arcpy.Union_analysis (inFeatures, outFeatures, "ONLY_FID", clusterTol)

        #ERASE NON-SUITABLE HABITAT UNION FROM REFERENCE CLIPPING POLYGON FEATURE
        #to have a final suitable habitat vectory layer to use as polygon mask for our rasters
        print 'Creating suitable habitat polygon mask...'
        eraseOutput = 'Habitat_mask.shp'
        xyTol = "0.1 Meters"
        arcpy.Erase_analysis(Centroid_buffer_sq, UnsuitHab_Union, eraseOutput, xyTol)
        print '\n'

        #change workspace to raster folder
        env.workspace = 'C:\\Temp\\Raster'

        #simulation years (based on rasters)
        start_yr = 2003
        end_yr = 2018
        sim_yrs = range(start_yr, end_yr + 1) #when using range remember to add 1 to the last year to include it

        #Monte Carlo envelopes
        MC_envel = [0,50,100]

        counter = 0

        #create list of labels (maybe better way to do it...but it works!)
        etiq = ['NA'] * len(sim_yrs) * len(MC_envel)
        mask_etiq = ['NA'] * len(sim_yrs) * len(MC_envel)

        for yr in sim_yrs:
            s = 'RS_' + str(yr) + '_'
            s_mask = 'Mask_' + str(yr) + '_'
            for m in MC_envel:
                s2 = str(m) + '.img'
                label = s + s2
                etiq[counter] = label
                label_mask = s_mask + s2
                mask_etiq[counter] = label_mask
                counter += 1

        etiq = sorted(etiq)
        mask_etiq = sorted(mask_etiq)

        counter = 0

        #loop through each raster in the folder
        for rast in arcpy.ListRasters('*'):

            #RESAMPLE ALL RASTERS DOWN TO 5meters (from 100m original) so that the
            #masking operation is more precise on the rasters

            # Determine the new output feature class path and name
            fileName, fileExtension = os.path.splitext(rast)
            # resampling cell size
            cell_size = '5'
            resampling_type = 'NEAREST'
            outRast = etiq[counter]
            print 'Resampling ' + rast + ' to ' + cell_size + ' meters...'
            arcpy.Resample_management(rast, outRast, cell_size, resampling_type)

            # Execute ExtractByMask
            inMaskData = os.path.join(newpath, 'Habitat_mask.shp')
            out_rast_masked = os.path.join(env.workspace, mask_etiq[counter])
            print 'Extracting ' + rast + ' by mask with ' + inMaskData + ' ...'
            outExtractByMask = ExtractByMask(outRast, inMaskData)
            # Save the output
            outExtractByMask.save(out_rast_masked)
            print 'Saved mask to ' + out_rast_masked

            counter += 1

            arcpy.Delete_management(rast, '')
            arcpy.Delete_management(outRast, '')

        #END OF LOOP!

    except arcpy.ExecuteError:
        print arcpy.GetMessages(2)
        arcpy.AddError(arcpy.GetMessages(2))
    except Exception as e:
        print e.args[0]
        arcpy.AddError(e.args[0])
        print arcpy.GetMessages()



if __name__ == '__main__':

    main()
    print 'DONE'







