# import os
import os

# import glob
import glob

# import patterns classes
from element.pattern.grd import Grd
from element.pattern.pat import Pat
import constant as cst
import element.station as stn

# stations file
stations_file = 'P:\\ASTRIUM\\Astra_2EFG5B_-_SES6\\FMSLATAM\\Ground Stations location\\SES6\\SES06.sta'

# input directory
input_dir = 'P:\\ASTRIUM\\Astra_2EFG5B_-_SES6\\FMSLATAM\\SES6 patterns\\Reference patterns'
F2_pattern_file = 'SES6_Brazil_36_Tx_11680.00_V.grd'
TM_pattern_file = 'SES 6_TM_FIST_102_1170050_V.pat'

# output directory
output_dir = 'C:\\Temp\\FMSLATAM'

# F2 pattern config
F2_config = {}
F2_config['filename'] = os.path.join(input_dir, F2_pattern_file)
F2_config['revert_x'] = False
F2_config['revert_y'] = False
F2_config['use_second_pol'] = True
F2_config['sat_alt'] = cst.ALTGEO
F2_config['sat_lon'] = -40.5
F2_config['display_slope'] = False
F2_config['offset'] = True
F2_config['azoffset'] = 0
F2_config['eloffset'] = 0

# TM pattern config
TM_config = {}
TM_config['filename'] = os.path.join(input_dir, TM_pattern_file)
TM_config['revert_x'] = False
TM_config['revert_y'] = False
TM_config['use_second_pol'] = False
TM_config['sat_alt'] = cst.ALTGEO
TM_config['sat_lon'] = -40.5
TM_config['display_slope'] = False
TM_config['offset'] = True
TM_config['azoffset'] = 0
TM_config['eloffset'] = 0

# import data
F2_pattern = Grd(conf=F2_config, parent=None)
TM_pattern = Pat(conf=TM_config, parent=None)
stations_list = stn.get_station_from_file(filename=stations_file, earthplot=None)

g = F2_pattern.directivity(-74.157917, 4.754417)


