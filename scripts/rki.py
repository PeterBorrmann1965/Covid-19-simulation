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
rki.to_excel("../data/RKI_COVID19_New.xlsx", index=False)

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

rki = rki[rki.Bundesland == "Nordrhein-Westfalen"]
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
writer.close()



