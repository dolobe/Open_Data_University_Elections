import pandas as pd
import folium
import streamlit as st
from streamlit_folium import st_folium
import requests
import logging
import json
import app2
from streamlit_option_menu import option_menu

logging.basicConfig(level=logging.INFO)

st.set_page_config(page_title="Data Visualization", layout="wide")

st.title("🌍 DATAVISUALISATION")

selected = option_menu(
    menu_title=None,
    options=["Carte interactive", "Graphique"],
    icons=["map", "bar-chart"],
    menu_icon="cast",
    default_index=0,
    orientation="horizontal",
)

st.session_state.page = 'Carte interactive' if selected == "Carte interactive" else 'Analyse'

@st.cache_data
def load_data():
    agesexcommunes = pd.read_csv('./Age_csp/agesexcommunes.csv')
    agesexdepartements = pd.read_csv('./Age_csp/agesexdepartements.csv')
    alphabetisation = pd.read_csv('./Alphabetisation/alphabetisationcommunes.csv')
    pres_df = pd.read_csv('./Elections/Pres2022.csv', low_memory=False)
    leg_df = pd.read_csv('./Elections/Legis2022.csv', low_memory=False)
    return agesexcommunes, agesexdepartements, alphabetisation, pres_df, leg_df

agesexcommunes, agesexdepartements, alphabetisation, pres_df, leg_df = load_data()

def get_coordinates(city_name):
    url = f"https://nominatim.openstreetmap.org/search?q={city_name},+France&format=json"
    headers = {'User-Agent': 'MonApplication/1.0'}
    try:
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        data = response.json()
        if data:
            lat = float(data[0]['lat'])
            lon = float(data[0]['lon'])
            logging.info(f"Coordonnées trouvées pour {city_name}: Latitude {lat}, Longitude {lon}")
            return lat, lon
        else:
            logging.warning(f"Aucune donnée trouvée pour {city_name}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Erreur de requête pour {city_name}: {e}")
    return None

def create_commune_map(commune_coordinates=None):
    m = folium.Map(location=[46.6034, 1.8883], zoom_start=5)
    
    with open('departements.geojson', 'r', encoding='utf-8') as f:
        geojson_data = json.load(f)
    
    folium.GeoJson(
        geojson_data,
        name='geojson'
    ).add_to(m)
    
    if commune_coordinates:
        folium.Marker(
            location=commune_coordinates,
            popup=f"Commune: {commune_selectionnee}",
            icon=folium.Icon(color='blue')
        ).add_to(m)
    
    folium.LayerControl().add_to(m)
    
    return m

def show_data(commune):
    st.write("Données de la commune sélectionnée :")
    data_dict = commune.to_dict()
    data_df = pd.DataFrame(data_dict.items(), columns=["Champ", "Valeur"]).T
    data_df.columns = data_df.iloc[0]
    data_df = data_df[1:]
    st.table(data_df)

type_election = st.sidebar.selectbox("Choisissez le type d'élection", ["Présidentielle", "Législative"])
df_election = pres_df if type_election == "Présidentielle" else leg_df

departement_selectionne = st.sidebar.selectbox("Sélectionnez un département", df_election['nomdep'].unique())
df_departement = df_election[df_election['nomdep'] == departement_selectionne]

commune_selectionnee = st.sidebar.selectbox("Sélectionnez une commune", df_departement['nomcommune'].unique())
coordinates_api = get_coordinates(commune_selectionnee)

votes_data = df_departement[df_departement['nomcommune'] == commune_selectionnee]

if st.session_state.page == 'Carte interactive':
    st.write("Bienvenue sur la page principale!")
    commune_map = create_commune_map(coordinates_api)

    if coordinates_api:
        lat_commune, lon_commune = coordinates_api
        folium.Marker(location=[lat_commune, lon_commune], popup=commune_selectionnee, icon=folium.Icon(color='blue')).add_to(commune_map)
        info_commune = df_departement[df_departement['nomcommune'] == commune_selectionnee].iloc[0]
        st.markdown(f"<h3 style='color: teal;'>Informations pour {info_commune['nomcommune']} :</h3>", unsafe_allow_html=True)
    else:
        st.warning("Aucune coordonnée disponible pour cette commune.")

    if 'info_commune' in locals():
        show_data(info_commune)

    st.subheader("Sélectionnez un candidat pour voir les résultats")
    candidats = [col.replace('voix', '') for col in votes_data.columns if col.startswith('voix')]
    candidat_selectionne = st.selectbox("Candidat", candidats)

    if candidat_selectionne:
        voix_col = f'voix{candidat_selectionne}'
        if voix_col in votes_data.columns:
            voix = votes_data[voix_col].sum()
            st.markdown(f"<p style='color: darkorange;'>Nombre de voix pour {candidat_selectionne}: {voix}</p>", unsafe_allow_html=True)
        else:
            st.warning(f"Aucune donnée de voix pour {candidat_selectionne}")

    exprimes = votes_data['exprimes'].sum()
    votants = votes_data['votants'].sum()
    inscrits = votes_data['inscrits'].sum()
    st.markdown(f"<p style='color: darkgreen;'>Nombre d'inscrits: {inscrits}</p>", unsafe_allow_html=True)
    st.markdown(f"<p style='color: darkgreen;'>Nombre de votes exprimés: {exprimes}</p>", unsafe_allow_html=True)
    st.markdown(f"<p style='color: darkgreen;'>Nombre de votants: {votants}</p>", unsafe_allow_html=True)

    st.subheader("Carte interactive de la France")
    st_folium(commune_map, width=700, height=500)

elif st.session_state.page == 'Analyse':
    app2.run(agesexcommunes, alphabetisation, commune_selectionnee, votes_data)

