import arcpy
import sys, os, math, csv

arcpy.env.overwriteOutput = True
arcpy.env.outputCoordinateSystem = arcpy.SpatialReference(3857)

def Encode(x):
    """Encodes values into 'utf-8' format"""
    if isinstance(x, unicode):
        return x.encode("utf-8", 'ignore')
    else:
        return str(x)

def ExcludeFields(table, types=[]):
    """Return a list of fields minus those with specified field types"""
    fieldNames = []
    fds = arcpy.ListFields(table)
    for f in fds:
        if f.type not in types:
            fieldNames.append(f.name)
    return fieldNames

def ExportToCSV(fc, output):
    """Export Data to a CSV file"""
    # create the output writer
    f = open(output, 'wb')
    outWriter = csv.writer(f, dialect='excel')

    excludeTypes = ['Geometry', 'OID']
    excludeTypes = []
    fields = ExcludeFields(fc, excludeTypes)

    # Create Search Cursor: the following only works with ArcGIS 10.1+
    with arcpy.da.SearchCursor(fc, fields) as cursor:
        outWriter.writerow(cursor.fields)
        for row in cursor:
            row = [v.decode('utf8') if isinstance(v, str) else v for v in row]
            outWriter.writerow([unicode(s).encode("utf-8") for s in row])
    del row, cursor

    # Close opened file
    f.close()


def calc_CO2_emissions():

    # Get the value of the input parameter
    inputFC = arcpy.GetParameterAsText(0)  # Polyline feature class
    flow_units = arcpy.GetParameterAsText(1) # Field from input FC representing number of transportation units transferred
    capacity_per_trip = arcpy.GetParameter(2) # Transportation capacity (transport units per trip)
    CO2_emission = arcpy.GetParameter(3)  # Amount of CO2 emission (kg/unit)

    # Local variable:
    out_flows_CO2_fc = os.path.join(arcpy.env.scratchGDB,"CO2Emissions_fc")
    out_CO2_Name = "CO2 Emissions"	
	
    try:

        #Create feature class from copy of input feature layer 
        arcpy.AddMessage('Creating Feature Class from Input Feature Layer ...')
        arcpy.SetProgressorLabel('Creating Feature Class from Input Feature Layer ...')
        arcpy.CopyFeatures_management(inputFC, out_flows_CO2_fc)
				
        ### ADD FIELD: creating new field to store CO2 total emission per trip ###
        arcpy.AddMessage('Adding CO2 Emission Field to Feature Class ...')
        arcpy.SetProgressorLabel('Adding CO2 Emission Field to Feature Class ...')
        # add new CO2 emission field
        arcpy.AddField_management(in_table=out_flows_CO2_fc, field_name="CO2_EMISSIONS_KG", field_type="LONG")

        ### CALCULATE FIELD: creating new field to store CO2 total emission per trip ###
        arcpy.AddMessage('Calculating CO2 Emissions for Each Flow Line ...')
        arcpy.SetProgressorLabel('Calculating CO2 Emissions for Each Flow Line ...')
        tot_emissions = 0        
		## Is there a field in the input feature layer representing quantity of flows? 
		## If not, assign a default value == 1 to the flow as units.
        if flow_units != '':	
		    #Check user input to make sure the transport units field specified matches one of the attributes of the inputFC
            fieldnames = [f.name for f in arcpy.ListFields(out_flows_CO2_fc)]
            if flow_units.capitalize() not in fieldnames and flow_units.upper() not in fieldnames:
                arcpy.AddError("ERROR: The chosen transportation units attribute does not exist in the input layer!")
                raise arcpy.ExecuteError
           
            cursor = arcpy.da.UpdateCursor(out_flows_CO2_fc, ['SHAPE@LENGTH', fieldnames[fieldnames.index(flow_units)], 'CO2_EMISSIONS_KG'])
            for row in cursor:
                if row[1] is None or str(row[1]).upper() == "n/a" or str(row[1]).upper() == r"n\a" or str(row[1]).upper() == "NA":			
                    continue 
                else:
                    total_trips = math.ceil(float(row[1])/capacity_per_trip)
                    #SHAPE@LENGTH will be likely in meters (depending on coordinate system)
                    row[2] = row[0] * total_trips * CO2_emission
                    tot_emissions += row[2]
                    cursor.updateRow(row)
            
            #Export feature layer to CSV##
            arcpy.AddMessage('Exporting Flows CO2 Emissions Layer to CSV Table ...')
            outTable_CSV = os.path.join(arcpy.env.scratchFolder, "CO2_Emission_Table.csv")
            ExportToCSV(fc=out_flows_CO2_fc, output=outTable_CSV)			

        #arcpy.AddMessage('Writing Total Estimated CO2 to Output Report File ...')
        #arcpy.SetProgressorLabel('Writing Total Estimated CO2 to Output Report File ...')
        #out_txt = os.path.join(arcpy.env.scratchFolder,"CO2_Report.txt")	
        #file = open(out_txt,"w") 	
        #file.write("The current scenario produces a total estimated amount of released CO2 equal to: " + #str(tot_emissions) + " kilograms")		
        #file.close() 
        #arcpy.AddMessage("The current scenario produces a total estimated amount of released CO2 equal to: " + str(tot_emissions) + " kilograms")

    	# Process: Create a feature layer from the joined feature class to send back as output to GP tools
        out_fl = arcpy.MakeFeatureLayer_management(out_flows_CO2_fc, out_CO2_Name)   
        
		#### Set Parameters ####    
        arcpy.SetParameter(4, out_fl)
        #arcpy.SetParameter(5, out_txt)
        arcpy.SetParameter(5, outTable_CSV)

    except Exception:
        e = sys.exc_info()[1]
        arcpy.AddError('An error occurred: {}'.format(e.args[0]))


if __name__ == '__main__':
    outFC = calc_CO2_emissions()