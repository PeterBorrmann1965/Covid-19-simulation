#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 23 09:24:33 2020

@author: borrmann
"""
import numpy as np
import pandas as pd

jhdir = "/home/borrmann/JohnsHopkins/COVID-19/csse_covid_19_data/csse_covid_19_time_series/"

reported = pd.read_csv(jhdir+"time_series_covid19_confirmed_global.csv")

reported = reported.melt(value_name="cases", var_name="date", id_vars=[
    'Province/State', 'Country/Region', 'Lat', 'Long'])

reported["date"] = pd.to_datetime(reported["date"], infer_datetime_format=True)

germany = reported[reported["Country/Region"] == "Germany"]
germany["newcases"] = np.diff(germany.cases, prepend=0)

