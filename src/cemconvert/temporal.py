class Temporal:
    '''
    Functions for calculating temporal factors from CEM activity and applying them
      to annual values
    '''

    def __init__(self, opts,
          temporal_hierarchy = ['HTINPUT','GLOAD','SLOAD','NOX']):
        # Define the hierarchy of variables to pull activity for 
        #  temporalizing annual pollutants not in the CEM data
        self.temporal_hierarchy = temporal_hierarchy
        # Variable name to use in the FF10 pollutant field for the temporalizer
        self.temporalvar = opts.temporalvar
        self.hrvals = ['hrval%s' %x for x in range(24)]
        self.hrfracs = ['hrfrac%s' %x for x in range(24)]
        # Fields to use to identify a unit
        self.unitids = ['oris_facility_code','oris_boiler_id']

    def set_temporal_var(self, annsum):
        '''
        Iterate through the temporal hierarchy
        Select the variable to use for temporalizing non NOX/SO2/CO2
        This is on a per unit basis using the most representative populated field in a hierarchy
        '''
        annsum['tempvar'] = 999
        for n, poll in enumerate(self.temporal_hierarchy):
            idx = (annsum['poll'] == poll) & (annsum['anntot'] > 0) & (annsum['tempvar'] == 999)
            annsum.loc[idx, 'tempvar'] = n 
        annsum = annsum.sort_values('tempvar', ascending=True).drop_duplicates(self.unitids, 
          keep='first')
        annsum.drop_duplicates(self.unitids, keep='first', inplace=True)
        # Display any units that do not have a populated variable valid for temporalization of other
        #  vars
        units = annsum[self.unitids+['tempvar',]].drop_duplicates()
        if len(annsum[annsum['tempvar'].fillna(999) == 999]) > 0:
            print('\nMissing data for temporalization:\n', 
              units[~ units.duplicated(self.unitids, keep=False)])
        return annsum
       
    def calc_cem_temporal(self, df):
        '''
        Calculate the unit level hourly level CEMs temporal factors to apply to the annual
          emissions
        '''
        cols = self.unitids+['poll',]
        annsum = df[cols+['daytot',]].groupby(cols, as_index=False).sum()
        annsum.rename(columns={'daytot': 'anntot'}, inplace=True)
        annsum = self.set_temporal_var(annsum)
        idx = (annsum['tempvar'].fillna(999) != 999)
        # Merge in these annual values
        df = df.merge(annsum[idx], on=cols, how='left')
        df.loc[df['tempvar'].fillna(999) != 999, 'poll'] = self.temporalvar
        df = df[df['poll'] == self.temporalvar].copy()
        # Calculate the temporal factors at the hourly and daily levels
        df['dayfrac'] = df['daytot'] / df['anntot']
        df[self.hrfracs] = df[self.hrvals].fillna(0).div(df.anntot, axis=0)
        df[['daytot','anntot'] + self.hrvals] = df[['daytot','anntot'] + self.hrvals].fillna(0)
        df['month'] = df['month'].astype(int).astype(str)
        cols = self.unitids + ['month','date','dayfrac','daytot'] 
        df = df[cols+self.hrfracs+self.hrvals].groupby(cols, as_index=False).sum()
        return df

    def apply_temporal(self, emis, houract):
        '''
        Apply the hourly temporal factors to an annual value
        In: annual emissions and hourly factors by ORIS IDs
        Out: hourly emissions by ORIS ID
        '''

        fracs = houract[self.unitids+['month','date','dayfrac']+self.hrfracs].reset_index()
        emis = emis[self.unitids+['poll','ann_value','unit_frac']].merge(fracs, on=self.unitids, how='left')
        missingidx = emis.loc[emis['dayfrac'].isnull(), self.unitids].drop_duplicates()
        print('Missing unit matches: %s' %len(missingidx))
        emis['daytot'] = emis['dayfrac'] * emis['ann_value']
        emis[self.hrvals] = emis[self.hrfracs].fillna(0).multiply(emis.ann_value, axis=0)
        return emis

