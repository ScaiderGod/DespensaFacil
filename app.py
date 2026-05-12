import io
import os
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin

import pandas as pd
import requests
import streamlit as st
from bs4 import BeautifulSoup

APP_NAME = "AhorraDespensa"
DATA_DIR = Path(__file__).parent / "data"
SAMPLE_CSV = DATA_DIR / "sample_precios.csv"
ONLINE_SAMPLE_CSV = DATA_DIR / "sample_online.csv"
PROFECO_DATASET_URL = "https://www.datos.gob.mx/dataset/programa_quien_es_quien_precios_2025"
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
    {"name": "Huevos a la mexicana", "type": "Desayuno", "ingredients": ["huevo", "jitomate", "cebolla", "tortilla"], "note": "Rápido, barato y rendidor."},
    {"name": "Avena con plátano", "type": "Desayuno", "ingredients": ["avena", "platano", "leche"], "note": "Buena para varios días."},
    {"name": "Quesadillas con frijol", "type": "Desayuno", "ingredients": ["tortilla", "queso", "frijol"], "note": "Sencillo y llenador."},
    {"name": "Arroz con pollo y verduras", "type": "Comida", "ingredients": ["arroz", "pollo", "zanahoria", "cebolla"], "note": "Rinde muy bien por porción."},
    {"name": "Sopa de lentejas", "type": "Comida", "ingredients": ["lenteja", "jitomate", "cebolla", "zanahoria"], "note": "Económica y nutritiva."},
    {"name": "Pasta con atún", "type": "Comida", "ingredients": ["pasta", "atun", "jitomate", "cebolla"], "note": "Resuelve comida con poco presupuesto."},
    {"name": "Tacos de frijol con huevo", "type": "Comida", "ingredients": ["frijol", "huevo", "tortilla"], "note": "Muy llenador."},
    {"name": "Ensalada de atún con tostadas", "type": "Cena", "ingredients": ["atun", "mayonesa", "tostada", "zanahoria"], "note": "Ligera y rápida."},
    {"name": "Sincronizadas", "type": "Cena", "ingredients": ["tortilla", "queso", "jamon"], "note": "Cena simple."},
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

st.set_page_config(page_title=APP_NAME, page_icon="A", layout="wide", initial_sidebar_state="collapsed")


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
            --bg: #f7f3ed;
            --ink: #172033;
            --muted: #667085;
            --line: #eadfd3;
            --card: #ffffff;
            --cream: #fff7ed;
            --orange: #ef6c2f;
            --orange-dark: #bc4b1a;
            --green: #138a72;
            --red: #b42318;
            --amber: #b7791f;
            --shadow: 0 20px 60px rgba(22, 31, 48, .08);
        }
        html, body, [data-testid="stAppViewContainer"] { background: var(--bg); color: var(--ink); }
        [data-testid="stHeader"] { background: transparent; }
        .block-container { max-width: 1180px; padding-top: 1.1rem; padding-bottom: 5rem; }
        h1, h2, h3, h4, p, label, span, div { font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
        h1, h2, h3 { letter-spacing: -0.04em; color: var(--ink); }
        .topbar {
            display: flex; align-items: center; justify-content: space-between;
            padding: 10px 6px 18px;
        }
        .brand { display: flex; align-items: center; gap: 12px; font-weight: 900; color: var(--ink); font-size: 1.08rem; }
        .brand-mark { width: 36px; height: 36px; border-radius: 12px; display: grid; place-items: center; background: #172033; color: white; font-weight: 900; }
        .nav-note { color: var(--muted); font-size: .88rem; }
        .hero {
            border-radius: 34px; padding: 30px; border: 1px solid var(--line);
            background:
                radial-gradient(circle at 10% 10%, rgba(239,108,47,.18), transparent 34%),
                linear-gradient(135deg, #ffffff 0%, #fffaf3 58%, #ffedd5 100%);
            box-shadow: var(--shadow); margin-bottom: 18px;
        }
        .kicker { color: var(--orange-dark); font-size: .78rem; text-transform: uppercase; letter-spacing: .12em; font-weight: 900; }
        .hero-title { font-size: clamp(2.1rem, 5vw, 4rem); line-height: .95; margin: 8px 0 12px; font-weight: 950; max-width: 850px; }
        .hero-copy { color: #475467; font-size: 1.04rem; max-width: 760px; line-height: 1.55; }
        .hero-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-top: 22px; }
        .hero-step { background: rgba(255,255,255,.7); border: 1px solid #f5d9c8; border-radius: 20px; padding: 14px; }
        .hero-step b { display: block; color: var(--ink); margin-bottom: 4px; }
        .hero-step span { color: var(--muted); font-size: .88rem; }
        .panel { background: var(--card); border: 1px solid var(--line); border-radius: 28px; padding: 20px; box-shadow: var(--shadow); margin-bottom: 18px; }
        .soft-panel { background: #fffaf5; border: 1px solid #f5d9c8; border-radius: 26px; padding: 18px; margin-bottom: 16px; }
        .section-title { display: flex; align-items: end; justify-content: space-between; gap: 12px; margin-bottom: 14px; }
        .section-title h2, .section-title h3 { margin: 0; }
        .subtle { color: var(--muted); font-size: .9rem; line-height: 1.45; }
        .pill { display: inline-flex; align-items: center; gap: 6px; border-radius: 999px; padding: 7px 11px; background: #fff1e7; color: #9a3412; font-size: .78rem; font-weight: 900; }
        .metric-card { background: white; border: 1px solid var(--line); border-radius: 24px; padding: 17px; height: 100%; box-shadow: 0 12px 34px rgba(22,31,48,.05); }
        .metric-label { color: var(--muted); font-size: .82rem; font-weight: 800; }
        .metric-value { color: var(--ink); font-size: clamp(1.25rem, 2.6vw, 1.65rem); font-weight: 950; margin-top: 6px; }
        .budget-bar-wrap { height: 13px; background: #f1ebe4; border-radius: 999px; overflow: hidden; margin: 10px 0 4px; }
        .budget-bar { height: 100%; border-radius: 999px; background: linear-gradient(90deg, #138a72, #ef6c2f); }
        .budget-bar-over { height: 100%; border-radius: 999px; background: linear-gradient(90deg, #f04438, #b42318); }
        .source-strip { border-left: 5px solid var(--orange); background: #fff7ed; border-radius: 18px; padding: 13px 15px; color: #4b5563; margin: 12px 0 16px; }
        .good { color: var(--green); font-weight: 950; }
        .warn { color: var(--amber); font-weight: 950; }
        .bad { color: var(--red); font-weight: 950; }
        .product-card { border: 1px solid var(--line); border-radius: 20px; background: white; padding: 14px; margin-bottom: 10px; }
        .product-title { color: var(--ink); font-weight: 950; margin-bottom: 3px; }
        .product-meta { color: var(--muted); font-size: .85rem; }
        .store-card { border: 1px solid var(--line); border-radius: 22px; padding: 16px; background: white; height: 100%; }
        .store-rank { color: var(--orange-dark); font-weight: 950; font-size: .78rem; text-transform: uppercase; letter-spacing: .08em; }
        .store-name { color: var(--ink); font-weight: 950; font-size: 1.02rem; margin-top: 5px; }
        .store-total { color: var(--ink); font-weight: 950; font-size: 1.45rem; margin: 8px 0 2px; }
        .donate-float { position: fixed; right: 18px; bottom: 18px; z-index: 9999; text-decoration: none; background: rgba(255,255,255,.94); color: #9a3412 !important; border: 1px solid #fed7aa; padding: 9px 12px; border-radius: 999px; font-size: 12px; font-weight: 850; box-shadow: 0 10px 24px rgba(17, 24, 39, .12); }
        .donate-float:hover { background: #fff7ed; }
        [data-testid="stSidebar"] { background: #fffaf5; }
        .stButton>button, .stDownloadButton>button { border-radius: 999px; border: 1px solid #f5d9c8; font-weight: 850; min-height: 42px; }
        .stButton>button[kind="primary"] { background: #172033; color: white; border-color: #172033; }
        div[data-baseweb="select"] > div, div[data-testid="stNumberInputContainer"], input, textarea { border-radius: 16px !important; }
        [data-testid="stDataFrame"] { border-radius: 18px; overflow: hidden; border: 1px solid var(--line); }
        [data-testid="stExpander"] { border-radius: 20px; border: 1px solid var(--line); background: white; }
        @media (max-width: 800px) {
            .hero { padding: 22px; border-radius: 26px; }
            .hero-grid { grid-template-columns: 1fr; }
            .topbar { align-items: flex-start; flex-direction: column; gap: 6px; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def donation_button() -> None:
    st.markdown(f'<a class="donate-float" href="{PAYPAL_DONATION_LINK}" target="_blank">Donación opcional</a>', unsafe_allow_html=True)


def read_csv_any(source) -> pd.DataFrame:
    last_error = None
    for encoding in ["utf-8", "utf-8-sig", "latin-1"]:
        for sep in [",", ";", "|"]:
            try:
                if isinstance(source, (str, Path)) and str(source).startswith("http"):
                    response = requests.get(str(source), timeout=25)
                    response.raise_for_status()
                    df = pd.read_csv(io.BytesIO(response.content), sep=sep, encoding=encoding, low_memory=False)
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
    if col_map["producto"] is None or col_map["precio"] is None:
        raise ValueError("El CSV necesita columnas de producto y precio.")
    out = pd.DataFrame()
    for target, source in col_map.items():
        out[target] = df[source] if source else ""
    out["precio"] = (
        out["precio"].astype(str)
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
                urls.append(href if href.startswith("http") else urljoin(PROFECO_DATASET_URL, href))
        seen, final = set(), []
        for url in urls + FALLBACK_PROFECO_URLS:
            if url not in seen:
                seen.add(url)
                final.append(url)
        return final[:10]
    except Exception:
        return FALLBACK_PROFECO_URLS


@st.cache_data(ttl=3600, show_spinner=False)
def load_profeco_auto() -> Tuple[pd.DataFrame, Dict[str, str]]:
    for url in discover_profeco_urls():
        try:
            raw = read_csv_any(url)
            df = standardize_prices(raw, "PROFECO")
            if not df.empty:
                return df, {"source_label": "PROFECO automático", "source_url": url, "fallback": "no"}
        except Exception:
            pass
    raw = pd.read_csv(io.StringIO(EMBEDDED_SAMPLE_CSV))
    return standardize_prices(raw, "Ejemplo"), {"source_label": "Datos de ejemplo", "source_url": "Respaldo interno", "fallback": "sí"}


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
        return {"label": "Sin fecha", "class": "warn", "days": None, "min": None, "max": None}
    dates = pd.to_datetime(df["fecha"], errors="coerce").dropna()
    if dates.empty:
        return {"label": "Sin fecha detectada", "class": "warn", "days": None, "min": None, "max": None}
    max_date, min_date = dates.max(), dates.min()
    days = (pd.Timestamp.today().normalize() - max_date.normalize()).days
    if days <= 45:
        label, cls = "Actualizado", "good"
    elif days <= 120:
        label, cls = "Revisar vigencia", "warn"
    else:
        label, cls = "Datos antiguos", "bad"
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
            rows.append({"Producto": product, "Presentación": "", "Cantidad": qty, "Precio": None, "Total": None, "Tienda": "No encontrado", "Sucursal": "", "Fuente": "", "Fecha": ""})
            continue
        rows.append({
            "Producto": best["producto"],
            "Presentación": best.get("presentacion", ""),
            "Cantidad": qty,
            "Precio": float(best["precio"]),
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
            "Tienda": store.tienda or "Sin tienda",
            "Sucursal": store.sucursal,
            "Total estimado": total if len(missing) < len(cart) else None,
            "Encontrados": len(cart) - len(missing),
            "Faltantes": ", ".join(missing[:4]) + ("..." if len(missing) > 4 else ""),
        })
    result = pd.DataFrame(store_rows)
    if not result.empty:
        result = result.sort_values(["Encontrados", "Total estimado"], ascending=[False, True])
    return result


def ingredient_available(ingredient: str, available_norm: List[str]) -> bool:
    aliases = [normalize_text(x) for x in INGREDIENT_ALIASES.get(ingredient, [ingredient])]
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


def render_metric(label: str, value: str) -> None:
    st.markdown(f'<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value">{value}</div></div>', unsafe_allow_html=True)


def render_budget_bar(cart_total: float, budget: float) -> None:
    pct = 0 if budget <= 0 else min(cart_total / budget, 1.0)
    cls = "budget-bar-over" if budget > 0 and cart_total > budget else "budget-bar"
    st.markdown(f'<div class="budget-bar-wrap"><div class="{cls}" style="width:{pct*100:.1f}%"></div></div>', unsafe_allow_html=True)


def display_df(df: pd.DataFrame) -> None:
    if df.empty:
        st.info("No hay datos para mostrar todavía.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)


if "cart" not in st.session_state:
    st.session_state.cart = []

inject_css()
donation_button()

# Data controls kept in sidebar, but the main app is usable without opening it.
with st.sidebar:
    st.markdown("### Datos")
    source_mode = st.radio("Fuente principal", ["PROFECO automático", "Datos de ejemplo", "Pegar URL CSV", "Subir CSV"], index=0)
    custom_url = st.text_input("URL del CSV") if source_mode == "Pegar URL CSV" else ""
    uploaded_file = st.file_uploader("Subir CSV", type=["csv"]) if source_mode == "Subir CSV" else None
    st.divider()
    st.markdown("### Comparativo online")
    include_online_sample = st.checkbox("Usar precios online de ejemplo", value=True)
    online_url = st.text_input("CSV online opcional", placeholder="https://...")
    online_upload = st.file_uploader("Subir CSV online", type=["csv"], key="online_upload")
    st.caption("Los precios son estimados y pueden cambiar por fecha, sucursal, promoción y disponibilidad.")

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
if prices_df.empty:
    st.error("No hay precios disponibles. Revisa el CSV o cambia a Datos de ejemplo.")
    st.stop()

fresh = source_freshness(base_df)

st.markdown(
    """
    <div class="topbar">
        <div class="brand"><div class="brand-mark">A</div><div>AhorraDespensa</div></div>
        <div class="nav-note">Lista, presupuesto, tiendas y platillos en una sola vista</div>
    </div>
    <div class="hero">
        <div class="kicker">Despensa clara y sin vueltas</div>
        <div class="hero-title">Planea tu súper antes de salir de casa.</div>
        <div class="hero-copy">Elige tu ubicación, define tu presupuesto y arma una lista con precios de referencia. La app te muestra cuánto gastarías, dónde conviene comprar y qué platillos sencillos puedes preparar.</div>
        <div class="hero-grid">
            <div class="hero-step"><b>1. Ubica tu zona</b><span>Filtra por estado, municipio y tiendas disponibles.</span></div>
            <div class="hero-step"><b>2. Arma tu lista</b><span>Busca productos básicos y ve el total en tiempo real.</span></div>
            <div class="hero-step"><b>3. Decide mejor</b><span>Compara tiendas, revisa vigencia y planea platillos.</span></div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if load_errors:
    with st.expander("Avisos técnicos", expanded=False):
        for err in load_errors:
            st.warning(err)

# Planner controls
with st.container():
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="section-title"><div><span class="pill">Comienza aquí</span><h2>Tu presupuesto y ubicación</h2></div><div class="subtle">Estos datos solo ajustan el cálculo estimado.</div></div>', unsafe_allow_html=True)
    states = ["Todos"] + sorted([x for x in prices_df["estado"].dropna().unique() if str(x).strip()])
    c1, c2, c3, c4, c5 = st.columns([1.05, 1.05, .9, .75, .75])
    with c1:
        estado = st.selectbox("Estado", states, index=states.index("Yucatán") if "Yucatán" in states else 0)
    municipalities_df = prices_df if estado == "Todos" else prices_df[prices_df["estado"] == estado]
    municipalities = ["Todos"] + sorted([x for x in municipalities_df["municipio"].dropna().unique() if str(x).strip()])
    with c2:
        municipio = st.selectbox("Municipio", municipalities, index=municipalities.index("Mérida") if "Mérida" in municipalities else 0)
    with c3:
        budget = st.number_input("Presupuesto", min_value=0.0, value=800.0, step=50.0, format="%.2f")
    with c4:
        days = st.number_input("Días", min_value=1, max_value=31, value=7, step=1)
    with c5:
        people = st.number_input("Personas", min_value=1, max_value=12, value=2, step=1)

    filtered_for_stores = prices_df.copy()
    if estado != "Todos":
        filtered_for_stores = filtered_for_stores[filtered_for_stores["estado"] == estado]
    if municipio != "Todos":
        filtered_for_stores = filtered_for_stores[filtered_for_stores["municipio"] == municipio]
    store_options = sorted([x for x in filtered_for_stores["tienda"].dropna().unique() if str(x).strip()])
    show_all = st.toggle("Comparar con todas las tiendas disponibles", value=True)
    selected_stores = [] if show_all else st.multiselect("Elige tiendas", store_options, default=store_options[:4])
    st.markdown('</div>', unsafe_allow_html=True)

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
    render_metric("Te queda", currency(remaining))
with m3:
    render_metric("Por día", currency(daily_budget))
with m4:
    render_metric("Por persona al día", currency(per_person_day))

render_budget_bar(cart_total, budget)
if st.session_state.cart and budget > 0:
    if cart_total > budget:
        st.error(f"Tu lista supera el presupuesto por {currency(abs(remaining))}.")
    else:
        st.success(f"Vas dentro del presupuesto. Te quedarían {currency(remaining)}.")

last_detail = "No se pudo detectar fecha de registro." if fresh["days"] is None else f"Último registro detectado hace {fresh['days']} días."
st.markdown(
    f'<div class="source-strip">Fuente principal: <strong>{meta.get("source_label", "")}</strong> · <span class="{fresh["class"]}">{fresh["label"]}</span><br><span class="subtle">{last_detail}</span></div>',
    unsafe_allow_html=True,
)

main_tab, compare_tab, meals_tab, source_tab = st.tabs(["Armar lista", "Comparar tiendas", "Platillos", "Fuente y confianza"])

with main_tab:
    left, right = st.columns([.95, 1.2], gap="large")
    with left:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="section-title"><div><span class="pill">Paso 1</span><h3>Busca y agrega</h3></div></div>', unsafe_allow_html=True)
        search = st.text_input("Producto", placeholder="Ej. huevo, arroz, leche, pollo...")
        options = get_product_options(filtered, search)
        if not options:
            st.info("No encontré productos con ese filtro. Prueba con otra palabra o cambia ubicación.")
        else:
            product_option = st.selectbox("Resultado", options)
            qty = st.number_input("Cantidad", min_value=0.1, value=1.0, step=0.5)
            cadd, cclear = st.columns([1.2, .8])
            with cadd:
                if st.button("Agregar a mi lista", type="primary", use_container_width=True):
                    st.session_state.cart.append({"producto": product_name_from_option(product_option), "cantidad": qty})
                    st.rerun()
            with cclear:
                if st.button("Limpiar", use_container_width=True):
                    st.session_state.cart = []
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="soft-panel">', unsafe_allow_html=True)
        st.markdown('<div class="section-title"><div><span class="pill">Ideas rápidas</span><h3>Básicos baratos</h3></div></div>', unsafe_allow_html=True)
        cheap = filtered.sort_values("precio").head(7)[["producto", "presentacion", "precio", "tienda", "fuente"]].copy()
        for row in cheap.itertuples(index=False):
            st.markdown(f'<div class="product-card"><div class="product-title">{row.producto}</div><div class="product-meta">{row.presentacion} · {currency(row.precio)} · {row.tienda} · {row.fuente}</div></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="section-title"><div><span class="pill">Paso 2</span><h3>Tu lista</h3></div><div class="subtle">Precio más bajo encontrado por producto.</div></div>', unsafe_allow_html=True)
        if cart_df.empty:
            st.info("Agrega productos para ver el costo estimado.")
        else:
            for i, row in cart_df.iterrows():
                price = "Sin precio" if pd.isna(row["Precio"]) else currency(row["Precio"])
                total = "" if pd.isna(row["Total"]) else currency(row["Total"])
                st.markdown(
                    f'<div class="product-card"><div class="product-title">{row["Producto"]}</div><div class="product-meta">Cantidad: {row["Cantidad"]} · {price} · Total: {total}<br>{row["Tienda"]} · {row["Fuente"]} · {row["Fecha"]}</div></div>',
                    unsafe_allow_html=True,
                )
                if st.button("Quitar", key=f"remove_{i}"):
                    st.session_state.cart.pop(i)
                    st.rerun()
            download_df = cart_df.copy()
            st.download_button("Descargar mi lista", data=download_df.to_csv(index=False).encode("utf-8-sig"), file_name="mi_lista_ahorradespensa.csv", mime="text/csv", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

with compare_tab:
    store_compare = compare_stores(filtered, st.session_state.cart)
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="section-title"><div><span class="pill">Comparativo</span><h2>¿Dónde conviene comprar?</h2></div><div class="subtle">Se calcula con los productos disponibles por fuente y sucursal.</div></div>', unsafe_allow_html=True)
    if store_compare.empty:
        st.info("Agrega productos para comparar tiendas.")
    else:
        top = store_compare.head(3).reset_index(drop=True)
        cols = st.columns(3)
        for idx, row in top.iterrows():
            with cols[idx]:
                total = "Sin cálculo" if pd.isna(row["Total estimado"]) else currency(row["Total estimado"])
                st.markdown(
                    f'<div class="store-card"><div class="store-rank">Opción {idx+1}</div><div class="store-name">{row["Tienda"]}</div><div class="store-total">{total}</div><div class="product-meta">{row["Sucursal"]}<br>{row["Fuente"]} · {row["Encontrados"]}/{len(st.session_state.cart)} productos encontrados</div></div>',
                    unsafe_allow_html=True,
                )
        display = store_compare.copy()
        display["Total estimado"] = display["Total estimado"].apply(lambda x: "" if pd.isna(x) else currency(x))
        display_df(display)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="section-title"><div><span class="pill">Detalle</span><h3>Precios por producto</h3></div></div>', unsafe_allow_html=True)
    if not st.session_state.cart:
        st.info("Agrega productos para ver el detalle.")
    else:
        detail_rows = []
        for item in st.session_state.cart:
            pnorm = normalize_text(item["producto"])
            subset = filtered[filtered["producto_norm"] == pnorm].sort_values("precio").head(15)
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
        display_df(pd.DataFrame(detail_rows))
    st.markdown('</div>', unsafe_allow_html=True)

with meals_tab:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="section-title"><div><span class="pill">Comidas posibles</span><h2>Platillos con tu lista</h2></div><div class="subtle">Ideas sencillas. No sustituye orientación nutricional.</div></div>', unsafe_allow_html=True)
    if not st.session_state.cart:
        st.info("Agrega productos para recibir ideas de platillos.")
    else:
        matches = recipe_matches(st.session_state.cart)
        cols = st.columns(2)
        for idx, recipe in enumerate(matches[:8]):
            with cols[idx % 2]:
                score_pct = int(recipe["score"] * 100)
                missing = ", ".join(recipe["missing"]) if recipe["missing"] else "Nada"
                st.markdown(
                    f'<div class="product-card"><div class="product-title">{recipe["name"]}</div><div class="product-meta">{recipe["type"]} · Coincidencia: {score_pct}%<br>Falta: {missing}<br>{recipe["note"]}</div></div>',
                    unsafe_allow_html=True,
                )
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="section-title"><div><span class="pill">Plan simple</span><h3>Distribución por días</h3></div></div>', unsafe_allow_html=True)
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
            display_df(pd.DataFrame(plan))
    else:
        st.info("Tu plan aparecerá cuando agregues productos.")
    st.markdown('</div>', unsafe_allow_html=True)

with source_tab:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="section-title"><div><span class="pill">Transparencia</span><h2>Fuente y confianza</h2></div><div class="subtle">La app debe decir de dónde salen los precios.</div></div>', unsafe_allow_html=True)
    min_date, max_date = fresh.get("min"), fresh.get("max")
    source_info = pd.DataFrame([
        {"Dato": "Fuente principal", "Valor": meta.get("source_label", "")},
        {"Dato": "Archivo o URL", "Valor": meta.get("source_url", "")},
        {"Dato": "Registros cargados", "Valor": f"{len(base_df):,}"},
        {"Dato": "Primer registro detectado", "Valor": "" if min_date is None else pd.to_datetime(min_date).strftime("%Y-%m-%d")},
        {"Dato": "Último registro detectado", "Valor": "" if max_date is None else pd.to_datetime(max_date).strftime("%Y-%m-%d")},
        {"Dato": "Estado de vigencia", "Valor": fresh.get("label", "")},
        {"Dato": "Usó respaldo", "Valor": meta.get("fallback", "no")},
    ])
    display_df(source_info)
    st.markdown('<p class="subtle">PROFECO sirve como referencia oficial, pero no siempre representa el precio exacto del día. Los precios en línea pueden variar por código postal, disponibilidad, promociones, método de entrega y sucursal.</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="section-title"><div><span class="pill">Resumen</span><h3>Fuentes cargadas</h3></div></div>', unsafe_allow_html=True)
    source_summary = prices_df.groupby("fuente", dropna=False).agg(
        registros=("producto", "count"),
        productos=("producto_norm", "nunique"),
        tiendas=("tienda", "nunique"),
        ultimo_registro=("fecha", "max"),
    ).reset_index()
    source_summary["ultimo_registro"] = pd.to_datetime(source_summary["ultimo_registro"], errors="coerce").dt.strftime("%Y-%m-%d").fillna("")
    display_df(source_summary)
    st.markdown('</div>', unsafe_allow_html=True)
