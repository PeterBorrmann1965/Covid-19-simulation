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
import scipy.stats
from IPython.display import display
import pkg_resources
from sklearn.preprocessing import LabelEncoder

warnings.filterwarnings("ignore")


STATEDEF_EN = {0: "not infected", 1: "immun", 2: "infected",
               3: "identified", 4: "dead (other)", 5: 'hospital',
               6: 'intensive', 7: 'Covid-19 dead'}

STATEDEF_DE = {0: "nicht infiziert", 1: "immun", 2: "infiziert",
               3: "identifiziert", 4: "tod (Sonstige)",
               5: 'hospitalisiert', 6: 'ICU', 7: 'tod (Covid-19)'}

STATEDEF = STATEDEF_DE


def isnotebook():
    """Check if executed in Jupyter."""
    try:
        shell = get_ipython().__class__.__name__
        if shell == 'ZMQInteractiveShell':
            return True   # Jupyter notebook or qtconsole
        elif shell == 'TerminalInteractiveShell':
            return False  # Terminal running IPython
        else:
            return False  # Other type (?)
    except NameError:
        return False


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


def sim(age, drate, mean_serial=7.0, std_serial=3.4, nday=140, day0icu=20,
        cutdown=25000, prob_icu=0.005, mean_days_to_icu=12,
        mean_duration_icu=10, immunt0=0.0, icu_fatality=0.5,
        long_term_death=False, hnr=None, com_attack_rate=0.6,
        contacts=None, r_mean=1.5, cutr_mean=1.5, simname="test"):
    """Simulate model.

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
    cutr_mean : mean_r at forced lockdown
    cutdown : if the number of occupied icu beds exceeds cutdown the mean r
        is reduced to cut_meanr

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
    day0 : the simualtion day on which the number of icu care patients exceeds
        for the first time day0icu
    re :  array of length nday
        the effective reporoduction number per day
    params : a copy of all input paramters as a data frame
    """
    # This must be the first line
    args = locals()
    args["mean_age"] = np.mean(age)
    tstart = time.time()
    # Initialize r and cutr
    if contacts is None:
        r = np.ones(shape=age.shape[0]) * r_mean
    else:
        r = contacts / np.mean(contacts) * r_mean

    if cutr_mean is None:
        cutr = None
    else:
        cutr = r / np.mean(r) * cutr_mean

    # Simulation name
    r0aux = np.mean(r)
    name = simname

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
    time_to_icu = np.random.poisson(lam=mean_days_to_icu, size=n)

    # individual prob icu
    ind_prob_icu = drate/np.mean(drate) * prob_icu
    # ind_prob_icu = prob_icu
    # print("Mean prob icu:" + str(np.mean(ind_prob_icu)))

    # Precalculate time to icu
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
    r = 2.5 * r / np.mean(r)
    day0 = -1
    burn = True

    toticu = 0
    re = np.zeros(shape=nday)
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
            state[i, (rans < drate) & (state[i, :] != 7)] = 4

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

        # The new infections are mapped to household
        if hnr is not None:
            # The infections risk depends on the time profile
            hnr_risk = hnrinfected[:, imin:i].dot(delay[-len(h):])

            # new infections due to community attack
            hnr_risk = com_attack_rate * hnr_risk
            # We can reuses the last randoms because people in state 6 and 0
            # can not overlap
            filt2 = (rans < hnr_risk[hnr]) & (state[i, ] == 0)
            state[i, filt2] = 2

            # Reduce the new infected by those infected by community attack
            addinf = np.mean(r) * newinf - np.sum(filt2)
            addinf = np.max([0.0, addinf])/np.mean(r)
            pinf = r * addinf / n
            rans = np.random.random(size=n)
            filt = (rans < pinf) & (state[i, ] == 0)
            state[i, filt] = 2

            # Store the new infections in each hosusehold
            filt = filt | filt2
            hnrinfected[:, i] = np.where(
                np.bincount(hnr, weights=filt) > 0, 1, 0)
        else:
            # infection probabilties by case
            pinf = r * newinf / n
            # We can reuses the last randoms because people in state 6 and 0
            # can not overlap
            filt = (rans < pinf) & (state[i, ] == 0)
            state[i, filt] = 2

        # store first infections day
        firstdayinfected[filt] = i

        # number of new infections new infections
        infections[i] = np.sum(filt)
        if newinf > 0:
            re[i] = infections[i] / newinf
        else:
            re[i] = 0

        statesum[:, i] = np.bincount(state[i, :], minlength=nstate)

        if (np.sum(statesum[2, i]) > 100) and burn:
            r = rstart
            burn = False

        # if the number of icus exceeds
        if (np.sum(statesum[6, i]) > day0icu) and (day0 == -1):
            r = rstart
            day0 = i

        # if the number of icus exceeds cutdown r is devided by cutr
        if (cutr is not None) and (statesum[6, i] > cutdown):
            r = cutr
        else:
            r = rstart

    # return only simulation parameter and no populations parameters
    argsnew = {}
    for key, value in args.items():
        if type(value) in [int, bool, float, str]:
            argsnew[key] = value
    params = pd.DataFrame.from_dict(argsnew, orient="index")
    params = params.reset_index()
    params.columns = ["Parameter", "Wert"]

    tanalyse = time.time()
    agegroup = (age/10).astype(int)*10
    print("Simulation time: " + str(tanalyse-tstart))
    results, groupresults = analysestate(state, title=name, day0=day0,
                                         group=agegroup)
    tcfr = time.time()
    cfr = prob_icu * icu_fatality
    analyse_cfr(statesum, re, cfr=cfr, darkrate=1,
                timetodeath=mean_duration_icu+mean_days_to_icu,
                delay=5, name=name, day0=day0)
    tend = time.time()
    display(results)

    # Write each dataframe to a different worksheet.
    writer = pd.ExcelWriter("../results/" + name + ".xlsx",
                            engine='xlsxwriter')

    params.to_excel(writer, sheet_name="Parameter", index=False)
    results.to_excel(writer, sheet_name='Ergebnis Übersicht', index=False)
    groupresults.to_excel(writer, sheet_name='Gruppen pro Tag', index=False)
    ws = writer.sheets["Gruppen pro Tag"]
    workbook = writer.book
    format1 = workbook.add_format({'num_format': '0.000%'})
    ws.set_column('I:M', None, format1)
    ws.autofilter("A1:M100")
    ws.filter_column('A', 'x == ' + str(nday-1))
    writer.save()

    return state, statesum, infections, day0, re, params


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

    statesumday = {}
    nmax = 0
    results = {}
    lastday = state.shape[0]-1
    n = state.shape[1]
    ngraph = 0
    for key, value in STATEDEF.items():
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
            results[value] = resnow

    fig2 = make_subplots(rows=ngraph, cols=2, column_titles=(
        "Zustand", "Änderung zum Vortag (Delta)"), shared_xaxes=True)

    k = 0
    for key, value in STATEDEF.items():
        if max(statesumday[value]) > 0:
            k = k + 1
            deltastatesum = np.diff(statesumday[value][:nmax],
                                    prepend=statesumday[value][0])
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

    fig2.update_layout(showlegend=True, title=title, legend_orientation="h")
    fig2.update_xaxes(title_text="Tag", row=ngraph, col=1)
    fig2.update_xaxes(title_text="Tag", row=ngraph, col=2)
    fig2.update_xaxes(automargin=True)
    for k in range(0, ngraph):
        fig2.update_yaxes(title_text="Anzahl", row=k+1, col=1)

    if isnotebook():
        fig2.show()
    else:
        plot(fig2, filename="../figures/" + title + "_linear.html")

    nday = state.shape[0]
    groupresults = []
    if group is not None:
        df = pd.DataFrame({"group": group})
        for i in range(1, nday):
            df["state"] = state[i, :]
            a = df.groupby(["group", "state"], sort=False,
                           ).agg(n=("state", "count")).reset_index()
            a.reset_index(inplace=True)
            a = a.pivot_table(values="n", columns="state",
                              index=["group"], margins=True,
                              aggfunc="sum", fill_value=0)
            a.reset_index(inplace=True)
            a.rename(columns=STATEDEF, inplace=True)
            a["day"] = i
            groupresults.append(a)

        groupresults = pd.concat(groupresults)
        groupresults.fillna(0, inplace=True)
        groupresults = groupresults[['day', 'group', 'nicht infiziert',
                                     'infiziert', 'immun', 'ICU',
                                     'tod (Covid-19)', 'All']]
        groupresults.rename(columns={"group": "Gruppe", "day": "Tag", "All":
                                     "Gesamt"}, inplace=True)
        for col in ['nicht infiziert', 'infiziert', 'immun', 'ICU',
                    'tod (Covid-19)']:
            groupresults[col + str(" %")] = groupresults[col] / groupresults[
                "Gesamt"]
    return results, groupresults


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
            for s in range(0, 35):
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
                day0=0):
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
    pdf = [scipy.stats.poisson.pmf(i, timetodeath) for i in range(0, 500)]
    pdf = np.array(pdf)
    corrected2 = np.empty_like(cuminfected)
    corrected2[0] = 0
    for t in range(1, len(newinfections)):
        corrected2[t] = 0
        for s in range(0, 35):
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
                              y=reffektive[:nmax], mode='lines',
                              name="R effektiv"), row=2, col=1)

    fig1.update_xaxes(title_text="Tag", automargin=True, row=3, col=1)
    fig1.update_yaxes(title_text="CFR", row=3, col=1)
    fig1.update_yaxes(title_text="R<sub>e</sub>", row=2, col=1)
    fig1.update_yaxes(title_text="Anzahl", row=1, col=1)
    fig1.update_layout(showlegend=True, title=name, legend_orientation="h")
    if isnotebook():
        fig1.show()
    else:
        plot(fig1, filename="../figures/" + name + "_cfr.html")
    return
