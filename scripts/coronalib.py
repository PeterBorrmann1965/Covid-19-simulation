"""Corona Library."""
import pandas as pd
import numpy as np
from scipy.stats import gamma
import plotly.graph_objects as go
from plotly.offline import plot
from plotly.subplots import make_subplots


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


def sim(age, gender, dr, r, gmean=7.0, gsd=3.4, nday=140, burnin=1000,
        cutdown=25000, cutr=None, prob_icu=0.05, mean_days_to_icu=12,
        std_days_to_icu=3, mean_duration_icu=10, std_duration_icu=3):
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
    burnin : number of infections ro be reached to stop burnin
    probicu : mean probility, that an infected needs icu care
    mean_days_to_icu : mean days from infection to icucare
    std_days_to_icu : std deviation of days to icu
    mean_duration_icu : mean days on icu
    std_duration_icu : std deviation of days to icu

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
    state = np.zeros(shape=(nday, n), dtype="uint8")
    # set ni individuals to infected
    state[0, np.random.choice(n, 20)] = 2

    nstate = 7
    statesum = np.zeros(shape=(nstate, nday))
    statesum[:, 0] = np.bincount(state[0, :], minlength=nstate)

    # Precalculate profile infection
    p = gmean**2/gsd**2
    b = gsd**2/gmean
    x = np.linspace(0, 28, num=29, dtype=("int"))
    x = gamma.cdf(x, a=p, scale=b)
    delay = x[1:29] - x[0:28]
    delay = np.ascontiguousarray(delay[::-1])

    # Precalculate time to icu
    p = mean_days_to_icu**2/std_days_to_icu**2
    b = std_days_to_icu**2/mean_days_to_icu
    x = np.linspace(0, 28, num=29, dtype=("int"))
    x = gamma.cdf(x, a=p, scale=b)
    delay_icu = x[1:29] - x[0:28]
    delay_icu = np.ascontiguousarray(delay_icu[::-1])

    # individual prob icu
    ind_prob_icu = dr/np.mean(dr) * prob_icu
    print("Mean prob icu:" + str(np.mean(ind_prob_icu)))

    # Precalculate time to icu
    p = mean_duration_icu**2/std_duration_icu**2
    b = std_duration_icu**2/mean_duration_icu
    x = np.linspace(0, 28, num=29, dtype=("int"))
    x = gamma.cdf(x, a=p, scale=b)
    duration_icu = x[1:29] - x[0:28]
    duration_icu = np.ascontiguousarray(duration_icu[::-1])

    # initialize arrays
    infections = np.zeros(shape=nday)
    infections[0] = np.sum(state[0, :] == 2)
    firstdayinfected = np.full(shape=n, fill_value=1000, dtype="int")
    firstdayinfected[state[0, :] == 2] = 0

    firstdayicu = np.full(shape=n, fill_value=1000, dtype="int")

    # save the original r
    rstart = r
    # start with a high r0 in the burn in phase
    burn = 3.0 * r / np.mean(r)
    r = burn
    day0 = -1

    expinf = []
    for i in range(1, nday):
        # set state to state day before
        state[i, :] = state[i-1, :]

        # New infections on day i
        imin = max(0, i-28)
        h = infections[imin: i]
        newinf = np.sum(h*delay[-len(h):])
        expinf.append(newinf)

        # Generate randoms
        rans = np.random.random(size=n)

        # unconditional deaths
        state[i, rans < dr] = 4

        # Calculate the number of days infected
        days_infected = i - firstdayinfected

        # set all non dead cases with more than 27 days to status "immun"
        state[i, (days_infected > 27) & (state[i, :] != 4)] = 1

        # for infected cases calcualate the probality of icu admission
        days_infected_lim = np.clip(days_infected, 0, 27)
        picu = delay_icu[days_infected_lim] * ind_prob_icu
        rans = np.random.random(size=n)

        # only those in state infected can go to icu
        filt = (rans < picu) & (state[i, ] == 2)
        state[i, filt] = 6

        # calculate the number of days on icu
        days_icu = np.clip(i - firstdayicu, 0, 27)

        # Now we calculate the probability to move from icu out
        rans = np.random.random(size=n)
        prelease = duration_icu[days_icu]
        filt = (rans < prelease) & (state[i, ] == 6)
        state[i, filt] = 1
        # release all people with more than 27 days on icu
        state[i, days_icu == 27] = 1

        # infection probabilties by case
        pinf = r * newinf / n

        # only not infected people can be infected
        rans = np.random.random(size=n)
        filt = (rans < pinf) & (state[i, ] == 0)
        state[i, filt] = 2

        # store first infections day
        firstdayinfected[filt] = i

        # number of new infections new infections
        infections[i] = np.sum(filt)

        statesum[:, i] = np.bincount(state[i, :], minlength=nstate)

        # if the number of infections exceeds
        if (np.sum(infections) > burnin) and (day0 == -1):
            r = rstart
            day0 = i

        # if the number of infection exceeds cutdown r is devided by cutr
        if (cutr is not None) and (statesum[2, i] > cutdown):
            r = cutr
        else:
            r = rstart

    return state, statesum, infections, day0


def readpop(filename, n=1000000):
    """Read population data."""
    popi = pd.read_csv(filename)
    popi["N1M"] = np.around(popi.portion * n)
    dn = n - np.sum(popi["N1M"])
    nmax = np.argmax(popi.N1M)
    popi.iloc[nmax, popi.columns.get_loc('N1M')] = dn +\
        popi.iloc[nmax, popi.columns.get_loc('N1M')]
    np.sum(popi["N1M"])

    # Generate individuals by repeating the groups
    age = np.repeat(popi.age, popi.N1M)
    agegroup = np.repeat(popi.agegroup, popi.N1M)
    gender = np.repeat(popi.gender, popi.N1M)
    contacts = np.repeat(popi.contacts_mean, popi.N1M)
    family = np.repeat(popi.family_factor, popi.N1M)

    # normalize contacts to a mean of one
    contacts = contacts / np.sum(contacts)*len(contacts)
    dr = np.repeat(popi.deathrate, popi.N1M)

    # Calculate daily mortality per case
    dr = 1 - (1-dr)**(1/365)

    return age, agegroup, gender, family, contacts, dr


def analysestate(state, title="Scenario", group=None, day0=0):
    """Visualize and explore simulation results."""
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b',
              '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
    # Create figure
    fig1 = make_subplots(rows=2, cols=2, row_heights=[0.3, 0.7],
                         subplot_titles=("Ergebnisse", "Zustand", "Änderung"),
                         specs=[[{"type": "table", "colspan": 2}, None],
                                [{"type": "scatter"}, {"type": "scatter"}]])

    statesumday = {}
    nmax = 0
    results = {}
    lastday = state.shape[0]-1
    n = state.shape[1]
    for key, value in statdef.items():
        statesumday[value] = np.array([np.sum((state[i, :] == key))
                                       for i in range(0, state.shape[0])])
        if max(statesumday[value]) > 0:
            nmaxnow = np.max(np.where(statesumday[value] > 0))
            # print(value + " " + str(nmaxnow))
            if (nmax < nmaxnow) and (key == 2):
                nmax = nmaxnow
            resnow = {}
            resnow["Peaktag"] = np.argmax(statesumday[value]) -day0
            resnow["Peakwert"] = np.max(statesumday[value])
            resnow["Peakwert %"] = resnow["Peakwert"] / n * 100
            resnow["Endwert"] = statesumday[value][lastday]
            resnow["Endwert %"] = resnow["Endwert"] / n * 100
            results[value] = resnow

    for key, value in statdef.items():
        if max(statesumday[value]) > 0:
            fig1.add_trace(go.Scatter(x=[dw-day0 for dw in range(0, nmax)],
                                      y=statesumday[value][:nmax],
                                      mode='lines', name=value,
                                      legendgroup=value,
                                      line_color=colors[key]),
                           row=2, col=1)
            deltastatesum = np.diff(statesumday[value][:nmax],
                                    prepend=statesumday[value][0])
            fig1.add_trace(go.Scatter(x=[dw-day0 for dw in range(0, nmax)],
                                      y=deltastatesum,
                                      mode='lines', name=value,
                                      legendgroup=value,
                                      showlegend=False,
                                      line_color=colors[key]),
                           row=2, col=2)

    results = pd.DataFrame.from_dict(results, orient="index")
    results['Peakwert %'] = results['Peakwert %'].map('{:,.1f}%'.format)
    results['Endwert %'] = results['Endwert %'].map('{:,.1f}%'.format)
    results.reset_index(inplace=True)
    results.rename(columns={"index": "Zustand"})
    fig1.add_trace(go.Table(
        header=dict(values=list(results.columns),
                    align='center'),
        cells=dict(values=[results[c] for c in results.columns],
                   align='right')
        ), row=1, col=1)

    fig1.update_layout(showlegend=True, title=title, legend_orientation="h",
                       font=dict(family="Courier New, monospace", size=14))
    fig1.update_xaxes(title_text="Tag", row=2, col=1)
    fig1.update_yaxes(title_text="Anzahl", row=2, col=1)
    fig1.update_xaxes(title_text="Tag", row=2, col=2)
    fig1.update_yaxes(title_text="Anzahl", row=2, col=2)

    plot(fig1, filename="../figures/" + title + ".html")
    fig1.write_image("../figures/" + title + ".png")

    nday = state.shape[0]

    groupresults = []
    if group is not None:
        df = pd.DataFrame(group)
        for i in range(1, nday):
            df["state"] = state[i, :]
            a = df.groupby(["group", "state"]).agg(n=("state", "count"))
            a.reset_index(inplace=True)
            a = a.pivot_table(values="n", columns="state",
                              index=["group"], margins=True,
                              aggfunc="sum", fill_value=0)
            a.reset_index(inplace=True)
            a.rename(columns=statdef, inplace=True)
            a["not infected %"] = a["not infected"] / a["All"]*100
            a["scenario"] = key
            a["day"] = i
            groupresults.append(a)

        groupresults = pd.concat(groupresults)
    return results, groupresults







def sim(age, gender, dr, r, gmean=7.0, gsd=3.4, nday=140, ni=500,
        cutdown=25000, cutr=0.7,nh=10, gsd_h=5.1,gmean_h=5.9, p_h=1/10):
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
    p_h: probability that someone needs to go to hospital after infection
    nh= number of people initally in hospital
    gmean_h= mean of gamma distribution for the hospitality time profile
    gsd_h= std of gamma distribution for the hospitality time profile
    
    Returns:
    --------
    state : array shape (n,nday) with the state of each indivial on every day
        0 : not infected
        1 : immun
        2.: infected but not identified
        3.: infected and identified (not used yet)
        4 : dead
        5:  in hospital 
    statesum : array of shape (5, nday) with the count of each individual per
        days
    infections : array of length nday with the number of infections
    hospitalization: array of length nday with the number of people in hospital
    """
    # start configuation
    n = len(age)
    state = np.zeros(shape=(nday, n), dtype="int")
    # set ni individuals to infected
    state[0, np.random.choice(n, ni)] = 2
    # set nh people to be in hospital
    state[0, np.random.choice(n, nh)] = 6

    
    nstate = 7
    statesum = np.zeros(shape=(nstate, nday))
    statesum[:, 0] = np.bincount(state[0, :], minlength=nstate)
    
   
    
    # Precalculate profile
    p = gmean**2/gsd**2
    b = gsd**2/gmean
    x = np.linspace(0, 28, num=29, dtype=("int"))
    x = gamma.cdf(x, a=p, scale=b)
    delay = x[1:29] - x[0:28]
    delay = np.ascontiguousarray(delay[::-1])

    

    # Precalculate profile for hospitalzed people
    p_h = gmean_h**2/gsd_h**2
    b_h = gsd_h**2/gmean_h
    x_h = np.linspace(0, 28, num=29, dtype=("int"))
    x_h = gamma.cdf(x, a=p_h, scale=b_h)
    delay_h = x_h[1:29] - x_h[0:28]
    delay_h = np.ascontiguousarray(delay_h[::-1])


    infections = np.zeros(shape=nday)
    infections[0] = np.sum(state[0, :] == 2)
    
    hospitalzed = np.zeros(shape=nday)
    hospitalzed[0] = np.sum(state[0, :] == 6)
 
    firstdayinfected = np.full(shape=n, fill_value=1000, dtype="int")
    firstdayinfected[state[0, :] == 2] = 0
    
    firstdayinhospital = np.full(shape=n, fill_value=1000, dtype="int")
    firstdayinhospital[state[0, :] == 6] = 0

    for i in range(1, nday):
        # set state to state day before
        state[i, :] = state[i-1, :]

        # New infections on day i
        imin = max(0, i-28)
        h = infections[imin: i]
        newinf = np.sum(h*delay[-len(h):])
        
        #new people in hospital
        h_h=hospitalzed[imin:i]
        newhos=np.sum(h*delay_h[-len(h):])


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

        #hosptitality probabilties by case * basic probability that someone goes to hospital if infected
        phos=p_h*newhos/n
        #only infected people can go to hospital
        filt_h= (rans<phos) & (state[i, ]==2)
        state[i, filt_h]=5
  
        hospitalzed[i]=np.sum(filt_h)

        statesum[:, i] = np.bincount(state[i, :], minlength=nstate)
        # if the number of infection exceeds cutdown r is devided by cutr
        if statesum[2, i] > cutdown:
            r = r / np.mean(r) * cutr
        else:
            pass

    return state, statesum, infections,hospitalzed