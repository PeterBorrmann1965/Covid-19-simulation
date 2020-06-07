import covid19sim.coronalib as cl
import pandas as pd 
import numpy as np
import plotly.express as px
import os
import datetime
import json

with open("../data/landkreises.geojson") as f:
    geojson = json.load(f)
    
import plotly.graph_objects as go
# =============================================================================
# fig = go.Figure(go.Choroplethmapbox(geojson=lkshapes,  locations=lk.Landkreis,
#                                     z=lk.AnzahlFall,
#                                     featureidkey="properties.county",
#                                     colorscale="Viridis", zmin=0, zmax=100,
#                                     marker_opacity=0.5, marker_line_width=0))
# fig = px.choropleth_mapbox(lk, geojson=geojson, color="AnzahlFall",
#                            locations="Landkreis", featureidkey="properties.county",
#                            center={"lat": 50.110924, "lon":8.682127},
#                            mapbox_style="carto-positron", zoom=9)
# fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
# plot(fig)
# 
# =============================================================================

rki = pd.read_csv("../data/RKI_COVID19.csv")
rki["Meldedatum"] = pd.to_datetime(rki.Meldedatum, infer_datetime_format=True)
rki["Meldedatum"] = rki["Meldedatum"].dt.date
rki["Refdatum"] = pd.to_datetime(rki.Refdatum, infer_datetime_format=True)
rki["Refdatum"] = rki["Refdatum"].dt.date
rki["KW"] = [x.isocalendar()[1] for x in rki.Meldedatum]
rki["Meldeverzug"] = (rki["Meldedatum"]-rki["Refdatum"]).dt.days
rki["Meldeverzug"] = np.where(rki.IstErkrankungsbeginn == 0, np.NaN,
                              rki["Meldeverzug"])
rki["VorErkrankung"] = np.where(rki["Meldeverzug"] < 0, rki.AnzahlFall, 0)


bl = pd.read_csv("../data/RKI_Corona_Landkreise.csv", sep=",")
rki = rki.merge(bl[["RS", "EWZ", "Shape__Area", "GEN"]],
                left_on="IdLandkreis", right_on="RS", how="left")

rki["Anzahl_Meldeverzug0"] = np.where(rki.IstErkrankungsbeginn == 0, rki.AnzahlFall, 0)
rki["Anzahl_Meldeverzug!=0"] = np.where(rki.IstErkrankungsbeginn != 0, rki.AnzahlFall, 0)
rki["Meldeverzug_Sum"] = rki.Meldeverzug*rki.AnzahlFall


rki["Alter"] = 0
rki["Alter"] = np.where(rki.Altersgruppe == "A00-A04", 2, rki["Alter"])
rki["Alter"] = np.where(rki.Altersgruppe == "A05-A14", 9, rki["Alter"])
rki["Alter"] = np.where(rki.Altersgruppe == "A15-A34", 24, rki["Alter"])
rki["Alter"] = np.where(rki.Altersgruppe == "A35-A59", 47, rki["Alter"])
rki["Alter"] = np.where(rki.Altersgruppe == "A60-A79", 70, rki["Alter"])
rki["Alter"] = np.where(rki.Altersgruppe == "A80+", 85, rki["Alter"])

lk = rki.groupby("Landkreis").agg(
    AnzahlTodesfall=("AnzahlTodesfall", "sum"),
    AnzahlFall=("AnzahlFall", "sum"),
    EWZ=("EWZ", "max"),
    AREA=("Shape__Area", "max"),
    Anzahl_Meldeverzug0=("Anzahl_Meldeverzug0", "sum"),
    Anzahl_Meldeverzug1=("Anzahl_Meldeverzug!=0", "sum"),
    Meldeverzug_sum=("Meldeverzug_Sum", "sum"),
    Alter=("Alter", "mean"),
    LetzerFall=("Refdatum", "max"),
    LetzeMeldung=("Meldedatum", "max"),
    Erkrankungsbeginn=("IstErkrankungsbeginn", "mean"),
    VorErkrankung=("VorErkrankung", "sum")
    )
lk["Inzidenzen"] = lk.AnzahlFall / lk.EWZ * 100000
lk["Mean_Meldeverzug"] = lk.Meldeverzug_sum / lk.Anzahl_Meldeverzug1
lk["Anteil_D0"] = lk.Anzahl_Meldeverzug0 / lk.AnzahlFall
lk["Dichte"] = lk.EWZ  / lk.AREA
lk["CFR"] = lk.AnzahlTodesfall / lk.AnzahlFall
lk.fillna(0,inplace=True)
lk = lk.sort_values(by="Inzidenzen",ascending=False)
lk["EWcum"] = lk.EWZ.cumsum() /  lk.EWZ.sum()
lk["Fallcum"] = lk.AnzahlFall.cumsum() /  lk.AnzahlFall.sum()
px.scatter(lk,x="EWcum",y="Fallcum")

age, agegroup, gender, contacts, drate, hnr, persons = cl.makepop("current",
                                                                  1000000)
drate = 1-(1-drate)**365
df = pd.DataFrame({"Alter": age, "Sterberate": drate})
df["Altersgruppe"] = "A00-A04"
df["Altersgruppe"] = np.where(age > 4, "A05-A14", df.Altersgruppe)
df["Altersgruppe"] = np.where(age > 14, "A15-A34", df.Altersgruppe)
df["Altersgruppe"] = np.where(age > 34, "A35-A59", df.Altersgruppe)
df["Altersgruppe"] = np.where(age > 59, "A60-A79", df.Altersgruppe)
df["Altersgruppe"] = np.where(age > 79, "A80+", df.Altersgruppe)
agpop = df.groupby("Altersgruppe").agg(Anteil_Pop=("Alter", "count"),
                                       Sterberate=("Sterberate", "mean"))

germany = rki.groupby(["Meldedatum"]).agg(
    Tote=('AnzahlTodesfall', 'sum'), Fälle=("AnzahlFall", "sum"))
germany["Fälle_kum"] = np.cumsum(germany.Fälle)
germany["Tote_kum"] = np.cumsum(germany.Tote)
germany["Region"] = "Deutschland"
germany["Ebene"] = "Land"
germany.reset_index(inplace=True)

regionen = [germany]
for bl in rki.Bundesland.unique():
    bundesland = rki[rki.Bundesland == bl].copy()
    bundesland = bundesland.groupby(["Meldedatum"]).agg(
        Tote=('AnzahlTodesfall', 'sum'), Fälle=("AnzahlFall", "sum"))
    bundesland["Fälle_kum"] = np.cumsum(bundesland.Fälle)
    bundesland["Tote_kum"] = np.cumsum(bundesland.Tote)
    bundesland["Region"] = bl
    bundesland["Ebene"] = "Bundesland"
    bundesland.reset_index(inplace=True)
    regionen.append(bundesland)

for bl in rki.Landkreis.unique():
    bundesland = rki[rki.Landkreis == bl].copy()
    bundesland = bundesland.groupby(["Meldedatum"]).agg(
        Tote=('AnzahlTodesfall', 'sum'), Fälle=("AnzahlFall", "sum"))
    bundesland["Fälle_kum"] = np.cumsum(bundesland.Fälle)
    bundesland["Tote_kum"] = np.cumsum(bundesland.Tote)
    bundesland["Region"] = bl
    bundesland["Ebene"] = "Landkreis"
    bundesland.reset_index(inplace=True)
    regionen.append(bundesland)

regionen = pd.concat(regionen)
regionen.to_excel("../data/RKI_COVID19_Kum.xlsx", index=False)

nrw = regionen[regionen.Region == 'Nordrhein-Westfalen']

#rki = rki[rki.Bundesland == "Nordrhein-Westfalen"]
writer = pd.ExcelWriter("../data/agnew.xlsx")
ag = rki.pivot_table(columns="KW", index="Altersgruppe",
        values="AnzahlFall", aggfunc="sum", fill_value=0)
ag = ag.merge(agpop, on="Altersgruppe", how="left")
ag = ag.transpose()
ag["All"] = ag["All"] = ag.sum(axis=1)
ag.loc["Sterberate","All"] = 1
ag.reset_index(inplace=True)
ag.to_excel(writer, sheet_name="Fälle", index=False)
for c in rki.Altersgruppe.unique():
    ag[c] = ag[c] / ag["All"]

ag.to_excel(writer, sheet_name="Fälle_Anteil", index=False)

ag = rki.pivot_table(columns="KW", index="Altersgruppe",
                     values="AnzahlTodesfall", aggfunc="sum", fill_value=0)
ag = ag.merge(agpop, on="Altersgruppe", how="left")
ag = ag.transpose()
ag["All"] = ag["All"] = ag.sum(axis=1)
ag.loc["Sterberate","All"] = 1
ag.reset_index(inplace=True)
ag.to_excel(writer, sheet_name="Fälle_Tote", index=False)
for c in rki.Altersgruppe.unique():
    ag[c] = ag[c] / ag["All"]

ag.to_excel(writer, sheet_name="Tote_anteil", index=False)

lastcase = rki.groupby("Landkreis").agg(
        AnzahlFall=("AnzahlFall", "sum"),
        LetzerFall=("Refdatum", "max"),
        LetzeMeldung=("Meldedatum", "max")
    )

writer.close()

heinsberg = rki[rki["Landkreis"] =="LK Heinsberg"]




