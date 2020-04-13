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
import glob

datadir="/mnt/wd1/nrw_corona/"
run = 0

for fname in glob.glob(datadir+"/Restart*.xlsx"):
    print(fname)
    args = pd.read_excel(os.path.join(datadir, fname), sheet_name=0)
    args = dict(zip(args.Parameter, args.Wert))
    gr = pd.read_excel(os.path.join(datadir, fname), sheet_name=2)
    gr.loc[gr.Datum == datetime.datetime(2020, 4, 9), "RKI Neu-Meldefälle"] = np.NAN
    gr.loc[gr.Datum == datetime.datetime(2020, 4, 9), "RKI Gesamt-Meldefälle"] = np.NAN
    gr["Wochentag"] = [x.weekday() for x in gr.Datum]
    gr["WE"] = np.where(gr.Wochentag > 4, "WE", "WT")
    fig = make_subplots(rows=1, cols=1)
    fig.add_trace(go.Scatter(x=gr["Datum"], y=gr["Erwartete Gesamt-Meldefälle"],
                            name="Erwartete Gesamt-Meldefälle",
                            mode="lines"), row=1, col=1)
    fig.add_trace(go.Scatter(x=gr["Datum"], y=gr["RKI Gesamt-Meldefälle"],
                            name="RKI Gesamt-Meldefälle",
                            mode="lines"), row=1, col=1)
    k = 0
    for dat in [datetime.date(2020, 3, 8), datetime.date(2020, 3, 16),
                datetime.date(2020, 3, 23), datetime.date(2020, 4, 20)]:
        fig.add_shape(
                # Line Vertical
                dict(type="line", x0=dat, y0=0, x1=dat,
                     y1=max(gr["Erwartete Gesamt-Meldefälle"]),
                     line=dict(color="MediumPurple", dash="dot", width=1)))
        k = k+1
        fig.add_trace(go.Scatter(
        x=[dat],
        y=[max(gr["Erwartete Gesamt-Meldefälle"])*1.03],
        text=["M"+str(k)],
        mode="text",showlegend=False))
    
    fig.update_layout(legend_orientation="h", font=dict(size=22))
    fig.update_traces(textfont_size=16)
    fig.update_yaxes(title_text="Anzahl Gesamt-Meldefälle", tickformat="digit")
    fig.write_image(os.path.join(datadir, args["simname"] + "_cum22.png"),
                    width=1200, height=800)





