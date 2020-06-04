"""Simulation of infections for different scenarios."""
import covid19sim.coronalib as cl
import pandas as pd
import numpy as np
import plotly.express as px
import os
import datetime

import plotly.graph_objects as go
from plotly.offline import plot
from plotly.subplots import make_subplots

age, agegroup, gender, contacts, drate, hnr, persons = cl.makepop("household",
                                                                  1790000)

day0date = datetime.date(2020, 3, 8)
rki = pd.read_csv("../data/RKI_COVID19.csv")
rki["Meldedatum"] = pd.to_datetime(rki.Meldedatum, infer_datetime_format=True)
rki["Meldedatum"] = rki["Meldedatum"].dt.date
rki["Refdatum"] = pd.to_datetime(rki.Refdatum, infer_datetime_format=True)
rki["Refdatum"] = rki["Refdatum"].dt.date
rki["KW"] = [x.isocalendar()[1] for x in rki.Meldedatum]
rki["Delta"] = (rki["Meldedatum"]-rki["Refdatum"]).dt.days

brd = rki.copy()
brd = brd.groupby(["Meldedatum", "Altersgruppe"]).agg(Fälle=("AnzahlFall",
                                                             "sum"))
brd.reset_index(inplace=True)
brd = brd.pivot_table(values="Fälle", index="Meldedatum", columns="Altersgruppe",
                margins=True, aggfunc="sum", fill_value=0, margins_name="Fälle")
brd.drop(labels="Fälle",inplace=True)
brd.reset_index(inplace=True)
brd["Fälle_kum"] = np.cumsum(brd.Fälle)
brd["day"] = (brd.Meldedatum - min(brd.Meldedatum)).dt.days
day0 = np.argmax(brd["Meldedatum"] == day0date)
brd["day"] = brd["day"] - brd["day"][day0]

brd_tote = pd.DataFrame({"Datum": [max(rki.Meldedatum)],
                         "Tote": [np.sum(rki.AnzahlTodesfall)],
                         "Intensiv": [np.NaN]
                         })
brd = brd.merge(brd_tote, left_on="Meldedatum",
                right_on="Datum", how="left")
brd["Tote_kum"] = np.cumsum(brd.Tote)
brd.rename(columns={"Tote_kum": "cumdeath"}, inplace=True)
brd.to_excel("./brd_dat.xlsx", index=False)

nrw = rki[(rki.Bundesland == 'Nordrhein-Westfalen')].copy()
nrw = nrw.groupby(["Meldedatum", "Altersgruppe"]).agg(Fälle=("AnzahlFall",
                                                             "sum"))
nrw.reset_index(inplace=True)
nrw = nrw.pivot_table(values="Fälle", index="Meldedatum", columns="Altersgruppe",
                margins=True, aggfunc="sum", fill_value=0, margins_name="Fälle")
nrw.drop(labels="Fälle",inplace=True)
nrw.reset_index(inplace=True)
nrw["Fälle_kum"] = np.cumsum(nrw.Fälle)
nrw["day"] = (nrw.Meldedatum - min(nrw.Meldedatum)).dt.days
day0 = np.argmax(nrw["Meldedatum"] == day0date)
nrw["day"] = nrw["day"] - nrw["day"][day0]

# Tote NRW
nrw_tote = pd.read_csv("../data/nrw_tote.csv")
nrw_tote["Datum"] = pd.to_datetime(nrw_tote.Datum, infer_datetime_format=True)
nrw_tote["Datum"] = nrw_tote["Datum"].dt.date
nrw_tote = nrw_tote[["Datum", "Tote", "Intensiv"]]
nrw_tote.rename(columns={"Tote ohne HS": "Tote"}, inplace=True)
nrw = nrw.merge(nrw_tote, left_on="Meldedatum",
                right_on="Datum", how="left")
nrw["Tote_kum"] = np.cumsum(nrw.Tote)
nrw.rename(columns={"Tote_kum": "cumdeath"}, inplace=True)

# transform contacts
# =============================================================================
# ncon = 12 * contacts
# ncon = np.random.poisson(lam=ncon)
# ncon = ncon /np.mean(ncon)
# contacts = ncon
# =============================================================================


r_change = {}
# Intial r0
r_change['2020-01-01'] = 3 * contacts/np.mean(contacts)
# First change point (8.3.2020)
contacts_new = np.where(age < 20, contacts, contacts)
r_change['2020-03-08'] = 1.0 * contacts_new/np.mean(contacts_new)
# second change point (16.3.2020)
contacts_new = np.where(age < 20, contacts, contacts)
r_change['2020-03-16'] = 0.4 * contacts_new/np.mean(contacts_new)
# third change point (23.3.2020)
contacts_new = np.where(age < 20, contacts, contacts)
r_change['2020-03-23'] = 0.4 * contacts_new/np.mean(contacts_new)

com_attack_rate = {}
com_attack_rate["2020-01-1"] = 0.5
com_attack_rate["2020-05-4"] = 0.25

state, statesum, infections, day0, rnow, args, gr = cl.sim(
        age, drate, nday=180, prob_icu=0.009, day0cumrep=450,
        mean_days_to_icu=16, mean_duration_icu=14,
        mean_time_to_death=21,
        mean_serial=7.5, std_serial=3.0, immunt0=0.0, ifr=0.003,
        long_term_death=False, hnr=None, com_attack_rate=com_attack_rate,
        r_change=r_change, simname="Test",
        datadir="/mnt/wd1/nrw_corona/",
        realized=nrw, rep_delay=13, alpha=0.125, day0date=day0date)

cl.plotoverview(gr, args)
