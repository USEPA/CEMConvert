import pandas as pd

class CemCorrect:
    '''
    '''

    def __init__(self):
        '''
        '''
        self.peakfactor = 3
        self.threshold = 0.3
        self.heat = 'HTINPUT'
        self.anomcols = ['HIMEAS','NOXMEAS','SO2MEAS','CO2MEAS','noxrmeasure']
        # Value columns from the CEM file to set as values in the resulting pivot 
        self.valcols = ['HTINPUT','NOX','SO2','CO2']
        self.measmap = dict(zip(self.valcols, self.anomcols))
        # Group fields
        self.unithour = ['oris_facility_code','oris_boiler_id','hour']
        self.unitmonth = self.unithour + ['month',]
        # Init a dataframe to store the unit level hourly mean values
        self.unitmeans = pd.DataFrame()
        # Init a dataframe for storing QA
        self.unitqa = pd.DataFrame()

    def calc_mean(self, col, hourly):
        '''
        Calculate the unit-hour mean values using values not flagged as anomalous
        If the ratio of the number of unit-hourly values to the number of days in the month
          exceeds the threshold then use the monthly mean, otherwise use the annual mean
        '''
        # Calculate the means only using measured or calculated values
        df = hourly.loc[hourly[self.measmap[col]].isin((1,2)), self.unitmonth+['date',col]].copy()
        # Count the unit hour values for the month and find the fraction of days in the month
        daycnt = df[df[col].notnull()].groupby(self.unitmonth, as_index=False)[col].count()
        df = df.merge(daycnt, on=self.unitmonth, how='left', suffixes=['','_cnt'])
        df['frac'] = df[f'{col}_cnt'].fillna(0) / df.date.dt.daysinmonth
        # Calculate monthly means for the unit/hour that >= threshold
        idx = (df['frac'] >= self.threshold) & (df[col].notnull())
        monmeans = df[idx].groupby(self.unitmonth, as_index=False).mean()
        # Otherwise use the annual mean
        annmeans = df[df[col].notnull()].groupby(self.unithour, as_index=False).mean()
        df = pd.merge(df.loc[df['frac'] < self.threshold, self.unitmonth].drop_duplicates(),
          annmeans, on=self.unithour, how='left', suffixes=['','_unit'])
        cols = self.unitmonth + [col,]
        df = pd.concat((monmeans[cols], df[cols]))
        if len(self.unitmeans) > 0:
            self.unitmeans = self.unitmeans.merge(df, on=self.unitmonth, how='left')
        else:
            self.unitmeans = df.copy()

    def calc_rate(self, col, hourly):
        '''
        Calculate the average rate (mass/heat input) for the col after the average values are filled
        '''
        # Calculate the means only using measured or calculated values
        cols = self.unitmonth+['date',col,self.heat,self.measmap[self.heat]]
        df = hourly.loc[hourly[self.measmap[col]].isin((1,2)), cols].copy()
        # Fill in the average heat input and fill where needed
        df = df.merge(self.unitmeans[self.unitmonth+[self.heat,]], on=self.unitmonth,
          how='left', suffixes=['','_mean'])
        # Fill average heat where heat is null, 0, or flagged and 2 times the mean
        idx = (df[self.heat].fillna(0) == 0) | \
          ((df[self.measmap[self.heat]] > 2) & (df[self.heat].fillna(0) > (df['%s_mean' %self.heat] * 2)))
        df.loc[idx, self.heat] = df.loc[idx, '%s_mean' %self.heat]
        # Now divide out into a rate
        df[f'{col}_rate'] = df[col].fillna(0) / df[self.heat]
        # Count the unit hour values for the month and find the fraction of days in the month
        daycnt = df[df[f'{col}_rate'] > 0].groupby(self.unitmonth, 
          as_index=False)[f'{col}_rate'].count()
        df = df.merge(daycnt, on=self.unitmonth, how='left', suffixes=['','_cnt'])
        df['frac'] = df[f'{col}_rate_cnt'].fillna(0) / df.date.dt.daysinmonth
        # Calculate monthly means for the unit/hour that >= threshold
        idx = (df['frac'] >= self.threshold) & (df[f'{col}_rate'] > 0)
        monmeans = df[idx].groupby(self.unitmonth, as_index=False).mean()
        # Otherwise use the annual mean
        annmeans = df[df[f'{col}_rate'] > 0].groupby(self.unithour, as_index=False).mean()
        df = pd.merge(df.loc[df['frac'] < self.threshold, self.unitmonth].drop_duplicates(),
          annmeans, on=self.unithour, how='left', suffixes=['','_unit'])
        cols = self.unitmonth + [f'{col}_rate',]
        df = pd.concat((monmeans[cols], df[cols]))
        self.unitmeans = self.unitmeans.merge(df[df[f'{col}_rate'] > 0], on=self.unitmonth, how='left')

    def fill_mean(self, col, hourly):
        '''
        Fill the anomalous values with the mean value
        '''
        cols = list(hourly.columns)
        hourly = hourly.merge(self.unitmeans[self.unitmonth+[col,]], on=self.unitmonth,
          how='left', suffixes=['','_mean'])
        # If anything is flagged with a measurement code > 2 and the value is anomalous
        idx = ((hourly[self.anomcols].gt(2).any(axis=1)) & \
          (hourly[col].notnull()) & \
          (hourly[col] > hourly[f'{col}_mean'] * self.peakfactor) & \
          (hourly[f'{col}_mean'].fillna(0) > 0))
        self.store_qa(col, hourly[idx].copy())
        hourly.loc[idx, col] = hourly.loc[idx, f'{col}_mean']
        return hourly[cols].copy()

    def fill_rate(self, col, hourly):
        '''
        Fill the anomalous values with rate multiplied by heat input 
        '''
        cols = list(hourly.columns)
        hourly = hourly.merge(self.unitmeans[self.unitmonth+[f'{col}_rate',self.heat]], on=self.unitmonth,
          how='left', suffixes=['','_mean'])
        hourly[f'{col}_mean'] = hourly[f'{col}_rate'].fillna(0) * hourly[f'{self.heat}_mean'].fillna(0)
        idx = ((hourly[self.anomcols].gt(2).any(axis=1)) & \
          (hourly[col].notnull()) & \
          (hourly[col] > hourly[f'{col}_mean'] * self.peakfactor) & \
          (hourly[f'{col}_mean'].fillna(0) > 0))
        self.store_qa(col, hourly[idx].copy())
        hourly.loc[idx, col] = hourly.loc[idx, f'{col}_mean']
        return hourly[cols].copy()

    def store_qa(self, col, df):
        '''
        Write the QA to the main QA df
        '''
        df['field'] = col
        df.rename(columns={col: 'original_value', f'{col}_mean': 'replacement_value',
          self.measmap[col]: 'measurement_code'}, inplace=True)
        self.unitqa = pd.concat((self.unitqa, df))

    def write_qa(self, fn):
        '''
        Write the CEMCorrect QA
        '''
        self.unitqa.sort_values(['oris_facility_code','oris_boiler_id','date','field'], inplace=True)
        self.unitqa['year'] = self.unitqa.date.dt.year.astype(str)
        self.unitqa['month'] = self.unitqa.date.dt.month.astype(str)
        self.unitqa['day'] = self.unitqa.date.dt.day.astype(str)
        cols = ['oris_facility_code','oris_boiler_id','year','month','day','hour','field',
          'measurement_code','original_value','replacement_value']
        self.unitqa[['original_value','replacement_value']] =\
           self.unitqa[['original_value','replacement_value']].round(4)
        self.unitqa.to_csv(fn, index=False, columns=cols)

