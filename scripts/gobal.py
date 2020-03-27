#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 23 09:24:33 2020

@author: borrmann
"""
import numpy as np
import pandas as pd
import coronalib as cl
import scipy.stats 
from scipy.optimize import minimize

def l2(x, repo, deaths):
    lamb, cfr = x[0], x[1]
    pdf = [scipy.stats.poisson.pmf(i, lamb) for i in range(0, 200)]
    expected = np.zeros(shape=repo.shape[0])
    expected[0] = 0
    for t in range(1, len(repo)):
        expected[t] = 0
        for s in range(0, t):
            expected[t] = expected[t] + repo[t-s] * pdf[s]
    expected = expected * cfr
    return np.mean(np.abs(expected-deaths))

jhdir = "/home/borrmann/JohnsHopkins/COVID-19/csse_covid_19_data/csse_covid_19_time_series/"

reported = pd.read_csv(jhdir+"time_series_covid19_confirmed_global.csv")
deaths = pd.read_csv(jhdir+"time_series_covid19_deaths_global.csv")

reported = reported.melt(value_name="cases", var_name="date", id_vars=[
    'Province/State', 'Country/Region', 'Lat', 'Long'])
deaths = deaths.melt(value_name="cases", var_name="date", id_vars=[
    'Province/State', 'Country/Region', 'Lat', 'Long'])

reported["date"] = pd.to_datetime(reported["date"], infer_datetime_format=True)
deaths["date"] = pd.to_datetime(deaths["date"], infer_datetime_format=True)
reported.drop(columns=["Lat", "Long"], inplace=True)
deaths.drop(columns=["Lat", "Long"], inplace=True)

reported.rename(columns={"cases": "reported"}, inplace=True)
deaths.rename(columns={"cases": "deaths"}, inplace=True)
reported["Province/State"].fillna("None", inplace=True)
deaths["Province/State"].fillna("None", inplace=True)

cases = reported.merge(deaths, on=['Province/State', 'Country/Region', 'date'])

italy = pd.read_csv(
    "../data/COVID-19/dati-regioni/dpc-covid19-ita-regioni.csv")
italy = italy[['data', 'stato', 'denominazione_regione', 'deceduti',
               'totale_casi']]
italy.rename(columns={"data": "date", 'denominazione_regione':
                      'Province/State', 'deceduti': "deaths",
                      'stato': 'Country/Region', 'totale_casi': 'reported'},
             inplace=True)
italy["Country/Region"] = "Italy"
cases = pd.concat([cases, italy])


aux = cases.groupby(['Province/State', 'Country/Region']).agg(
    reported=("reported", "max"),
    deaths=("deaths", "max")
    )
aux = aux.sort_values(by=["deaths"], ascending=False)
aux.reset_index(inplace=True)

allres = []
for index, row in aux.iterrows():
    if row["deaths"] >= 150:
        country = cases[(cases["Country/Region"] == row["Country/Region"]) &
                        (cases["Province/State"] == row["Province/State"])
                        ].copy()
        country = country.sort_values(by=["date"]).copy()
        name = row["Country/Region"]
        if row["Province/State"] != "None":
            name = name + ", " + row["Province/State"]
            
        repo = np.diff(country.reported, prepend=0)
        deaths = np.diff(country.deaths, prepend=0)
        pars = minimize(l2,[6,0.02], args=(repo,deaths), method='Nelder-Mead')
        print(name, pars.x)
# =============================================================================
#         res = cl.cfr_from_ts(country["date"], country["reported"],
#                              country["deaths"], 15, name)
#         res["country"] = row["Country/Region"]
#         res["state"] = row["Province/State"]
#         allres.append(res)
# =============================================================================
allres = pd.DataFrame(allres)
print(allres)

country = cases[(cases["Country/Region"] == "Germany")].copy()






