import pandas as pd
import numpy as np
import os
import geopy.distance
from scipy.stats import gamma
import matplotlib.pyplot as plt
import time

def sim(age, gender, dr, r, gmean=7.0, gsd=3.4, nday = 140, ni=500):
    """Simulate model.

    Parameters:
    ----------- 
    age : array of length n with the age of each individual
    gender :  array of length n with the gender of each individual
    dr :  array of length n with the daily mortality rate of each individual 
    r : array of lenght n with the averay indivial r
    gmean : mean of the gamma distribution for the infections profile 
    gstd : std of the gamma distribution for the infections profile
    nday : number of days to simulated 
    ni : number of infections to be assigned in the initial population

    Returns:
    state : array of shape (n,nday) with the state of each indivial on every day
        0 : not infected
        1 : immun
        2.: infected but not identified
        3.: infected and identified (not used yet)
        4 : dead
    statesum : array of shape (5, nday) with the count of each individual per days
    infections : array of length nday with the number of infections
    """
    # start configuation
    n = len(age)
    state = np.zeros(shape=(nday, n), dtype="int")
    # set ni individuals to infected
    state[0, np.random.choice(n, ni)] = 2

    nstate = 5
    statesum = np.zeros(shape=(nstate, nday))
    statesum[:, 0] = np.bincount(state[0, :], minlength=nstate)

    # Precalculate profile
    p = gmean**2/gsd**2
    b = gsd**2/gmean
    x = np.linspace(0, 28, num=29, dtype=("int"))
    x = gamma.cdf(x, a=p, scale=b)
    delay = x[1:29] - x[0:28]
    delay = np.ascontiguousarray(delay[::-1])

    infections = np.zeros(shape=nday)
    infections[0] = np.sum(state[0, :] == 2)
    firstdayinfected = np.full(shape=n, fill_value=1000, dtype="int")
    firstdayinfected[state[0, :] == 2] = 0

    for i in range(1, nday):
        # set state to state day before
        state[i, :] = state[i-1, :]

        # New infections on day i
        imin = max(0, i-28)
        h = infections[imin: i]
        newinf = np.sum(h*delay[-len(h):])

        # Generate randoms
        rans = np.random.random(size=n)

        # unconditional deaths
        state[i, rans < dr] = 4

        # Calculate the number of days infected
        days_infected = i - firstdayinfected
        # set all non dead cases with more than 27 days to status "immun"
        state[i, (days_infected > 27) & (state[i, :] != 4)] = 1

        # infection probabilties by case
        pinf = r * newinf / n
        # only not infected people can be infected
        filt = (rans < pinf) & (state[i, ] == 0)
        state[i, filt] = 2
        firstdayinfected[filt] = i
        # new infections
        infections[i] = np.sum(filt)

        statesum[:, i] = np.bincount(state[i, :], minlength=nstate)

    return state, statesum, infections

# Read population data
popi = pd.read_csv("../data/population_germany.csv")

# Generate individuals by repeating the groups
age = np.repeat(popi.age, popi.N1M)
agegroup = np.repeat(popi.agegroup, popi.N1M)
gender = np.repeat(popi.gender, popi.N1M)
contacts = np.repeat(popi.contacts_mean, popi.N1M)

# normalize contacts to a mean of one
contacts = contacts / np.sum(contacts)*len(contacts)
dr = np.repeat(popi.deathrate, popi.N1M)

# Calculate daily mortality per case
dr = 1 - (1-dr)**(1/365)

# prepare dataframe 
df = pd.DataFrame({"agegroup": agegroup, "contacts": contacts})

scenario = {}
# set r per case 
r0 = 3.0
# all individual get a r value proportional to their normal contact rates
r1 = contacts * r0
scenario["base"] = r1
# people below 20 have get only a 25% contact rate (schools closing)
r2 = np.where(age < 20, r1 / 4, r1)
scenario["school closing"] = r2
# people above 60 have get only a 25% contact rate (schools closing)
r3 = np.where(age > 60, r1 / 4, r1)
scenario["elderly protecion"] = r3

results = []
for key, r in scenario.items():
    state, statesum, infections = sim(age, gender, dr, r, nday=365)
    nday = state.shape[0]-1
    df["state"] = state[nday, :]
    a = df.groupby(["agegroup", "state"]).agg(n=("state", "count"))
    a.reset_index(inplace=True)
    a = a.pivot_table(values="n", columns="state", index="agegroup", margins=True, aggfunc="sum", fill_value=0)
    a.reset_index(inplace=True)
    a.rename(columns={0: "not infected", 1: "immun or dead", 2: "infected",
                    3: "identified", 4: "dead (other)"}, inplace=True)
    a["not infected %"] = a["not infected"] / a["All"]*100
    a["scenario"] = key
    results.append(a)

results = pd.concat(results)
print(results)
results.to_csv("results.csv")
