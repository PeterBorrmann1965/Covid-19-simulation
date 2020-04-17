# Covid-19-simulation

## News

### Covid19sim as a python package
codid19sim is now available as a python package:

* Download the latest wheel (https://github.com/PeterBorrmann1965/Covid-19-simulation/blob/master/package/dist/covid19sim-0.2.1-py3-none-any.whl)
* Install the package:  pip install covid19sim-0.2.1-py3-none-any.whl
* Run a simulation with your parameters


```python
print(cl.sim.__doc__)
```

    Simulate model.
    
        Parameters
        ----------
        age : array of length n, age of each individual
        drate :  array of length n, daily mortality rate of each individual
        mean_serial : mean of the gamma distribution for the infections profile
        std_serial : std of the gamma distribution for the infections profile
        nday : number of days to simulated
        day0cumrep : number of cumulated reported at day0 (used to set day0)
        prob_icu : mean probility, that an infected needs icu care
        mean_days_to_icu : mean days from infection to icucare
        mean_duration_icu : mean days on icu
        immunt0 : percentage immun at t0
        ifr : infected fatality rate
        long_term_death : Flag to simulate death from long term death rate
        hnr : array of length n, household number
        com_attack_rate : infection probabilty within a community
        simname : name of the simulation
        datadir : directory where all results are saved
        realized : dataframe with realized data til now
        rep_delay : delay between infection and report
        alpha : factor between infected and reported
        r_change : dictionary with individual r at change points, keys are the
            day numbers relative to day0, values are vectors of length n
            with individual r's
        day0date : date of day 0
    
        Returns
        -------
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
        results : daily results as a dataframe
        


Covid-19 Sim provides two populations:<br>
"current" : The population is based on the current population (2019) <br>
"household" : The population is bases on a subsample in 2010 but with household numbers and additional persons per household


```python
age, agegroup, gender, contacts, drate, hnr, persons = cl.makepop("household",1000000)
```


```python
day0date = datetime.date(2020, 3, 8)
r_change = {}
# Intial r0
r_change[-1] = 5 * np.ones(shape=age.shape[0],dtype="double")
state, statesum, infections, day0, rnow, args, gr = cl.sim(
        age, drate, nday=400, prob_icu=0.015, day0cumrep=450,
        mean_days_to_icu=16, mean_duration_icu=10,
        mean_time_to_death=20,
        mean_serial=7.5, std_serial=3.0, immunt0=0.0, ifr=0.003,
        long_term_death=False, hnr=None, com_attack_rate=0.5,
        r_change=r_change, simname="Test",
        datadir=".",
        realized=None, rep_delay=13, alpha=0.125, day0date=day0date)
```


<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>Peaktag</th>
      <th>Peakwert</th>
      <th>Summe</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>Erwartete Neu-Infektionen</th>
      <td>2020-03-20</td>
      <td>73728.0</td>
      <td>1001512.0</td>
    </tr>
    <tr>
      <th>Erwartete Neu-Meldefälle</th>
      <td>2020-04-02</td>
      <td>9061.0</td>
      <td>125183.0</td>
    </tr>
    <tr>
      <th>ICU</th>
      <td>2020-04-09</td>
      <td>7573.0</td>
      <td>148107.0</td>
    </tr>
    <tr>
      <th>Erwartete neue Tote</th>
      <td>2020-04-10</td>
      <td>179.0</td>
      <td>3016.0</td>
    </tr>
  </tbody>
</table>
</div>


    Simulation time: 10.63197922706604



```python

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

## First scenarios (21.3.2020)

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
* Kurt Schubert

