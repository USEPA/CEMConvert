# cemconvert
Tool for converting Continuous Emissions Monitoring Systems (CEMS) hourly data to hourly flat file (FF10) and scaling annual FF10 to CEMS values.

The cemconvert tool can prepare annual and hourly emissions inventories integrated with CEMS emissions and heat input data for both base and future year scenarios. Cemconvert optionally integrates the CEMCorrect algorithms (https://github.com/CEMPD/cemcorrect) for adjusting anomalous values in the CEMS. 

# Install
Recent versions are available from pypi. To install from pip run:<br>
<i>pip install cemconvert</i><br><br>
To install from github source clone or download this repository and run:<br>
<i>python setup.py sdist</i><br>
<i>pip install dist/cemconvert_VERSION.tar.gz</i>

# Usage
cemconvert [options] egu_annual_ff10

Options:<br>
&nbsp;&nbsp;-h, --help            show this help message and exit<br>
&nbsp;&nbsp;-p CEMPOLLS, --cempolls=CEMPOLLS<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;List of pollutants in hourly CEM files to process<br>
&nbsp;&nbsp;-y YEAR, --year=YEAR  Year to process<br>
&nbsp;&nbsp;-i INPUT_PATH, --input_path=INPUT_PATH<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Hourly CEM input path<br>
&nbsp;&nbsp;-o OUTPUT_PATH, --output_path=OUTPUT_PATH<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;FF10 inventory output path<br>
&nbsp;&nbsp;-c, --write_cems      Write hourly CEM data in old SMOKE format<br>
&nbsp;&nbsp;-g, --gmt             Output hourly FF10 to GMT instead of local time<br>
&nbsp;&nbsp;-r, --ramp_up         Timeshift hours for the year after the designated year<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;back one year<br>
&nbsp;&nbsp;-t TEMPORALVAR, --temporal_var=TEMPORALVAR<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Variable name used for temporal activity<br>
&nbsp;&nbsp;-n CALCPOLLS, --inven_polls=CALCPOLLS<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;List of inventory pollutants to temporalize using the<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;CEM activity<br>
&nbsp;&nbsp;-m MONTHS, --months=MONTHS<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;List of CEM months to process as a comma-delimited<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;list of integers            Default behavior is an<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;annual run<br>
&nbsp;&nbsp;-l LABEL, --label=LABEL<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Output inventory label<br>
&nbsp;&nbsp;-k, --keep_annual     Keep and temporalize annual temporal values in FF10<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;that match CEMs.            Default is to replace the<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;emissions values with CEMs.<br>
&nbsp;&nbsp;-e, --cemcorrect      Apply CEMCorrect to the CEMS<br>

# Examples

Download annual 2021 CEMS from CAMPD bulk download site using provided download tool:<br>
get_camd_cems_bulk -y 2021 -o ./cems/2021 -a "YOURAPIKEY"<br>

An API key is required to retrieve CEMS using the download tools in this pacakge. The API key can be requested using the form on the CAMPD data website:<br>
https://www.epa.gov/power-sector/cam-api-portal#/api-key-signup

Example 1. Generate 2021 base year EGU inventories from annual 2021 FF10 and 2021 CEMS for SMOKE with CEMCorrect<br>
cemconvert -y 2021 -i ./cems/2021 -o ./output -g -n PM25-PRI -l 2021_egu_2021cems -e ptegu_2021_annual_FF10.csv

Example 2. Generate 2032 summer season EGU inventories from annual 2032 FF10 and 2021 CEMS for SMOKE with CEMCorrect. Scale hourly CEMS values to 2032 values.<br>
cemconvert -y 2032 -i ./cems/2021 -o ./output -g -n PM25-PRI -m "5,6,7,8,9" -e -k -l 2032_egu_2021cems ptegu_2032_annual_FF10.csv

Example 3. Convert 2021 CEMS from new format to old and apply CEMCorrect<br>
cemconvert -y 2021 -i ./cems/2021 -o ./output -c -e ptegu_2021_annual_FF10.csv

Contact: beidler.james@epa.gov for assistance with this project

Disclaimer: The United States Environmental Protection Agency (EPA) GitHub project code is provided on an "as is" basis and the user assumes responsibility for its use. EPA has relinquished control of the information and no longer has responsibility to protect the integrity, confidentiality, or availability of the information. Any reference to specific commercial products, processes, or services by service mark, trademark, manufacturer, or otherwise, does not constitute or imply their endorsement, recommendation or favoring by EPA. The EPA seal and logo shall not be used in any manner to imply endorsement of any commercial product or activity by EPA or the United States Government. 
