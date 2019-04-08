import numpy as np

import patternviewer.utils as utils

from patternviewer.element.pattern.abstractpattern import AbstractPattern


class Grd(AbstractPattern):
    """This class implement an antenna pattern object using data from a Ticra .grd file.
    """

    def read_file(self, filename):
        """Read data from TICRA .grd file.
        Params:
            filename: the path to the file to read
        Returns:
            nb_sets: number of data sets
            grid: type de grid
            x: grid stations x coordinates
            y: grid stations y coordinates
            E_mag_co: magnitude of electrical field in copolarisation (dBi)
            E_phs_co: phase of electrical field in copolarisation (degrees)
            E_mag_cr: magnitude of electrical field in crosspolarisation (dBi)
            E_phs_cr: pahse of electrical field in crosspolarisation (degrees)
        """
        utils.trace('in')
        # open file and read text data
        file = open(filename, "r")
        # read all lines in a table
        lines = file.readlines()
        # close file
        file.close()

        # line number
        linesnumber = len(lines)
        istart = -1

        # map header data into dicData
        for i in range(linesnumber):
            # detect end of comments
            if lines[i][:4] == '++++':
                istart = i + 1
                break

        # header content
        # should always be 1
        ktype = int(lines[istart].split()[0])
        istart += 1
        # number of patterns
        nb_sets = int(lines[istart].split()[0])
        # field components
        # 1: linear E_theta and E_phi
        # 2: RHCP and LHCP
        # 3: linear co and cx
        # 4: Major and minor axes of polarization ellipse
        # 5: XPD fields: E_theta/E_phi and E_phi/E_theta
        # 6: XPD fields: RHCP/LHCP and LHCP/RHCP
        # 7: XPD fields: co/cx and cx/co
        # 8: XPD fields: major/minor and minor/major
        # 9: total power norm(E) and sqrt(RHCP/LHCP)
        icomp = int(lines[istart].split()[1])
        # number of field component (2 for far field, 3 for near field)
        ncomp = int(lines[istart].split()[2])
        # Type of field grid
        # 1: uv-grid
        # 4: Elevation over Azimuth
        # 5: Elevation and Azimuth
        # 6: Azimuth over Elevation
        # 7: thetaphi grid
        grid = int(lines[istart].split()[3])
        istart += 1
        # center of beams
        xi = [int(lines[istart+i_set].split()[0]) for i_set in range(nb_sets)]
        yi = [int(lines[istart+i_set].split()[1]) for i_set in range(nb_sets)]
        istart += nb_sets

        # data table reading
        iSet = 0
        iRow = 0
        iCol = 0
        nx = []               # number of points of the grid along x axis
        ny = []               # number of pointd of the grid along y axis
        klimit = []           # ???
        # Electrical field in copolarisation (complex format)
        E_field_copol = []
        # Electrical field in crosspolarisation (complex format)
        E_field_cross = []
        x = []                # x coordinates of points of the grid (vector)
        y = []                # y coordinates of points of the grid (vector)
        xs = []               # x start
        xe = []               # x end
        ys = []               # y start
        ye = []               # y end
        iLine = istart
        for iSet in range(nb_sets):
            # get limits of the pattern grid
            xs.append(float(lines[iLine].split()[0]))
            xe.append(float(lines[iLine].split()[2]))
            ys.append(float(lines[iLine].split()[1]))
            ye.append(float(lines[iLine].split()[3]))
            iLine += 1
            # begin of new set, configure set
            nx.append(int(lines[iLine].split()[0]))
            ny.append(int(lines[iLine].split()[1]))
            klimit.append(int(lines[iLine].split()[2]))
            E_field_copol.append(
                np.zeros((nx[iSet], ny[iSet]), dtype=np.complex_))
            E_field_cross.append(
                np.zeros((nx[iSet], ny[iSet]), dtype=np.complex_))
            x.append(np.zeros((nx[iSet], ny[iSet]), dtype=np.float_))
            y.append(np.zeros((nx[iSet], ny[iSet]), dtype=np.float_))
            iLine += 1
            # put data in the table
            for iTabLine in range(iLine, iLine + nx[iSet] * ny[iSet]):
                E_real_copol = float(lines[iTabLine].split()[0])
                E_imag_copol = float(lines[iTabLine].split()[1])
                E_real_cross = float(lines[iTabLine].split()[2])
                E_imag_cross = float(lines[iTabLine].split()[3])

                E_field_copol[iSet][iRow, iCol] = E_real_copol + \
                    1j * E_imag_copol
                E_field_cross[iSet][iRow, iCol] = E_real_cross + \
                    1j * E_imag_cross
                dx = (xe[iSet] - xs[iSet]) / (nx[iSet] - 1)
                dy = (ye[iSet] - ys[iSet]) / (ny[iSet] - 1)
                x[iSet][iRow, iCol] = iRow * dx + xs[iSet] + xi[iSet] * dx
                y[iSet][iRow, iCol] = iCol * dy + ys[iSet] + yi[iSet] * dy

                iRow += 1
                if iRow == nx[iSet]:
                    iRow = 0
                    iCol += 1
                    if iCol == ny[iSet]:
                        iCol = 0
                        iLine = iTabLine + 1
        # end of file reading

        # initialize some grided data
        E_mag_co = 20*np.log10(np.absolute(E_field_copol))
        E_phs_co = np.angle(E_field_copol, deg=True)
        E_mag_cr = 20*np.log10(np.absolute(E_field_cross))
        E_phs_cr = np.angle(E_field_cross, deg=True)

        return nb_sets, \
            grid, \
            x, \
            y, \
            E_mag_co, \
            E_phs_co, \
            E_mag_cr, \
            E_phs_cr
    # end of read_file

    def grid_type(self):
        """Return file grid type is a standardised format.
        1 - uv grid
        2 - theta/phi
        3 - Az and El
        4 - Elevation over Azimuth
        5 - Azimuth over Elevation
        """
        # Type of grd field grid
        # 1: uv-grid
        # 4: Elevation over Azimuth
        # 5: Elevation and Azimuth
        # 6: Azimuth over Elevation
        # 7: thetaphi grid
        convert = {1: 1,
                   4: 4,
                   5: 3,
                   6: 5,
                   7: 2}
        return convert[self._grid]
    # end function grid_type

    # return gradient of Co-polarisation pattern along Azimuth

    def azel_slope(self, signed=False, set=0):
        # get gradient of Azimuth coordinate
        azimuth_grad, _ = np.gradient(self.azimuth())
        # get gradient of Elevation coordinate
        _, elevation_grad = np.gradient(self.elevation())
        # get gradient of pattern in Azimuth and Elevation
        copol_azgrad, copol_elgrad = np.gradient(self.copol(set))
        # normalize gradient of pattern in Azimuth direction
        copol_azgrad /= azimuth_grad
        # normalize gradient of pattern in Elevation direction
        copol_elgrad /= elevation_grad
        # use absolute value
        if not signed:
            return {'Az': np.absolute(copol_azgrad), 'El': np.absolute(copol_elgrad)}
        else:
            return {'Az': copol_azgrad, 'El': copol_elgrad}
    # end of function azel_slope

    def interpolate_azel_slope(self, az, el, signed=False):
        """return interpolated value of the pattern
        """
        if not self.interpolated_copol_azgrad or not self.interpolated_copol_elgrad:
            # if not yet use interpolation of slopes
            self.interpolated_copol_azgrad = interp.RectBivariateSpline(
                self._x[set][:, 0], self._y[set][0, :], self.azel_slope()['Az'])
            self.interpolated_copol_elgrad = interp.RectBivariateSpline(
                self._x[set][:, 0], self._y[set][0, :], self.azel_slope()['El'])

        # transform azel into uv (-1 because azimuth positive toward East)
        u = -1 * np.cos(el * cst.DEG2RAD) * np.sin(az * cst.DEG2RAD)
        v = np.sin(el * cst.DEG2RAD)

        # if uv are 2D, flat them. Use absolute value depending on signed flag
        if not signed:
            return {'Az': np.absolute(np.reshape(self.interpolated_copol_azgrad.ev(u.flatten(), v.flatten()), np.array(az).shape)),
                    'El': np.absolute(np.reshape(self.interpolated_copol_elgrad.ev(u.flatten(), v.flatten()), np.array(az).shape))}
        else:
            return {'Az': np.reshape(self.interpolated_copol_azgrad.ev(u.flatten(), v.flatten()), np.array(az).shape),
                    'El': np.reshape(self.interpolated_copol_elgrad.ev(u.flatten(), v.flatten()), np.array(az).shape)}
    # end of function interpolate_azel_slope
# end of class Grd
