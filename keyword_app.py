import streamlit as st
import pandas as pd

# Sprachpakete für spacy
import en_core_web_sm
import de_core_news_sm

# import de_core_news_lg
import matplotlib.pyplot as plt


from nltk.stem.snowball import SnowballStemmer
import random

import textgraph
import textmetrics


# ------------------ settings --------------------
st.set_page_config(layout="wide")

# hier die gewünschte Sprache angeben ('en' oder 'de')
language = "de"

# hier Wörter hinzufügen, die ignoriert werden sollen
additional_stopwords = ["PLATZHALTER", "PLATZHALTER 2", "-"]

if language == "en":
    nlp = en_core_web_sm.load()
    stemmer = SnowballStemmer("english")

elif language == "de":
    # nlp = de_core_news_sm.load()
    nlp = de_core_news_sm.load()
    stemmer = SnowballStemmer("german")

stopwords = nlp.Defaults.stop_words
stopwords = stopwords.union(set(additional_stopwords))

# ---------------------- functions for caching --------------------------


@st.cache
def load_data(uploaded_file, col=0):
    texts = pd.read_csv(uploaded_file, header=None, sep=";")
    texts = texts[col].to_list()
    texts = random.sample(texts, 50)
    return texts


@st.cache(allow_output_mutation=True)
def create_wcn(texts_tokenized, link_filter):
    wcn = textgraph.create_wcn(texts=texts_tokenized, link_filter=link_filter)
    return wcn


@st.cache
def calculate_metrics(G, texts_tokenized, parallel, calc_connectivity):
    mtrcs = textmetrics.calculateTextMetrics(G, texts_tokenized, parallel=parallel, calc_connectivity=calc_connectivity)
    return mtrcs


session_state_keys = ["is_file", "kw_extracted", "plot_settings", "is_extract"]

for key in session_state_keys:
    if key not in st.session_state.keys():
        st.session_state[key] = False


with st.container():
    st.header("Keyword Extraction aus Textdateien")

    # ------------------ load texts --------------------
    st.write("Füge eine .csv Datei mit Texten ein.")
    col_name = st.text_input("Name der Textspalte. Wenn kein Name, leer lassen.")

    if col_name == "":
        col_name = 0

    uploaded_file = st.file_uploader("Choose a file")
    if uploaded_file is not None:
        texts = load_data(uploaded_file, col=col_name)
        st.write("Anzahl Texte:", len(texts))
        st.write("Ein Beispieltext")
        st.write(texts[0])
        st.session_state["is_file"] = True
    else:
        texts = None

    # ------------------ cleaning and graph  --------------------
    if st.session_state["is_file"]:

        if st.button("Extract Keywords"):
            st.session_state["is_extract"] = True

    if st.session_state["is_extract"]:

        # Die Texte werden bereinigt und in Tokens zerlegt
        texts_tokenized = textgraph.clean_texts(texts=texts, stopwords=stopwords, stemmer=stemmer)  # bei Bedarf Stemmer übergeben

        link_filter = 2
        G = create_wcn(texts_tokenized=texts_tokenized, link_filter=link_filter)

        # ------------------ calculate metrics  --------------------
        metrics = calculate_metrics(G, texts_tokenized, parallel=True, calc_connectivity=False)

        # Anzahl der Top X Elemente, sortiert nach prevalence
        n_top = 20

        result = metrics.iloc[:n_top, :].sort_values(by="diversity", ascending=False)
        result.rename(columns={"prevalence": "relative Häufigkeit", "diversity": "Diversität"}, inplace=True)
        st.subheader("Folgende Schlüsselwörter wurden identifiziert")
        result  # magic

        st.session_state["kw_extracted"] = True

    # ------------------ settings for plot ----------------------
    if st.session_state["kw_extracted"]:
        st.subheader("Folgende Schlüsselwörter wurden identifiziert")
        node = st.text_input("Schlüsselwort", value=result.index[0])
        recommendation = textgraph.recommend_min_weight(G=G, node=node, radius=1)
        st.write("Empfohlenes Kantengewicht:", recommendation)
        min_weight = st.number_input("Minimales zu berücksichtigendes Gewicht", min_value=1, value=recommendation)

        st.session_state["plot_settings"] = True

    # ------------------ plot -----------------------------------

    if st.session_state["plot_settings"]:
        st.subheader(f"Andere Wörter im Zusammenhang mit {node}")
        fig = textgraph.get_figure_ego_of_word(G=G, node=node, radius=1, min_weight=min_weight)
        st.write(fig)
