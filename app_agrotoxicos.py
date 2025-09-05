from shiny.express import ui, render
import pandas as pd
import requests
from io import StringIO
import numpy as np
from ipyleaflet import Map, Marker, MarkerCluster, CircleMarker, basemaps
from shinywidgets import render_widget
from ipyleaflet import Map, CircleMarker
import matplotlib.cm as cm
import matplotlib.colors as colors
import numpy as np
from ipywidgets import HTML

# --- Importação dos dados ---
url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRR1E1xhXucgiQW8_cOOZ0BzBlMpfz6U9sUY9p1t8pyn3gu0NvWBYsMtCHGhJvXt2QYvCLM1rR7ZpAG/pub?output=csv"
res = requests.get(url)
# Set the encoding after getting the response
res.encoding = 'utf-8'
dados = pd.read_csv(StringIO(res.text))

# --- Limpeza das colunas de latitude/longitude ---
dados["Latitude"] = pd.to_numeric(dados["Latitude"].astype(str).str.replace(",", "."), errors="coerce")
dados["Longitude"] = pd.to_numeric(dados["Longitude"].astype(str).str.replace(",", "."), errors="coerce")
dados = dados.replace([np.inf, -np.inf], np.nan)
dados = dados.dropna(subset=["Latitude", "Longitude"]).copy()

# --- UI Express ---
ui.page_opts(title="Detecção de Agrotóxicos em Água para Consumo Humano", fillable=True)

with ui.layout_columns():

    with ui.card():
        ui.h2("Mapa")
        @render_widget
        def mapa():
            center_lat = dados["Latitude"].mean()
            center_lon = dados["Longitude"].mean()
            m = Map(center=(center_lat, center_lon, ), zoom=7, scroll_wheel_zoom=True, basemap=basemaps.CartoDB.DarkMatter)
        
            # Normalizar Detecção para escala de cores
            detec_min = dados["Detecção"].min()
            detec_max = dados["Detecção"].max()
            norm = colors.Normalize(vmin=detec_min, vmax=detec_max)
            colormap = cm.get_cmap("Reds")  # escala de cores
        
            # Normalizar raio (3 a 15 pixels)
            def escala_raio(valor):
                if np.isnan(valor):
                    return 5
                return 3 + (valor - detec_min) / (detec_max - detec_min) * 12
        
            for idx, row in dados.iterrows():
                valor = row["Detecção"]
                raio = escala_raio(valor)
        
                # Cor da escala Reds
                rgba = colormap(norm(valor))  # retorna RGBA 0-1
                cor_hex = colors.to_hex(rgba)  # converter para hexadecimal
        
                circle = CircleMarker(
                    location=(row["Latitude"], row["Longitude"]),
                    radius=int(raio),
                    color=cor_hex,
                    fill_color=cor_hex,
                    fill_opacity=0.7,
                    popup=HTML(f"""
                        <b>{row['Municipio']}</b><br>
                        Detecção: {valor}<br>
                        Parâmetros: {row['Parametros detectados']}
                        """)
                )
                m.add_layer(circle)
        
            return m
