#!/bin/csh -f
# This script applies hourly CEMS emissions to an annual FF10
#   For units matched between the CEMS and the annual FF10 NOX, SO2, and CO2 values are replaced in the annual file
#     Hourly values are written for the NOX, SO2, and CO2. By default annual PM2.5 is temporalized to hourly.
#     Units are matched on ORIS facility and boiler IDs. Matches are only made when the field is properly populated in the annual FF10.

# Path to EGU annual FF10. This is usually a subset of the point selection where the IPM_YN is not null.
set inv = egu_SmokeFlatFile_POINT_20230430.csv
# Label to give the output inventory files
set label = 2021_2021cems
# Year to process. In most cases this will be the same as the CEMS year
set year = 2021

# This runs the script, reading in the monthly CEMS files from the path after -i and writing the inventories to the path after -o
# The "-e" flag applies the cemcorrect algorithm to all outputs and the "-g" flag outputs the hourly FF10 values in GMT rather than local time
# GMT is required if running a scenario through SMOKE that includes the DST transition dates 
cemconvert $inv -l $label -i ./${year}_CEMS -o ./output -y $year -e -g

