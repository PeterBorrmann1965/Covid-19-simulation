"""Create Population with family status."""
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


popi = pd.read_csv("../data/populatzion_with_family_status.csv", sep=";",
                   decimal=",")

for c in ['ledig', 'verheiratet', 'verwitwet', 'geschieden', 'verheiratet_lp',
          'geschieden_lp', 'verwitwet_lp']:
    popi[c] = pd.to_numeric(popi[c], errors="coerce")
popi.fillna(0, inplace=True)


popi = popi.melt(id_vars=["nationality", "gender", "age_from", "age_to"],
                 value_name="cnt", var_name="family")
popi = popi.groupby(["gender", "age_from", "age_to", "family"]).agg(
    cnt=("cnt", "sum"))
popi.reset_index(inplace=True)

popi = replicate_rows(popi)
popi["cnt"] = popi["cnt"] / popi["nrep"]

aux = pd.read_csv("../data/population_germany.csv")
popi = popi.merge(aux[['agegroup', 'age', 'deathrate', 'gender', 'contacts_mean']])
popi["family_factor"] = np.where(popi.family.isin(
                                 ['verheiratet', "'verheiratet_lp'"]), 1, 0)
popi["portion"] = popi["cnt"] / np.sum(popi["cnt"])

popi.to_csv("../data/population_new.csv", index=False)
