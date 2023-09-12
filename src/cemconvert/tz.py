import pandas as pd
import os.path

class TZ:
    '''
    Timezone related functions
    FIPS to timezone file in data/county_fips_tz.csv
    '''

    def __init__(self):
        '''
        Load the county FIPS timezone table
        tzname are the standard timezone names
        lst_offset is the offset from UTC in local standard time (LST)
        '''
        tz_fn = os.path.join(os.path.dirname(__file__), 'data', 'county_fips_tz.csv')
        self.tbl = pd.read_csv(tz_fn, 
                               usecols=['region_cd','tzname','lst_offset'], 
                               dtype={'region_cd': str})

    def fips_to_unit(self, oris_fips):
        '''
        Reset the table so it converts ORIS unit IDs to tz
        '''
        self.tbl = self.tbl.merge(oris_fips, on='region_cd', how='left')
        self.tbl = self.tbl[['oris_facility_code','oris_boiler_id','tzname','lst_offset']].copy()

    def timeshift_to_gmt(self, df):
        '''
        Shift from local standard time (LST) to UTC using lst_offset
        '''
        df = df.merge(self.tbl, on=['oris_facility_code','oris_boiler_id'], how='left')
        for lst_offset in list(df.lst_offset.drop_duplicates()):
            idx = df.lst_offset == lst_offset
            df.loc[idx, 'date'] = df.loc[idx, 'date'] - pd.Timedelta(lst_offset, 'h')
        df.drop(['tzname','lst_offset'], axis=1, inplace=True)
        # Shift the date format back to df from object (date - timedelta)
        df['date'] = pd.to_datetime(df.date)
        return df

    def timeshift_to_gmt_dst(self, df):
        '''
        Shift from local time with DST adjustments to GMT 
        CAMPD CEMS are in local standard time so this function is currently not in use
        I'm holding it here in case CEMS ever move from LST to DST
        '''
        df = df.merge(self.tbl, on=['oris_facility_code','oris_boiler_id'], how='left')
        # Loop over timezones in DS. There won't be many. Unfortunately pd doesn't support setting from another field
        df_aware = pd.DataFrame()
        # Cannot mix tz-naive and tz-aware values so I have to create a new df 
        for tzname in list(df.tzname.drop_duplicates()):
            tzdf = df[df.tzname == tzname].copy()
            tzdf.date = tzdf.date.dt.tz_localize(tzname, nonexistent='NaT', 
              ambiguous='NaT').dt.tz_convert('UTC').dt.tz_localize(None)
            df_aware = pd.concat((df_aware, tzdf))
        # Drop DST leap hour
        df = df_aware[df_aware.date.notnull()].copy()
        df.drop(['tzname','lst_offset'], axis=1, inplace=True)
        return df


