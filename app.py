import io
import os
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
import requests
import streamlit as st
from bs4 import BeautifulSoup

APP_NAME = "AhorraDespensa"
DATA_DIR = Path(__file__).parent / "data"
SAMPLE_CSV = DATA_DIR / "sample_precios.csv"
ONLINE_SAMPLE_CSV = DATA_DIR / "sample_online.csv"
PROFECO_DATASET_URL = "https://www.datos.gob.mx/dataset/programa_quien_es_quien_precios_2025"

# Cambia este enlace por tu PayPal.me o PayPal Donate real.
PAYPAL_DONATION_LINK = os.getenv(
    "PAYPAL_DONATION_LINK",
    "https://www.paypal.com/donate/?hosted_button_id=REEMPLAZA_ESTO",
)

FALLBACK_PROFECO_URLS = [
    "https://repodatos.atdt.gob.mx/api_update/profeco/programa_quien_es_quien_precios_2025/11-2025_01.csv",
    "https://repodatos.atdt.gob.mx/api_update/profeco/programa_quien_es_quien_precios_2025/11-2025_02.csv",
    "https://repodatos.atdt.gob.mx/api_update/profeco/programa_quien_es_quien_precios_2025/10-2025_01.csv",
    "https://repodatos.atdt.gob.mx/api_update/profeco/programa_quien_es_quien_precios_2025/10-2025_02.csv",
    "https://repodatos.atdt.gob.mx/api_update/profeco/programa_quien_es_quien_precios_2025/09-2025_01.csv",
    "https://repodatos.atdt.gob.mx/api_update/profeco/programa_quien_es_quien_precios_2025/09-2025_02.csv",
]

EMBEDDED_SAMPLE_CSV = """producto,presentacion,marca,categoria,precio,cadena_comercial,nombre_comercial,direccion,estado,municipio,fechaRegistro,latitud,longitud
Huevo,18 piezas,Bachoco,Básicos,58.90,Walmart,Walmart Mérida Norte,"Calle 60 Norte, Mérida",Yucatán,Mérida,2026-05-01,21.0285,-89.6208
Huevo,18 piezas,San Juan,Básicos,61.50,Soriana,Soriana Hiper Canek,"Av. Jacinto Canek, Mérida",Yucatán,Mérida,2026-05-01,20.9845,-89.6505
Huevo,18 piezas,Genérica,Básicos,55.00,Bodega Aurrera,Bodega Aurrera Itzaes,"Av. Itzaes, Mérida",Yucatán,Mérida,2026-05-01,20.9642,-89.6420
Leche,1 litro,Lala,Lácteos,29.90,Walmart,Walmart Mérida Norte,"Calle 60 Norte, Mérida",Yucatán,Mérida,2026-05-01,21.0285,-89.6208
Leche,1 litro,Alpura,Lácteos,31.20,Chedraui,Chedraui Selecto Norte,"Mérida Norte",Yucatán,Mérida,2026-05-01,21.0302,-89.6290
Leche,1 litro,Genérica,Lácteos,27.50,Súper Aki,Súper Aki Alemán,"Col. Alemán, Mérida",Yucatán,Mérida,2026-05-01,20.9994,-89.5941
Arroz,1 kg,Verde Valle,Básicos,35.80,Walmart,Walmart Mérida Norte,"Calle 60 Norte, Mérida",Yucatán,Mérida,2026-05-01,21.0285,-89.6208
Arroz,1 kg,Genérico,Básicos,28.90,Bodega Aurrera,Bodega Aurrera Itzaes,"Av. Itzaes, Mérida",Yucatán,Mérida,2026-05-01,20.9642,-89.6420
Arroz,1 kg,Súper Aki,Básicos,30.50,Súper Aki,Súper Aki Alemán,"Col. Alemán, Mérida",Yucatán,Mérida,2026-05-01,20.9994,-89.5941
Frijol negro,1 kg,Verde Valle,Básicos,48.00,Soriana,Soriana Hiper Canek,"Av. Jacinto Canek, Mérida",Yucatán,Mérida,2026-05-01,20.9845,-89.6505
Frijol negro,1 kg,Genérico,Básicos,42.50,Bodega Aurrera,Bodega Aurrera Itzaes,"Av. Itzaes, Mérida",Yucatán,Mérida,2026-05-01,20.9642,-89.6420
Frijol negro,1 kg,Súper Aki,Básicos,44.90,Súper Aki,Súper Aki Alemán,"Col. Alemán, Mérida",Yucatán,Mérida,2026-05-01,20.9994,-89.5941
Tortilla de maíz,1 kg,Genérica,Básicos,24.00,Súper Aki,Súper Aki Alemán,"Col. Alemán, Mérida",Yucatán,Mérida,2026-05-01,20.9994,-89.5941
Tortilla de maíz,1 kg,Genérica,Básicos,25.50,Chedraui,Chedraui Selecto Norte,"Mérida Norte",Yucatán,Mérida,2026-05-01,21.0302,-89.6290
Tortilla de maíz,1 kg,Genérica,Básicos,23.80,Bodega Aurrera,Bodega Aurrera Itzaes,"Av. Itzaes, Mérida",Yucatán,Mérida,2026-05-01,20.9642,-89.6420
Pechuga de pollo,1 kg,Genérica,Carnes,112.00,Soriana,Soriana Hiper Canek,"Av. Jacinto Canek, Mérida",Yucatán,Mérida,2026-05-01,20.9845,-89.6505
Pechuga de pollo,1 kg,Genérica,Carnes,109.90,Walmart,Walmart Mérida Norte,"Calle 60 Norte, Mérida",Yucatán,Mérida,2026-05-01,21.0285,-89.6208
Pechuga de pollo,1 kg,Genérica,Carnes,105.50,Chedraui,Chedraui Selecto Norte,"Mérida Norte",Yucatán,Mérida,2026-05-01,21.0302,-89.6290
Atún en agua,140 g,Dolores,Enlatados,22.90,Walmart,Walmart Mérida Norte,"Calle 60 Norte, Mérida",Yucatán,Mérida,2026-05-01,21.0285,-89.6208
Atún en agua,140 g,Tuny,Enlatados,20.90,Súper Aki,Súper Aki Alemán,"Col. Alemán, Mérida",Yucatán,Mérida,2026-05-01,20.9994,-89.5941
Atún en agua,140 g,Genérico,Enlatados,19.50,Bodega Aurrera,Bodega Aurrera Itzaes,"Av. Itzaes, Mérida",Yucatán,Mérida,2026-05-01,20.9642,-89.6420
Pasta espagueti,200 g,La Moderna,Básicos,11.90,Walmart,Walmart Mérida Norte,"Calle 60 Norte, Mérida",Yucatán,Mérida,2026-05-01,21.0285,-89.6208
Pasta espagueti,200 g,Genérica,Básicos,10.50,Bodega Aurrera,Bodega Aurrera Itzaes,"Av. Itzaes, Mérida",Yucatán,Mérida,2026-05-01,20.9642,-89.6420
Lenteja,500 g,Verde Valle,Básicos,29.90,Soriana,Soriana Hiper Canek,"Av. Jacinto Canek, Mérida",Yucatán,Mérida,2026-05-01,20.9845,-89.6505
Lenteja,500 g,Genérica,Básicos,25.00,Bodega Aurrera,Bodega Aurrera Itzaes,"Av. Itzaes, Mérida",Yucatán,Mérida,2026-05-01,20.9642,-89.6420
Avena,400 g,Quaker,Cereales,38.90,Walmart,Walmart Mérida Norte,"Calle 60 Norte, Mérida",Yucatán,Mérida,2026-05-01,21.0285,-89.6208
Avena,400 g,Genérica,Cereales,30.00,Bodega Aurrera,Bodega Aurrera Itzaes,"Av. Itzaes, Mérida",Yucatán,Mérida,2026-05-01,20.9642,-89.6420
Plátano,1 kg,Genérico,Frutas,24.90,Súper Aki,Súper Aki Alemán,"Col. Alemán, Mérida",Yucatán,Mérida,2026-05-01,20.9994,-89.5941
Plátano,1 kg,Genérico,Frutas,25.90,Chedraui,Chedraui Selecto Norte,"Mérida Norte",Yucatán,Mérida,2026-05-01,21.0302,-89.6290
Jitomate,1 kg,Genérico,Verduras,29.90,Súper Aki,Súper Aki Alemán,"Col. Alemán, Mérida",Yucatán,Mérida,2026-05-01,20.9994,-89.5941
Jitomate,1 kg,Genérico,Verduras,31.50,Walmart,Walmart Mérida Norte,"Calle 60 Norte, Mérida",Yucatán,Mérida,2026-05-01,21.0285,-89.6208
Cebolla blanca,1 kg,Genérica,Verduras,26.90,Bodega Aurrera,Bodega Aurrera Itzaes,"Av. Itzaes, Mérida",Yucatán,Mérida,2026-05-01,20.9642,-89.6420
Cebolla blanca,1 kg,Genérica,Verduras,28.00,Soriana,Soriana Hiper Canek,"Av. Jacinto Canek, Mérida",Yucatán,Mérida,2026-05-01,20.9845,-89.6505
Zanahoria,1 kg,Genérica,Verduras,22.90,Chedraui,Chedraui Selecto Norte,"Mérida Norte",Yucatán,Mérida,2026-05-01,21.0302,-89.6290
Zanahoria,1 kg,Genérica,Verduras,21.50,Súper Aki,Súper Aki Alemán,"Col. Alemán, Mérida",Yucatán,Mérida,2026-05-01,20.9994,-89.5941
Queso Oaxaca,400 g,Esmeralda,Lácteos,72.90,Walmart,Walmart Mérida Norte,"Calle 60 Norte, Mérida",Yucatán,Mérida,2026-05-01,21.0285,-89.6208
Queso manchego,400 g,Genérico,Lácteos,69.50,Bodega Aurrera,Bodega Aurrera Itzaes,"Av. Itzaes, Mérida",Yucatán,Mérida,2026-05-01,20.9642,-89.6420
Jamón de pavo,250 g,Fud,Embutidos,49.90,Soriana,Soriana Hiper Canek,"Av. Jacinto Canek, Mérida",Yucatán,Mérida,2026-05-01,20.9845,-89.6505
Jamón de pavo,250 g,Genérico,Embutidos,42.00,Bodega Aurrera,Bodega Aurrera Itzaes,"Av. Itzaes, Mérida",Yucatán,Mérida,2026-05-01,20.9642,-89.6420
Mayonesa,390 g,McCormick,Abarrotes,45.90,Walmart,Walmart Mérida Norte,"Calle 60 Norte, Mérida",Yucatán,Mérida,2026-05-01,21.0285,-89.6208
Tostadas,280 g,Milpa Real,Básicos,38.50,Chedraui,Chedraui Selecto Norte,"Mérida Norte",Yucatán,Mérida,2026-05-01,21.0302,-89.6290
Bolillo,1 pieza,Panadería,Básicos,4.50,Súper Aki,Súper Aki Alemán,"Col. Alemán, Mérida",Yucatán,Mérida,2026-05-01,20.9994,-89.5941
"""

RECIPES = [
    {"name": "Huevos a la mexicana con tortillas", "type": "Desayuno", "ingredients": ["huevo", "jitomate", "cebolla", "tortilla"], "note": "Barato, rápido y rendidor."},
    {"name": "Avena con plátano", "type": "Desayuno", "ingredients": ["avena", "platano", "leche"], "note": "Ideal para varios días."},
    {"name": "Quesadillas con frijol", "type": "Desayuno", "ingredients": ["tortilla", "queso", "frijol"], "note": "Fácil y llenador."},
    {"name": "Arroz con pollo y verduras", "type": "Comida", "ingredients": ["arroz", "pollo", "zanahoria", "cebolla"], "note": "Rinde bien para varias porciones."},
    {"name": "Sopa de lentejas", "type": "Comida", "ingredients": ["lenteja", "jitomate", "cebolla", "zanahoria"], "note": "Económica y nutritiva."},
    {"name": "Pasta con atún", "type": "Comida", "ingredients": ["pasta", "atun", "jitomate", "cebolla"], "note": "Resuelve comida con poco presupuesto."},
    {"name": "Tacos de frijol con huevo", "type": "Comida", "ingredients": ["frijol", "huevo", "tortilla"], "note": "Muy llenador."},
    {"name": "Ensalada de atún con tostadas", "type": "Cena", "ingredients": ["atun", "mayonesa", "tostada", "zanahoria"], "note": "Ligera y rápida."},
    {"name": "Sincronizadas", "type": "Cena", "ingredients": ["tortilla", "queso", "jamon"], "note": "Cena sencilla."},
    {"name": "Tostadas de frijol con queso", "type": "Cena", "ingredients": ["tostada", "frijol", "queso"], "note": "Rinde y cuesta poco."},
    {"name": "Molletes sencillos", "type": "Cena", "ingredients": ["bolillo", "frijol", "queso"], "note": "Buena cena rápida."},
    {"name": "Sopa de pasta con verduras", "type": "Comida", "ingredients": ["pasta", "zanahoria", "jitomate", "cebolla"], "note": "Rinde mucho."},
]

INGREDIENT_ALIASES = {
    "atun": ["atun", "atún"],
    "platano": ["platano", "plátano", "banana"],
    "jitomate": ["jitomate", "tomate"],
    "tortilla": ["tortilla"],
    "frijol": ["frijol", "frijoles"],
    "huevo": ["huevo", "huevos"],
    "leche": ["leche"],
    "avena": ["avena"],
    "queso": ["queso"],
    "pollo": ["pollo", "pechuga", "pierna", "muslo"],
    "arroz": ["arroz"],
    "lenteja": ["lenteja", "lentejas"],
    "pasta": ["pasta", "spaghetti", "espagueti", "fideo", "codito"],
    "zanahoria": ["zanahoria"],
    "cebolla": ["cebolla"],
    "mayonesa": ["mayonesa"],
    "tostada": ["tostada", "tostadas"],
    "jamon": ["jamon", "jamón"],
    "bolillo": ["bolillo", "pan blanco", "telera"],
}

st.set_page_config(page_title=APP_NAME, page_icon="🛒", layout="wide", initial_sidebar_state="expanded")


def normalize_text(value: object) -> str:
    text = "" if value is None else str(value)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9ñ\s]+", " ", text)
    return re.sub(r"\s+", " ", text)


def currency(value: float) -> str:
    try:
        return f"${value:,.2f} MXN"
    except Exception:
        return "$0.00 MXN"


def inject_css() -> None:
    st.markdown(
        """
        <style>
        :root {
            --bg: #0f172a;
            --panel: #ffffff;
            --soft: #fff7ed;
            --line: #eadfd1;
            --text: #111827;
            --muted: #6b7280;
            --orange: #f97316;
            --green: #0f766e;
            --red: #b42318;
            --yellow: #a16207;
        }
        .block-container { padding-top: 1.5rem; padding-bottom: 5rem; max-width: 1250px; }
        section[data-testid="stSidebar"] { background: #111827; color: #ffffff; }
        section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] span { color: #ffffff !important; }
        section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3 { color: #ffffff !important; }
        h1, h2, h3 { letter-spacing: -0.035em; }
        .hero {
            padding: 26px 28px;
            border: 1px solid var(--line);
            border-radius: 28px;
            background: radial-gradient(circle at top left, #ffedd5 0%, #fff7ed 34%, #ffffff 72%);
            box-shadow: 0 16px 45px rgba(17, 24, 39, .06);
            margin-bottom: 18px;
        }
        .hero-kicker { font-size: .82rem; color: var(--orange); font-weight: 800; text-transform: uppercase; letter-spacing: .09em; }
        .hero-title { font-size: 2.4rem; font-weight: 900; color: var(--text); margin: 4px 0 8px; line-height: 1.05; }
        .hero-subtitle { color: #4b5563; font-size: 1.03rem; max-width: 840px; }
        .mini-note { color: var(--muted); font-size: .88rem; }
        .card {
            background: #ffffff;
            border: 1px solid var(--line);
            border-radius: 22px;
            padding: 18px;
            box-shadow: 0 10px 30px rgba(17, 24, 39, .05);
            margin-bottom: 16px;
        }
        .step-card {
            background: #ffffff;
            border: 1px solid var(--line);
            border-radius: 22px;
            padding: 18px 18px 14px;
            margin-bottom: 14px;
        }
        .step-pill {
            display: inline-block;
            padding: 5px 10px;
            border-radius: 999px;
            background: #ffedd5;
            color: #9a3412;
            font-size: .78rem;
            font-weight: 800;
            margin-bottom: 8px;
        }
        .metric-card {
            border: 1px solid var(--line);
            border-radius: 20px;
            padding: 15px;
            background: #ffffff;
            height: 100%;
        }
        .metric-label { color: var(--muted); font-size: .78rem; font-weight: 650; }
        .metric-value { color: var(--text); font-size: 1.45rem; font-weight: 900; margin-top: 4px; }
        .status-good { color: #0f766e; font-weight: 800; }
        .status-warn { color: #a16207; font-weight: 800; }
        .status-bad { color: #b42318; font-weight: 800; }
        .product-row {
            padding: 12px 14px;
            border: 1px solid var(--line);
            border-radius: 16px;
            background: #fff;
            margin-bottom: 8px;
        }
        .product-title { font-weight: 800; color: var(--text); margin-bottom: 2px; }
        .product-meta { color: var(--muted); font-size: .86rem; }
        .donate-float {
            position: fixed;
            right: 18px;
            bottom: 18px;
            z-index: 9999;
            text-decoration: none;
            background: rgba(255,255,255,.94);
            color: #9a3412 !important;
            border: 1px solid #fed7aa;
            padding: 9px 12px;
            border-radius: 999px;
            font-size: 12px;
            font-weight: 800;
            box-shadow: 0 10px 24px rgba(17, 24, 39, .12);
        }
        .donate-float:hover { background: #fff7ed; }
        .small-source {
            border-left: 4px solid #f97316;
            padding: 10px 12px;
            background: #fff7ed;
            border-radius: 12px;
            color: #4b5563;
            font-size: .9rem;
        }
        div[data-testid="stDataFrame"] { border-radius: 18px; overflow: hidden; }
        .stButton>button {
            border-radius: 999px;
            border: 1px solid #fed7aa;
            font-weight: 800;
        }
        .stDownloadButton>button {
            border-radius: 999px;
            border: 1px solid #fed7aa;
            font-weight: 800;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def donation_button() -> None:
    st.markdown(
        f'<a class="donate-float" href="{PAYPAL_DONATION_LINK}" target="_blank">Donar</a>',
        unsafe_allow_html=True,
    )


def read_csv_any(source) -> pd.DataFrame:
    last_error = None
    for encoding in ["utf-8", "utf-8-sig", "latin-1"]:
        for sep in [",", ";", "|"]:
            try:
                if isinstance(source, (str, Path)) and str(source).startswith("http"):
                    response = requests.get(str(source), timeout=25)
                    response.raise_for_status()
                    content = io.BytesIO(response.content)
                    df = pd.read_csv(content, sep=sep, encoding=encoding, low_memory=False)
                else:
                    df = pd.read_csv(source, sep=sep, encoding=encoding, low_memory=False)
                if df.shape[1] >= 3:
                    return df
            except Exception as exc:
                last_error = exc
    raise ValueError(f"No se pudo leer el CSV. Detalle: {last_error}")


def find_column(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    normalized = {normalize_text(col): col for col in df.columns}
    for candidate in candidates:
        key = normalize_text(candidate)
        if key in normalized:
            return normalized[key]
    for key, col in normalized.items():
        if any(normalize_text(candidate) in key for candidate in candidates):
            return col
    return None


def standardize_prices(df: pd.DataFrame, source_name: str) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    col_map = {
        "producto": find_column(df, ["producto", "nombre_producto", "producto_servicio", "articulo", "descripción", "descripcion"]),
        "presentacion": find_column(df, ["presentacion", "presentación", "unidad", "empaque"]),
        "marca": find_column(df, ["marca"]),
        "categoria": find_column(df, ["categoria", "categoría", "departamento", "grupo"]),
        "precio": find_column(df, ["precio", "precio_promedio", "precio_minimo", "precio_menudeo"]),
        "tienda": find_column(df, ["cadena_comercial", "cadena", "tienda", "establecimiento"]),
        "sucursal": find_column(df, ["nombre_comercial", "sucursal", "tienda", "establecimiento"]),
        "direccion": find_column(df, ["direccion", "dirección", "domicilio"]),
        "estado": find_column(df, ["estado", "entidad", "entidad_federativa"]),
        "municipio": find_column(df, ["municipio", "alcaldia", "alcaldía", "ciudad"]),
        "fecha": find_column(df, ["fechaRegistro", "fecha_registro", "fecha", "fecha_consulta"]),
        "latitud": find_column(df, ["latitud", "latitude"]),
        "longitud": find_column(df, ["longitud", "longitude"]),
        "url": find_column(df, ["url", "link", "enlace"]),
    }

    required = ["producto", "precio"]
    missing = [name for name in required if col_map[name] is None]
    if missing:
        raise ValueError("El CSV necesita al menos columnas de producto y precio.")

    out = pd.DataFrame()
    for target, source in col_map.items():
        if source:
            out[target] = df[source]
        else:
            out[target] = ""

    out["precio"] = (
        out["precio"]
        .astype(str)
        .str.replace("$", "", regex=False)
        .str.replace(",", "", regex=False)
        .str.extract(r"(-?\d+(?:\.\d+)?)", expand=False)
    )
    out["precio"] = pd.to_numeric(out["precio"], errors="coerce")
    out = out.dropna(subset=["producto", "precio"])
    out = out[out["precio"] > 0]

    for col in ["producto", "presentacion", "marca", "categoria", "tienda", "sucursal", "direccion", "estado", "municipio", "url"]:
        out[col] = out[col].fillna("").astype(str).str.strip()

    out["fecha"] = pd.to_datetime(out["fecha"], errors="coerce", dayfirst=False)
    out["fuente"] = source_name
    out["producto_norm"] = out["producto"].map(normalize_text)
    out["tienda_norm"] = out["tienda"].map(normalize_text)
    out["ubicacion_norm"] = (out["estado"] + " " + out["municipio"] + " " + out["sucursal"]).map(normalize_text)
    out = out.drop_duplicates(subset=["producto_norm", "presentacion", "marca", "precio", "tienda", "sucursal", "estado", "municipio", "fuente"])
    return out


@st.cache_data(ttl=3600, show_spinner=False)
def discover_profeco_urls() -> List[str]:
    try:
        html = requests.get(PROFECO_DATASET_URL, timeout=20).text
        soup = BeautifulSoup(html, "html.parser")
        urls = []
        for link in soup.find_all("a", href=True):
            href = link["href"]
            if ".csv" in href.lower():
                if href.startswith("http"):
                    urls.append(href)
                else:
                    urls.append(requests.compat.urljoin(PROFECO_DATASET_URL, href))
        # Primero intenta los recursos encontrados, después respaldos conocidos.
        seen = set()
        final = []
        for url in urls + FALLBACK_PROFECO_URLS:
            if url not in seen:
                seen.add(url)
                final.append(url)
        return final[:10]
    except Exception:
        return FALLBACK_PROFECO_URLS


@st.cache_data(ttl=3600, show_spinner=False)
def load_profeco_auto() -> Tuple[pd.DataFrame, Dict[str, str]]:
    errors = []
    for url in discover_profeco_urls():
        try:
            raw = read_csv_any(url)
            df = standardize_prices(raw, "PROFECO")
            if not df.empty:
                return df, {"source_label": "PROFECO automático", "source_url": url, "fallback": "no"}
        except Exception as exc:
            errors.append(str(exc)[:120])
    # Respaldo para que la app funcione siempre.
    raw = pd.read_csv(io.StringIO(EMBEDDED_SAMPLE_CSV))
    df = standardize_prices(raw, "Ejemplo")
    return df, {"source_label": "Datos de ejemplo", "source_url": "Respaldo interno", "fallback": "sí"}


@st.cache_data(ttl=3600, show_spinner=False)
def load_sample() -> Tuple[pd.DataFrame, Dict[str, str]]:
    try:
        raw = read_csv_any(SAMPLE_CSV)
    except Exception:
        raw = pd.read_csv(io.StringIO(EMBEDDED_SAMPLE_CSV))
    return standardize_prices(raw, "Ejemplo"), {"source_label": "Datos de ejemplo", "source_url": str(SAMPLE_CSV), "fallback": "no"}


@st.cache_data(ttl=3600, show_spinner=False)
def load_url_csv(url: str, source_name: str) -> pd.DataFrame:
    return standardize_prices(read_csv_any(url), source_name)


def load_uploaded_csv(uploaded_file, source_name: str) -> pd.DataFrame:
    return standardize_prices(read_csv_any(uploaded_file), source_name)


def source_freshness(df: pd.DataFrame) -> Dict[str, object]:
    if df.empty or "fecha" not in df.columns:
        return {"label": "Sin fecha", "class": "status-warn", "days": None, "min": None, "max": None}
    dates = pd.to_datetime(df["fecha"], errors="coerce").dropna()
    if dates.empty:
        return {"label": "Sin fecha detectada", "class": "status-warn", "days": None, "min": None, "max": None}
    max_date = dates.max()
    min_date = dates.min()
    days = (pd.Timestamp.today().normalize() - max_date.normalize()).days
    if days <= 45:
        label, cls = "Actualizado", "status-good"
    elif days <= 120:
        label, cls = "Revisar vigencia", "status-warn"
    else:
        label, cls = "Datos antiguos", "status-bad"
    return {"label": label, "class": cls, "days": days, "min": min_date, "max": max_date}


def apply_location_filters(df: pd.DataFrame, estado: str, municipio: str, stores: List[str]) -> pd.DataFrame:
    filtered = df.copy()
    if estado != "Todos":
        filtered = filtered[filtered["estado"].fillna("") == estado]
    if municipio != "Todos":
        filtered = filtered[filtered["municipio"].fillna("") == municipio]
    if stores:
        filtered = filtered[filtered["tienda"].isin(stores)]
    return filtered


def get_product_options(df: pd.DataFrame, query: str, limit: int = 250) -> List[str]:
    if df.empty:
        return []
    q = normalize_text(query)
    products = df[["producto", "presentacion", "categoria", "producto_norm"]].drop_duplicates()
    if q:
        products = products[products["producto_norm"].str.contains(q, na=False)]
    products = products.sort_values(["producto", "presentacion"]).head(limit)
    return [f"{row.producto} · {row.presentacion}" if row.presentacion else row.producto for row in products.itertuples()]


def product_name_from_option(option: str) -> str:
    return option.split(" · ")[0].strip()


def cheapest_for_product(df: pd.DataFrame, product: str) -> Optional[pd.Series]:
    product_norm = normalize_text(product)
    subset = df[df["producto_norm"] == product_norm]
    if subset.empty:
        subset = df[df["producto_norm"].str.contains(product_norm, na=False)]
    if subset.empty:
        return None
    return subset.sort_values("precio", ascending=True).iloc[0]


def compute_cart(filtered: pd.DataFrame, cart: List[Dict[str, object]]) -> pd.DataFrame:
    rows = []
    for item in cart:
        product = str(item["producto"])
        qty = float(item["cantidad"])
        best = cheapest_for_product(filtered, product)
        if best is None:
            rows.append({
                "Producto": product,
                "Cantidad": qty,
                "Mejor precio": None,
                "Total": None,
                "Tienda": "No encontrado",
                "Sucursal": "",
                "Fuente": "",
                "Fecha": "",
            })
            continue
        rows.append({
            "Producto": best["producto"],
            "Presentación": best.get("presentacion", ""),
            "Cantidad": qty,
            "Mejor precio": float(best["precio"]),
            "Total": float(best["precio"]) * qty,
            "Tienda": best.get("tienda", ""),
            "Sucursal": best.get("sucursal", ""),
            "Fuente": best.get("fuente", ""),
            "Fecha": "" if pd.isna(best.get("fecha")) else pd.to_datetime(best.get("fecha")).strftime("%Y-%m-%d"),
        })
    return pd.DataFrame(rows)


def compare_stores(filtered: pd.DataFrame, cart: List[Dict[str, object]]) -> pd.DataFrame:
    if filtered.empty or not cart:
        return pd.DataFrame()
    store_rows = []
    keys = filtered[["fuente", "tienda", "sucursal"]].drop_duplicates()
    for store in keys.itertuples(index=False):
        total = 0.0
        missing = []
        for item in cart:
            product_norm = normalize_text(item["producto"])
            qty = float(item["cantidad"])
            subset = filtered[
                (filtered["fuente"] == store.fuente)
                & (filtered["tienda"] == store.tienda)
                & (filtered["sucursal"] == store.sucursal)
                & (filtered["producto_norm"] == product_norm)
            ]
            if subset.empty:
                subset = filtered[
                    (filtered["fuente"] == store.fuente)
                    & (filtered["tienda"] == store.tienda)
                    & (filtered["sucursal"] == store.sucursal)
                    & (filtered["producto_norm"].str.contains(product_norm, na=False))
                ]
            if subset.empty:
                missing.append(str(item["producto"]))
            else:
                total += float(subset.sort_values("precio").iloc[0]["precio"]) * qty
        store_rows.append({
            "Fuente": store.fuente,
            "Tienda": store.tienda,
            "Sucursal": store.sucursal,
            "Total estimado": total if len(missing) < len(cart) else None,
            "Productos encontrados": len(cart) - len(missing),
            "Faltantes": ", ".join(missing[:4]) + ("..." if len(missing) > 4 else ""),
        })
    result = pd.DataFrame(store_rows)
    if not result.empty:
        result = result.sort_values(["Productos encontrados", "Total estimado"], ascending=[False, True])
    return result


def ingredient_available(ingredient: str, available_norm: List[str]) -> bool:
    aliases = INGREDIENT_ALIASES.get(ingredient, [ingredient])
    aliases = [normalize_text(x) for x in aliases]
    return any(any(alias in product for alias in aliases) for product in available_norm)


def recipe_matches(cart: List[Dict[str, object]]) -> List[Dict[str, object]]:
    available = [normalize_text(item["producto"]) for item in cart]
    matches = []
    for recipe in RECIPES:
        total = len(recipe["ingredients"])
        have = sum(ingredient_available(ing, available) for ing in recipe["ingredients"])
        missing = [ing for ing in recipe["ingredients"] if not ingredient_available(ing, available)]
        matches.append({**recipe, "have": have, "total": total, "missing": missing, "score": have / total if total else 0})
    return sorted(matches, key=lambda x: (x["score"], x["have"]), reverse=True)


def source_badge_html(fresh: Dict[str, object]) -> str:
    label = fresh["label"]
    cls = fresh["class"]
    days = fresh["days"]
    if days is None:
        detail = "No se pudo detectar fecha de registro."
    else:
        detail = f"Último registro detectado hace {days} días."
    return f'<span class="{cls}">{label}</span><br><span class="mini-note">{detail}</span>'


def render_metric(label: str, value: str) -> None:
    st.markdown(f'<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value">{value}</div></div>', unsafe_allow_html=True)


def safe_dataframe(df: pd.DataFrame, **kwargs) -> None:
    if df.empty:
        st.info("No hay datos para mostrar todavía.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True, **kwargs)


# -----------------------------
# Estado de sesión
# -----------------------------
if "cart" not in st.session_state:
    st.session_state.cart = []

inject_css()
donation_button()

with st.sidebar:
    st.markdown("## Configuración")
    source_mode = st.radio(
        "Fuente principal de precios",
        ["PROFECO automático", "Datos de ejemplo", "Pegar URL CSV", "Subir CSV"],
        help="PROFECO es la referencia oficial. Los datos de ejemplo sirven para probar la app.",
    )

    custom_url = ""
    uploaded_file = None
    if source_mode == "Pegar URL CSV":
        custom_url = st.text_input("URL del CSV")
    if source_mode == "Subir CSV":
        uploaded_file = st.file_uploader("Sube tu archivo CSV", type=["csv"])

    st.divider()
    st.markdown("### Comparativo online")
    include_online_sample = st.checkbox("Agregar precios online de ejemplo", value=True)
    online_url = st.text_input("CSV online opcional", placeholder="https://...")
    online_upload = st.file_uploader("Subir CSV de precios online", type=["csv"], key="online_upload")

    st.divider()
    st.caption("Los precios son estimados. Pueden variar por fecha, sucursal, promoción, disponibilidad y ubicación.")

# Carga de datos principal
load_errors = []
meta = {"source_label": source_mode, "source_url": "", "fallback": "no"}
try:
    if source_mode == "PROFECO automático":
        base_df, meta = load_profeco_auto()
    elif source_mode == "Datos de ejemplo":
        base_df, meta = load_sample()
    elif source_mode == "Pegar URL CSV" and custom_url:
        base_df = load_url_csv(custom_url, "CSV externo")
        meta = {"source_label": "CSV externo", "source_url": custom_url, "fallback": "no"}
    elif source_mode == "Subir CSV" and uploaded_file is not None:
        base_df = load_uploaded_csv(uploaded_file, "CSV cargado")
        meta = {"source_label": "CSV cargado", "source_url": uploaded_file.name, "fallback": "no"}
    else:
        base_df, meta = load_sample()
        meta["fallback"] = "sí"
except Exception as exc:
    load_errors.append(str(exc))
    base_df, meta = load_sample()
    meta = {"source_label": "Datos de ejemplo", "source_url": str(SAMPLE_CSV), "fallback": "sí"}

frames = [base_df]
if include_online_sample:
    try:
        frames.append(standardize_prices(read_csv_any(ONLINE_SAMPLE_CSV), "Online ejemplo"))
    except Exception as exc:
        load_errors.append(f"Online ejemplo: {exc}")
if online_url:
    try:
        frames.append(load_url_csv(online_url, "Online CSV"))
    except Exception as exc:
        load_errors.append(f"Online CSV: {exc}")
if online_upload is not None:
    try:
        frames.append(load_uploaded_csv(online_upload, "Online cargado"))
    except Exception as exc:
        load_errors.append(f"Online cargado: {exc}")

prices_df = pd.concat([f for f in frames if not f.empty], ignore_index=True) if frames else pd.DataFrame()
prices_df = prices_df.drop_duplicates()
fresh = source_freshness(base_df)

st.markdown(
    """
    <div class="hero">
      <div class="hero-kicker">Despensa inteligente</div>
      <div class="hero-title">AhorraDespensa</div>
      <div class="hero-subtitle">
        Arma tu lista, revisa cuánto gastarías cerca de ti y recibe ideas de platillos sencillos según tu presupuesto.
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if load_errors:
    with st.expander("Avisos de carga", expanded=False):
        for err in load_errors:
            st.warning(err)

if prices_df.empty:
    st.error("No hay precios disponibles. Revisa el CSV o cambia a Datos de ejemplo.")
    st.stop()

# Controles rápidos de ubicación y presupuesto
states = ["Todos"] + sorted([x for x in prices_df["estado"].dropna().unique() if str(x).strip()])
cols = st.columns([1, 1, 1, 1])
with cols[0]:
    estado = st.selectbox("Estado", states, index=states.index("Yucatán") if "Yucatán" in states else 0)
municipalities_df = prices_df if estado == "Todos" else prices_df[prices_df["estado"] == estado]
municipalities = ["Todos"] + sorted([x for x in municipalities_df["municipio"].dropna().unique() if str(x).strip()])
with cols[1]:
    municipio = st.selectbox("Municipio", municipalities, index=municipalities.index("Mérida") if "Mérida" in municipalities else 0)
with cols[2]:
    budget = st.number_input("Presupuesto", min_value=0.0, value=800.0, step=50.0, format="%.2f")
with cols[3]:
    days = st.number_input("¿Para cuántos días?", min_value=1, max_value=31, value=7, step=1)

cols2 = st.columns([1, 1, 2])
with cols2[0]:
    people = st.number_input("Personas", min_value=1, max_value=12, value=2, step=1)
filtered_for_stores = prices_df.copy()
if estado != "Todos":
    filtered_for_stores = filtered_for_stores[filtered_for_stores["estado"] == estado]
if municipio != "Todos":
    filtered_for_stores = filtered_for_stores[filtered_for_stores["municipio"] == municipio]
store_options = sorted([x for x in filtered_for_stores["tienda"].dropna().unique() if str(x).strip()])
with cols2[1]:
    max_stores = st.checkbox("Ver todas las tiendas", value=True)
with cols2[2]:
    selected_stores = [] if max_stores else st.multiselect("Tiendas", store_options, default=store_options[:4])

filtered = apply_location_filters(prices_df, estado, municipio, selected_stores)
cart_df = compute_cart(filtered, st.session_state.cart)
cart_total = float(cart_df["Total"].dropna().sum()) if not cart_df.empty and "Total" in cart_df else 0.0
remaining = budget - cart_total
daily_budget = budget / max(days, 1)
per_person_day = budget / max(days * people, 1)

m1, m2, m3, m4 = st.columns(4)
with m1:
    render_metric("Lista estimada", currency(cart_total))
with m2:
    render_metric("Presupuesto restante", currency(remaining))
with m3:
    render_metric("Presupuesto por día", currency(daily_budget))
with m4:
    render_metric("Por persona al día", currency(per_person_day))

st.markdown(
    f"""
    <div class="small-source">
      Fuente principal: <strong>{meta.get('source_label', '')}</strong> · {source_badge_html(fresh)}
    </div>
    """,
    unsafe_allow_html=True,
)

main_tab, compare_tab, meals_tab, source_tab = st.tabs(["Armar lista", "Comparar tiendas", "Platillos", "Fuente y confianza"])

with main_tab:
    left, right = st.columns([0.95, 1.25], gap="large")
    with left:
        st.markdown('<div class="step-card"><span class="step-pill">Paso 1</span><h3>Agrega productos</h3>', unsafe_allow_html=True)
        search = st.text_input("Buscar producto", placeholder="Ej. huevo, arroz, leche, pollo...")
        options = get_product_options(filtered, search)
        if not options:
            st.info("No encontré productos con ese filtro. Prueba con otra palabra o cambia ubicación.")
        else:
            product_option = st.selectbox("Producto", options)
            qty = st.number_input("Cantidad", min_value=0.1, value=1.0, step=0.5)
            c1, c2 = st.columns([1, 1])
            with c1:
                if st.button("Agregar a mi lista", use_container_width=True):
                    st.session_state.cart.append({"producto": product_name_from_option(product_option), "cantidad": qty})
                    st.rerun()
            with c2:
                if st.button("Limpiar lista", use_container_width=True):
                    st.session_state.cart = []
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="step-card"><span class="step-pill">Sugerencia rápida</span><h3>Productos económicos en tu zona</h3>', unsafe_allow_html=True)
        cheap = filtered.sort_values("precio").head(8)[["producto", "presentacion", "precio", "tienda", "fuente"]].copy()
        if not cheap.empty:
            cheap["precio"] = cheap["precio"].map(currency)
        safe_dataframe(cheap)
        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        st.markdown('<div class="step-card"><span class="step-pill">Paso 2</span><h3>Tu lista estimada</h3>', unsafe_allow_html=True)
        if cart_df.empty:
            st.info("Agrega productos para ver el costo estimado.")
        else:
            display_cart = cart_df.copy()
            display_cart["Mejor precio"] = display_cart["Mejor precio"].apply(lambda x: "" if pd.isna(x) else currency(x))
            display_cart["Total"] = display_cart["Total"].apply(lambda x: "" if pd.isna(x) else currency(x))
            safe_dataframe(display_cart[["Producto", "Presentación", "Cantidad", "Mejor precio", "Total", "Tienda", "Fuente", "Fecha"]])
            st.download_button(
                "Descargar lista CSV",
                data=cart_df.to_csv(index=False).encode("utf-8-sig"),
                file_name="mi_lista_ahorradespensa.csv",
                mime="text/csv",
                use_container_width=True,
            )
        if remaining < 0:
            st.error(f"Tu lista supera el presupuesto por {currency(abs(remaining))}.")
        elif st.session_state.cart:
            st.success(f"Vas dentro del presupuesto. Te quedarían {currency(remaining)}.")
        st.markdown('</div>', unsafe_allow_html=True)

        if st.session_state.cart:
            st.markdown('<div class="step-card"><span class="step-pill">Editar</span><h3>Quitar productos</h3>', unsafe_allow_html=True)
            for i, item in enumerate(st.session_state.cart):
                c1, c2, c3 = st.columns([2, 1, .8])
                with c1:
                    st.write(f"**{item['producto']}**")
                with c2:
                    st.write(f"Cantidad: {item['cantidad']}")
                with c3:
                    if st.button("Quitar", key=f"remove_{i}"):
                        st.session_state.cart.pop(i)
                        st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

with compare_tab:
    st.markdown('<div class="card"><h3>Comparativo por tienda</h3><p class="mini-note">La tabla compara el total de tu lista usando los precios disponibles por fuente y sucursal. Si faltan productos, lo muestra para que no tomes una decisión incompleta.</p>', unsafe_allow_html=True)
    store_compare = compare_stores(filtered, st.session_state.cart)
    if store_compare.empty:
        st.info("Agrega productos para comparar tiendas.")
    else:
        display_compare = store_compare.copy()
        display_compare["Total estimado"] = display_compare["Total estimado"].apply(lambda x: "" if pd.isna(x) else currency(x))
        safe_dataframe(display_compare)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="card"><h3>Precios encontrados por producto</h3>', unsafe_allow_html=True)
    if not st.session_state.cart:
        st.info("Agrega productos para ver el detalle.")
    else:
        detail_rows = []
        for item in st.session_state.cart:
            pnorm = normalize_text(item["producto"])
            subset = filtered[filtered["producto_norm"] == pnorm].sort_values("precio").head(12)
            for row in subset.itertuples():
                detail_rows.append({
                    "Producto": row.producto,
                    "Presentación": row.presentacion,
                    "Precio": currency(row.precio),
                    "Tienda": row.tienda,
                    "Sucursal": row.sucursal,
                    "Fuente": row.fuente,
                    "Fecha": "" if pd.isna(row.fecha) else pd.to_datetime(row.fecha).strftime("%Y-%m-%d"),
                })
        safe_dataframe(pd.DataFrame(detail_rows))
    st.markdown('</div>', unsafe_allow_html=True)

with meals_tab:
    st.markdown('<div class="card"><h3>Platillos que puedes armar</h3><p class="mini-note">La app no calcula nutrición médica. Solo te da ideas sencillas con base en lo que agregaste.</p>', unsafe_allow_html=True)
    if not st.session_state.cart:
        st.info("Agrega productos para recibir ideas de platillos.")
    else:
        matches = recipe_matches(st.session_state.cart)
        for recipe in matches[:8]:
            score_pct = int(recipe["score"] * 100)
            missing = ", ".join(recipe["missing"]) if recipe["missing"] else "Nada"
            st.markdown(
                f"""
                <div class="product-row">
                    <div class="product-title">{recipe['name']} · {recipe['type']}</div>
                    <div class="product-meta">Coincidencia: {score_pct}% · Te faltaría: {missing}</div>
                    <div class="product-meta">{recipe['note']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="card"><h3>Plan sencillo por días</h3>', unsafe_allow_html=True)
    if st.session_state.cart:
        matches = [r for r in recipe_matches(st.session_state.cart) if r["score"] >= 0.5]
        if not matches:
            st.info("Agrega más básicos para generar un plan más útil.")
        else:
            plan = []
            meal_types = ["Desayuno", "Comida", "Cena"]
            for day in range(1, int(days) + 1):
                for meal_type in meal_types:
                    candidates = [r for r in matches if r["type"] == meal_type] or matches
                    selected = candidates[(day - 1) % len(candidates)]
                    plan.append({"Día": day, "Momento": meal_type, "Idea": selected["name"]})
            safe_dataframe(pd.DataFrame(plan))
    else:
        st.info("Tu plan aparecerá cuando agregues productos.")
    st.markdown('</div>', unsafe_allow_html=True)

with source_tab:
    st.markdown('<div class="card"><h3>Fuente y confianza</h3>', unsafe_allow_html=True)
    min_date = fresh.get("min")
    max_date = fresh.get("max")
    source_info = pd.DataFrame([
        {"Dato": "Fuente principal", "Valor": meta.get("source_label", "")},
        {"Dato": "Archivo o URL", "Valor": meta.get("source_url", "")},
        {"Dato": "Registros cargados", "Valor": f"{len(base_df):,}"},
        {"Dato": "Primer registro detectado", "Valor": "" if min_date is None else pd.to_datetime(min_date).strftime("%Y-%m-%d")},
        {"Dato": "Último registro detectado", "Valor": "" if max_date is None else pd.to_datetime(max_date).strftime("%Y-%m-%d")},
        {"Dato": "Estado de vigencia", "Valor": fresh.get("label", "")},
        {"Dato": "Usó respaldo", "Valor": meta.get("fallback", "no")},
    ])
    safe_dataframe(source_info)
    st.markdown(
        """
        <p class="mini-note">
        PROFECO sirve como referencia oficial, pero no siempre representa el precio exacto del día. Los precios en línea pueden variar por código postal, disponibilidad, promociones, método de entrega y sucursal.
        </p>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="card"><h3>Fuentes cargadas</h3>', unsafe_allow_html=True)
    source_summary = prices_df.groupby("fuente", dropna=False).agg(
        registros=("producto", "count"),
        productos=("producto_norm", "nunique"),
        tiendas=("tienda", "nunique"),
        ultimo_registro=("fecha", "max"),
    ).reset_index()
    source_summary["ultimo_registro"] = pd.to_datetime(source_summary["ultimo_registro"], errors="coerce").dt.strftime("%Y-%m-%d").fillna("")
    safe_dataframe(source_summary)
    st.markdown('</div>', unsafe_allow_html=True)
