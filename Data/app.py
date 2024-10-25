import pandas as pd
import folium
import streamlit as st
from streamlit_folium import st_folium
import requests
import logging
import seaborn as sns
import matplotlib.pyplot as plt

logging.basicConfig(level=logging.INFO)

agesexcommunes = pd.read_csv('./Age_csp/agesexcommunes.csv')
agesexdepartements = pd.read_csv('./Age_csp/agesexdepartements.csv')
alphabetisation = pd.read_csv('./Alphabetisation/alphabetisationcommunes.csv')
pres_df = pd.read_csv('./Elections/Pres2022.csv', low_memory=False)
leg_df = pd.read_csv('./Elections/Legis2022.csv', low_memory=False)

def get_coordinates(city_name):
    """Get the coordinates for a given city name."""
    url = f"https://nominatim.openstreetmap.org/search?q={city_name},+France&format=json"
    headers = {'User-Agent': 'MonApplication/1.0'}
    try:
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        data = response.json()
        if data:
            lat = float(data[0]['lat'])
            lon = float(data[0]['lon'])
            logging.info(f"Coordinates found for {city_name}: Latitude {lat}, Longitude {lon}")
            return lat, lon
        else:
            logging.warning(f"No data found for {city_name}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Request error for {city_name}: {e}")
    return None

def create_commune_map(commune_coordinates=None):
    """Create a map centered on a specific commune."""
    m = folium.Map(location=[46.6034, 1.8883], zoom_start=5)
    
    for _, row in agesexdepartements.iterrows():
        pass
    
    if commune_coordinates:
        folium.Marker(
            location=commune_coordinates,
            popup=f"Commune: {commune_coordinates[2]}",
            icon=folium.Icon(color='blue')
        ).add_to(m)
    
    return m

st.title("Analyse des Élections en France")
st.markdown("Cette application vous permet d'explorer les données des élections présidentielles et législatives en France, ainsi que la démographie des communes sélectionnées.")

type_election = st.sidebar.selectbox("Choisissez le type d'élection", ["Présidentielle", "Législative"])
df_election = pres_df if type_election == "Présidentielle" else leg_df

departement_selectionne = st.sidebar.selectbox("Sélectionnez un département", df_election['nomdep'].unique())
df_departement = df_election[df_election['nomdep'] == departement_selectionne]

commune_selectionnee = st.sidebar.selectbox("Sélectionnez une commune", df_departement['nomcommune'].unique())
coordinates_api = get_coordinates(commune_selectionnee)

commune_map = create_commune_map()

if coordinates_api:
    lat_commune, lon_commune = coordinates_api
    folium.Marker(location=[lat_commune, lon_commune], popup=commune_selectionnee, icon=folium.Icon(color='blue')).add_to(commune_map)

    info_commune = df_departement[df_departement['nomcommune'] == commune_selectionnee].iloc[0]
    st.write(f"**Informations pour {info_commune['nomcommune']} :**")
else:
    st.warning("Aucune coordonnée disponible pour cette commune.")

st.sidebar.subheader("Sélectionnez une tranche d'âge")
age_group = st.sidebar.selectbox("Tranche d'âge", ['0-14', '15-39', '40-59', '60 et plus'])
age_column = {
    '0-14': 'poph0141962',
    '15-39': 'poph15391962',
    '40-59': 'poph40591962',
    '60 et plus': 'poph60p1962'
}[age_group]

age_data_filtered = agesexcommunes[agesexcommunes['nomcommune'] == commune_selectionnee]

if not age_data_filtered.empty:
    population_age = age_data_filtered[age_column].values[0]
    st.success(f"Population dans la tranche d'âge {age_group} à {commune_selectionnee}: {population_age}")

    st.subheader("Statistiques descriptives pour les populations par tranche d'âge :")
    st.write(age_data_filtered[['poph0141962', 'poph15391962', 'poph40591962', 'poph60p1962']].describe())
    
    correlation_data = age_data_filtered[['poph0141962', 'poph15391962', 'poph40591962', 'poph60p1962']]
    correlation_matrix = correlation_data.corr()
    
    st.subheader("Matrice de corrélation :")
    st.write(correlation_matrix)

    plt.figure(figsize=(8, 6))
    sns.heatmap(correlation_matrix, annot=True, fmt=".2f", cmap='coolwarm', cbar=True)
    st.pyplot(plt)
else:
    st.warning("Aucune donnée disponible pour cette commune.")
    
st.sidebar.subheader("Sélectionnez une année d'alphabétisation")
annee_alphabetisation = st.sidebar.selectbox("Année", [1866, 1871, 1876, 1882, 1887, 1890, 1895, 1900, 1905, 1910, 1915, 1920, 1925, 1930, 1935, 1940, 1945, 1946])

alpha_column = f'alpha{annee_alphabetisation}'
alpha_data_filtered = alphabetisation[alphabetisation['nomcommune'] == commune_selectionnee]

if not alpha_data_filtered.empty:
    alphabetisation_count = alpha_data_filtered[alpha_column].values[0]
    st.success(f"Nombre d'alphabétisation en {annee_alphabetisation} à {commune_selectionnee}: {alphabetisation_count}")

    st.subheader("Statistiques descriptives pour l'alphabétisation :")
    st.write(alpha_data_filtered[['alpha1866', 'alpha1871', 'alpha1876', 'alpha1882', 'alpha1887', 'alpha1890', 
                                'alpha1895', 'alpha1900', 'alpha1905', 'alpha1910', 'alpha1915', 
                                'alpha1920', 'alpha1925', 'alpha1930', 'alpha1935', 'alpha1940', 
                                'alpha1945', 'alpha1946']].describe())
else:
    st.warning("Aucune donnée d'alphabétisation disponible pour cette commune.")




st.subheader("Carte interactive de la France")
st_folium(commune_map, width=700, height=500)


def show_data(commune):
    """Show selected commune data in a table."""
    st.write("Données de la commune sélectionnée :")
    data_dict = commune.to_dict()
    data_df = pd.DataFrame(data_dict.items(), columns=["Champ", "Valeur"]).T
    data_df.columns = data_df.iloc[0]
    data_df = data_df[1:]
    st.table(data_df)

if st.button("Afficher les données de la commune sélectionnée"):
    show_data(info_commune)