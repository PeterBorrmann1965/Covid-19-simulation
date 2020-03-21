"""Simulation of infections for different scenarios."""
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.offline import plot
import coronalib as cl

# Read population data
popi = pd.read_csv("../data/population_new.csv")
n = 1000000
popi["N1M"] = np.around(popi.portion * n)
dn = n - np.sum(popi["N1M"])
nmax = np.argmax(popi.N1M)
popi.iloc[nmax, popi.columns.get_loc('N1M')] = dn +\
    popi.iloc[nmax, popi.columns.get_loc('N1M')]
np.sum(popi["N1M"])

# Generate individuals by repeating the groups
age = np.repeat(popi.age, popi.N1M)
agegroup = np.repeat(popi.agegroup, popi.N1M)
gender = np.repeat(popi.gender, popi.N1M)
contacts = np.repeat(popi.contacts_mean, popi.N1M)
family = np.repeat(popi.family_factor, popi.N1M)

# normalize contacts to a mean of one
contacts = contacts / np.sum(contacts)*len(contacts)
dr = np.repeat(popi.deathrate, popi.N1M)

# Calculate daily mortality per case
dr = 1 - (1-dr)**(1/365)

# prepare dataframe
df = pd.DataFrame({"agegroup": agegroup, "contacts": contacts,
                   "gender": gender})

scenario = {}
# set r per case
r0 = 5.0
# all individual get a r value proportional to their normal contact rates
r1 = contacts * r0
scenario["base r0=5.0"] = r1
# =============================================================================
# # people below 20 have get only a 25% contact rate (schools closing)
# r2 = np.where(age < 20, r1 / 4, r1)
# scenario["school closing r0=5.0"] = r2
# # people above 60 have get only a 25% contact rate (schools closing)
# r3 = np.where(age > 60, r1 / 4, r1)
# scenario["elderly protection r0=5.0"] = r3
# 
# =============================================================================
r0 = 2.5
# all individual get a r value proportional to their normal contact rates
r4 = contacts * r0
scenario["base r0=2.5"] = r4
# =============================================================================
# # people below 20 have get only a 25% contact rate (schools closing)
# r5 = np.where(age < 20, r4 / 4, r4)
# scenario["school closing r0=2.5"] = r5
# # people above 60 have get only a 25% contact rate (schools closing)
# r6 = np.where(age > 60, r4 / 4, r4)
# scenario["elderly protection r0=2.5"] = r6
# =============================================================================

fig1 = go.Figure()
fig2 = go.Figure()
fig3 = go.Figure()

results = []
for r0 in [1.5, 1, 7, 2.0, 2.5, 3.0, 3.5]:
    for ff in [0]:
        cutr = r0
        r = contacts * r0
        r = r + ff * family
        r = r * r0 / np.mean(r)
        if r0 == cutr:
            key = "base r0=" + str(r0)
        else:
            key = "lock r0= " + str(r0) + " rlock="+str(cutr)

        key = key + " f=" + str(ff)
        state, statesum, infections = cl.sim(age, gender, dr, r, nday=365,
                                          cutr=cutr)

        # Report the state on the last day
        nday = state.shape[0]-1
        for i in range(1, nday):
            df["state"] = state[i, :]
            a = df.groupby(["agegroup", "gender", "state"]).agg(n=("state", "count"))
            a.reset_index(inplace=True)
            a = a.pivot_table(values="n", columns="state",
                              index=["agegroup", "gender"], margins=True,
                                     aggfunc="sum", fill_value=0)
            a.reset_index(inplace=True)
            a.rename(columns={0: "not infected", 1: "immun or dead", 2: "infected",
                              3: "identified", 4: "dead (other)"}, inplace=True)
            a["not infected %"] = a["not infected"] / a["All"]*100
            a["scenario"] = key
            a["day"] = i
            results.append(a)

        # plot infections
        nmax = np.max(np.where(infections > 0))
        fig1.add_trace(go.Scatter(y=infections[:nmax], mode='lines', name=key))

        # The hospital index is given by the sum of the mortality rates
        # of infected cases
        hospital_index = np.array([np.sum((state[i, :] == 2) * dr)
                                   for i in range(0, state.shape[0])])
        nmax = np.max(np.where(hospital_index > 0))
        fig2.add_trace(go.Scatter(y=hospital_index[:nmax], mode='lines', name=key))

        # infected people
        infected = np.array([np.sum((state[i, :] == 2))
                                   for i in range(0, state.shape[0])])
        nmax = np.max(np.where(infected > 0))
        fig3.add_trace(go.Scatter(y=infected[:nmax], mode='lines', name=key))

        # infected people in age group

        print(key + str(": day with max new infections = ") +
              str(np.argmax(infections)))
        print(key + str(": max infected at the same time = ") +
              str(np.max(statesum[2, :])))


fig1.update_layout(
    title="New Infections over time",
    xaxis_title="day",
    yaxis_title="infections",
    legend_orientation="h",
    font=dict(
        family="Courier New, monospace",
        size=14,
        color="#7f7f7f"
    )
)

fig2.update_layout(
    title="Hospital index over time",
    xaxis_title="day",
    yaxis_title="hospital index",
    legend_orientation="h",
    font=dict(
        family="Courier New, monospace",
        size=14,
        color="#7f7f7f"
    )
)

fig3.update_layout(
    title="Infected people over time",
    xaxis_title="day",
    yaxis_title="infected",
    legend_orientation="h",
    font=dict(
        family="Courier New, monospace",
        size=14,
        color="#7f7f7f"
    )
)

plot(fig1, filename="../data/infections.html")
plot(fig2, filename="../data/hospital.html")
plot(fig3, filename="../data/infected.html")

results = pd.concat(results)
results.to_csv("results3.csv")

fig1.write_image("infections3.png")
fig2.write_image("hospital_index3.png")
fig3.write_image("infected3.png")
