import streamlit as st
import pandas as pd

import matplotlib.pyplot as plt
import seaborn as sns

import accountanalysis as acc


# ------------------ settings --------------------
st.set_page_config(layout="wide")


# ---------------------- functions for caching --------------------------


@st.cache
def load_data(uploaded_file, col=0):
    df = pd.read_csv(uploaded_file, index_col=0, parse_dates=["Date"])
    return df


def get_account_information(df, account_name):
    n_send = len(df[df["From"] == account_name].drop_duplicates("Date"))
    n_recieved = len(df[df["To"] == account_name].drop_duplicates("Date"))
    date_first_mail = df[df["From"] == account_name]["Date"].min().date()
    date_last_mail = df[df["From"] == account_name]["Date"].max().date()
    df_poi = acc.filter_df_for_poi(df=df, poi=account_name)
    n_contacts = len(acc.get_contacts_of_poi(df=df_poi, poi=account_name))

    st.write("Anzahl gesendeter E-Mails:", n_send)
    st.write("Anzahl empfangener E-Mails:", n_recieved)
    st.write("Erste gesendete E-Mail:", date_first_mail)
    st.write("Letzte gesendete E-Mail:", date_last_mail)
    st.write("Anzahl Kontakte:", n_contacts)


@st.cache
def create_timeline(df, col_name):
    timeline = acc.create_timeline(df=df, col_name="Date")
    return timeline


@st.cache
def create_communication_timeline(df, poi, timeline):
    df_poi_sent = df[df["From"] == poi][~df[df["From"] == poi].index.duplicated(keep="first")]
    df_poi_recieved = df[df["To"] == poi][~df[df["To"] == poi].index.duplicated(keep="first")]

    com_time_series = pd.DataFrame(index=timeline)

    com_time_series["sent"] = acc.get_cumulated_elements_per_day(df_raw=df_poi_sent, timeline=timeline)
    com_time_series["recieved"] = acc.get_cumulated_elements_per_day(df_raw=df_poi_recieved, timeline=timeline)
    return com_time_series


@st.cache
def get_df_poi(df, poi):
    df_poi = acc.filter_df_for_poi(df=df, poi=poi).drop_duplicates("Date")
    return df_poi


@st.cache
def get_contacts_of_poi(df_poi, poi):
    contacts_of_poi = acc.get_contacts_of_poi(df=df_poi, poi=poi)
    contacts_with_count = acc.get_contacts_with_count(df_poi=df_poi, poi=poi, contacts_of_poi=contacts_of_poi)
    return contacts_with_count.sort_values(by="sent", ascending=False)


session_state_keys = ["file_cached", "is_analyzed", "plot_settings", "is_analyze"]

for key in session_state_keys:
    if key not in st.session_state.keys():
        st.session_state[key] = False


with st.container():
    st.header("Analyse der Kommuniaktion eines E-Mail Accounts")

    # ------------------ load mails --------------------
    st.write("Füge eine .csv Datei mit Texten ein. Die Spalten 'Date', 'From' und 'To' werden erwartet.")

    uploaded_file = st.file_uploader("Choose a file")
    if uploaded_file is not None:
        df = load_data(uploaded_file)
        st.write("Anzahl der Mails:", len(df))
        st.session_state["file_cached"] = True
    else:
        df = None

    # ------------------ settings  --------------------
    if st.session_state["file_cached"]:
        mail_accounts = set(df["From"]).union(set(df["To"]))
        poi = st.sidebar.selectbox("Wähle einen E-Mail Account:", mail_accounts)
        df_poi = get_df_poi(df=df, poi=poi)
        # TODO: filter time

        if st.button("Show E-Mail Activities"):
            st.session_state["is_analyze"] = True

    if st.session_state["is_analyze"]:

        # show general information about the data
        st.subheader("Algemeine Informationen über den Account:")
        get_account_information(df=df, account_name=poi)

        timeline = create_timeline(df=df, col_name="Date")

        # create cumulated mail count of poi
        st.subheader("Kumulierte empfange und gesendete E-Mails")
        com_time_series = create_communication_timeline(df=df, poi=poi, timeline=timeline)

        fig_com_time_series, ax_com_time_series = plt.subplots()

        fig_com_time_series.set_figwidth(20)
        fig_com_time_series.set_figheight(10)

        sns.lineplot(data=com_time_series, x=com_time_series.index, y="sent", label="sent", ax=ax_com_time_series)
        sns.lineplot(data=com_time_series, x=com_time_series.index, y="recieved", label="recieved", ax=ax_com_time_series)
        st.pyplot(fig_com_time_series)

        # show mail distribution during the day of poi
        st.subheader("Verteilung gesendeter und empfangener E-Mails nach Uhrzeit")
        df_time = acc.get_daily_distribution(df_poi=df_poi, poi=poi)

        fig_time_distribution, ax_time_distribution = plt.subplots()

        fig_time_distribution.set_figwidth(20)
        fig_time_distribution.set_figheight(10)

        sns.histplot(data=df_time, x="time", bins=24, hue="action", ax=ax_time_distribution)
        st.pyplot(fig_time_distribution)

        # contacts of poi
        st.subheader("Häufigste Kontakte des E-Mail Accounts")
        contacts_with_count = get_contacts_of_poi(df_poi=df_poi, poi=poi)
        st.write(contacts_with_count.sort_values("sent", ascending=False))

        kind_of_mail = st.text_input("Gesendete oder empfangene E-Mails betrachten?", value="gesendete")
        n_contacts = st.number_input("Nr. von Kontakten", min_value=1, value=5)

        if kind_of_mail == "gesendete":
            sent = True
        else:
            sent = False

        # show contacts with count
        st.subheader(f"Kumulierte {kind_of_mail} E-Mail Kommunikation zwischen dem E-Mail Account und seinen Top {n_contacts} Kontakten")
        fig_contacts = acc.plot_communication_with_contacts(df_poi=df_poi, poi=poi, contacts_with_count=contacts_with_count, n_contacts=n_contacts, timeline=timeline, sent=sent)

        fig_contacts.set_figwidth(20)
        fig_contacts.set_figheight(10)

        st.pyplot(fig_contacts)

        st.session_state["is_analyzed"] = True

    # ------------------ settings for plot ----------------------
    if st.session_state["is_analyzed"]:
        st.subheader("Wähle einen Kontakt zu weiteren Analyse")
        # contacts = contacts_of_poi = acc.get_contacts_of_poi(df=df_poi, poi=poi)
        contact = st.selectbox("Wähle einen Kontakt:", contacts_with_count["contact"])
        cum_contact_time_series = acc.get_cumulated_contact_time_series(df_poi=df_poi, poi=poi, contact=contact, timeline=timeline)

        fig_contact, ax_contact = plt.subplots()

        fig_contact.set_figwidth(20)
        fig_contact.set_figheight(10)

        sns.lineplot(data=cum_contact_time_series, x=cum_contact_time_series.index, y=poi, label=poi, ax=ax_contact)
        sns.lineplot(data=cum_contact_time_series, x=cum_contact_time_series.index, y=contact, label=contact, ax=ax_contact)

        st.write("Kumulierte gesendete E-Mail Kommunikation zwischen dem Account und einem Kontakt")
        st.pyplot(fig_contact)

        st.session_state["plot_settings"] = True

    # ------------------ plot -----------------------------------

    if st.session_state["plot_settings"]:
        pass
