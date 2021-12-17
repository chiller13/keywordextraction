import pandas as pd
import graphmetrics
import matplotlib.pyplot as plt
import seaborn as sns


def filter_df_for_poi(df, poi):
    df_poi = df[(df["From"] == poi) | (df["To"] == poi)]
    return df_poi


def get_contacts_of_poi(df, poi):
    contacts_of_poi = set(df["From"]).union(set(df["To"]))
    contacts_of_poi.remove(poi)
    return contacts_of_poi


def create_timeline(df, col_name):
    """Creates Timeline for Snapshots."""
    start_date = df[col_name].dt.date.min()
    end_date = df[col_name].dt.date.max()

    timeline = pd.date_range(start_date, end_date, freq="d")
    timeline = pd.to_datetime(timeline, utc=True)
    return timeline


def get_contacts_with_count(df_poi, poi, contacts_of_poi):
    contacts_with_count = pd.DataFrame(columns=["contact", "sent", "recieved"])

    for contact in contacts_of_poi:
        poi_to_contact = len(graphmetrics.filter_person(df=df_poi, pers1=poi, pers2=contact))
        contact_to_poi = len(graphmetrics.filter_person(df=df_poi, pers1=contact, pers2=poi))

        contacts_with_count = contacts_with_count.append({"contact": contact, "sent": poi_to_contact, "recieved": contact_to_poi}, ignore_index=True)
    return contacts_with_count


def show_account_information(df, account_name):
    print("Anzahl gesendeter E-Mails:", len(df[df["From"] == account_name].drop_duplicates("Date")))
    print("Anzahl empfangener E-Mails:", len(df[df["To"] == account_name].drop_duplicates("Date")))
    print("Erste gesendete E-Mail:", df[df["From"] == account_name]["Date"].min().date())
    print("Letzte gesendete E-Mail:", df[df["From"] == account_name]["Date"].max().date())
    df_poi = filter_df_for_poi(df=df, poi=account_name)
    print("Anzahl Kontakte:", len(get_contacts_of_poi(df=df_poi, poi=account_name)))


def get_cumulated_elements_per_day(df_raw: pd.DataFrame, timeline):
    cum_series = [0] * len(timeline)
    cum_sum = 0

    df = df_raw.groupby([df_raw["Date"].dt.date]).count()

    for ind, day in enumerate(timeline):
        if day.date() in df.index:
            cum_sum += df[df.index == day.date()]["Date"][0]

        cum_series[ind] = cum_sum

    return cum_series


def get_elements_per_day(df_raw: pd.DataFrame, timeline):
    daily_series = [0] * len(timeline)

    df = df_raw.groupby([df_raw["Date"].dt.date]).count()

    for ind, day in enumerate(timeline):
        if day.date() in df.index:
            daily_series[ind] = df[df.index == day.date()]["Date"][0]

    return daily_series


def get_daily_distribution(df_poi, poi):
    df_time = pd.DataFrame({"time": df_poi["Date"].dt.hour, "action": df_poi["From"]})
    df_time["action"] = df_time["action"].apply(lambda x: "sent" if x == poi else "recieved")
    return df_time


def plot_communication_with_contacts(df_poi, poi, contacts_with_count, n_contacts, timeline, sent):
    # show communication distribution of poi with top X contacts

    fig, ax = plt.subplots()

    for contact in contacts_with_count.sort_values("sent", ascending=False)["contact"][:n_contacts]:

        if sent:
            filtered_df = graphmetrics.filter_person(df=df_poi, pers1=poi, pers2=contact)
        else:
            filtered_df = graphmetrics.filter_person(df=df_poi, pers1=contact, pers2=poi)

        cum_contact_time_series = get_cumulated_elements_per_day(df_raw=filtered_df, timeline=timeline)

        sns.lineplot(x=timeline, y=cum_contact_time_series, label=contact, ax=ax)

    return fig


def get_cumulated_contact_time_series(df_poi, poi, contact, timeline):
    cum_contact_time_series = pd.DataFrame(index=timeline)

    poi_to_contact = graphmetrics.filter_person(df=df_poi, pers1=poi, pers2=contact)
    contact_to_poi = graphmetrics.filter_person(df=df_poi, pers1=contact, pers2=poi)

    cum_contact_time_series[poi] = get_cumulated_elements_per_day(df_raw=poi_to_contact, timeline=timeline)
    cum_contact_time_series[contact] = get_cumulated_elements_per_day(df_raw=contact_to_poi, timeline=timeline)
    return cum_contact_time_series
