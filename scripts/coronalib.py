"""Corona Library."""
import pandas as pd
import numpy as np
from scipy.stats import gamma
import plotly.graph_objects as go
from plotly.offline import plot
from plotly.subplots import make_subplots
import scipy.stats


statdef_en = {0: "not infected", 1: "immun or dead", 2: "infected",
              3: "identified", 4: "dead (other)", 5: 'hospital',
              6: 'intensive', 7: 'Covid-19 dead'}

statdef_de = {0: "nicht infiziert", 1: "immun", 2: "infiziert",
               3: "identifiziert", 4: "tod (Sonstige)",
               5: 'hospitalisiert', 6: 'ICU', 7: 'tod (Covid-19)'}

statdef = statdef_de


def infection_profile(mean_serial=7.0, std_serial=3.4, nday=21):
    """Calc the infections profile."""
    p = mean_serial**2/std_serial**2
    b = std_serial**2/mean_serial
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


def sim(age, gender, dr, r, mean_serial=7.0, std_serial=3.4, nday=140, burnin=20,
        cutdown=25000, cutr=None, prob_icu=0.005, mean_days_to_icu=12,
        std_days_to_icu=3, mean_duration_icu=10, std_duration_icu=3,
        immunt0=0.0, icu_fatality=0.5, long_term_death=False, hnr=None,
        persons=None, com_attack_rate=0.6):
    """Simulate model.

    Parameters:
    -----------
    age : array of length n with the age of each individual
    gender :  array of length n with the gender of each individual
    dr :  array of length n with the daily mortality rate of each individual
    r : array of lenght n with the averay indivial r
    mean_serial : mean of the gamma distribution for the infections profile
    gstd : std of the gamma distribution for the infections profile
    nday : number of days to simulated
    burnin : number of infections ro be reached to stop burnin
    probicu : mean probility, that an infected needs icu care
    mean_days_to_icu : mean days from infection to icucare
    std_days_to_icu : std deviation of days to icu
    mean_duration_icu : mean days on icu
    std_duration_icu : std deviation of days to icu
    immunt0 : percentage immun at t0
    icu_fataliy : percentage with fatal outcome
    long_term_death : Flag to simulate death from long term death rate
    hnr : array of length n with a hausehold number
    persons : number of additional persons in household/accomodation

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
    nimmun = int(immunt0*n)
    state[0, np.random.choice(n, nimmun)] = 1
    state[0, np.random.choice(n, 20)] = 2

    nstate = 8
    statesum = np.zeros(shape=(nstate, nday))
    statesum[:, 0] = np.bincount(state[0, :], minlength=nstate)

    # If we use houseolds
    if hnr is not None:
        hnrinfected = np.zeros(shape=(max(hnr)+1, nday), dtype="uint8")
        # Count per household if at least one persons is infected
        hnrinfected[:, 0] = np.where(
            np.bincount(hnr, weights=state[0, :] == 2) > 0, 1, 0)

    # Precalculate profile infection
    p = mean_serial**2/std_serial**2
    b = std_serial**2/mean_serial
    x = np.linspace(0, 28, num=29, dtype=("int"))
    x = gamma.cdf(x, a=p, scale=b)
    delay = x[1:29] - x[0:28]
    delay = np.ascontiguousarray(delay[::-1])

    # Precalculate time to icu
# =============================================================================
#     p = mean_days_to_icu**2/std_days_to_icu**2
#     b = std_days_to_icu**2/mean_days_to_icu
#     x = np.linspace(0, 28, num=29, dtype=("int"))
#     x = gamma.cdf(x, a=p, scale=b)
#     delay_icu = x[1:29] - x[0:28]
#     delay_icu = np.ascontiguousarray(delay_icu[::-1])
# =============================================================================
    time_to_icu = np.random.poisson(lam=mean_days_to_icu, size=n)

    # individual prob icu
    ind_prob_icu = dr/np.mean(dr) * prob_icu
    # ind_prob_icu = prob_icu
    print("Mean prob icu:" + str(np.mean(ind_prob_icu)))

    # Precalculate time to icu
# =============================================================================
#     p = mean_duration_icu**2/std_duration_icu**2
#     b = std_duration_icu**2/mean_duration_icu
#     x = np.linspace(0, 28, num=29, dtype=("int"))
#     y = gamma.cdf(x, a=p, scale=b)
#     duration_icu = np.diff(y, prepend=0)
#     #duration_icu = np.ascontiguousarray(duration_icu[::-1])
#     duration_icu = np.ascontiguousarray(duration_icu)
#     #print(np.sum(duration_icu))
# =============================================================================
    time_on_icu = np.random.poisson(lam=mean_duration_icu, size=n)

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

    rnow = []
    toticu = 0
    for i in range(1, nday):
        # set state to state day before
        state[i, :] = state[i-1, :]

        # New infections on day i
        imin = max(0, i-28)
        h = infections[imin: i]
        newinf = np.sum(h*delay[-len(h):])

        # unconditional deaths
        if long_term_death:
            rans = np.random.random(size=n)
            state[i, (rans < dr) & (state[i, :] != 7)] = 4

        # Calculate the number of days infected
        days_infected = i - firstdayinfected

        # set all infected and identified case with more than 30 days to immun
        state[i, (days_infected > 30) & (state[i, :] < 4)] = 1

        # for infected cases calculate the probability of icu admission
        rans = np.random.random(size=n)
        filt = (time_to_icu == days_infected) & \
            (rans < ind_prob_icu) &\
            (state[i, :] == 2)
        toticu = toticu + np.sum(filt)
        state[i, filt] = 6
        firstdayicu[filt] = i

        # Use the precalculated days to move out from ICU
        # rans = np.random.random(size=n)
        filt = time_on_icu == i - firstdayicu
        state[i, filt] = 1
        state[i, filt & (rans < icu_fatality)] = 7

        # infection probabilties by case
        pinf = r * newinf / n

        # only not infected people can be infected
        # We can reuse the last random number
        # rans = np.random.random(size=n)
        filt = (rans < pinf) & (state[i, ] == 0)
        state[i, filt] = 2

        # The new infections are mapped to household
        if hnr is not None:
            hnrinfected[:, i] = np.where(
                np.bincount(hnr, weights=filt) > 0, 1, 0)
            # The infections risk depends on the time profile
            hnr_risk = hnrinfected[:, imin:i].dot(delay[-len(h):])
            # new infections due to community attack
            rans = np.random.random(size=n)
            hnr_risk = com_attack_rate * hnr_risk
            filt = (rans < hnr_risk[hnr]) & (state[i, ] == 0)
            state[i, filt] = 2

        # store first infections day
        firstdayinfected[filt] = i

        # number of new infections new infections
        infections[i] = np.sum(filt)

        statesum[:, i] = np.bincount(state[i, :], minlength=nstate)

        rnow.append(np.mean(r))
        # if the number of infections exceeds
        if (np.sum(statesum[6, i]) > burnin) and (day0 == -1):
            r = rstart
            day0 = i

        # if the number of infection exceeds cutdown r is devided by cutr
        if (cutr is not None) and (statesum[6, i] > cutdown):
            r = cutr
        else:
            r = rstart

    print("toticu:" + str(toticu))
    return state, statesum, infections, day0, np.array(rnow, dtype="double")

def read_campus(filename, n=1000000):
    """Generate popupulation from campus."""
    campus = pd.read_csv(filename)
    nrep = int(np.around(n/campus.shape[0]))
    repid = np.array([x for x in range(0, nrep)], dtype="int")
    replica = np.tile(repid, campus.shape[0])
    age = np.repeat(np.array(campus.age), nrep)
    gender = np.repeat(np.array(campus.gender), nrep)
    persons = np.repeat(np.array(campus.Personenzahl - 1), nrep)
    contacts = np.repeat(np.array(campus.contacts_mean), nrep)
    agegroup = np.repeat(np.array(campus.agegroup), nrep)
    dr_year = np.repeat(np.array(campus.deathrate), nrep)
    hnr = np.repeat(np.array(campus.hnrnew), nrep)
    nhnr = np.max(hnr)+1
    hnr = hnr + replica * nhnr

    # normalize contacts to a mean of one
    contacts = contacts / np.sum(contacts)*len(contacts)

    # Calculate daily mortality per case
    dr_day = 1 - (1-dr_year)**(1/365)

    return age, agegroup, gender, contacts, dr_day, hnr, persons


def readpop(filename, n=1000000):
    """Read population data."""
    popi = pd.read_csv(filename)
    popi["N1M"] = np.around(popi.portion * n).astype("int")
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
    fig1 = make_subplots(rows=2, cols=2, row_heights=[0.4, 0.6],
                         subplot_titles=("Ergebnisse", "Zustand",
                                         "Änderung zum Vortag (Delta)"),
                         specs=[[{"type": "table", "colspan": 2}, None],
                                [{"type": "scatter"}, {"type": "scatter"}]])
    
    statesumday = {}
    nmax = 0
    results = {}
    lastday = state.shape[0]-1
    n = state.shape[1]
    ngraph = 0
    for key, value in statdef.items():
        statesumday[value] = np.array([np.sum((state[i, :] == key))
                                       for i in range(0, state.shape[0])])
        if max(statesumday[value]) > 0:
            ngraph = ngraph + 1
            nmaxnow = np.max(np.where(statesumday[value] > 0))
            # print(value + " " + str(nmaxnow))
            if (nmax < nmaxnow) and (key == 2):
                nmax = nmaxnow
            resnow = {}
            resnow["Peaktag"] = np.argmax(statesumday[value]) - day0
            resnow["Peakwert"] = np.max(statesumday[value])
            resnow["Peakwert %"] = resnow["Peakwert"] / n * 100
            resnow["Endwert"] = statesumday[value][lastday]
            resnow["Endwert %"] = resnow["Endwert"] / n * 100
            #resnow["Mind. 1 Tag"] = np.sum(np.max(state == key, axis=0))
            #resnow["Mittelwert Tage/EW"] = np.sum(statesumday[value]) / n
            results[value] = resnow


    fig2 = make_subplots(rows=ngraph, cols=2, column_titles = 
                         ("Zustand","Änderung zum Vortag (Delta)"),
                         shared_xaxes=True)

    k = 0 
    for key, value in statdef.items():
        if max(statesumday[value]) > 0:
            k = k + 1
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

            fig2.add_trace(go.Scatter(x=[dw-day0 for dw in range(0, nmax)],
                                      y=statesumday[value][:nmax],
                                      mode='lines', name=value,
                                      legendgroup=value,
                                      line_color=colors[key]),
                           row=k, col=1)

            fig2.add_trace(go.Scatter(x=[dw-day0 for dw in range(0, nmax)],
                                      y=deltastatesum,
                                      mode='lines', name=value,
                                      legendgroup=value,
                                      showlegend=False,
                                      line_color=colors[key]),
                           row=k, col=2)

    results = pd.DataFrame.from_dict(results, orient="index")
    results['Peakwert %'] = results['Peakwert %'].map('{:,.3f}%'.format)
    results['Endwert %'] = results['Endwert %'].map('{:,.3f}%'.format)
    # results['Mittelwert Tage/EW'] =\
    #    results['Mittelwert Tage/EW'].map('{:,.5f}'.format)
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
    fig1.update_yaxes(type="log", row=2, col=1)
    
    fig2.update_layout(showlegend=True, title=title, legend_orientation="h",
                       font=dict(family="Courier New, monospace", size=14))
    fig2.update_xaxes(title_text="Tag", row=ngraph, col=1)
    fig2.update_xaxes(title_text="Tag", row=ngraph, col=2)
    for k in range(0, ngraph):
        fig2.update_yaxes(title_text="Anzahl", row=k+1, col=1)

    plot(fig1, filename="../figures/" + title + ".html")
    fig1.write_image("../figures/" + title + ".png", width=1500, height=1000)
    plot(fig2, filename="../figures/" + title + "_linear.html")

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


def analyse_cfr(statesum, delay, darkrate, cfr, timetodeath):
    """Analyse the case fatality rates.

    Parameters
    ----------
    statesum : resuls from covid-19 sim
    delay : delay between infection and reporting
    darkrate: percentage of infections indentified

    """
    # The cumalated infection are immun + infected + intensive + corona death +
    # hospital
    cuminfected = statesum[1]+statesum[2]+statesum[7]+statesum[6]+statesum[5]

    # newinfections
    newinfections = np.diff(cuminfected, prepend=0)
    newdeath = np.diff(statesum[7], prepend=0)

    # reported
    reported = np.empty_like(cuminfected)
    reported[:delay] = 0
    reported[delay:] = np.around(darkrate * cuminfected[:-delay]).astype(int)
    # Constant line
    cfr_real = cfr * np.ones(shape=len(reported))

    # corrected
    corrected = np.empty_like(cuminfected)
    corrected[:timetodeath] = 0
    corrected[timetodeath:] = cuminfected[:-timetodeath]
    corrected = statesum[7] / corrected
    
    # corrected
    pdf = [scipy.stats.poisson.pmf(i, timetodeath) for i in range(0,500)]
    pdf = np.array(pdf)
    corrected2 = np.empty_like(cuminfected)
    corrected2[0] = 0
    for t in range(1, len(newinfections)):
        corrected2[t] = 0
        for s in range(0, t):
            corrected2[t] = corrected2[t] + newinfections[t-s] * pdf[s]
    corrected2 = np.cumsum(corrected2)
    corrected2 = statesum[7] / corrected2

    crude_rate = statesum[7]/cuminfected
    crude_reported = statesum[7]/reported
    nmax = np.argmax(statesum[7])

    fig1 = make_subplots(rows=2, cols=1, subplot_titles=
                         ("Crude Case fatality Rate", "neue Infektionen"))
    fig1.add_trace(go.Scatter(y=crude_rate[:nmax], mode='lines',
                              name="crude"), row=1, col=1)
    fig1.add_trace(go.Scatter(y=crude_reported[:nmax], mode='lines',
                              name="crude reported"), row=1, col=1)
    fig1.add_trace(go.Scatter(y=cfr_real[:nmax], mode='lines',
                              name="real"), row=1, col=1)
    fig1.add_trace(go.Scatter(y=corrected2[:nmax], mode='lines',
                              name="korrigiert"), row=1, col=1)
    fig1.add_trace(go.Scatter(y=newinfections[:nmax], mode='lines',
                              name="neue Infektionen"), row=2, col=1)
    fig1.update_xaxes(title_text="Tag", row=1, col=1)
    fig1.update_xaxes(title_text="Tag", row=2, col=1)
    fig1.update_yaxes(title_text="CFR", row=1, col=1)
    fig1.update_yaxes(title_text="Anzahl", row=2, col=1)
    plot(fig1, filename="../figures/cfr2.html")
    return newdeath, corrected2


