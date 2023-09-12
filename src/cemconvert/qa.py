import os.path
import pandas as pd

def write_annual_qa(fn, annual, ann_ff10, temporalvar):
    '''
    Write the QA of the annual inventory
    '''
    idx = ['facility_id','unit_id','oris_facility_code','oris_boiler_id','poll']
    month_vals = ['jan_value','feb_value','mar_value','apr_value','may_value','jun_value',
      'jul_value','aug_value','sep_value','oct_value','nov_value','dec_value']
    annual['monthsum'] = annual[month_vals].fillna(0).sum(axis=1).round(6)
    outunit = annual[idx+['ann_value','monthsum']].groupby(idx, as_index=False).sum()
    inunit = ann_ff10[idx+['ann_value',]].groupby(idx, as_index=False).sum()
    qa = pd.merge(inunit, outunit, on=idx, how='outer', suffixes=['_in','_out'])
    qa = qa[qa['poll'] != temporalvar].copy()
    qa['diff'] = (qa['ann_value_out'].fillna(0) - qa['ann_value_in'].fillna(0)).round(4)
    qa['absolute_pctdiff'] = (abs(qa['diff']/qa['ann_value_in'].fillna(0)) * 100).round(2)
    qa[['ann_value_in','ann_value_out']] = qa[['ann_value_in','ann_value_out']].round(6)
    qa.to_csv(fn, index=False)

def write_hourly_qa(hourly, hourlymth, opts):
    '''
    Write the hourly QA of the CEM data
    '''
    month = int(hourlymth['month'].drop_duplicates().values[0])
    fn = os.path.join(opts.output_path, 
      'qa_pthour_%0.2d_%s_%s.csv' %(month, opts.year, opts.label))
    idx = ['oris_facility_code','oris_boiler_id','month','poll']
    inunit = hourly.loc[hourly['month'] == month, idx+['ann_value',]].groupby(idx, 
      as_index=False).sum()
    outunit = hourlymth.loc[hourlymth['month'] == month, idx+['ann_value',]].groupby(idx, 
      as_index=False).sum()
    qa = pd.merge(inunit, outunit, on=idx, how='outer', suffixes=['_in','_out'])
    qa = qa[qa['poll'].isin(('NOX','SO2'))].copy()
    qa['diff'] = (qa['ann_value_out'].fillna(0) - qa['ann_value_in'].fillna(0)).round(6)
    qa['pd'] = abs(qa['diff']/qa['ann_value_in'].fillna(0)) * 100
    qa[(qa['diff'] != 0) & (qa['pd'] > 0.01)].to_csv(fn, index=False)


