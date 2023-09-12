import os.path
import pandas as pd

class CEM:
    '''
    Functions related to CEM format processing
    '''

    def __init__(self):
        # Columns to read in. Use exactly these column names as specified by CAMD.
        self.cemcols = ['Facility ID','Unit ID','Date','Hour','Gross Load (MW)',
          'Steam Load (1000 lb/hr)','SO2 Mass (lbs)','CO2 Mass (short tons)','Heat Input (mmBtu)',
          'SO2 Mass Measure Indicator','NOx Mass Measure Indicator','CO2 Mass Measure Indicator',
          'Operating Time','NOx Rate (lbs/mmBtu)','NOx Rate Measure Indicator','NOx Mass (lbs)',
          'Heat Input Measure Indicator']
        # CEM column to a shortened column name
        self.colmap = {'Facility ID': 'oris_facility_code', 'Unit ID': 'oris_boiler_id',
          'Date': 'date', 'Gross Load (MW)': 'GLOAD', 'Steam Load (1000 lb/hr)': 'SLOAD', 
          'Heat Input (mmBtu)': 'HTINPUT','SO2 Mass (lbs)': 'SO2', 'CO2 Mass (short tons)': 'CO2', 
          'SO2 Mass Measure Indicator': 'SO2MEAS', 'NOx Mass (lbs)': 'NOX',
          'NOx Mass Measure Indicator': 'NOXMEAS','CO2 Mass Measure Indicator': 'CO2MEAS',
          'Operating Time': 'OPTIME', 'NOx Rate (lbs/mmBtu)': 'noxrate', 
          'NOx Rate Measure Indicator': 'noxrmeasure', 'Hour': 'hour', 
          'Heat Input Measure Indicator': 'HIMEAS'}
        # Value columns from the CEM file to set as values in the resulting pivot 
        self.valcols = ['GLOAD','SLOAD','HTINPUT','SO2','CO2','NOX','OPTIME']#,'SO2MEAS','NOXMEAS','CO2MEAS']
        # Measurement names to integer codes
        self.measxref = {'Measured': 1, 'Calculated': 2, 'Substitute': 3,
          'Measured and Substitute': 4, 'LME': 5, 'Other': 6}
        # Old CEM columns
        self.oldcem = ['oris_facility_code','oris_boiler_id','date','hour','NOX','SO2','noxrate',
         'OPTIME','GLOAD','SLOAD','HTINPUT','htinputmeas','SO2MEAS','NOXMEAS','noxrmeasure','flow']
        # List of months names used in the CEMS monthly file
        self.months = ('jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec')
        # Initialize the dataframe to hold the hourly values for the period
        self.hourly = pd.DataFrame()

    def set_measure_codes(self, df):
        '''
        Set the measurement string to an integer for cemcorrect
        '''
        for col in ['SO2MEAS','NOXMEAS','CO2MEAS','noxrmeasure','HIMEAS']:
            df[col] = df[col].replace(to_replace=self.measxref).fillna(0).astype(int)
        return df

    def load_cems_period(self, input_path, year, period):
        '''
        Load in the CAMPD CEMS monthly files of hourly values
        period is a list of months as integers
        ''' 
        for n in period:
            month = self.months[n-1]
            print('Processing %s' %month, flush=True)
            # Read in CAMPD CEM inputs
            fn = os.path.join(input_path, 'campd-%s-%s-hourly.txt' %(year, month))
            self.hourly = pd.concat((self.hourly, self.read_cems_month(fn)))

    def read_cems_month(self, fn):
        '''
        Read in the monthly CEM hourly values and return a dataframe
        '''
        dtype = {'Facility ID': str, 'Unit ID': str, 'SO2 Mass Measure Indicator': str,
          'NOx Mass Measure Indicator': str, 'CO2 Mass Measure Indicator': str,
          'NOx Rate Measure Indicator': str, 'Heat Input Measure Indicator': str}
        df = pd.read_csv(fn, usecols=self.cemcols, dtype=dtype)
        # Rename columns to shorten names and fit formats
        df.rename(columns=self.colmap, inplace=True)
        df['date'] = pd.to_datetime(df.date + ' ' + df.hour.astype(str).str.zfill(2), format='%Y-%m-%d %H')
        df['month'] = df.date.dt.month.astype(int).astype(str)
        df = self.set_measure_codes(df)
        dupes = df.duplicated(['oris_facility_code','oris_boiler_id','date','hour'], keep=False)
        if len(df[dupes]) > 0:
            raise ValueError('Duplicate ORIS/Date/Hour combinations found in CEMS')
        print('Records read: %s  NOX sum (lb): %s' %(len(df), sum(df['NOX'].fillna(0).round(6))))
        return df

    def write_old_cems(self, output_path, year, period):
        '''
        Write the old format CEMS for the period
        '''
        for mon in period:
            # Write out old CEM format
            fn = os.path.join(output_path, 'HOUR_UNIT_%s_%0.2d.txt' %(year, mon))
            idx = (self.hourly.date.dt.year.astype(int) == int(year)) &\
              (self.hourly.date.dt.month.astype(int) == mon)
            self.write_old_cems_month(fn, self.hourly[idx])

    def format_old_cems(self, df):
        '''
        Format to the old CEMs format by month and export the dataframe
        '''
        # Heat input measure code and unit flow not available in new format
        #  Neither are used by SMOKE
        df['htinputmeas'] = ''
        df['flow'] = '-9'
        cems = df[self.oldcem].copy()
        cems['hour'] = cems['hour'].astype(int)
        cems['date'] = cems['date'].dt.strftime('%y%m%d').astype(int)
        valcols = ['NOX','SO2','noxrate','GLOAD','SLOAD','HTINPUT']
        for col in valcols:
            cems[col] = cems[col].fillna(-9).round(4).astype(str)
            cems.loc[cems[col] == '-9.0', col] = '-9'
        return cems

    def write_old_cems_month(self, fn, monthly):
        ''''
        Format the old CEMs and write to an output file
        '''
        # Format to the old CEMs format and write the monthly file
        cems = self.format_old_cems(monthly.copy())
        cems.to_csv(fn, index=False, header=False)

    def pivot_hourly(self, df):
        '''
        Pivot the hourly data out to columns by hour
        '''
        idx = ['oris_facility_code','oris_boiler_id','date']
        # Update the pollutant values from lbs->tons
        for col in ['SO2','NOX']:
            df[col] = df[col] / 2000
        df['hour'] = 'hrval' + df['hour'].astype(int).astype(str)
        df = df[idx+self.valcols+['hour',]].copy()
        # Melt down the pollutant names
        df = pd.melt(df, id_vars=idx+['hour',], value_vars=self.valcols, var_name='poll', 
          value_name='val')
        df = pd.pivot_table(df, values='val', columns='hour', index=idx+['poll',], aggfunc='sum')
        df.reset_index(inplace=True)
        hours = ['hrval%s' %hr for hr in range(24)]
        # Fill in hour columns that may be missing
        for hour in hours:
            if hour not in list(df.columns):
                df[hour] = None
        df[hours] = df[hours].fillna(0).round(4)
        df['daytot'] = df[hours].fillna(0).sum(axis=1).round(4)
        print('Records postpivot: %s  NOX sum (lb): %s' %(len(df), 
          sum(df.loc[df['poll'] == 'NOX', 'daytot'].fillna(0).round(6)) * 2000))
        # Drop daily records that are 0 for every hour
        return df[df['daytot'] > 0].copy()

