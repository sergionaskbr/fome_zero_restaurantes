# --------------------
# Libraries
# --------------------
import pandas as pd
import streamlit as st
from PIL import Image 
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import folium_static
import inflection

# -----------------
# Import Dataset
# -----------------
df = pd.read_csv('dataset/zomato.csv')

# --------------
# Funções
# --------------

RAW_DATA_PATH = f"dataset/zomato.csv"

COUNTRIES = {
    1: "India",
    14: "Australia",
    30: "Brazil",
    37: "Canada",
    94: "Indonesia",
    148: "New Zealand",
    162: "Philippines",
    166: "Qatar",
    184: "Singapore",
    189: "South Africa",
    191: "Sri Lanka",
    208: "Turkey",
    214: "United Arab Emirates",
    215: "England",
    216: "United States of America",
}

COLORS = {
    "3F7E00": "darkgreen",
    "5BA829": "green",
    "9ACD32": "lightgreen",
    "CDD614": "orange",
    "FFBA00": "red",
    "CBCBC8": "darkred",
    "FF7800": "darkred",
}

def country_name(country_id):
  return COUNTRIES[country_id]

def color_name(color_code):
  return COLORS[color_code]

def create_price_type(price_range):
  if price_range == 1:
    return "cheap"
  elif price_range == 2:
    return "normal"
  elif price_range == 3:
    return "expensive"
  else:
    return "gourmet"

def adjust_columns_order(dataframe):
    df = dataframe.copy()

    new_cols_order = [
        "restaurant_id",
        "restaurant_name",
        "country",
        "city",
        "address",
        "locality",
        "locality_verbose",
        "longitude",
        "latitude",
        "cuisines",
        "price_type",
        "average_cost_for_two",
        "currency",
        "has_table_booking",
        "has_online_delivery",
        "is_delivering_now",
        "aggregate_rating",
        "rating_color",
        "color_name",
        "rating_text",
        "votes",
    ]

    return df.loc[:, new_cols_order]

def rename_columns(dataframe):
    df = dataframe.copy()
    title = lambda x: inflection.titleize(x)
    snakecase = lambda x: inflection.underscore(x)
    spaces = lambda x: x.replace(" ", "")
    cols_old = list(df.columns)
    cols_old = list(map(title, cols_old))
    cols_old = list(map(spaces, cols_old))
    cols_new = list(map(snakecase, cols_old))
    df.columns = cols_new
    return df

def process_data(file_path):
    df = pd.read_csv(file_path)
    df = df.dropna()
    df = rename_columns(df)
    df["price_type"] = df.loc[:, "price_range"].apply(lambda x: create_price_type(x))
    df["country"] = df.loc[:, "country_code"].apply(lambda x: country_name(x))
    df["color_name"] = df.loc[:, "rating_color"].apply(lambda x: color_name(x))
    df["cuisines"] = df.loc[:, "cuisines"].apply(lambda x: x.split(",")[0])
    df = df.drop_duplicates()
    df = adjust_columns_order(df)
    df.to_csv("dataset/processed.csv", index=False)
    return df

df_raw = pd.read_csv(RAW_DATA_PATH)
df1 = df_raw.copy()
df1 = rename_columns(df1)
df1 = df1.dropna()
df2 = process_data(RAW_DATA_PATH)

st.set_page_config( 
    page_title="Home", page_icon="📊", layout="wide"
)

# =================
# Barra Lateral (Sidebar) do Streamlit
# =================
image = Image.open('img/1.png')

col1, col2 = st.sidebar.columns([1, 4], gap="small")
col1.image(image, width=60)
col2.markdown("# Fome Zero")
st.sidebar.markdown('## Filtros')
country_options = st.sidebar.multiselect(
    'Escolha os países cujos restaurantes deseja visualizar',
    df2.loc[:, "country"].unique().tolist(),
        default=["Brazil", "England", "Qatar", "South Africa", "Canada", "Australia"],
    )
st.sidebar.markdown("""---""")

st.sidebar.markdown("### Dados Tratados")

processed_data = pd.read_csv("dataset/processed.csv")

st.sidebar.download_button(
    label="Download",
    data=processed_data.to_csv(index=False, sep=";"),
    file_name="processed.csv",
    mime="text/csv",
    )

# Filtro de países:
selected_countries = df2['country'].isin(country_options) 
df2 = df2.loc[selected_countries, :]

# =================
# Layout da Página Principal do Streamlit 
# =================

st.write('# Fome Zero!')
st.write('## O melhor lugar para encontrar seu mais novo restaurante favorito!')
st.write('### Temos as seguintes marcas dentro da nossa plataforma:')

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
  restaurantes_cadastrados = df2['restaurant_id'].nunique()
  col1.metric('Restaurantes cadastrados', restaurantes_cadastrados)

with col2:
  paises_cadastrados = df2['country'].nunique()
  col2.metric('Países cadastrados', paises_cadastrados)

with col3:
  cidades_cadastradas = df2['city'].nunique()
  col3.metric('Cidades cadastradas', cidades_cadastradas)

with col4:
  total_votes = df2['votes'].sum()
  col4.metric('Avaliações feitas na plataforma', "{:,}".format(total_votes).replace(",", "."))

with col5:
  total_cuisines = df2['cuisines'].nunique()
  col5.metric('Tipos de culinária oferecidos', total_cuisines)

def create_map(dataframe):
    f = folium.Figure(width=1920, height=1080)
    m = folium.Map(max_bounds=True).add_to(f)
    marker_cluster = MarkerCluster().add_to(m)

    for _, line in dataframe.iterrows():

        name = line["restaurant_name"]
        price_for_two = line["average_cost_for_two"]
        cuisine = line["cuisines"]
        currency = line["currency"]
        rating = line["aggregate_rating"]
        color = f'{line["color_name"]}'

        html = "<p><strong>{}</strong></p>"
        html += "<p>Price: {},00 ({}) para dois"
        html += "<br />Type: {}"
        html += "<br />Aggregate Rating: {}/5.0"
        html = html.format(name, price_for_two, currency, cuisine, rating)

        popup = folium.Popup(
            folium.Html(html, script=True),
            max_width=500,
        )

        folium.Marker(
            [line["latitude"], line["longitude"]],
            popup=popup,
            icon=folium.Icon(color=color, icon="home", prefix="fa"),
        ).add_to(marker_cluster)

    folium_static(m, width=1024, height=768)

map_df = df2.loc[df2["country"].isin(country_options), :]
create_map(map_df)

st.markdown(f"""<a href="https://www.comunidadeds.com/"> ##### Projeto final da disciplina FTC - Análise de Dados com Python do Curso de Formação em Ciência de Dados da <em>Comunidade DS</em>. Feito por Sérgio Nascimento.</a>""")
st.write('###### LinkedIn - https://www.linkedin.com/in/sergionasc/')
st.write('###### GitHub - https://github.com/sergionaskbr')


