import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.offline import plot
from plotly.subplots import make_subplots
import plotly.express as px
import coronalib as cl

campus = pd.read_csv("/home/borrmann/campusfiles/mz2010_cf.csv", sep=";",
                     decimal=".")
popi = pd.read_csv("../data/population_germany_v2.csv")

campus.columns = [str(x) for x in campus.columns]

colnames = {
    "EF44": "age",
    "EF46": "gender",
    "EF3s": "ab",
    "EF4s": "hnr",
    "EF5s": "pnr",
    "EF20": "Personenzahl",
    "EF31": "Art_Unterkunft"}

campus.columns = [str(x) for x in campus.columns]

campus = campus[[x for x in colnames.keys()]].copy()
campus.rename(columns=colnames, inplace=True)
campus["gender"] = np.where(campus.gender == 1, "m", "f")

# Convert hnr to int
campus["hnrnew"] = campus["ab"].astype(str) + "_" + campus["hnr"].astype(str)
campus["hnrnew"] = campus["hnrnew"].astype("category").cat.codes

# Merge contacts an deathrate
popi = popi.drop_duplicates(subset=["gender", "age", "deathrate",
                                    "contacts_mean", "agegroup"])
campus = campus.merge(popi[["gender", "age", "deathrate", "contacts_mean",
                           "agegroup"]], on=["age", "gender"], how="left")

campus[['age', 'gender', 'hnrnew', 'Personenzahl', 'Art_Unterkunft',
               'deathrate', 'contacts_mean', 'agegroup']].to_csv(
                   "../data/population_campus.csv")



# =============================================================================
# aux = campus.groupby(["age"]).agg(Anzahl=("hnr", "count"),
#                             Personen=("Personenzahl", "mean"))
# aux.reset_index(inplace=True)
# aux["Personen"] = aux["Personen"] - 1
# 
# fig = px.scatter(aux, x="age", y="Personen",
#                  title="Mittlere Anzahl weiterer Personen im HH/GU")
# fig.show()
# 
# campus["agegroup"] = np.array(campus["age"]/10, dtype="int")*10
# campus["persgroup"] = campus["Personenzahl"]-1
# campus["persgroup"] = np.where(campus.persgroup > 4,
#                                ">4", campus.persgroup.astype(str))
# 
# aux = campus.groupby(["agegroup", "persgroup"]).agg(Anzahl=("age", "count"))
# aux.reset_index(inplace=True)
# aux = aux.pivot_table(index="agegroup", columns="persgroup", margins=True,
#                       aggfunc="sum")
# aux.fillna(0, inplace=True)
# aux.columns = aux.columns.get_level_values(1)
# 
# aux = aux / campus.shape[0] 
# aux.reset_index(inplace=True)
# aux.to_excel("../results/age_weitere_personen.xlsx")
# =============================================================================



