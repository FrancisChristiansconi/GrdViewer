# import os
import os

# import glob
import glob

# import patterns classes
import pattern

# input directory
input_dir = 'P:\\Antenna_models\\SES6\\Andes\\grd_files_predictions'

# output directory
output_dir = 'P:\\ASTRIUM\\Astra_2EFG5B_-_SES6\\IRESLess\\SES6 patterns\\Shrunk patterns\\Andes_shrunk0.25'


# get grd files
os.chdir(input_dir)
files = glob.glob('*.grd')

for f in files:
    input_file = os.path.join(input_dir, f)
    output_file = os.path.join(output_dir, f[:-3] + 'pat')
    second_pol = False
    if output_file[-5] == 'H':
        second_pol = True 
    # import data
    if f[-3:] == 'grd':
        p = pattern.Grd(filename = input_file,
                        revert_x = False,
                        revert_y = False,
                        use_second_pol = second_pol,
                        sat_alt = pattern.ALTGEO,
                        sat_lon = -40.5,
                        display_slope = False,
                        shrink = True,
                        azshrink = 0.25,
                        elshrink = 0.25)
    elif f[-3:] == 'pat':
        p = pattern.Pat(filename = input_file,
                        revert_x = False,
                        revert_y = False,
                        use_second_pol = second_pol,
                        sat_alt = pattern.ALTGEO,
                        sat_lon = -40.5,
                        display_slope = False,
                        shrink = True,
                        azshrink = 0.25,
                        elshrink = 0.25)

    p.export_to_file(output_file, True, 0)

