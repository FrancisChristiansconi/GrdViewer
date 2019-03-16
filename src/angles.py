"""This module provides conversion routines between
(u,v,w), (theta, phi), (Az and El), (Az over El) and (El over Az) coordinates
systems.
Angles are to be provided in radians and will be returned in radians.
As much as possible, a first conversion from the input format to (theta, phi)
will be done and then conversion from (theta, phi) to the output format will
be applied.
"""
# import numpy for trigonometry functions
import numpy as np

import matplotlib.pyplot as plt

# angles conversion constant
DEG2RAD = np.pi / 180.0
RAD2DEG = 180.0 / np.pi

# Conversion to (theta, phi)
#============================================================================
def uv2thetaphi(u, v, degrees=True):
    """Convert (u,v) to (theta,phi) using the following formulae inverted:
    u = sin(theta) * cos(phi)
    v = sin(theta) * sin(phi)
    w parameter is not required
    """
    theta = np.arcsin(np.sqrt(u**2 + v**2))
    phi = np.arctan2(v, u)
    phi = phi % (2 * np.pi)
    mask = theta != 0
    phi = phi * mask
    if degrees:
        k = RAD2DEG
    else:
        k = 1
    return theta * k, phi * k
# end of function uv2thetaphi

def azel2thetaphi(az, el, degrees=True):
    """Convert (az and el) to (theta, phi) using the following formulae inverted:
    Az = theta * cos(phi)
    El = theta * sin(phi)
    (Grasp documentation)
    """
    if degrees:
        c = DEG2RAD
        k = RAD2DEG
    else:
        c = 1
        k = 1
    theta = np.sqrt((az * c)**2 + (el * c)**2)
    phi = np.arctan2(el * c, az * c)
    
    return theta * k, phi * k
# end of function azel2thetaphi

def azovel2thetaphi(az, el, degrees=True):
    """Convert (az over el) to (u, v, w) and then (theta, phi)
    using the following formulae:
    u = sin(az) * cos(el)
    v = sin(el)
    and function uv2thetaphi
    """
    u, v = azovel2uv(az, el, degrees)
    return uv2thetaphi(u, v, degrees)
# end of function azel2thetaphi

def elovaz2thetaphi(az, el, degrees=True):
    """Convert (az over el) to (u, v, w) and then (theta, phi)
    using the following formulae:
    u = sin(az)
    v = cos(az) * sin(el)
    and function uv2thetaphi
    """
    u, v = elovaz2uv(az, el, degrees)
    return uv2thetaphi(u, v, degrees)
# end of function elovaz2thetaphi

# Conversion from (theta, phi)
#============================================================================
def thetaphi2uv(theta, phi, degrees=True):
    """Convert (theta, phi) with straight formulae:
    u = sin(theta) * cos(phi)
    v = sin(theta) * sin(phi)
    """
    if degrees:
        k = DEG2RAD
    else:
        k = 1
    u = np.sin(theta * k) * np.cos(phi * k)
    v = np.sin(theta * k) * np.sin(phi * k)
    return u, v
# end of function thetaphi2uv

def thetaphi2azel(theta, phi, degrees=True):
    """Convert (theta, phi) with straight formulae:
    az = theta * cos(phi)
    el = theta * sin(phi)
    """
    if degrees:
        k = DEG2RAD
    else:
        k = 1
    az = theta * np.cos(phi * k)
    el = theta * np.sin(phi * k)
    return az, el
# end of function thetaphi2azel

def thetaphi2azovel(theta, phi, degrees=True):
    """Convert (theta, phi) with thetaphi2uv and reverted formulae:
    u = sin(az) * cos(el)
    v = sin(el)
    """
    u, v = thetaphi2uv(theta, phi, degrees)
    return uv2azovel(u, v, degrees)
# end of function thetaphi2azovel

def thetaphi2elovaz(theta, phi, degrees=True):
    """Convert (theta, phi) to (el over az) with thetaphi2uv and reverted formulae:
    u = sin(az)
    v = cos(az) * sin(el)
    """
    u, v = thetaphi2uv(theta, phi, degrees)
    return uv2elovaz(u, v, degrees)

# Conversion from (u,v)
#============================================================================
def uv2azel(u, v, degrees=True):
    if degrees:
        k = RAD2DEG
    else:
        k = 1
    r = np.sqrt(u**2 + v**2)
    arcsin_r = np.arcsin(r)
    def limit_zero(r, arcsin_r):
        if r:
            return arcsin_r / r 
        else:
            return 1
    factor = np.vectorize(limit_zero)(r, arcsin_r)
    az = - k * u * factor
    el = k * v * factor
    return az, el
    # sin_el = v
    # tan_az = - u / np.sqrt(1 - u**2 - v**2)
    # return np.arctan(tan_az) * k, np.arcsin(sin_el) * k
    # theta, phi = uv2thetaphi(u, v, degrees)
    # return thetaphi2azel(theta, phi, degrees)

def uv2azovel(u, v, degrees=True):
    """Use reverted formulae:
    u = sin(az) * cos(el)
    v = sin(el)
    """
    if degrees:
        k = RAD2DEG
    else:
        k = 1
    az = - np.arcsin(u)
    w = np.sqrt(1 - u**2 - v**2)
    el = np.arctan2(v, w)
    return az * k, el * k

def uv2elovaz(u, v, degrees=True):
    """Use reverted formulae:
    u = - sin(az) * cos(el)
    v = sin(el)
    """
    if degrees:
        k = RAD2DEG
    else:
        k = 1
    el = np.arcsin(v)
    tan_el = np.tan(el)
    def limit_zero(u, v, tan_el):
        if v:
            return np.arcsin(u / v * tan_el)
        else:
            return np.arcsin(u)
    az = - np.vectorize(limit_zero)(u, v, tan_el)
    return az * k, el * k

# Conversion to (u, v)
#============================================================================
def azel2uv(az, el, degrees=True):
    if degrees:
        k = DEG2RAD
    else:
        k = 1
    # u = - np.sin(az * k) * np.cos(el * k)
    # v = np.sin(el * k)
    az_rad = az * k
    el_rad = el * k
    r = np.sqrt(az_rad**2 + el_rad**2)
    sin_r = np.sin(r)
    def limit_zero(r, sin_r):
        if r:
            return sin_r / r 
        else:
            return 1
    factor = np.vectorize(limit_zero)(r, sin_r)
    u = - az_rad * factor
    v = el_rad * factor
    return u, v

def azovel2uv(az, el, degrees=True):
    if degrees:
        k = DEG2RAD
    else:
        k = 1
    u = - np.sin(az * k)
    v = np.cos(az * k) * np.sin(el * k)
    return u, v

def elovaz2uv(az, el, degrees=True):
    if degrees:
        k = DEG2RAD
    else:
        k = 1
    u = - np.sin(az * k) * np.cos(el * k)
    v = np.sin(el * k)
    return u, v

# Convert from (az, el)
#============================================================================
def azel2azovel(az, el, degrees=True):
    u, v = azel2uv(az, el, degrees)
    return uv2azovel(u, v, degrees)
    # theta, phi = azel2thetaphi(az, el, degrees)
    # return thetaphi2azovel(theta, phi, degrees)

def azel2elovaz(az, el, degrees=True):
    u, v = azel2uv(az, el, degrees)
    return uv2elovaz(u, v, degrees)

# convert to (az, el)
#============================================================================
def azovel2azel(az, el, degrees=True):
    u, v = azovel2uv(az, el, degrees)
    return uv2azel(u, v, degrees)
    # theta, phi = azovel2thetaphi(az, el, degrees)
    # return thetaphi2azel(theta, phi, degrees)

def elovaz2azel(az, el, degrees=True):
    u, v = elovaz2uv(az, el, degrees)
    return uv2azel(u, v, degrees)


# Auto test
if __name__ == '__main__':
    print('uv2thetaphi(0, 0) = ', str(uv2thetaphi(0, 0)))
    print('uv2thetaphi(0.157, 0) = ', str(uv2thetaphi(0.157, 0)))
    print('uv2thetaphi(0 , 0.157) = ', str(uv2thetaphi(0, 0.157)))
    print('uv2thetaphi(0.157 , 0.157) = ', str(uv2thetaphi(0.157, 0.157)))
    print('')
    print('azel2thetaphi(0, 0) = ', str(azel2thetaphi(0, 0)))
    print('azel2thetaphi(9, 0) = ', str(azel2thetaphi(9, 0)))
    print('azel2thetaphi(0 , 9) = ', str(azel2thetaphi(0, 9)))
    print('azel2thetaphi(9 , 9) = ', str(azel2thetaphi(9, 9)))
    print('')
    print('azovel2thetaphi(0, 0) = ', str(azovel2thetaphi(0, 0)))
    print('azovel2thetaphi(9, 0) = ', str(azovel2thetaphi(9, 0)))
    print('azovel2thetaphi(0 , 9) = ', str(azovel2thetaphi(0, 9)))
    print('azovel2thetaphi(9 , 9) = ', str(azovel2thetaphi(9, 9)))
    print('')
    print('elovaz2thetaphi(0, 0) = ', str(elovaz2thetaphi(0, 0)))
    print('elovaz2thetaphi(9, 0) = ', str(elovaz2thetaphi(9, 0)))
    print('elovaz2thetaphi(0 , 9) = ', str(elovaz2thetaphi(0, 9)))
    print('elovaz2thetaphi(9 , 9) = ', str(elovaz2thetaphi(9, 9)))
    
    print('')
    print('test (theta,phi) to (u,v) to (theta, phi)')
    theta_lin = np.linspace(0, 90, 5)
    phi_lin = np.linspace(0, 360, 5)
    theta, phi = np.meshgrid(theta_lin, phi_lin)
    u, v = thetaphi2uv(theta, phi)
    theta_res, phi_res = uv2thetaphi(u, v)
    # plt.plot(u, v)
    # plt.show()
    print(np.max(np.abs(theta - theta_res)))
    print(np.max(np.abs(phi[:, 1:] - phi_res[:, 1:])))

    print('')
    print('test (u,v) to (theta, phi) to (u, v)')
    u_lin = np.linspace(-0.10, 0.10, 5)
    v_lin = np.linspace(-0.157, 0.157, 5)
    u, v = np.meshgrid(u_lin, v_lin)
    theta, phi = uv2thetaphi(u, v)
    u_res, v_res = thetaphi2uv(theta, phi)
    # plt.plot(u, v)
    # plt.plot(u_res, v_res)
    # plt.show()
    print(np.max(np.abs((u-u_res, v - v_res))))
    
    print('')
    print('test (az,el) to (theta, phi) to (az, el)')
    az_lin = np.linspace(-7, 7, 5)
    el_lin = np.linspace(-9, 9, 5)
    az, el = np.meshgrid(az_lin, el_lin)
    theta, phi = azel2thetaphi(az, el)
    az_res, el_res = thetaphi2azel(theta, phi)
    print(np.max(np.abs((az - az_res, el - el_res))))

    print('')
    print('test (az over el) to (theta, phi) to (az over el)')
    az_lin = np.linspace(-7, 7, 5)
    el_lin = np.linspace(-9, 9, 5)
    az, el = np.meshgrid(az_lin, el_lin)
    theta, phi = azovel2thetaphi(az, el)
    az_res, el_res = thetaphi2azovel(theta, phi)
    print(np.max(np.abs((az - az_res, el - el_res))))

    print('')
    print('test (el over az) to (theta, phi) to (el over az)')
    az_lin = np.linspace(-7, 7, 5)
    el_lin = np.linspace(-9, 9, 5)
    az, el = np.meshgrid(az_lin, el_lin)
    theta, phi = elovaz2thetaphi(az, el)
    az_res, el_res = thetaphi2elovaz(theta, phi)
    print(np.max(np.abs((az - az_res, el - el_res))))
    
    print('')
    print('test (az,el) to (u, v) to (az, el)')
    az_lin = np.linspace(-7, 7, 5)
    el_lin = np.linspace(-9, 9, 5)
    az, el = np.meshgrid(az_lin, el_lin)
    u, v = azel2uv(az, el)
    az_res, el_res = uv2azel(u, v)
    print(np.max(np.abs((az - az_res, el - el_res))))
    
    print('')
    print('test (az over el) to (u, v) to (az over el)')
    az_lin = np.linspace(-7, 7, 5)
    el_lin = np.linspace(-9, 9, 5)
    az, el = np.meshgrid(az_lin, el_lin)
    u, v = azovel2uv(az, el)
    az_res, el_res = uv2azovel(u, v)
    # plt.figure('az')
    # plt.plot(az, el)
    # plt.plot(az_res, el_res)
    # plt.figure('uv')
    # plt.plot(u, v)
    # plt.show()
    print(np.max(np.abs((az - az_res, el - el_res))))
    
    print('')
    print('test (el over az) to (u, v) to (el over az)')
    az_lin = np.linspace(-7, 7, 5)
    el_lin = np.linspace(-9, 9, 5)
    az, el = np.meshgrid(az_lin, el_lin)
    u, v = elovaz2uv(az, el)
    az_res, el_res = uv2elovaz(u, v)
    print(np.max(np.abs((az - az_res, el - el_res))))

    
    print('')
    print('test (u, v) to (az,el) to (u, v)')
    u_lin = np.linspace(-0.10, 0.10, 5)
    v_lin = np.linspace(-0.157, 0.157, 5)
    u, v = np.meshgrid(u_lin, u_lin)
    az, el = uv2azel(u, v)
    u_res, v_res = azel2uv(az, el)
    # plt.figure('az')
    # plt.plot(az, el)
    # plt.figure('uv')
    # plt.plot(u, v)
    # plt.plot(u_res, v_res)
    # plt.show()
    print(np.max(np.abs((u-u_res, v - v_res))))



# end of module angles