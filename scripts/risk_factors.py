"""Generate different risk Factors."""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.offline import plot
from plotly.subplots import make_subplots


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


# Population data Germany
popi = pd.read_csv("../data/population_germany.csv")
popi.rename(columns={"age": "age_from"}, inplace=True)
popi["age_to"] = popi["age_from"]
popi["age_to"] = np.where(popi["age_to"] == 100, 100, popi["age_to"])
popi = replicate_rows(popi)

# Population by statistical regions
regions = pd.read_csv("../data/nrw/population_regierungsbezirke.csv",
                      encoding="latin1", sep=";")

# Number of inhabitants by age, gender and statistical region
regions = regions.melt(id_vars=["Kennung", "Bezeichnung", "Alter_von"],
                       value_vars=["männlich", "weiblich"], value_name="count",
                       var_name="gender")
regions["gender"] = np.where(regions.gender == "männlich", "m", "f")
regions.rename(columns={"Bezeichnung": "region", "Alter_von": "age_from",
                        "Kennung": "region_id"}, inplace=True)
regions = regions.sort_values(by=["region_id", "gender", "age_from"])
regions["age_to"] = regions["age_from"]
regions["age_to"] = [regions["age_from"][i]-1 for i in
                     range(1, regions.shape[0])] + [100]
regions["age_to"] = np.where(regions["age_from"] == 90, 100, regions["age_to"])
regions["agegroup"] = regions["age_from"].astype(str) + "-" +\
    regions["age_to"].astype(str)
regions["count"] = pd.to_numeric(regions["count"], errors="coerce")
regions = replicate_rows(regions)

# actual death rates from italy for covid 19 cases
italy = pd.read_csv("../data/Italy_reported_cases_versus_death_rates.csv",
                    sep=";", decimal=",")
italy["age_to"] = np.where(italy["age_to"] > 100, 100, italy["age_to"])
italy = replicate_rows(italy)

# Now we have thre dataset with different age segment and we need to
# merge them properly
regions = regions.merge(popi[["age", "gender", "deathrate", "contacts_mean"]],
                        on=["age", "gender"], how='left')
regions = regions.merge(italy[["age", "gender", "death_per_mio",
                              "cases_per_mio"]], on=["age", "gender"],
                        how="left")

regions = regions.groupby(['region_id', 'region', 'agegroup', 'gender',
                           'age_from']).agg(
                          count=("count", "mean"),
                          death_per_mio=('death_per_mio', 'mean'),
                          cases_per_mio=('cases_per_mio', 'mean'),
                          contacts_mean=('contacts_mean', 'mean'),
                          deathrate=('deathrate', 'mean'),)

regions.reset_index(inplace=True)
regions.rename(columns={"deathrate": "long_term_deathrate"}, inplace=True)
regions["deaths_100k_index1"] = regions["long_term_deathrate"] *\
    regions["count"]
regions["deaths_100k_index1"] = regions["deaths_100k_index1"] * 100000 /\
    np.sum(regions["deaths_100k_index1"])

regions["deaths_100k_index2"] = regions["death_per_mio"] *\
    regions["count"]
regions["deaths_100k_index2"] = regions["deaths_100k_index2"] * 100000 /\
    np.sum(regions["deaths_100k_index2"])
regions = regions[regions["count"].notna()]

byregion = regions.groupby("region").agg(
    deaths_100k_index1=("deaths_100k_index1", "sum"),
    deaths_100k_index2=("deaths_100k_index2", "sum"),
    inhabitants=("count", "sum"),
)
byregion.reset_index(inplace=True)
byregion["per100k_index1"] = byregion["deaths_100k_index1"] *100000 /\
    byregion["inhabitants"]
byregion["per100k_index2"] = byregion["deaths_100k_index2"] *100000 /\
    byregion["inhabitants"]
    
aux = regions[["death_per_mio", "deaths_100k_index1", "count"]]
aux = aux.sort_values(by="deaths_100k_index1", ascending=False)
aux["inhab"] = np.cumsum(aux["count"])
aux["deaths"] = np.cumsum(aux["deaths_100k_index1"])

fig = go.Figure()
fig.add_trace(go.Scatter(x=aux["inhab"],y=aux["deaths"], mode='lines'))
fig.update_layout(
    title="Kumulierte Tote sortiert nach Riskiofaktor 1",
    xaxis_title="Einwohner",
    yaxis_title="Tote",
    showlegend=False,
    font=dict(
        family="Courier New, monospace",
        size=14,
        color="#7f7f7f"
    )
)

fig.write_image("ungleichverteilung.png")
with pd.ExcelWriter('regierungsbezierke.xlsx') as writer:
    regions.to_excel(writer, sheet_name='Details', index=False)
    byregion.to_excel(writer, sheet_name='Zusammenfassung', index=False)



