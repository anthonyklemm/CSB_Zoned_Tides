# CSB_Zoned_Tides
This script automates the tide correction of crowdsourced bathymetry (CSB) files (in JSON format) downloaded from the Internation Hydrographic Organization's (IHO) Data Centre for Digital Bathymetry Crowdsourced Bathymetry Database (https://maps.ngdc.noaa.gov/viewers/iho_dcdb/). 

When you download the CSB Data, it comes all nested in a bunch of *.tar.gz files.... I use 7zip from the command line to do some recursive extraction for the json files, but I'm sure there is a fancy way in python to do it... just don't know how. 

Here is the cmd command I use for 7zip: 

FOR /R "E:\csb\json\port arthur\" %I IN (*.tar.gz) DO "C:\Program Files\7-Zip\7z.exe" x "%I" -r -aoa -o"%~dpI"

Just change your working directory. Might have to use it a few times since they are all nested so deep in the directory. 

A dependency is an ESRI polygon shapefile with the discrete zoned tides corrector data. 

This script determines the zoned tide reference stations by performing an initial spatial join with the unprocessed CSB (in json format). It then downloads the vereified waterlevel data from the CO-OPS tide reference stations using the CO-OPS datagetter API.

It then corrects the verified waterlevel data based on the magnitude correction coefficient and time offset, and applies the corrected waterlevels to the data to create depths referenced to MLLW. 

The output is an ESRI point shapefile. Positions are in crs EPSG 4326 (WGS84). 


