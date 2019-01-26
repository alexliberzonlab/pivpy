# -*- coding: utf-8 -*-

"""
Contains functions for reading flow fields in various formats
"""

import numpy as np
import xarray as xr
from glob import glob
import os
from pivpy.pivpy import VectorField

def get_units(fname, path='.'):
    """ given a .vec file this will return the names 
    of length and velocity units 
    fallback option is all None
    """

    lUnits, velUnits, tUnits = None, None, None

    fname = os.path.join(os.path.abspath(path),fname) # just make a full path name 
    # new way of opening and closing the file
    with open(fname) as f:
        header = f.readline()
    

    ind2= header.find('VARIABLES=')
    print(ind2)

    if ind2 > 0: # only if there is a valid header

        ind3 = header.find('"X',ind2)
        ind4 = header.find('"',ind3+1)
        header[ind3:ind4+1]
        lUnits = header[ind3+3:ind4]

        ind3 = header.find('"U',ind2)
        ind4 = header.find('"',ind3+1)
        header[ind3:ind4+1]
        velUnits = header[ind3+3:ind4]

        if velUnits == 'pixel':
            tUnits = 'dt'
        else:
            tUnits = velUnits.split('/')[1]

        # fallback if nothing is read properly
        if lUnits is None:
            lUnits = 'mm'
        if velUnits is None:
            velUnits = 'm/s'
        if tUnits is None:
            tUnits = 's'
    
    return lUnits, velUnits, tUnits


def get_dt(fname,path='.'):
    """given a .vec file this will return the delta t 
    from the file in micro seconds"""
    # os.chdir(path) BUG
    fname = os.path.join(os.path.abspath(path),fname) # just make a full path name 
    # new way of opening and closing the file
    with open(fname) as f:
        header = f.readline()
        
    ind1 = header.find('MicrosecondsPerDeltaT')
    dt = float(header[ind1:].split('"')[1])
    return dt

def load_directory(directory):
    """ 
    load_directory (path)

    Loads all the .VEC files in the directory into a single
    xarray dataset with variables and units added as attributes

    Input: 
        directory : path to the directory with .vec files

    Output:
        data : xarray DataSet with dimensions: x,y,t and 
               data arrays of u,v,
               attributes of variables and units


    See more: loadvec
    """
    files  = glob(os.path.join(directory,'*.vec'))
    variables, units, rows, cols = parse_header(files[0])
    
    data = []
    for f in files:
        data.append(loadvec(f,rows,cols,variables,units))
           
    
    combined = xr.concat(data, dim='t')
    combined.attrs['variables'] = variables
    combined.attrs['units'] = units
    return combined

def parse_header(filename):
    """ 
    parse_header ( filename )
    Parses header of the file (.vec) to get the variables (typically X,Y,U,V)
    and units (can be m,mm, pix/dt or mm/sec, etc.), and the size of the dataset
    by the number of rows and columns.
    Input:
        filename : complete path of the file to read
    Returns:
        variables : list of strings
        units : list of strings
        rows : number of rows of the dataset
        cols : number of columns of the dataset 
    """
    with open(filename) as fid:
        header = fid.readline()

    header_list = header.replace(',',' ').replace('=',' ').replace('"',' ').split()
    
    variables = header_list[3:12][::2]
    units = header_list[4:12][::2]
    rows = int(header_list[-5])
    cols = int(header_list[-3])
    
    
    return (variables, units, rows, cols)
    
        

def loadvec(filename, rows=None, cols=None, variables=None, units=None, dt=None):
    """
        loadvec(filename,rows=rows,cols=cols)
        Loads the VEC file (TECPLOT format by TSI Inc.) and OpenPIV format
        Arguments:
            filename : file name, expected to have a header and 5 columns
            rows, cols : number of rows and columns of a vector field,
            if None, None, then parse_header is called to infer the number
            written in the header
        Output:
            data is a xAarray Dataset, see xarray for help 
    """
    if rows is None or cols is None:
        variables,units,rows,cols = parse_header(filename)

    if dt is None:
        dt = get_dt(filename)

    d = np.loadtxt(filename,skiprows=1,delimiter=',',usecols=(0,1,2,3,4)).reshape(rows,cols,5)
    
    u = xr.DataArray(d[:,:,2],dims=('x','y'),coords={'x':d[:,:,0][0,:],'y':d[:,:,1][:,0]})
    v = xr.DataArray(d[:,:,3],dims=('x','y'),coords={'x':d[:,:,0][0,:],'y':d[:,:,1][:,0]})
    cnc = xr.DataArray(d[:,:,4],dims=('x','y'),coords={'x':d[:,:,0][0,:],'y':d[:,:,1][:,0]})
    data = xr.Dataset({'u': u, 'v': v,'cnc':cnc})


    if variables is not None or units is None:
        data.attrs['variables'] = variables
        data.attrs['units'] = units  
        data.attrs['dt'] = dt
    
    return data
    
    
    


