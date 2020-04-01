# Covid-19-simulation

## News

codid19sim is now available as a python package:

* Download the latest wheel (https://github.com/PeterBorrmann1965/Covid-19-simulation/blob/master/package/dist/covid19sim-0.1.2-py3-none-any.whl)
* Install the package:  pip install covid19sim-0.1.2-py3-none-any.whl
* Run a simulation with your parameters

```python
"""Simulation of infections for different scenarios."""
import covid19sim.coronalib as cl
import pandas as pd 
import numpy as np
import plotly.express as px
```


```python
print(cl.sim.__doc__)
```

    Simulate model.
    
        Parameters:
        -----------
        age : array of length n, age of each individual
        drate :  array of length n, daily mortality rate of each individual
        mean_serial : mean of the gamma distribution for the infections profile
        std_serial : std of the gamma distribution for the infections profile
        nday : number of days to simulated
        day0icu : number of icu beds at day0 (used to set day0)
        prob_icu : mean probility, that an infected needs icu care
        mean_days_to_icu : mean days from infection to icucare
        mean_duration_icu : mean days on icu
        immunt0 : percentage immun at t0
        icu_fataliy : percentage with fatal outcome
        long_term_death : Flag to simulate death from long term death rate
        hnr : array of length n, household number
        com_attack_rate : infection probabilty within a community
        contacts : array of length n, number of daily contacts per person or None
            if contacts is not None the individual r is proportional to contacts
        r_mean : mean r for the population at simulation start
        rlock_mean : mean_r at forced lockdown
        lock_icu : if the number of occupied icu beds exceeds lock_icu the mean r
            is reduced to cut_meanr
        simname : name of the simulation
        datadir : directory where all results are saved
    
        Returns:
        --------
        state : array shape (n,nday) with the state of each indivial on every day
            0 : not infected
            1 : immun
            2.: infected but not identified
            3.: not used
            4 : dead (long term mortality)
            5 : not used
            6 : ICU care
            7 : dead (Covid-19)
        statesum : array of shape (5, nday) with the count of each individual per
            days
        infections : array of length nday
            the number of infections
        day0 : the simulation day on which the number of icu care patients exceeds
            for the first time day0icu
        re :  array of length nday
            the effective reporoduction number per day
        params : a copy of all input paramters as a data frame
        


Covid-19 Sim provides two populations:<br>
"current" : The population is based on the current population (2019) <br>
"household" : The population is based on a subsample in 2010 but with household numbers and additional persons per household


```python
age, agegroup, gender, contacts, drate, hnr, persons = cl.makepop("household",1000000)
```


```python
contacts = np.where(persons > 4,0.2,1.0)
contacts = contacts/np.mean(contacts)
state, statesum, infections, day0, rnow, args = cl.sim(
        age, drate, nday=365, lock_icu=120, prob_icu=0.006, day0icu=120,
        mean_days_to_icu=10, mean_duration_icu=16, mean_serial=7,
        std_serial=3.4,
        immunt0=0.0, icu_fatality=0.5, long_term_death=False, hnr=hnr,
        com_attack_rate=0.8, contacts=contacts, r_mean=3.5,
        rlock_mean=0.7, simname="Test",
        datadir="/mnt/wd1/nrw_corona/")
```


```python
display(cl.groupresults({"Geschlecht":gender,"Alter":agegroup}, state[:(day0)]))
```



## Overview
Simulation of individual an governmental actions and estimation of parameters

The first version of this simulation project is intended to simulate the effects of indiviual of governmental actions to change the daily contact rates. 

The current model has the following inputs: 

Population: 
- Number of individuals by age, gender, and family status for Germany  (Source: Statistisches Bundesamt)
- Mortality rate of each individual (Source: Statistisches Bundesamt)
- Average daily contact rate (Source: https://journals.plos.org/plosmedicine/article/file?id=10.1371/journal.pmed.0050074&type=printable)
- An alternative population is bases on a representative sample with the household size as additional information

The model simulates the daily changes of each individual in the population with the following states: 
0 - not infected 
1 - immun or dead (due to infection)
2 - infected 
3 - infected and identified (not used)
4 - dead (due to other reasons)
5 - hospialized (not used)
6 - ICU
7 - dead ( Covid-19 )

The infection profile is simulated with a gamma distribution. For Covid 19 we currently use a mean of 7.0 and a standard deviation of 3.4. 

The parameter R (number of people infected by an infected person) is used in the following fashion: 
- all contacts in the population are normalized to one 
- the suceptibility of an individual is R times the individual normalized contact rate 

The indivual R can be tweaked, e.g.:
- individuals cut their contacts by a factor 10 
- closing of schools and kindergartens reduces the contacts by a factor of 4 
- special protectment of elderly people reduces the contact rate by a factor of 4 

The results contain the state of each individual, which can be analysed for peaks regarding the healthcare system, duration and general social impacts. 

## First scenarios

The following figure show two base sceanrios with r0 = 2.5 and 5.0 and additional scenarios where the contact rate of people youger than 20 or people older than 60 are cut by a factor 4. We call these actions "school closing" and "elderly" protection". The first figure shows the number of new infections per day with a total population of 1 million. The second figure show the hospital index, which we define as the sum of the base mortality rates (without Covid-19) of all infected people. All infected people are assumed to be recovered or dead 28 days after infection. 

The hospital index should be a quite good indicator for the impact on the healthcare system since, since the severeness of a Covid-19 infection seems to be linked to the health condition of an individual, which should on average be propportional to its mortality rate. 

* The difference between base 5.0 and base 2.5 can be seen as a country wide slow down halfving all contacts on average. This cuts down the peak in the hospital index from around 30 to 18. This comes with the expense, that the duration is extended. The peak is after 72 days instead of 45.
* School closings have overall a small effect. The peak and the duration are not changed very much. 
* The most prominent effect hat the protection of elderly people. Here to effects play together. The eldely contribute more to the hospitaliy index and on the hand the fast infection and immunization of younger people reduces the infection risk later on. 
* It must be noted that any action changing contact rate has massive social and economical consequences.

![Infections](https://github.com/PeterBorrmann1965/Covid-19-simulation/blob/master/infections.png)

![Hospital index](https://github.com/PeterBorrmann1965/Covid-19-simulation/blob/master/hospital_index.png)

### Questions
* What is the optimal schedule to keep the maximum healthcare demand below the maximum capacity while minimizimng the social and financial impact?
* What happens after a "blow out" reducing R0 significantyl below 1.0 - but leaving a lot of people not immunized? 

## Improvements
- Include conditional Covid-19 mortality, hospitalization and intensive care into the model
- Use contact matrix between age groups 
- Improve anlysis of outputs (infections peaks, duration, ...)

## Links
* Covid-19 cases in Italy. Deatailed numbers down to regions with number of identified cases, tests, death, hospital an intesive care. (daily update) https://github.com/pcm-dpc/COVID-19
* Collection of articels and data on Covid-19, overview on parameter estimates https://github.com/midas-network/COVID-19

## Contributors (direct and indirect)
* Dr. Tobias Sproll
* Simon Hommel
* Priv.-Doz. Dr. Peter Borrmann

