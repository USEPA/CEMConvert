# Misc processes

import os.path
import pandas as pd
from cemconvert.cem import CEM
from cemconvert.cemcorrect import CemCorrect

def proc_hourly(opts, tz):
    '''
    Read in the hourly CEM values by month in the new format
    Write to the old format
    Return a pivoted version
    '''
    cems = CEM()
    cems.load_cems_period(opts.input_path, opts.year, opts.months)
    # Run CEMCorrect
    if opts.cemcorrect:
        correct = CemCorrect()
        # Start by calculating the means of the non-flagged values
        for col in correct.valcols:
            correct.calc_mean(col, cems.hourly)
        # Correct the heat input
        cems.hourly = correct.fill_mean('HTINPUT', cems.hourly)
        # Correct the mass values
        for col in correct.valcols:
            if col != 'HTINPUT':
                correct.calc_rate(col, cems.hourly)
                cems.hourly = correct.fill_rate(col, cems.hourly)
        fn = os.path.join(opts.output_path, 'cemcorrect_qa_%s_%s.csv' %(opts.label, opts.year))
        correct.write_qa(fn)
    cems.write_old_cems(opts.input_path, opts.year, opts.months)
    # Timeshift hourly FF10 to GMT
    if opts.gmt_output:
        cems.hourly = tz.timeshift_to_gmt(cems.hourly)
    # Extract the hour into the hour column and reset the date
    cems.hourly['hour'] = cems.hourly.date.dt.hour.astype(int)
    cems.hourly['date'] = cems.hourly.date.dt.normalize()
    # Pivot the hourly values to columns
    cems.hourly = cems.pivot_hourly(cems.hourly)
    if opts.gmt_output and opts.ramp_up:
        cems.hourly = fill_ramp_up(cems.hourly, opts.year)
    idx = ['oris_facility_code','oris_boiler_id','date','poll']
    cems.hourly = cems.hourly.groupby(idx, as_index=False).sum()
    cems.hourly['month'] = cems.hourly.date.dt.month.astype(int).astype(str)
    return cems.hourly

def gapfill_dates(df, year):
    '''
    Gapfill the dates by unit/poll combo to have all dates for every month in the run
    '''
    cols = list(df.columns)
    # Find all the dates for the selected months
    months = list(df.date.dt.month.astype(int).sort_values().drop_duplicates())
    fdays = [pd.to_datetime(f'{m} {year}', format='%m %Y') for m in months]
    ranges = [pd.date_range(start=d, periods=d.daysinmonth, freq='D').to_series() for d in fdays]
    # Define a datetimeindex of all of the days
    days = pd.DatetimeIndex(pd.concat(ranges))
    df = set_key(df)
    # Define the unit/poll info for each key
    keyids = df.reset_index()[['key','oris_facility_code','oris_boiler_id','poll']].drop_duplicates()
    df.set_index([df.index, 'date'], inplace=True)
    idx = pd.MultiIndex.from_product([df.index.get_level_values(0).unique(), days])
    # Reindex by the key/date range combo
    df = df.reindex(idx)
    df.reset_index(inplace=True)
    df.rename(columns={'level_0': 'key', 'level_1': 'date'}, inplace=True)
    df = df.merge(keyids, on='key', how='left', suffixes=['_o',''])
    df['month'] = df['date'].dt.month.astype(int).astype(str)
    df[['daytot',]+['hrval%s' %x for x in range(24)]] = df[['daytot',]+['hrval%s' %x for x in range(24)]].fillna(0)
    return df[cols].copy()

def fill_ramp_up(df, year):
    '''
    Fill the annual ramp-up by shifting the hours after the base year back one year
    '''
    days_in_year = pd.Timestamp(int(year), 12, 31).dayofyear
    idx = df.date.dt.year.astype(int) == int(year) + 1
    df.loc[idx, 'date'] = df.loc[idx, 'date'] - pd.Timedelta(value=days_in_year, unit='days')
    return df

def proc_hourly_meta(hourlymth, fips, sccs):
    '''
    Add in fips and sccs, write files, merge in NOX, SO2, and CO2 into annual FF10 --  
     update and write
    '''
    hourlymth.reset_index(inplace=True)
    hourlymth = hourlymth.merge(fips, on='facility_id', how='left')
    hourlymth = hourlymth.merge(sccs, on=['unit_id','process_id'], how='left')
    #hourlymth = hourlymth[hourlymth['daytot'].fillna(0) > 0].copy()
    hourlymth[hourlymth['region_cd'].isnull()].to_csv('nullfips.csv', index=False)
    hourlymth['date'] = hourlymth['date'].dt.strftime('%Y%m%d')
    return hourlymth[hourlymth['region_cd'].notnull()].copy()

def set_key(df, cols=['oris_facility_code','oris_boiler_id','poll']):
    '''
    Set the ORIS - poll key index
    '''
    for col in cols:
        df[col] = df[col].fillna('').astype(str).str.strip()
    df['key'] = df[cols].agg('_'.join, axis=1)
    df.set_index('key', inplace=True)
    return df.copy()

def scale_hourly(hourly, monemis):
    '''
    Scale the hourly values to the monthly values from the annual FF10
    '''
    hrcols = list(hourly.columns)
    # Roll the hourly up to monthly
    idx = ['oris_facility_code','oris_boiler_id','poll','month']
    hrmonth = hourly[idx+['daytot',]].reset_index().groupby(idx, as_index=False).sum()
    unitfac = monemis.merge(hrmonth, on=idx, how='left')
    # Calculate a unit monthly factor for CEMs to annual FF10
    unitfac['scalar'] = unitfac['montot'].fillna(0)/unitfac['daytot'].fillna(0)
    hourly = hourly.merge(unitfac[idx+['scalar',]], on=idx, how='left')
    print(list(hourly.columns))
    valcols = ['daytot',]+['hrval%s' %hr for hr in range(24)]
    hourly[valcols] = hourly[valcols].fillna(0).multiply(hourly['scalar'].fillna(0), axis=0)
    return hourly[hrcols].copy()


