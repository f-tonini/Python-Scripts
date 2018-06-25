# Import all necessary module dependencies
import arcpy, os, sys

arcpy.env.overwriteOutput = True
arcpy.env.outputCoordinateSystem = arcpy.SpatialReference(3857)

def DrawRadialFlows():

    # Get the value of the input parameter
    inTable = arcpy.GetParameterAsText(0)
    startX_field = arcpy.GetParameterAsText(1)
    startY_field = arcpy.GetParameterAsText(2)
    endX_field = arcpy.GetParameterAsText(3)
    endY_field = arcpy.GetParameterAsText(4)
    id_field = arcpy.GetParameterAsText(5)
    flow_amnt = arcpy.GetParameterAsText(6)
    lineType_str = arcpy.GetParameterAsText(7)
    wkid = arcpy.GetParameter(8)
    # Try to assign the spatial reference by using the Well-Known ID for the input
    try:
        spRef = arcpy.SpatialReference(int(wkid))    
    except:
    # If the SR cannot be created, assume 4326
        arcpy.AddWarning("Problem creating the spatial reference!! Assumed to be WGS84 (wkid: 4326)")
        spRef = arcpy.SpatialReference(4326)
		
    # Local variable:
    out_flows_fc = r"in_memory\FlowsLineXY"
    out_tbl = r"in_memory\tmpTable"
    out_Name = "Telecoupling Flows"	
	
    if inTable and inTable != "#":

        try:
            # XY To Line
            arcpy.AddMessage('Creating Radial Flow Lines from Input File ...')
            arcpy.SetProgressorLabel('Creating Radial Flow Lines from Input File ...')
            if id_field and flow_amnt:
                arcpy.XYToLine_management(in_table=inTable, out_featureclass=out_flows_fc,
                                          startx_field=startX_field, starty_field=startY_field,
                                          endx_field=endX_field, endy_field=endY_field,
                                          line_type=lineType_str, id_field=id_field, spatial_reference=spRef)

                arcpy.CopyRows_management(inTable, out_tbl)
                ## JOIN output flows with attribute from input table
                arcpy.JoinField_management(out_flows_fc, id_field, out_tbl, id_field, flow_amnt)

			# Process: Create a feature layer from the joined feature class to send back as output to GP tools
            out_fl = arcpy.MakeFeatureLayer_management(out_flows_fc, out_Name)    

            # Send string of (derived) output parameters back to the tool
            arcpy.SetParameter(9, out_fl)

        except Exception:
            e = sys.exc_info()[1]
            arcpy.AddError('An error occurred: {}'.format(e.args[0]))


if __name__ == '__main__':
    DrawRadialFlows()