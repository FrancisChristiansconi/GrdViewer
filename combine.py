import numpy as np 

from patternviewer.element.pattern.grd import Grd

pattern_dir = 'C:\\ANT_MAP\\SES14_MONSTER\\Antmap\\TEST\\pattern\\'

sat_lon = -47.5


# list of files for palettes Yellow Red
files_YR_H = [
    'SES14_YR_Steering_model_301_AF1_beam41_TX_12422.00_H.grd',
    'SES14_YR_Steering_model_301_AF3_beam43_TX_10982.50_H.grd',
    'SES14_YR_Steering_model_301_AR3_beam03_TX_11012.50_H.grd',
    'SES14_YR_Steering_model_301_BR12_beam16_TX_11762.50_H.grd',
    'SES14_YR_Steering_model_301_BR2_beam06_TX_11732.50_H.grd',
    'SES14_YR_Steering_model_301_BR3_beam07_TX_11040.50_H.grd',
    'SES14_YR_Steering_model_301_CA1_beam17_TX_11108.50_H.grd',
    'SES14_YR_Steering_model_301_CA3_beam19_TX_10982.50_H.grd',
    'SES14_YR_Steering_model_301_CA7_beam23_TX_10982.50_H.grd',
    'SES14_YR_Steering_model_301_MO5_beam29_TX_11138.50_H.grd',
    'SES14_YR_Steering_model_301_MO7_beam31_TX_11071.00_H.grd',
    'SES14_YR_Steering_model_301_PE3_beam39_TX_11012.50_H.grd',
]
files_YR_V = [
    'SES14_YR_Steering_model_301_AF2_beam42_TX_12362.00_V.grd',
    'SES14_YR_Steering_model_301_AR1_beam01_TX_11040.50_V.grd',
    'SES14_YR_Steering_model_301_BR10_beam14_TX_11575.00_V.grd',
    'SES14_YR_Steering_model_301_BR6_beam10_TX_11732.50_V.grd',
    'SES14_YR_Steering_model_301_BR7_beam11_TX_11762.50_V.grd',
    'SES14_YR_Steering_model_301_CA4_beam20_TX_10982.50_V.grd',
    'SES14_YR_Steering_model_301_CA8_beam24_TX_11732.50_V.grd',
    'SES14_YR_Steering_model_301_MO11_beam35_TX_11136.00_V.grd',
    'SES14_YR_Steering_model_301_MO4_beam28_TX_10982.50_V.grd',
    'SES14_YR_Steering_model_301_MO9_beam33_TX_11136.00_V.grd',
    'SES14_YR_Steering_model_301_PE2_beam38_TX_10982.50_V.grd',
]

# list of files for palette Green Blue
files_GB_H = [
    'SES14_GB_Steering_model_301_AR2_beam02_TX_11732.50_H.grd',
    'SES14_GB_Steering_model_301_BR1_beam05_TX_11040.50_H.grd',
    'SES14_GB_Steering_model_301_BR4_beam08_TX_11040.50_H.grd',
    'SES14_GB_Steering_model_301_BR5_beam09_TX_11732.50_H.grd',
    'SES14_GB_Steering_model_301_BR9_beam13_TX_11732.50_H.grd',
    'SES14_GB_Steering_model_301_CA5_beam21_TX_11762.50_H.grd',
    'SES14_GB_Steering_model_301_MO12_beam36_TX_11136.00_H.grd',
    'SES14_GB_Steering_model_301_MO3_beam27_TX_10982.50_H.grd',
    'SES14_GB_Steering_model_301_PE1_beam37_TX_11762.50_H.grd',
    'SES14_GB_Steering_model_301_PE4_beam40_TX_11762.50_H.grd',
]
files_GB_V = [
    'SES14_GB_Steering_model_301_AF4_beam44_TX_11012.50_V.grd',
    'SES14_GB_Steering_model_301_AR2_beam02_TX_11575.00_V.grd',
    'SES14_GB_Steering_model_301_AR4_beam04_TX_10982.50_V.grd',
    'SES14_GB_Steering_model_301_BR11_beam15_TX_10982.50_V.grd',
    'SES14_GB_Steering_model_301_BR8_beam12_TX_10982.50_V.grd',
    'SES14_GB_Steering_model_301_CA2_beam18_TX_11108.50_V.grd',
    'SES14_GB_Steering_model_301_CA6_beam22_TX_11012.50_V.grd',
    'SES14_GB_Steering_model_301_MO1_beam25_TX_11138.50_V.grd',
    'SES14_GB_Steering_model_301_MO10_beam34_TX_11012.50_V.grd',
    'SES14_GB_Steering_model_301_MO2_beam26_TX_11508.50_V.grd',
    'SES14_GB_Steering_model_301_MO6_beam30_TX_11071.00_V.grd',
    'SES14_GB_Steering_model_301_MO8_beam32_TX_11012.50_V.grd',
]


def combine(patlist, pallet):
    # import all patterns
    patterns = {}
    for f in patlist:
        tokens = f.split('_')
        beam_name = tokens[1] + '_' + tokens[5]
        patterns[beam_name] = {
            'file': pattern_dir + f,
            'rotate': True,
            'second polarisation': tokens[-1][0] == 'V',
        }
        patterns[beam_name]['pattern'] = Grd(
            pattern_dir + f, conf=patterns[beam_name], dialog=False)

    # combine patterns
    pat = next(iter(patterns.values()))

    dims = pat['pattern'].copol().shape
    matrix = np.ones(dims) * -999.0
    for k, i in patterns.items():
        if i['second polarisation']:
            matrix = np.maximum(matrix, i['pattern'].cross())
        else:
            matrix = np.maximum(matrix, i['pattern'].copol())

    # rotate matrix by 90 degrees
    matrix = np.flip(np.flip(matrix, 0).T, 0)

    pat['pattern'].export_to_pat(
        filename=(pattern_dir + 'SES14_'
                  + pallet
                  + '_Steering_model_301_combined.pat'),
        data=matrix
    )


combine(files_GB_H, 'GB_H')
combine(files_GB_V, 'GB_V')
combine(files_YR_H, 'YR_H')
combine(files_YR_V, 'YR_V')
