#!/usr/bin/env python3

# import os
import os

# import sys for command line argument
from sys import argv

# import glob
import glob

# import numpy
import numpy as np

# import patterns classes
from patternviewer.element.pattern.grd import Grd
from patternviewer.element.pattern.pat import Pat
import patternviewer.constant as cst
import patternviewer.element.station as stn
import patternviewer.utils as utils


def main():
    utils.mute(True)
    # debug option, print all arguments
    print(argv)

    # stations file
    # stations_file = 'P:\\ASTRIUM\\Astra_2EFG5B_-_SES6\\FMSLATAM\\' + \
    #                 'Ground Stations location\\SES6\\SES06.sta'
    stations_file = argv[1]

    # depointing file
    # azel_file = 'C:\\Temp\\FMSLATAM\\azel.txt'
    azel_file = argv[2]

    # input directory
    # input_dir = 'P:\\ASTRIUM\\Astra_2EFG5B_-_SES6\\FMSLATAM\\' + \
    #             'SES6 patterns\\Reference patterns'
    # F2_pattern_file = os.path.join(input_dir,
    #                                'SES6_Brazil_36_Tx_11680.00_V.grd')
    # TM_pattern_file = os.path.join(input_dir,
    #                                'SES 6_TM_FIST_102_1170050_V.pat')
    F2_pattern_file = argv[3]
    TM_pattern_file = argv[4]

    # output directory
    output_dir = argv[5]

    # F2 pattern config
    F2_config = {}
    F2_config['filename'] = F2_pattern_file
    F2_config['revert_x'] = False
    F2_config['revert_y'] = False
    F2_config['rotate'] = True
    F2_config['use_second_pol'] = False
    F2_config['sat_alt'] = cst.ALTGEO
    F2_config['sat_lon'] = -40.5
    F2_config['sat_lat'] = 0
    F2_config['display_slope'] = False
    F2_config['offset'] = True
    F2_config['azoffset'] = 0
    F2_config['eloffset'] = 0
    F2_config['shrink'] = False
    F2_config['azshrink'] = 0
    F2_config['elshrink'] = 0

    # TM pattern config
    TM_config = {}
    TM_config['filename'] = TM_pattern_file
    TM_config['revert_x'] = False
    TM_config['revert_y'] = False
    TM_config['rotate'] = True
    TM_config['use_second_pol'] = False
    TM_config['sat_alt'] = cst.ALTGEO
    TM_config['sat_lon'] = -40.5
    TM_config['sat_lat'] = 0
    TM_config['display_slope'] = False
    TM_config['offset'] = True
    TM_config['azoffset'] = 0
    TM_config['eloffset'] = 0
    TM_config['shrink'] = False
    TM_config['azshrink'] = 0
    TM_config['elshrink'] = 0

    # import data
    F2_pattern = Grd(conf=F2_config, parent=None)
    TM_pattern = Grd(conf=TM_config, parent=None)
    stations_list = stn.get_station_from_file(
        filename=stations_file, earthplot=None)
    F2_gain = {}
    TM_gain = {}
    azoffset = 0
    eloffset = 0

    # open output file
    outfile = open(os.path.join(output_dir, 'out.txt'), 'w')

    # write reference directivity in output text file
    outfile.write('Reference Antenna gain:\n')
    for station in stations_list:
        conf = station.configure()
        lon = conf['longitude']
        lat = conf['latitude']
        name = conf['tag']
        F2_gain[name] = {}
        TM_gain[name] = {}
        F2_gain[name][(azoffset, eloffset)] = F2_pattern.directivity(lon, lat)
        TM_gain[name][(azoffset, eloffset)] = TM_pattern.directivity(lon, lat)
        str_temp = '{0}: {1:0.2f}dBi {2:0.2f}dBi \n'.format(name,
                                                            F2_gain[name][(
                                                                azoffset,
                                                                eloffset)],
                                                            TM_gain[name][(
                                                                azoffset,
                                                                eloffset)])
        outfile.write(str_temp)

    # open file and read text data (azel offset)
    file = open(azel_file, "r")
    # read all lines in a table
    lines = file.readlines()
    # close file
    file.close()

    # if azel file is not empty, use its value otherwise generate standard grid
    az = []
    el = []
    if len(lines) > 0:
        for line in lines:
            if line is not '':
                tokens = line.split(',')
                az.append(tokens[0])
                el.append(tokens[1])
    else:
        azvec = np.linspace(-0.3, 0.3, 61)
        elvec = np.linspace(-0.3, 0.3, 61)
        azgrid, elgrid = np.meshgrid(azvec, elvec)
        az = azgrid.flatten()
        el = elgrid.flatten()

    # write header of output file
    temp = 'Test ID,Pitch,Roll,'
    for station in stations_list:
        conf = station.configure()
        temp = temp + conf['tag'] + ' F2' + ',' + conf['tag'] + ' TM' + ','
    outfile.write(temp[:-1] + '\n')

    # write data in output file
    for itest in range(len(az)):
        print('Test ID: {0:05d}'.format(itest))
        azoffset = az[itest]
        eloffset = el[itest]
        temp = '{0:05d},{1:0.2f},{2:0.2f},'.format(itest, azoffset, eloffset)
        for station in stations_list:
            F2_config['azoffset'] = azoffset
            F2_config['eloffset'] = eloffset
            F2_pattern.configure(F2_config)
            TM_config['azoffset'] = azoffset
            TM_config['eloffset'] = eloffset
            TM_pattern.configure(TM_config)
            conf = station.configure()
            lon = conf['longitude']
            lat = conf['latitude']
            name = conf['tag']
            F2_gain[name][(azoffset, eloffset)
                          ] = F2_pattern.directivity(lon, lat)
            TM_gain[name][(azoffset, eloffset)
                          ] = TM_pattern.directivity(lon, lat)
            F2_delta = F2_gain[name][(azoffset, eloffset)] - \
                F2_gain[name][(0, 0)]
            TM_delta = TM_gain[name][(azoffset, eloffset)] - \
                TM_gain[name][(0, 0)]
            temp = temp + '{0:0.1f},{1:0.1f},'.format(F2_delta, TM_delta)
        outfile.write(temp[:-1] + '\n')
    outfile.close()
# end of main function


# Main execution
if __name__ == '__main__':
    main()
    print('Finished')
# end of module grdviewer
