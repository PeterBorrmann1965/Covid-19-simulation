"""Simulation of infections for different scenarios."""
import coronalib as cl

# Einlesen und erstellen der Population
# age, agegroup, gender, family, contacts, dr = cl.readpop(
#    "../data/population_germany_v2.csv", n=10000000)

age, agegroup, gender, contacts, dr, hnr, persons = cl.read_campus(
    "../data/population_campus.csv", 17900000)

state, statesum, infections, day0, rnow, args = cl.sim(
    age, gender, dr, nday=730, cutdown=2000, prob_icu=0.01125, day0icu=200,
    mean_days_to_icu=10, mean_duration_icu=10, mean_serial=7, std_serial=3.4,
    immunt0=0.0, icu_fatality=0.5, long_term_death=False, hnr=hnr,
    persons=persons, com_attack_rate=0.8, contacts=contacts,
    r_mean=1.5, cutr_mean=1.05)
