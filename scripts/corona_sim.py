"""Simulation of infections for different scenarios."""
import covid19sim.coronalib as cl
import pandas as pd 
import numpy as np
import plotly.express as px
import os


age, agegroup, gender, contacts, drate, hnr, persons = cl.makepop("current",
                                                                  17900000)

for r0 in [2.5, 3.5]:
    for rlock in [0.7, 0.9, 1.2]:
        state, statesum, infections, day0, rnow, args = cl.sim(
            age, drate, nday=183, lock_icu=120, prob_icu=0.006, day0icu=120,
            mean_days_to_icu=10, mean_duration_icu=16, mean_serial=7,
            std_serial=3.4,
            immunt0=0.0, icu_fatality=0.5, long_term_death=False, hnr=None,
            com_attack_rate=0.0, contacts=contacts, r_mean=r0,
            rlock_mean=rlock, simname="Kurzfrist Szenario: R0="
            + str(r0) + " und Lockdown auf Re=" + str(rlock),
            datadir="/mnt/wd1/nrw_corona/")

        np.savez_compressed(os.path.join(args["datadir"], args["simname"]) +
                            ".npz", age=age, gender=gender, contacts=contacts,
                            drate=drate, persons=persons, state=state,
                            infectons=infections, re=rnow)
