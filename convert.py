# import os
import os

# import glob
import glob

# import patterns classes
from patternviewer.element.pattern.grd import Grd
from patternviewer.element.pattern.pat import Pat
import patternviewer.constant as cst

# input directory
input_dir = 'P:\\Antenna_models\\SES6\\Andes\\grd_files_predictions'

# output directory
output_dir = 'C:\Temp\shrunk_pattern'


# get grd files
os.chdir(input_dir)
files = glob.glob('*.grd')

for f in files:
    input_file = os.path.join(input_dir, f)
    output_file = os.path.join(output_dir, f[:-3] + 'pat')
    second_pol = False
    if output_file[-5] == 'H':
        second_pol = True

    config = {}
    config['filename'] = input_file
    config['revert_x'] = False
    config['revert_y'] = False
    config['use_second_pol'] = second_pol
    config['sat_alt'] = cst.ALTGEO
    config['sat_lon'] = -40.5
    config['display_slope'] = False
    config['shrink'] = True
    config['azshrink'] = 0.25
    config['elshrink'] = 0.25

    # import data
    if f[-3:] == 'grd':
        p = Grd(conf=config, parent=None)
    elif f[-3:] == 'pat':
        p = Pat(conf=config, parent=None)
    p.export_to_file(output_file, True, 0)
