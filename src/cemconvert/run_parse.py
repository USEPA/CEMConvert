import os
from sys import exit
from optparse import OptionParser,OptionGroup

class RunOpts(object):
    '''
    Command line arguments
    '''

    def __init__(self):
        self.set_ev()
        options, args = self.get_opts()
        self.check_valid(options, args)
        self.set_opt_args(options)
        self.set_cmd_args(args)
        self.init_run()

    def get_opts(self):
        '''
        Handle command line arguments and options.
        '''
        self.parser = OptionParser(usage = 'usage: %prog [options] egu_annual_ff10')
        self.parser.add_option('-p', '--cempolls', dest='cempolls', 
          help='List of pollutants in hourly CEM files to process', default='NOX,SO2,CO2')
        self.parser.add_option('-y', '--year', dest='year', help='Year to process', default='2016')
        self.parser.add_option('-i', '--input_path', dest='input_path', 
          help='Hourly CEM input path', default='input')
        self.parser.add_option('-o', '--output_path', dest='output_path', 
          help='FF10 inventory output path', default='output')
        self.parser.add_option('-c', '--write_cems', action='store_true', dest='write_cems', 
          help='Write hourly CEM data in old SMOKE format', default=False)
        self.parser.add_option('-g', '--gmt', action='store_true', dest='gmt_output', 
          help='Output hourly FF10 to GMT instead of local time', default=False)
        self.parser.add_option('-r', '--ramp_up', action='store_true', dest='ramp_up', 
          help='Timeshift hours for the year after the designated year back one year', default=False)
        self.parser.add_option('-t', '--temporal_var', dest='temporalvar', 
          help='Variable name used for temporal activity', default='HOURACT')
        self.parser.add_option('-n', '--inven_polls', dest='calcpolls', 
          help='List of inventory pollutants to temporalize using the CEM activity', default='PM25-PRI')
        self.parser.add_option('-m', '--months', dest='months', default='',
          help='List of CEM months to process as a comma-delimited list of integers \
           Default behavior is an annual run')
        self.parser.add_option('-l', '--label', dest='label', default='ptegu',
          help='Output inventory label')
        self.parser.add_option('-k', '--keep_annual', dest='keepann', action='store_true',
          default=False, help='Keep and temporalize annual temporal values in FF10 that match CEMs.\
            Default is to replace the emissions values with CEMs.')
        self.parser.add_option('-e', '--cemcorrect', dest='cemcorrect', action='store_true',
          default=False, help='Apply CEMCorrect to the CEMS')
        return self.parser.parse_args()

    def set_ev(self):
        '''
        Set the attributes with the environment variables
        '''
        self.evs = {'MONTHS': 'months', 'YEAR': 'year', 'CEMPATH': 'input_path', 
          'OUTPATH': 'output_path'}
        for ev, att_name in self.evs.items():
            setattr(self, att_name, check_ev(ev))

    def set_opt_args(self, options):
        '''
        Set the self.parser options to object attributes
        '''
        int_list = ['months',]
        lower_list = []
        upper_list = ['cempolls','calcpolls']
        for opt, val in options.__dict__.items():
            if type(val) == str:
                val = val.strip()
            if opt in int_list:
                if val != '':
                    val = [int(x) for x in val.strip().split(',')]
            elif opt in lower_list:
                val = [col.strip() for col in val.lower().strip().split(',')]
            elif opt in upper_list:
                val = [col.strip() for col in val.upper().strip().split(',')]
            # Don't override an att that was set by an EV but not set on the command line
            if opt in self.evs and opt == '':
                pass
            else:
                setattr(self, opt, val)

    def set_cmd_args(self, args):
        ''''
        Map the command line arguments to the internal variable
        '''
        self.ann_ff10 = args[0]

    def check_valid(self, options, args):
        '''
        Misc. option validity checks
        '''
        if len(args) != 1: 
            print('Must specify an input annual FF10')
            exit()
        if len(options.cempolls) == 0:
            raise ValueError('No CEM variables specified. Nothing to do.')

    def init_run(self): 
        '''
        Setup other attributes that need additional processing or logic to define
        '''
        if not self.months:
            self.months = range(1,13)

def check_ev(ev_name):
    """
    Checks if an environment variable is set.
    """
    try:
        var = os.environ[ev_name]
    except KeyError:
        return ''
    else:
        return var

