#!/bin/csh -f
# This script pulls down the CAMD hourly CEMS emissions from api.epa.gov
# The year to pull down is specified after -y and the output path after -o
# The API key appears after -a. Please acquire and enter an API key from api.epa.gov

get_camd_cems_bulk -y 2021 -o ./2021_CEMS -a "YOURAPIKEY"

