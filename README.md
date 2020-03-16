# Covid-19-simulation
Simulation of individual an governmental actions and estimation of parameters

The first version of this simulation project is intended to simulate the effects of indiviual of governmental actions to change the daily contact rates. 

The current model has the following inputs: 

Population: 
- Number of individuals by age an gender for Germany  (Source: Statistsiches Bundesamt)
- Mortality rate of each individual (Source: Statistsiches Bundesamt)
- Average daily contact rate (Source: https://journals.plos.org/plosmedicine/article/file?id=10.1371/journal.pmed.0050074&type=printable)

The model simulates the daily changes of each individual in the population with the following states: 
0 - not infected 
1 - immun or dead (due to infection)
2 - infected 
3 - infected and identified (not uses currently)
4 - dead (right now only based on general mortality rater)

The infection profile is simulated with a gamma distribution. For Covid 19 we currently use a mean of 7.0 and a standard deviation of 3.4. 

The paramter R (number of people infected by an infected person) is used in the following fashion: 
- all contacts in the population are normalized to one 
- the suzeptibility of individual is R times the individual normalized contact rate 

The indivual R can be tweaked, e.g.:
- individual cut their contacts by a factor 10 
- closing of schools an kindergartens reduced the contacts by a factor of 4 
- special protectment of elderly people reduces the contact rate by a factor of 4 

The results contain the state of each individual, which can be analysed for peaks regarding the healthcare system, duration and general social impacts. 


