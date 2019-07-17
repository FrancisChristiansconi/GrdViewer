
from patternviewer.element.pattern.multigrd import MultiGrd
from patternviewer.element.pattern.grd import Grd
# from mlg import MultiGrd


def getitemlist(filename):
    file = open(filename, 'r')
    items = file.readlines()
    file.close()
    return [i[:-1] for i in items]

datadir = 'C:\\Users\\cfrance\\Dev\\Python' + \
    '\\GrdViewer\\data\\ADS - Element pattern\\'

filelist = getitemlist(datadir + 'text.txt')
pathlist = [datadir + f for f in filelist]
excfile = datadir + 't4h.wts'

conf_grd = {'filename': pathlist[0]}
grd = Grd(filename=pathlist[0], conf=conf_grd)

conf_multigrd = {'filename': pathlist}
multigrd = MultiGrd(filenames=pathlist,
                    excfilename=excfile,
                    conf=conf_multigrd)
