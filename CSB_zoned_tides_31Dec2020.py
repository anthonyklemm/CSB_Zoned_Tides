# -*- coding: utf-8 -*-
"""
Created on Mon Dec 28 13:57:44 2020

This script automates the tide correction of crowdsourced bathymetry (CSB) files (in JSON format)
downloaded from the Internation Hydrographic Organization's (IHO) Data Centre for Digital Bathymetry 
Crowdsourced Bathymetry Database. 

The output is a shapefile.


@author: Anthony
"""


import geopandas as gpd
import numpy as np
import pandas as pd
import json
import requests
import fiona
import os
import glob
import ntpath
pd.set_option('display.max_columns', None)

directory = r'E:\csb\json\p-goula'
files = []

os.chdir(directory)
fp_zones = r"E:\csb\tide zone polygons\tide_zone_polygons.shp"

def getFiles():
    for filepath in glob.iglob(directory + '/*.json', recursive=False):
        files.append(filepath)
        
def CorrectTides():
    nameList = []
    for filepath in files:
        head, filename = ntpath.split(filepath)
        title = filename[15:]
        nameList.append(title)
        print("Reading file: "+filename)
        zones=gpd.read_file(fp_zones)
        df = gpd.read_file(filepath)
        y=open(filepath)
        x=json.load(y)
        df['name']= x['properties']['platform']['name']
                
        #spatial join of CSB data and discrete zoned time polygons
        join = gpd.sjoin(df, zones, how="inner", op="within")
        join = join.astype({'time':'datetime64'})
        #join = join.dropna()


        #find min and max times for each tide control station
        ts = join.groupby('ControlStn').agg(['min','max'])
        ts = ts['time']
        ts = ts.reset_index(drop=False)
        
        #format timestamps for NOAA CO-OPS Tidal Data API
        ts['min'] = ts['min'].dt.strftime("%Y%m%d %H:%M")
        ts['max'] = ts['max'].dt.strftime("%Y%m%d %H:%M")
        ts['ControlStn'] = ts.astype(str)
                
        #get tide data from referenced control stations
        tdf = []
        for ind in ts.index:
            URL_API = 'https://tidesandcurrents.noaa.gov/api/datagetter?begin_date='+ts['min'][ind]+'&end_date='+ts['max'][ind]+'&station='+ts['ControlStn'][ind]+'&product=water_level&datum=mllw&units=metric&time_zone=gmt&application=NOAA_Coast_Survey&format=json'
            
            response = requests.get(URL_API)
            json_dict = response.json()
            
            #export out as individual json files of the reference tide station data
            #out_file = open("E:/csb/jsondump1/"+ts['ControlStn'][ind]+'.json', 'w')
            #json.dump(json_dict, out_file, indent = 6)
            #out_file.close()
            
            try:
                data = pd.json_normalize(json_dict["data"])
                data[['v']] = data[['v']].apply(pd.to_numeric)
                data = data.astype({'t':'datetime64'})
                #data = data.rename(columns={'t': 'time'})
                tdf.append(data)
            except Exception:
                continue
        try:
            tdf = pd.concat(tdf)
        except Exception:
            continue
        tdf = tdf.sort_values('t')
        join = join.sort_values('time')
              
        jtdf = pd.merge_asof(join, tdf, left_on='time', right_on='t')
        jtdf = jtdf.drop(columns=['ControlS_1'])
        jtdf = jtdf.drop(columns=['ControlS_2'])
        jtdf = jtdf.dropna()
        jtdf['t_corr'] = jtdf['t'] + pd.to_timedelta(jtdf['ATCorr'], unit='m')
        
        #jtdf.to_csv(r'E:\csb\jtdf_test3.csv', index=True)
        
        newdf = jtdf[['t_corr','v']].copy()
        newdf = newdf.rename(columns={'v':'v_new', 't_corr':'t_new'})
        newdf = newdf.sort_values('t_new')
        newdf = newdf.dropna() 
        csb_corr = pd.merge_asof(jtdf, newdf, left_on='time', right_on='t_new')
        csb_corr = csb_corr.dropna()
        
        csb_corr['depth_new'] = csb_corr['depth'] - (csb_corr['RR'] * csb_corr['v_new'])                
        csb_corr = gpd.GeoDataFrame(csb_corr, geometry='geometry')
        csb_corr['time'] = csb_corr['time'].dt.strftime("%Y%m%d %H:%M")
        #filter out depths less than 1.5m and greater than 1000m
        csb_corr = csb_corr[csb_corr['depth'] > 1.5]
        csb_corr = csb_corr[csb_corr['depth'] < 1000]
        csb_corr = csb_corr.drop(columns=['index_right','ATCorr','RR','ATCorr2','RR2','DataProv','Shape_Leng','Shape_Area','Shape_Le_1','t','v','s','f','q','t_corr','t_new','v_new','depth'])
        print(csb_corr)
        try:   
            csb_corr.to_file('E:/csb/shapefiles/test/csb_'+ title +'.shp', driver='ESRI Shapefile')
        except Exception:
            pass
   
if __name__=="__main__":
    getFiles()
    CorrectTides()