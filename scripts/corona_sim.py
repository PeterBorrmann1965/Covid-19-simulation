"""Simulation of infections for different scenarios."""
import numpy as np
import time
import coronalib as cl
import pandas as pd
import datetime


# Einlesen und erstellen der Population
#age, agegroup, gender, family, contacts, dr = cl.readpop(
#    "../data/population_germany_v2.csv", n=10000000)

age, agegroup, gender, contacts, dr, hnr, persons = cl.read_campus(
    "../data/population_campus.csv", 17900000)


for r0 in [1.5, 2.0, 2.5]:
    for prob_icu in [0.01125]:
        r = contacts
        #r = 1
        #dr = 1
        r = r * r0 / np.mean(r)
        cutr = r * 1
        infstart = 213
        icu_fatality = 0.5
        mean_duration_icu = 10
        mean_days_to_icu = 10

        meanr = np.mean(r)
        meancut = np.mean(cutr)
        name = "r0=" + str("{:2.2f}".format(r0)) +\
            " prob_ICU=" + str("{:2.5f}".format(prob_icu)) +\
            " days_to_ICU=" + str("{:2.1f}".format(mean_days_to_icu)) +\
            " ICU_fat=" + str("{:2.3f}".format(icu_fatality)) +\
            " ICU_dur=" + str("{:2.1f}".format(mean_duration_icu)) +\
            " ICU_dur=" + str("{:2.1f}".format(mean_duration_icu)) +\
            " (akt. Belegung ICU=" + str(infstart) +\
            "," + str(datetime.date.today()) + ")"

        t1 = time.time()
        print(name)
        state, statesum, infections, day0, rnow = cl.sim(
            age, gender, dr, r, nday=365, cutr=cutr, burnin=infstart,
            cutdown=200, prob_icu=prob_icu, mean_days_to_icu=mean_days_to_icu,
            std_duration_icu=3, mean_duration_icu=mean_duration_icu,
            std_days_to_icu=3, mean_serial=7, std_serial=3.4, immunt0=0.0,
            icu_fatality=icu_fatality, long_term_death=False, hnr=hnr,
            persons=persons, com_attack_rate=0.8)

        t2 = time.time()
        results, groupresults = cl.analysestate(state, title=name, day0=day0,
                                                group=agegroup)
        cfr = prob_icu * icu_fatality
        cl.analyse_cfr(statesum, rnow, cfr=cfr, darkrate=1,
                              timetodeath=mean_duration_icu+mean_days_to_icu,
                              delay=5, name=name)
        t3 = time.time()
        print("Sim time: " + str(t2-t1) + " Analyse time: " + str(t3-t2))
        results.to_csv("../results/" + name + ".csv")
        groupresults.to_csv("../results/" + name + ".csv")




