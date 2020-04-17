"""Corona Library."""
import time
import datetime
import warnings
import pandas as pd
import numpy as np
from scipy.stats import gamma
import plotly.graph_objects as go
from plotly.offline import plot
from plotly.subplots import make_subplots
import plotly.io as pio
import scipy.stats
from IPython.display import display
import pkg_resources
import os
from numba import njit, prange

warnings.filterwarnings("ignore")


STATEDEF_EN = {0: "not infected", 1: "immun", 2: "infected",
               3: "identified", 4: "dead (other)", 5: 'hospital',
               6: 'intensive', 7: 'Covid-19 dead'}

STATEDEF_DE = {0: "nicht infiziert", 1: "immun", 2: "infiziert",
               3: "identifiziert", 4: "tod (Sonstige)",
               5: 'hospitalisiert', 6: 'ICU', 7: 'tod (Covid-19)'}

STATEDEF = STATEDEF_DE


def infection_profile(mean_serial=7.0, std_serial=3.4, nday=21):
    """Calc the infections profile."""
    gamma_a = mean_serial**2/std_serial**2
    gamma_scale = std_serial**2/mean_serial
    xval = np.linspace(0, nday, num=nday+1, dtype=("int"))
    yval = gamma.cdf(xval, a=gamma_a, scale=gamma_scale)
    delay = np.zeros(nday+1)
    delay[1:(nday+1)] = yval[1:(nday+1)] - yval[0:nday]
    return xval, yval, delay


def makepop(popname, n=1000000):
    """Generate population."""
    if popname == "current":
        germany = pkg_resources.resource_filename('covid19sim',
                                                  'population_germany.csv')
        age, agegroup, gender, family, contacts, dr_day = readpop(
            germany, n)
        hnr = None
        persons = None
    elif popname == "household":
        household = pkg_resources.resource_filename('covid19sim',
                                                    'population_household.csv')
        age, agegroup, gender, contacts, dr_day, hnr, persons = \
            read_campus(household, n)
    else:
        print("Unknown population")
        return None, None, None, None, None, None
    return age, agegroup, gender, contacts, dr_day, hnr, persons


def makeprofile_plot(mean_serial=7, mean_std=3.4, r0=2.7, re=0.9, isoday=4):
    """Plot the infections profile."""
    inf1 = go.Figure()
    inf2 = go.Figure()
    x, y, z = infection_profile(mean_serial, mean_std)
    inf1.add_trace(go.Scatter(x=x, y=r0*y, mode='lines',
                              name="ohne Maßnahmen"))
    inf1.add_trace(go.Scatter(x=x, y=re*y, mode='lines', name="Lockdown"))
    iso = np.where(x > isoday, 0.5 * r0*z, r0*z)
    inf1.add_trace(go.Scatter(x=x, y=np.cumsum(iso), mode='lines',
                              name="50% Isolation nach " +
                              str(isoday) + "Tagen"))

    inf2.add_trace(go.Scatter(x=x, y=r0*z, mode='lines+markers',
                              name="ohne Maßnahmen"))
    inf2.add_trace(go.Scatter(x=x, y=re*z, mode='lines+markers',
                              name="Lockdown"))
    inf2.add_trace(go.Scatter(x=x, y=iso, mode='lines+markers',
                              name="50% Isolation nach "+str(isoday) +
                              "Tagen"))
    x, y, z = infection_profile(1, 0.9)
    # inf1.add_trace(go.Scatter(x=x, y=y, mode='lines', name="Influenza"))
    # inf2.add_trace(go.Bar(x=x, y=z, name="Influenza"))
    inf1.update_layout(
        title="Sekundärdinfizierte",
        xaxis_title="Tage nach der Primärinfektion",
        yaxis_title="Kumlierte Sekundärinfizierte",
        legend_orientation="h",
        font=dict(size=18)
    )
    inf2.update_layout(
        title="Sekundärdinfizierte",
        xaxis_title="Tage nach der Primärinfektion",
        yaxis_title="Sekundärinfizierte",
        legend_orientation="h",
        font=dict(size=18)
    )
    plot(inf1)
    plot(inf2)
    inf1.write_image("cdf.png", width=1200, height=800)
    inf2.write_image("pdf.png", width=1200, height=800)
    return


@njit(parallel=True)
def getrans(n,m):
    x = np.zeros(shape=(m, n))
    for i in prange(0, m):
        x[i, :] = np.random.random(n)
    return x


def sim(age, drate, mean_serial=7.0, std_serial=3.4, nday=140,
        day0cumrep=20,
        prob_icu=0.005, mean_days_to_icu=12, mean_time_to_death=17,
        mean_duration_icu=10, immunt0=0.0, ifr=0.5,
        long_term_death=False, hnr=None, com_attack_rate=0.6,
        simname="test", datadir=".", realized=None, rep_delay=8.7,
        alpha=0.2, r_change=None, day0date=datetime.date(2020, 3, 15)):
    """Simulate model.

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
    """
    # This must be the first line
    args = locals()
    args["mean_age"] = np.mean(age)
    tstart = time.time()
    # Initialize r
    daymin = min(r_change.keys())
    r = r_change[daymin]
    rmean = np.mean(r)

    # Simulation name
    r0aux = np.mean(r)
    name = simname

    n = len(age)
    state = np.zeros(shape=(n), dtype="int")
    # set ni individuals to infected
    nimmun = int(immunt0*n)
    state[np.random.choice(n, nimmun)] = 1
    state[np.random.choice(n, 20)] = 2

    nstate = 8
    statesum = np.zeros(shape=(nstate, nday))
    statesum[:, 0] = np.bincount(state, minlength=nstate)


    # Precalculate profile infection
    p = mean_serial**2/std_serial**2
    b = std_serial**2/mean_serial
    x = np.linspace(0, 28, num=29, dtype=("int"))
    x = gamma.cdf(x, a=p, scale=b)
    delay = x[1:29] - x[0:28]
    delay = np.ascontiguousarray(delay[::-1])

    # Precalculate time to icu
    time_to_icu = np.random.poisson(lam=mean_days_to_icu, size=n)
    time_to_death = np.random.poisson(lam=mean_time_to_death, size=n)

    # individual prob icu
    ind_prob_icu = drate/np.mean(drate) * prob_icu

    # Precalculate time to icu
    time_on_icu = np.random.poisson(lam=mean_duration_icu, size=n)
    rans = np.random.random(size=n)
    go_to_icu = rans < ind_prob_icu

    rans = np.random.random(size=n)
    go_dead = rans < (drate/np.mean(drate) * ifr)

    # initialize arrays
    infections = np.zeros(shape=nday)
    rexternal = np.zeros(shape=nday)
    reported = np.zeros(shape=nday)
    cuminfected = np.zeros(shape=nday)
    infections[0] = np.sum(state == 2)
    firstdayinfected = np.full(shape=n, fill_value=1000, dtype="int")
    firstdayinfected[state == 2] = 0

    firstdayicu = np.full(shape=n, fill_value=1000, dtype="int")

    day0 = -1
    burn = True

    re = np.zeros(shape=nday)

    # Precalculate profile infection
    p = rep_delay**2/1**2
    b = 1**2/rep_delay
    x = np.linspace(0, 48, num=49, dtype=("int"))
    x = gamma.cdf(x, a=p, scale=b)
    pdf = x[1:49] - x[0:48]

    # Precalculate community attack
    if hnr is not None:
        nhnr = np.max(hnr)+1
        firstdayhnr = np.full(shape=n, fill_value=1000, dtype="int")
        p = mean_serial**2/std_serial**2
        b = std_serial**2/mean_serial
        x = np.linspace(0, 28, num=29, dtype=("int"))
        x = gamma.cdf(x, a=p, scale=b)
        rans = np.random.random(n)
        x = np.diff(x)
        x = x / np.sum(x)
        d = np.linspace(0, 27, num=28, dtype=("int"))
        com_days_to_infection = np.random.choice(d, n, p=x)
        rans = np.random.random(n)
        com_days_to_infection = np.where(rans < com_attack_rate, 2000,
                                         com_days_to_infection)

    for i in range(1, nday):

        # New infections on day i
        imin = max(0, i-28)
        h = infections[imin: i]
        newinf = np.sum(h*delay[-len(h):])

        # unconditional deaths
        if long_term_death:
            rans = np.random.random(size=n)
            state[(rans < drate) & (state != 7)] = 4

        # Calculate the number of days infected
        days_infected = i - firstdayinfected

        # set all infected and identified case with more than 30 days to immun
        state[((days_infected > 28) & (state < 4)) |
              (time_on_icu == (i - firstdayicu))] = 1

        # for infected cases calculate the probability of icu admission
        filt = (time_to_icu == days_infected) & go_to_icu & (state == 2)
        state[filt] = 6
        firstdayicu[filt] = i

        state[(time_to_death == days_infected) & go_dead] = 7

        # The new infections are mapped to households
        if hnr is not None:
            # Household infections
            filt2 = (com_days_to_infection == (i - firstdayhnr[hnr])) &\
                (state == 0)
            # external infections
            aux = n / newinf
            rans = np.random.random(size=n) * aux
            filt1 = (rans < r) & (state == 0)

            filt = filt1 | filt2
            state[filt] = 2

            # Store the new infections in each household
            newhnr = hnr[filt1]
            firstdayhnr[newhnr] = np.where(firstdayhnr[newhnr] < i,
                                           firstdayhnr[newhnr], i)
        else:
            # infection probabilties by case
            aux = n / newinf
            rans = np.random.random(size=n) * aux
            filt = (rans < r) & (state == 0)
            state[filt] = 2

        # store first infections day
        firstdayinfected[filt] = i

        rexternal[i] = rmean

        # number of new infections
        infections[i] = np.sum(filt)
        if newinf > 0:
            re[i] = infections[i] / newinf
        else:
            re[i] = 0

        statesum[:, i] = np.bincount(state, minlength=nstate)

        for s in range(0, min(i, 35)):
            reported[i] = reported[i] + infections[i-s] * pdf[s] * alpha

        # find day0
        if (np.sum(reported) > day0cumrep) and (day0 == -1):
            day0 = i

        # adjust r
        if (day0 > -1) and ((i-day0) in r_change.keys()):
            r = r_change[i-day0]
            rmean = np.mean(r)


    # return only simulation parameter and no populations parameters
    argsnew = {}
    for key, value in args.items():
        if type(value) in [int, bool, float, str]:
            argsnew[key] = value
    params = pd.DataFrame.from_dict(argsnew, orient="index")
    params = params.reset_index()
    params.columns = ["Parameter", "Wert"]

    agegroup = (age/10).astype(int)*10

    results = analysestate(statesum, day0)
    display(results)

    # Write each dataframe to a different worksheet.
    excelfile = os.path.join(datadir, name + ".xlsx")
    writer = pd.ExcelWriter(excelfile, engine='xlsxwriter')

    params.to_excel(writer, sheet_name="Parameter", index=False)
    results.to_excel(writer, sheet_name='Ergebnis Übersicht', index=False)

    groupresults = pd.DataFrame({"Tag": [(x-day0) for x in range(0, nday)]})
    groupresults["Datum"] = [day0date + datetime.timedelta(days=x-day0)
                             for x in range(0, nday)]
    groupresults["neue Infektionen"] = infections

    # Meldefälle
    cuminfected = statesum[1]+statesum[2]+statesum[7]+statesum[6]+statesum[5]

    # newinfections
    newinfections = np.diff(cuminfected, prepend=0)

    # reported
    reported = np.empty_like(cuminfected)
    reported[0] = 0
    for t in range(1, len(newinfections)):
        reported[t] = 0
        for s in range(0, min(t, 27)):
            reported[t] = reported[t] + newinfections[t-s] * pdf[s]
    groupresults["Meldefälle"] = np.around(reported * alpha)
    groupresults["Meldefälle (kum.)"] = groupresults["Meldefälle"].cumsum()

    groupresults["R effektiv"] = re
    groupresults["R extern"] = rexternal
    for key, values in STATEDEF.items():
        if max(statesum[key]) > 0:
            groupresults[values] = statesum[key]

    if realized is not None:
        realcases = realized[['Meldedatum', 'Tote', 'Fälle', 'Fälle_kum',
                              'cumdeath', "Intensiv"]].copy()
        realcases.rename(columns={"Meldedatum": "Datum", "cumdeath":
                                  "kum. Tote (Ist)", "Fälle": "Meldefälle (Ist)",
                                  "Fälle_kum": "kum. Meldefälle (Ist)",
                                  "Intensiv": "Ist Intensiv"
                                  }, inplace=True)
        groupresults = groupresults.merge(realcases, on="Datum", how="left")

    groupresults.rename(columns={
        "neue Infektionen": "Erwartete Neu-Infektionen",
        "Meldefälle": "Erwartete Neu-Meldefälle",
        "Meldefälle (kum.)": "Erwartete Gesamt-Meldefälle",
        "R effektiv": "Reproduktionszahl",
        "nicht infiziert": "Nicht-Infizierte",
        "immun": "Erwartete Genesene",
        "infiziert": "Erwartete akt. Infizierte",
        "tod (Covid-19)": "Erwartete Tote",
        "Tote": "IST Neue Tote",
        "Meldefälle (Ist)": "RKI Neu-Meldefälle",
        "kum. Meldefälle (Ist)": "RKI Gesamt-Meldefälle",
        'kum. Tote (Ist)': "IST Tote gesamt"
        }, inplace=True)

    groupresults = groupresults[groupresults.Datum >=
                                datetime.date(2020, 3, 1)]
    groupresults.to_excel(writer, sheet_name='Zustand pro Tag', index=False)
    writer.save()
    tanalyse = time.time()
    print("Simulation time: " + str(tanalyse-tstart))
    return statesum, infections, day0, re, argsnew, groupresults


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


def analysestate(statesum, day0):
    """Explore simulation results."""
    results = {}
    lastday = statesum.shape[1]-1
    n = np.sum(statesum[:1])
    for key, value in STATEDEF.items():
        if max(statesum[key, :]) > 0:
            resnow = {}
            resnow["Peaktag"] = np.argmax(statesum[key, :]) - day0
            resnow["Peakwert"] = np.max(statesum[key, :])
            resnow["Peakwert %"] = resnow["Peakwert"] / n * 100
            resnow["Endwert"] = statesum[key, lastday]
            resnow["Endwert %"] = resnow["Endwert"] / n * 100
            results[value] = resnow

    results = pd.DataFrame.from_dict(results, orient="index")
    results['Peakwert %'] = results['Peakwert %'].map('{:,.3f}%'.format)
    results['Endwert %'] = results['Endwert %'].map('{:,.3f}%'.format)
    # results['Mittelwert Tage/EW'] =\
    #    results['Mittelwert Tage/EW'].map('{:,.5f}'.format)
    results.reset_index(inplace=True)
    results.rename(columns={"index": "Zustand"})
    return results


def groupresults(groups, state):
    """Analyse state by group.

    Parameters
    ----------
    groups : dictionary with property names as keys and arrays of length n
        with the property value of each individual as values
    state : array of shape nday, n with state values pers day and individual

    Returns
    -------
    res : DataFrame with results per group
    """
    # number of people with icu care
    pers_icu = np.max(state == 6, axis=0)

    # days on icu
    pers_days_icu = np.sum(state == 6, axis=0)

    # covid 19 death
    pers_death_covid = np.max(state == 7, axis=0)

    # infected
    pers_infected = np.max(np.isin(state, [2, 3, 5, 6, 7]), axis=0)

    # Create datafram
    df = pd.DataFrame({"ICU": pers_icu, "ICU Tage": pers_days_icu,
                       "tod (Covid-19)": pers_death_covid,
                      "infiziert": pers_infected})
    for key, value in groups.items():
        df[key] = value

    res = df.groupby(list(groups.keys())).agg(
        Anzahl=("infiziert", "count"),
        ICU_Care=("ICU", "sum"),
        ICU_Tage=("ICU Tage", "sum"),
        C19_Tote=("tod (Covid-19)", "sum"),
        C19_Infizierte=("infiziert", "sum")
        ).reset_index()

    res["Anteil ICU Care"] = res["ICU_Care"] / res["Anzahl"]
    res["Anteil c19_Tote"] = res["C19_Tote"] / res["Anzahl"]
    res["Anteil C19_Infizierte"] = res["C19_Infizierte"] / res["Anzahl"]
    res["CFR"] = res["C19_Tote"] / res["C19_Infizierte"]
    return res


def cfr_from_ts(date, cum_reported, cum_deaths, timetodeath, name):
    """Calculate an estimated cfr from timeseries."""
    # date = np.array(date)
    cum_reported = np.array(cum_reported)
    cum_deaths = np.array(cum_deaths)
    imin = np.argmax(cum_deaths > 50)
    fig = go.Figure(layout={"title": name})
    crude = cum_deaths / cum_reported
    fig.add_traces(go.Scatter(x=date[imin:], y=crude[imin:], name="crude"))
    res = {}
    res["crude"] = crude[-1]
    for timetodeath in [4, 8, 10]:
        pdf = [scipy.stats.poisson.pmf(i, timetodeath) for i in range(0, 50)]
        pdf = np.array(pdf)
        corrected = np.empty_like(cum_reported)
        corrected[0] = 0
        newinfections = np.diff(cum_reported, prepend=0)
        for t in range(1, len(newinfections)):
            corrected[t] = 0
            for s in range(0, min(t, 35)):
                corrected[t] = corrected[t] + newinfections[t-s] * pdf[s]
        corrected = np.cumsum(corrected)
        corrected = cum_deaths / corrected
        fig.add_traces(go.Scatter(x=date[imin:], y=corrected[imin:],
                                  name=str(timetodeath)))
        res["ttd="+str(timetodeath)] = corrected[-1]
    fig.update_yaxes(title_text="CFR estimate", tickformat='.2%')
    plot(fig, filename="../figures/cfr_analysis/" + str(name) + ".html")
    return res


def analyse_cfr(statesum, reffektive, delay, darkrate, cfr, timetodeath, name,
                day0=0, datadir="."):
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

    # reported
    pdf = [scipy.stats.poisson.pmf(i, 8) for i in range(0, 500)]
    pdf = np.array(pdf)
    reported = np.empty_like(cuminfected)
    reported[0] = 0
    for t in range(1, len(newinfections)):
        reported[t] = 0
        for s in range(0, min(t, 35)):
            reported[t] = reported[t] + newinfections[t-s] * pdf[s]

    # Constant line
    cfr_real = cfr * np.ones(shape=len(reported))

    # corrected
    corrected = np.empty_like(cuminfected)
    corrected[:timetodeath] = 0
    corrected[timetodeath:] = cuminfected[:-timetodeath]
    corrected = statesum[7] / corrected

    # corrected
    pdf = [scipy.stats.poisson.pmf(i, timetodeath) for i in range(0, 500)]
    pdf = np.array(pdf)
    corrected2 = np.empty_like(cuminfected)
    corrected2[0] = 0
    for t in range(1, len(newinfections)):
        corrected2[t] = 0
        for s in range(0, min(t, 35)):
            corrected2[t] = corrected2[t] + newinfections[t-s] * pdf[s]
    corrected2 = np.cumsum(corrected2)
    corrected2 = statesum[7] / corrected2

    crude_rate = statesum[7]/cuminfected
    nmax = np.argmax(statesum[7])

    fig1 = make_subplots(rows=3, cols=1, subplot_titles=(
        "neue Infektionen", "R effektiv", "Case Fatality Rate"),
        shared_xaxes=True)
    fig1.add_trace(go.Scatter(x=[dw-day0 for dw in range(0, nmax)],
                              y=crude_rate[:nmax], mode='lines',
                              name="crude"), row=3, col=1)
    fig1.add_trace(go.Scatter(x=[dw-day0 for dw in range(0, nmax)],
                              y=cfr_real[:nmax], mode='lines',
                              name="real"), row=3, col=1)
    fig1.add_trace(go.Scatter(x=[dw-day0 for dw in range(0, nmax)],
                              y=corrected2[:nmax], mode='lines',
                              name="korrigiert"), row=3, col=1)
    fig1.add_trace(go.Scatter(x=[dw-day0 for dw in range(0, nmax)],
                              y=newinfections[:nmax], mode='lines',
                              name="neue Infektionen"), row=1, col=1)
    fig1.add_trace(go.Scatter(x=[dw-day0 for dw in range(0, nmax)],
                              y=reported[:nmax], mode='lines',
                              name="Meldungen"), row=1, col=1)
    fig1.add_trace(go.Scatter(x=[dw-day0 for dw in range(0, nmax)],
                              y=reffektive[:nmax], mode='lines',
                              name="R effektiv"), row=2, col=1)

    fig1.update_xaxes(title_text="Tag", automargin=True, row=3, col=1)
    fig1.update_yaxes(title_text="CFR", row=3, col=1)
    fig1.update_yaxes(title_text="R<sub>e</sub>", row=2, col=1)
    fig1.update_yaxes(title_text="Anzahl", row=1, col=1)
    fig1.update_layout(showlegend=True, title=name, legend_orientation="h")
    plot(fig1, filename=os.path.join(datadir, name + "_cfr.html"),
         auto_open=False, auto_play=False)
    if pio.renderers.default in ['png', 'jpeg', 'jpg', 'svg']:
        pio.renderers.default = 'browser'
    fig1.write_image(os.path.join(datadir, name + "_cfr.svg"), width=1200,
                                  height=800)
    # fig1.show()
    return
