"""Simulation of infections for different scenarios."""
import numpy as np
import time
import coronalib as cl
import pandas as pd

# Einlesen und erstellen der Population
age, agegroup, gender, family, contacts, dr = cl.readpop(
    "../data/population_new.csv", n=17900000)

all_results = []
all_groupresults = []
for r0 in [1.3, 1.5, 1.7, 2.0, 2.5]:
    for f in [1.0]:
        r = contacts * r0
        r = r * r0 / np.mean(r)
        cutr = r * f
        infstart = 65

        meanr = np.mean(r)
        meancut = np.mean(cutr)
        name = "r0 = " + str("{:2.2f}".format(meanr)) +\
            " ICU Tag0 = " + str(infstart)

        t1 = time.time()
        state, statesum, infections, day0, rnow = cl.sim(
            age, gender, dr, r, nday=365, cutr=cutr, burnin=infstart,
            cutdown=400, prob_icu=0.0125, mean_days_to_icu=10,
            std_duration_icu=3, mean_duration_icu=10, std_days_to_icu=3,
            mean_serial=7, std_serial=3, immunt0=0.0, icu_fatality=0.5)

        t2 = time.time()
        print(name + " day0 =" + str(day0))
        results, groupresults = cl.analysestate(state, title=name, day0=day0)
        t3 = time.time()
        print("Sim time: " + str(t2-t1) + " Analyse time: " + str(t3-t2))
        all_results.append(results)
        all_groupresults.append(groupresults)

all_results = pd.concat(all_results)
all_groupresults = pd.concat(all_groupresults)
all_results.to_csv("../results/results_nrw.csv")
all_groupresults.to_csv("../results/groupresults_nrw.csv")
