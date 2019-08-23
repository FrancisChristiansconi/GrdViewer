"""Invert Grd files polarisation
"""

# import os
import os
# system module
import sys
from sys import argv


if __name__ == '__main__':
    print(argv)
    if len(argv) > 1:
        # get input file name
        infilename = argv[1]
        # generate output filename
        outfilename = infilename[:-4] + '_out.grd'

        # read input file
        infile = open(infilename, 'r')
        lines = infile.readlines()
        infile.close()
        print('Number of lines in file: {0:d}'.format(len(lines)))

        # generate output file
        header = True
        dataheader = False
        dataheaderlinenb = 0
        outfile = open(outfilename, 'w')
        for line in lines:
            if header is True:
                if line[:4] == '++++':
                    header = False
                    dataheader = True
                outfile.write(line)
                print(line[:-1])
            elif dataheader is True:
                outfile.write(line)
                dataheaderlinenb += 1
                if dataheaderlinenb > 4:
                    dataheader = False
                print('dataheaderlinenb : {0:d}'.format(dataheaderlinenb))
                print(line[:-1])
            else:
                tab = line.split()
                outline = \
                    ' {2:17.10E} {3:17.10E} {0:17.10E} {1:17.10E}\n'.format(
                        *[float(t) for t in tab]
                    )
                # print(outline)
                outfile.write(outline)

        outfile.close()
