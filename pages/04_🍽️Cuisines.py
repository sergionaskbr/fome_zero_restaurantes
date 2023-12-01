# --------------------
# Libraries
# --------------------
import pandas as pd
import streamlit as st
from PIL import Image 
import inflection
import utils.cuisines as cdt
import plotly.express as px

# -----------------
# Import Dataset
# -----------------
df = pd.read_csv('dataset/zomato.csv')

# --------------
# Functions
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
    page_title="Cuisines", page_icon="🍽️", layout="wide"
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

restaurant_slider = st.sidebar.slider(
    "Selecione a quantidade de restaurantes que deseja visualizar", 1, 20, 10
)

cuisines = st.sidebar.multiselect(
    "Escolha os tipos de culinária",
    df2.loc[:, "cuisines"].unique().tolist(),
    default=[
        "Home-made",
        "BBQ",
        "Japanese",
        "Brazilian",
        "Arabian",
        "American",
        "Italian",
    ],
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
select = df2['country'].isin(country_options)
df2 = df2.loc[select, :]

# Filtro quantidade de restaurantes:
select = df2['restaurant_id'] < restaurant_slider
df2 = df2.loc[select, :]

# Filtro tipos de culinária:
select = df2['cuisines'].isin(cuisines)
df2 = df2.loc[select, :]


# =================
# Layout da Página Cuisines do Streamlit 
# =================

st.markdown("# 🍽️ Visão Culinária")
st.markdown('## Melhores restaurantes dos principais tipos culinários')

cdt.write_metrics()

st.markdown(f'## Top {restaurant_slider} Restaurantes')

def top_restaurants(country_options, cuisines, restaurant_slider):

    df2 = process_data(RAW_DATA_PATH)
   
    cols = [
        "restaurant_id",
        "restaurant_name",
        "country",
        "city",
        "cuisines",
        "average_cost_for_two",
        "aggregate_rating",
        "votes"
        ]

    lines = (df2["cuisines"].isin(cuisines)) & (df2["country"].isin(country_options))

    dataframe = df2.loc[lines, cols].sort_values(["aggregate_rating", "restaurant_id"], ascending=[False, True])

    return dataframe.head(restaurant_slider)

df_restaurants = top_restaurants(country_options, cuisines, restaurant_slider)
st.dataframe(df_restaurants, width=900)

st.container()
col1, col2 = st.columns(2)
with col1:
   
   df2 = process_data(RAW_DATA_PATH)
   df_aux = (df2.loc[:, ['cuisines', 'aggregate_rating']]
             .groupby('cuisines')
             .mean()
             .sort_values('aggregate_rating', ascending=False)
             .reset_index()
             .head(restaurant_slider))
   
   fig = px.bar(
      df_aux,
      x='cuisines',
      y='aggregate_rating', text='aggregate_rating', text_auto='.2f',
      title=f'Top {restaurant_slider} melhores tipos de culinária',
      labels={
         "cuisines": "Tipo de culinária",
         "aggregate_rating": "Média da avaliação média"
         })
   st.plotly_chart(fig, use_container_width=True)

with col2:
   
   df2 = process_data(RAW_DATA_PATH)
   df_aux = (df2.loc[:, ['cuisines', 'aggregate_rating']]
             .groupby('cuisines')
             .mean()
             .sort_values('aggregate_rating', ascending=True)
             .reset_index()
             .head(restaurant_slider))
   
   fig = px.bar(
      df_aux,
      x='cuisines',
      y='aggregate_rating', text='aggregate_rating', text_auto='.2f',
      title=f'Top {restaurant_slider} piores tipos de culinária',
      labels={
         "cuisines": "Tipo de culinária",
         "aggregate_rating": "Média da avaliação média"})
   st.plotly_chart(fig, use_container_width=True)


   

    
