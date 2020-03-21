"""Corona Library."""
import pandas as pd
import numpy as np
from scipy.stats import gamma
import plotly.graph_objects as go
from plotly.offline import plot

statdef = {0: "not infected", 1: "immun or dead", 2: "infected",
           3: "identified", 4: "dead (other)", 5: 'hospital',
           6: 'intensive'}

def infection_profile(gmean=7.0, gsd=3.4, nday=21):
    """Calc the infections profile."""
    p = gmean**2/gsd**2
    b = gsd**2/gmean
    x = np.linspace(0, nday, num=nday+1, dtype=("int"))
    y = gamma.cdf(x, a=p, scale=b)
    delay = np.zeros(nday+1)
    delay[1:(nday+1)] = y[1:(nday+1)] - y[0:nday]
    return x, y, delay


def makeprofile_plot():
    """Plot the infections profile."""
    inf1 = go.Figure()
    inf2 = go.Figure()
    x, y, z = infection_profile(7, 3.4)
    inf1.add_trace(go.Scatter(x=x, y=y, mode='lines', name="Covid-19"))
    inf2.add_trace(go.Bar(x=x, y=z, name="Covid-19"))
    x, y, z = infection_profile(1, 0.9)
    inf1.add_trace(go.Scatter(x=x, y=y, mode='lines', name="Influenza"))
    inf2.add_trace(go.Bar(x=x, y=z, name="Influenza"))
    inf1.update_layout(
        title="Cum. secondary infection probabilty",
        xaxis_title="day",
        yaxis_title="cdf",
        legend_orientation="h",
        font=dict(
            family="Courier New, monospace",
            size=14,
            color="#7f7f7f"
        )
    )
    inf2.update_layout(
        title="Secondary infection probabilty",
        xaxis_title="day",
        yaxis_title="pdf",
        legend_orientation="h",
        font=dict(
            family="Courier New, monospace",
            size=14,
            color="#7f7f7f"
        )
    )
    plot(inf1)
    plot(inf2)
    inf1.write_image("cdf.png")
    inf2.write_image("pdf.png")


def sim(age, gender, dr, r, gmean=7.0, gsd=3.4, nday=140, ni=500,
        cutdown=25000, cutr=0.7):
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
    --------
    state : array shape (n,nday) with the state of each indivial on every day
        0 : not infected
        1 : immun
        2.: infected but not identified
        3.: infected and identified (not used yet)
        4 : dead
    statesum : array of shape (5, nday) with the count of each individual per
        days
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
        # if the number of infection exceeds cutdown r is devided by cutr
        if statesum[2, i] > cutdown:
            r = r / np.mean(r) * cutr
        else:
            pass

    return state, statesum, infections
