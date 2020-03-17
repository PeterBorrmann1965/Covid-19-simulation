# Covid-19-simulation
Simulation of individual an governmental actions and estimation of parameters

The first version of this simulation project is intended to simulate the effects of indiviual of governmental actions to change the daily contact rates. 

The current model has the following inputs: 

Population: 
- Number of individuals by age an gender for Germany  (Source: Statistisches Bundesamt)
- Mortality rate of each individual (Source: Statistisches Bundesamt)
- Average daily contact rate (Source: https://journals.plos.org/plosmedicine/article/file?id=10.1371/journal.pmed.0050074&type=printable)

The model simulates the daily changes of each individual in the population with the following states: 
0 - not infected 
1 - immun or dead (due to infection)
2 - infected 
3 - infected and identified (currently not used)
4 - dead (right now only based on general mortality rate)

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

![Infections](https://github.com/PeterBorrmann1965/Covid-19-simulation/blob/master/scripts/infections.png)

![Hospital index](https://github.com/PeterBorrmann1965/Covid-19-simulation/blob/master/scripts/hospital_index.png)

### Questions
* What is the optimal schedule to keep the maximum healthcare demand below the maximum capacity while minimizimng the social and financial impact?
* What happens after a "blow out" reducing R0 significantyl below 1.0 - but leaving a lot of people not immunized? 

## Improvements
- Include conditional Covid-19 mortality, hospitalization and intensive care into the model
- Use contact matrix between age groups 
- Improve anlysis of outputs (infections peaks, duration, ...)

