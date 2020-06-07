import covid19sim.coronalib as cl
import pandas as pd 
import numpy as np
import plotly.express as px
import os

rki = pd.read_csv("../data/RKI_COVID19.csv")
rki["Meldedatum"] = pd.to_datetime(rki.Meldedatum, infer_datetime_format=True)
rki["Meldedatum"] = rki["Meldedatum"].dt.date
rki["Refdatum"] = pd.to_datetime(rki.Refdatum, infer_datetime_format=True)
rki["Refdatum"] = rki["Refdatum"].dt.date
rki["KW"] = [x.isocalendar()[1] for x in rki.Meldedatum]
rki["Delta"] = (rki["Meldedatum"]-rki["Refdatum"]).dt.days
bl = pd.read_csv("../data/RKI_Corona_Landkreise.csv", sep=",")
rki = rki.merge(bl[["RS", "EWZ", "Shape__Area", "GEN"]],
                left_on="IdLandkreis", right_on="RS", how="left")

rki["Anzahl_Delta0"] = np.where(rki.Delta == 0, rki.AnzahlFall, 0)
rki["Anzahl_Delta!=0"] = np.where(rki.Delta != 0, rki.AnzahlFall, 0)
rki["Delta_Sum"] = rki.Delta*rki.AnzahlFall


lk = rki.groupby(["Landkreis", "KW"]).agg(
    AnzahlTodesfall=("AnzahlTodesfall", "sum"),
    AnzahlFall=("AnzahlFall", "sum"),
    EWZ=("EWZ", "max"),
    AREA=("Shape__Area", "max"),
    Anzahl_Delta0=("Anzahl_Delta0", "sum"),
    Anzahl_Delta1=("Anzahl_Delta!=0", "sum"),
    Delta_sum=("Delta_Sum", "sum"),
    Alter=("Alter","mean")
    )
lk["Inzidenzen"] = lk.AnzahlFall / lk.EWZ * 100000
lk["Mean_Delta"] = lk.Delta_sum / lk.Anzahl_Delta1
lk["Anteil_D0"] = lk.Anzahl_Delta0 / lk.AnzahlFall
lk["Dichte"] = lk.EWZ  / lk.AREA
lk.reset_index(inplace=True)
lk.fillna(0,inplace=True)