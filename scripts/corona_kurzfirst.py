"""Simulation of infections for different scenarios."""
import covid19sim.coronalib as cl
import pandas as pd
import numpy as np
import plotly.express as px
import os
import datetime
import plotly.express as px

import plotly.graph_objects as go
from plotly.offline import plot
from plotly.subplots import make_subplots
import plotly.io as pio

age, agegroup, gender, contacts, drate, hnr, persons = cl.makepop("household",
                                                                  17900000)

day0date = datetime.date(2020, 3, 16)
rki = pd.read_csv("../data/RKI_COVID19.csv")
rki["Meldedatum"] = pd.to_datetime(rki.Meldedatum, infer_datetime_format=True)
rki["Meldedatum"] = rki["Meldedatum"].dt.date
rki["Refdatum"] = pd.to_datetime(rki.Refdatum, infer_datetime_format=True)
rki["Refdatum"] = rki["Refdatum"].dt.date
rki["KW"] = [x.isocalendar()[1] for x in rki.Meldedatum]
rki["Delta"] = (rki["Meldedatum"]-rki["Refdatum"]).dt.days

nrw = rki[(rki.Bundesland == 'Nordrhein-Westfalen') &
          (rki.Landkreis != "LK Heinsberg")
          ].copy()
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
nrw_tote = nrw_tote[["Datum", "Tote ohne HS"]]
nrw_tote.rename(columns={"Tote ohne HS": "Tote"}, inplace=True)
nrw = nrw.merge(nrw_tote, left_on="Meldedatum",
                right_on="Datum", how="left")
nrw["Tote_kum"] = np.cumsum(nrw.Tote)
nrw.rename(columns={"Tote_kum": "cumdeath"}, inplace=True)


statesums = {}
k = 0
akt = 0.9
for run in range(0, 1):
    for lr in [0.9]:
        state, statesum, infections, day0, rnow, args, gr = cl.sim(
                age, drate, nday=150, lock_icu=10, prob_icu=0.01125,
                day0cumrep=nrw[nrw.day == 0]["Fälle_kum"].values[0],
                mean_days_to_icu=7, mean_duration_icu=10,
                mean_serial=7.0, std_serial=3.0,
                immunt0=0.0, ifr=0.004, long_term_death=False,
                hnr=hnr,
                com_attack_rate=0.8, contacts=contacts, r_mean=3.3,
                day_change=[0, 6, 13, 42],
                r_change=[1.84, 1.04, akt, lr],
                rlock_mean=None, simname="Restart r="+str(lr) +
                    " (R_akt="+str(akt)+ ") Run="+ str(run),
                datadir="/mnt/wd1/nrw_corona/", deaths=nrw,
                contacts_lock=None, rep_delay=6.7, alpha=0.125,
                day0date=day0date)

        gr["Wochentag"] = [x.weekday() for x in gr.Datum]
        gr["WE"] = np.where(gr.Wochentag > 4, "WE", "WT")
        fig = make_subplots(rows=3, cols=1)

        fig.add_trace(go.Scatter(x=gr["Datum"], y=gr["Erwartete Neu-Meldefälle"],
                                mode="lines",
                    name="Erwartete Neu-Meldefälle"),
                    row=1, col=1)
        fig.add_trace(go.Scatter(x=gr[gr.WE == "WE"]["Datum"],
                                y=gr[gr.WE == "WE"]["RKI Neu-Meldefälle"],
                                name="RKI Neu-Meldefälle (WE)",
                                mode="markers"), row=1, col=1)
        fig.add_trace(go.Scatter(x=gr[gr.WE == "WT"]["Datum"],
                                y=gr[gr.WE == "WT"]["RKI Neu-Meldefälle"],
                                name="RKI Neu-Meldefälle (WT)",
                                mode="markers"), row=1, col=1)

        fig.add_trace(go.Scatter(x=gr["Datum"], y=gr["Erwartete Gesamt-Meldefälle"],
                                name="Erwartete Gesamt-Meldefälle",
                                mode="lines"), row=2, col=1)
        fig.add_trace(go.Scatter(x=gr["Datum"], y=gr["RKI Gesamt-Meldefälle"],
                                name="RKI Gesamt-Meldefälle",
                                mode="lines"), row=2, col=1)

        fig.add_trace(go.Scatter(x=gr["Datum"], y=gr["Erwartete Tote"],
                                name="Erwartete Tote",
                                mode="lines"), row=3, col=1)
        fig.add_trace(go.Scatter(x=gr["Datum"], y=gr["MAGS Tote gesamt"],
                                name="MAGS Tote gesamt",
                                mode="lines"), row=3, col=1)
        fig.update_layout(legend_orientation="h", title=args["simname"])
        plot(fig, filename=os.path.join(args["datadir"], args["simname"]+".html"))
