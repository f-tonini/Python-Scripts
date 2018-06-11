#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      ftonini
#
# Created:     31/07/2013
# Copyright:   (c) ftonini 2013
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#!/usr/bin/env python

# Import arcpy module
import arcpy, os, sys
from arcpy import env
from arcpy.sa import *

# Check out the ArcGIS Spatial Analyst extension license
arcpy.CheckOutExtension("Spatial")

def main():

    env.workspace = r'G:\University\University of Florida\PhD Research\Niche Models\GIS Layers\Climatic Data\Climate Change Projections\la_florida_data\A2\ukmo\prec_tifs'
    #create new folder (if it does not exist already) where to store all processed layers
    newFold = 'Projected'
    newpath = os.path.join(env.workspace, newFold)
    if not os.path.exists(newpath): os.makedirs(newpath)

    # Allow output to overwrite
    arcpy.gp.overwriteOutput = True

    # Local variables:
    Target_lyr = 'apr_prec_proj.tif'

    try:

        # Define a common target coordinate system
        desc = arcpy.Describe(Target_lyr)
        TargetSR = desc.spatialReference

        # Use ListRasters to generate a list of inputs
        for ras in arcpy.ListRasters('*',"TIF"):

            if ras != Target_lyr:

                # Input spatial reference
                ras_SR = arcpy.Describe(ras).spatialReference

                print 'Projecting ' + ras + '...'
                #if datum are the same just project without any transformation
                outRast = os.path.join(newpath, ras)
                arcpy.ProjectRaster_management(ras, outRast, TargetSR, "BILINEAR","#","#","#","#")
                print 'Projected ' + ras + ' from ' + ras_SR.Name + \
                           ' to ' + TargetSR.Name
            else:continue

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
