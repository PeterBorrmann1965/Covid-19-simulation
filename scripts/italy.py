"""Analyse der italienischen Corona Faelle."""
import numpy as np
import pandas as pd
import git
import plotly.graph_objects as go
from plotly.offline import plot
from plotly.subplots import make_subplots

# Get the latest data from Italy
try:
    git.Git("../data").clone("https://github.com/pcm-dpc/COVID-19.git")
except:
    repo = git.Repo('../data/COVID-19')
    o = repo.remotes.origin
    o.pull()

# Daten einlesen
provinzen = pd.read_csv(
    "../data/COVID-19/dati-province/dpc-covid19-ita-province.csv")

regionen = pd.read_csv(
    "../data/COVID-19/dati-regioni/dpc-covid19-ita-regioni.csv")
# Die Region 4 tritt doppelt auf und wird zusammengefasst
regionen.loc[regionen["denominazione_regione"] ==
             "P.A. Bolzano", "denominazione_regione"] = "P.A Bolzano/Trento"
regionen.loc[regionen["denominazione_regione"] ==
             "P.A. Trento", "denominazione_regione"] = "P.A Bolzano/Trento"
regionen.drop(columns=['lat', 'long', 'stato'])
regionen = regionen.groupby(['data', 'codice_regione',
                             'denominazione_regione']).sum()
regionen.reset_index(inplace=True)

national = pd.read_csv(
    "../data/COVID-19/dati-andamento-nazionale/dpc-covid19-ita-andamento-nazionale.csv")

national["denominazione_regione"] = "Italia"
national["codice_regione"] = -1
national["lat"] = 0.0
national["long"] = 0.0

regionen = pd.concat([regionen, national])

# Einwohnerzahlen
einwohner = pd.read_csv("../data/regionen_italy.csv")
ewitalia = np.sum(einwohner.Einwohner)
einwohner = einwohner.to_dict(orient="index")
einwohner[-1] = {'Code': -1,
      'Region': 'Italia',
      'Einwohner': ewitalia,
      'Flaeche': 0,
      'Gemeinden': 0}
einwohner = pd.DataFrame.from_dict(einwohner, orient="index")

regionen = regionen.merge(einwohner, left_on="codice_regione",
                          right_on="Code", how="left")

regionen["Faelle/Mio EW"] = regionen["totale_casi"]/regionen["Einwohner"] *\
    1000000
regionen["Krankenhaus/Mio EW"] = regionen["totale_ospedalizzati"] /\
    regionen["Einwohner"]*1000000
regionen["Intensiv/Mio EW"] = regionen["terapia_intensiva"] /\
    regionen["Einwohner"]*1000000

regionen["intensivrate"] = regionen["terapia_intensiva"] /\
    regionen["totale_ospedalizzati"]


reglist = []

figin = go.Figure()

for reg in regionen.denominazione_regione.unique():
    reg = reg.replace("/", "_")
    region = regionen[regionen.denominazione_regione == reg].copy()
    region = region.sort_values(by=["data"])
    region
    region["Tote"] = np.diff(region.deceduti, prepend=0)
    region["infections"] = np.diff(region.totale_casi, prepend=0)
    region["newtests"] = np.diff(region.tamponi, prepend=0)
    region["positivrate"] = region["infections"] / region["newtests"]

    cases = np.array(region["totale_casi"])
    region["growthcases"] = [0] + [0 if cases[i-1] == 0 else
                        (cases[i]/cases[i-1])-1 for i in range(1, len(cases))]

    cases = np.array(region["terapia_intensiva"])
    region["growthintensive"] = [0] + [0 if cases[i-1] == 0 else
                        (cases[i]/cases[i-1])-1 for i in range(1, len(cases))]
    region["weekintensive"] = [0] + [0 if cases[i-7] == 0 else
                        (cases[i]/cases[i-7])-1 for i in range(1, len(cases))]

    cases = np.array(region["totale_ospedalizzati"])
    region["growthospital"] = [0] + [0 if cases[i-1] == 0 else
                        (cases[i]/cases[i-1])-1 for i in range(1, len(cases))]

    region["weekhospital"] = [0] + [0 if cases[i-7] == 0 else
                        (cases[i]/cases[i-7])-1 for i in range(1, len(cases))]



    # Initialize figure with subplots
    fig = make_subplots(
        rows=2, cols=2, subplot_titles=("deaths per day",
                                        "new cases",
                                        "intensive care cases per million",
                                        "hospital cases per million")
    )

    # Add traces
    fig.add_trace(go.Scatter(x=region.data, y=region.Tote), row=1, col=1)
    fig.add_trace(go.Scatter(x=region.data, y=region.infections), row=1, col=2)
    fig.add_trace(go.Scatter(x=region.data, y=region["Intensiv/Mio EW"]),
                  row=2, col=1)
    fig.add_trace(go.Scatter(x=region.data, y=region["Krankenhaus/Mio EW"]),
                  row=2, col=2)

    # All Regions in one chart
    if reg in ['Piemonte', 'Lombardia', 'Italia', 'Umbria', 'Veneto',
               'Emilia Romagna', 'Toscana']:
        figin.add_trace(go.Scatter(x=region.data, y=region["Intensiv/Mio EW"],
                      name=reg))

    # Update xaxis properties
    fig.update_xaxes(title_text="Datum", row=1, col=1)
    fig.update_xaxes(title_text="Datum", row=1, col=2)
    fig.update_xaxes(title_text="Datum", row=2, col=1)
    fig.update_xaxes(title_text="Datum", row=2, col=2)

    # Update yaxis properties
    fig.update_yaxes(title_text="deaths per days", row=1, col=1)
    fig.update_yaxes(title_text="infections per day", row=1, col=2)
    fig.update_yaxes(title_text="intensive care / million", row=2, col=1)
    fig.update_yaxes(title_text="hospital / million", row=2, col=2)

    # Update title and height
    fig.update_layout(height=800, width=1200, showlegend=False, title=reg)
    fig.write_image("../figures/"+reg+".png")

    fig = make_subplots(
        rows=3, cols=2, subplot_titles=("intensive care / hospital",
                                        "growth rate intensive care",
                                        "growth rate hospital",
                                        "growth rate cases")
    )

    # Add traces
    fig.add_trace(go.Scatter(x=region.data, y=region.intensivrate),
                  row=1, col=1)
    fig.add_trace(go.Scatter(x=region.data, y=region.growthintensive),
                  row=1, col=2)
    fig.add_trace(go.Scatter(x=region.data, y=region.growthospital),
                  row=2, col=1)
    fig.add_trace(go.Scatter(x=region.data, y=region.growthcases),
                  row=2, col=2)

    # Update xaxis properties
    fig.update_xaxes(title_text="Datum", row=1, col=1)
    fig.update_xaxes(title_text="Datum", row=1, col=2)
    fig.update_xaxes(title_text="Datum", row=2, col=1)
    fig.update_xaxes(title_text="Datum", row=2, col=2)

    # Update yaxis properties
    fig.update_yaxes(title_text="intensive care / hospital", row=1, col=1)
    fig.update_yaxes(title_text="growth rate intensive care", row=1, col=2)
    fig.update_yaxes(title_text="growth rate hospital", row=2, col=1)
    fig.update_yaxes(title_text="growth rate cases", row=2, col=2)

    # Update title and height
    fig.update_layout(height=800, width=1200, showlegend=False, title=reg)
    fig.write_image("../figures/growth_"+reg+".png")

    fig = make_subplots(
        rows=3, cols=2, subplot_titles=("Tests",
                                        "Positive rate",
                                        "weekly growth intensive",
                                        "weekly growth hospital")
    )

    # Add traces
    fig.add_trace(go.Scatter(x=region.data, y=region.newtests),
                  row=1, col=1)
    fig.add_trace(go.Scatter(x=region.data, y=region.positivrate),
                  row=1, col=2)
    fig.add_trace(go.Scatter(x=region.data, y=region.weekintensive),
                  row=2, col=1)
    fig.add_trace(go.Scatter(x=region.data, y=region.weekhospital),
                  row=2, col=2)

    # Update xaxis properties
    fig.update_xaxes(title_text="Datum", row=1, col=1)
    fig.update_xaxes(title_text="Datum", row=1, col=2)
    fig.update_xaxes(title_text="Datum", row=2, col=1)
    fig.update_xaxes(title_text="Datum", row=2, col=2)

    # Update yaxis properties
    fig.update_yaxes(title_text="Test", row=1, col=1)
    fig.update_yaxes(title_text="postive rate", row=1, col=2)
    fig.update_yaxes(title_text="growth", row=2, col=1)
    fig.update_yaxes(title_text="growth", row=2, col=2)

    # Update title and height
    fig.update_layout(height=800, width=1200, showlegend=False, title=reg)
    fig.write_image("../figures/test_"+reg+".png")

    fig = go.Figure()
    fig.update_layout(height=800, width=1200, showlegend=True, title=reg,
                      legend_orientation="h",
                       font=dict(family="Courier New, monospace", size=16))
    fig.add_trace(go.Scatter(x=region.data, y=region.Tote, name="Tote"))
    fig.add_trace(go.Scatter(x=region.data, y=region.terapia_intensiva,
                             name="ICU"))
    fig.add_trace(go.Scatter(x=region.data, y=region.totale_ospedalizzati/4,
                             name="Krankenhaus/4 (RKI Bedarf)"))
    fig.update_xaxes(title_text="Datum")
    fig.update_yaxes(title_text="Anzahl")
    fig.write_image("../figures/ICU_Auslastung"+reg+".png")
    # plot(fig)
    # plot(fig)
    reglist.append(region)

regionen_new = pd.concat(reglist)
fig.write_image("../figures/intensive_care_regions.png")
regionen_new.to_excel("../results/italy_regions_new.xlsx")
