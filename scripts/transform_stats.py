#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 24 09:50:53 2020

@author: borrmann
"""
import pandas as pd
import numpy as np
def replicate_rows(df, from_col="age_from", to_col="age_to", new_col="age"):
    """Replicate rows."""
    idict = df.to_dict(orient="index")
    newdict = []
    for row in idict.values():
        for age in range(row[from_col], row[to_col]+1):
            newrow = row.copy()
            newrow["age"] = age
            newrow["nrep"] = row[to_col] - row[from_col] + 1
            newdict.append(newrow)
    res = pd.DataFrame(newdict)
    return res


sterbtafel = pd.read_csv("../data/sterbetafeln.csv", sep=";", decimal=",")
sterb = sterbtafel[sterbtafel.Zeitraum == "B"].copy()

popi = pd.read_csv("../data/populatzion_with_family_status.csv", sep=";",
                   decimal=",")

aux = popi.melt(id_vars=["nationality", "gender", "age_from", "age_to"],
                var_name="family")
aux["value"] = pd.to_numeric(aux["value"], errors="coerce")
aux["value"] = aux["value"].fillna(0)
aux = aux.groupby(by=['gender', 'age_from', 'age_to', 'family']).\
    agg(cnt=('value', 'sum'))
aux.reset_index(inplace=True)
aux = replicate_rows(aux)
aux = aux.merge(sterb, on=["age", "gender"])
aux["cnt2"] = aux["cnt"] / aux["nrep"]
aux["faktor"] = 1

for g in ["m", "f"]:
    for f in aux["family"].unique():
        filt = (aux.gender == g) & (aux.family == f)
        xm = np.array(aux[filt]["deathrate"])
        nrep = np.array(aux[filt]["nrep"])
        new = np.ones(shape=len(xm))
        for i in range(1, len(xm)):
            if nrep[i] > 1:
                new[i] = new[i-1] * (1-xm[i-1])
        new[nrep > 1] = new[nrep > 1] / np.sum(new[nrep > 1])
        aux.loc[filt, "faktor"] = new


aux["cnt"] = aux["cnt"] * aux["faktor"]
aux.drop(columns=["Alter", "Zeitraum", "cnt2", "faktor"],inplace=True)

print(np.sum(aux.cnt*aux.deathrate) / np.sum(aux.cnt) * 17.9 * 1.e6)
print(np.sum(aux.cnt*aux.deathrate))
aux["portion"] = aux["cnt"] / np.sum(aux["cnt"])

aux["family_factor"] = np.where(aux.family.isin(
                                 ['verheiratet', "'verheiratet_lp'"]), 1, 0)

aux2 = pd.read_csv("../data/population_germany.csv")
aux = aux.merge(aux2[["age", "gender", "agegroup", "contacts_mean"]],
                on=["age", "gender"], how="left")
aux.to_csv("../data/population_germany_v2.csv", index=False)
