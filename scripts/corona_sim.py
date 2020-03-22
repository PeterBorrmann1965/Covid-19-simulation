"""Simulation of infections for different scenarios."""
import numpy as np
import time
import coronalib as cl

# Einlesen und erstellen der Population
age, agegroup, gender, family, contacts, dr = cl.readpop(
    "../data/population_new.csv", n=179000)

results = []
#for r0 in [2.0, 2.5, 3.0, 3.5, 5.0]:
for r0 in [3.0]:
    for f in [1.0, 0.7, 0.5]:
        r = contacts * r0
        r = r * r0 / np.mean(r)
        cutr = r * f
        infstart = 65

        meanr = np.mean(r)
        meancut = np.mean(cutr)
        name = "r0 = " + str("{:2.2f}".format(meanr)) +\
            " rlock = "+str("{:2.2f}".format(meancut)) +\
            " ICU Tag0 = " + str(infstart)

        t1 = time.time()
        state, statesum, infections, day0, rnow = cl.sim(
            age, gender, dr, r, nday=365, cutr=cutr, burnin=infstart,
            cutdown=400, prob_icu=0.005, mean_days_to_icu=12,
            std_duration_icu=3, mean_duration_icu=10, std_days_to_icu=3,
            mean_serial=7, std_serial=3, immunt0=0.0, icu_fatality=0.5)

        t2 = time.time()
        print(name + " day0 =" + str(day0))
        results, groupresults = cl.analysestate(state, title=name, day0=day0)
        t3 = time.time()
        print("Sim time: " + str(t2-t1) + " Analyse time: " + str(t3-t2))