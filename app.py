import io
import os
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import requests
import streamlit as st
from bs4 import BeautifulSoup


APP_NAME = "AhorraDespensa"
DATA_DIR = Path(__file__).parent / "data"
SAMPLE_CSV = DATA_DIR / "sample_precios.csv"
PROFECO_DATASET_URL = "https://www.datos.gob.mx/dataset/programa_quien_es_quien_precios_2025"

# Pega aquí tu enlace real de PayPal Donate o PayPal.me.
# Ejemplos:
# PAYPAL_DONATION_LINK = "https://www.paypal.com/donate/?hosted_button_id=TU_ID_REAL"
# PAYPAL_DONATION_LINK = "https://www.paypal.me/tuusuario"
PAYPAL_DONATION_LINK = os.getenv(
    "PAYPAL_DONATION_LINK",
    "https://www.paypal.com/donate/?hosted_button_id=REEMPLAZA_ESTO",
)

FALLBACK_PROFECO_URLS = [
    "https://repodatos.atdt.gob.mx/api_update/profeco/programa_quien_es_quien_precios_2025/09-2025_01.csv",
    "https://repodatos.atdt.gob.mx/api_update/profeco/programa_quien_es_quien_precios_2025/08-2025_02.csv",
    "https://repodatos.atdt.gob.mx/api_update/profeco/programa_quien_es_quien_precios_2025/02-2025_02.csv",
]

RECIPES = [
    {
        "name": "Huevos a la mexicana con tortillas",
        "type": "Desayuno",
        "ingredients": ["huevo", "jitomate", "cebolla", "tortilla"],
        "note": "Rápido, barato y rendidor.",
    },
    {
        "name": "Avena con plátano",
        "type": "Desayuno",
        "ingredients": ["avena", "platano", "leche"],
        "note": "Buena opción para ahorrar y repetir varios días.",
    },
    {
        "name": "Quesadillas con frijol",
        "type": "Desayuno",
        "ingredients": ["tortilla", "queso", "frijol"],
        "note": "Fácil de preparar y con pocos ingredientes.",
    },
    {
        "name": "Arroz con pollo y verduras",
        "type": "Comida",
        "ingredients": ["arroz", "pollo", "zanahoria", "cebolla"],
        "note": "Rinde bien para varias porciones.",
    },
    {
        "name": "Sopa de lentejas",
        "type": "Comida",
        "ingredients": ["lenteja", "jitomate", "cebolla", "zanahoria"],
        "note": "Muy rendidora y económica.",
    },
    {
        "name": "Pasta con atún",
        "type": "Comida",
        "ingredients": ["pasta", "atun", "jitomate", "cebolla"],
        "note": "Buena para resolver comida con poco presupuesto.",
    },
    {
        "name": "Tacos de frijol con huevo",
        "type": "Comida",
        "ingredients": ["frijol", "huevo", "tortilla"],
        "note": "Muy barato y llenador.",
    },
    {
        "name": "Ensalada de atún con tostadas",
        "type": "Cena",
        "ingredients": ["atun", "mayonesa", "tostada", "zanahoria"],
        "note": "Ligera, rápida y fácil de ajustar.",
    },
    {
        "name": "Sincronizadas",
        "type": "Cena",
        "ingredients": ["tortilla", "queso", "jamon"],
        "note": "Simple y rápida para cena.",
    },
    {
        "name": "Tostadas de frijol con queso",
        "type": "Cena",
        "ingredients": ["tostada", "frijol", "queso"],
        "note": "Económica y rendidora.",
    },
    {
        "name": "Molletes sencillos",
        "type": "Cena",
        "ingredients": ["bolillo", "frijol", "queso"],
        "note": "Buena opción cuando hay poco tiempo.",
    },
    {
        "name": "Sopa de pasta con verduras",
        "type": "Comida",
        "ingredients": ["pasta", "zanahoria", "jitomate", "cebolla"],
        "note": "Rinde mucho y usa ingredientes básicos.",
    },
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


st.set_page_config(
    page_title=APP_NAME,
    page_icon="A",
    layout="wide",
    initial_sidebar_state="expanded",
)


# -----------------------------
# Helpers
# -----------------------------
def normalize_text(value: object) -> str:
    text = "" if value is None else str(value)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9ñ\s]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


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
          --bg-soft: #f7f3ea;
          --card: #ffffff;
          --text: #1f2933;
          --muted: #6b7280;
          --accent: #ef7d22;
          --accent-soft: #fff2e7;
          --green: #0f766e;
          --red: #b42318;
          --border: #eadfce;
        }
        .main .block-container { padding-top: 2rem; padding-bottom: 4rem; }
        h1, h2, h3 { letter-spacing: -0.03em; }
        .hero {
          padding: 22px 24px;
          border: 1px solid var(--border);
          border-radius: 24px;
          background: linear-gradient(135deg, #fffaf3 0%, #ffffff 62%, #fff1e4 100%);
          margin-bottom: 18px;
        }
        .hero-title {
          font-size: 2.1rem;
          font-weight: 800;
          color: var(--text);
          margin-bottom: 6px;
        }
        .hero-subtitle { color: var(--muted); font-size: 1.02rem; max-width: 850px; }
        .soft-card {
          background: var(--card);
          border: 1px solid var(--border);
          border-radius: 20px;
          padding: 18px 18px;
          margin-bottom: 14px;
          box-shadow: 0 6px 18px rgba(31, 41, 51, 0.04);
        }
        .metric-card {
          background: #ffffff;
          border: 1px solid var(--border);
          border-radius: 18px;
          padding: 14px 15px;
        }
        .metric-label { color: var(--muted); font-size: .82rem; }
        .metric-value { font-size: 1.35rem; font-weight: 800; color: var(--text); }
        .good { color: var(--green); font-weight: 700; }
        .bad { color: var(--red); font-weight: 700; }
        .tiny-muted { color: var(--muted); font-size: .82rem; }
        .donation-float {
          position: fixed;
          right: 18px;
          bottom: 16px;
          z-index: 9999;
          opacity: .92;
        }
        .donation-float a {
          display: inline-block;
          font-size: 12px;
          text-decoration: none;
          color: #5c3417;
          background: rgba(255, 244, 232, .95);
          border: 1px solid #f2c79c;
          border-radius: 999px;
          padding: 7px 11px;
          box-shadow: 0 8px 24px rgba(0,0,0,.08);
        }
        .donation-float a:hover { background: #ffe9d2; color: #331b09; }
        div[data-testid="stMetricValue"] { font-size: 1.35rem; }
        .stButton button { border-radius: 12px; }
        .stSelectbox div[data-baseweb="select"] > div { border-radius: 12px; }
        .stNumberInput input, .stTextInput input { border-radius: 12px; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_donation_button() -> None:
    if PAYPAL_DONATION_LINK:
        st.markdown(
            f"""
            <div class="donation-float">
              <a href="{PAYPAL_DONATION_LINK}" target="_blank" title="Donación voluntaria por PayPal">Apoyar este proyecto</a>
            </div>
            """,
            unsafe_allow_html=True,
        )


@st.cache_data(ttl=60 * 60 * 12, show_spinner=False)
def discover_profeco_csv_urls(dataset_url: str) -> List[str]:
    urls: List[str] = []
    try:
        response = requests.get(dataset_url, timeout=18)
        response.raise_for_status()
        html = response.text
        soup = BeautifulSoup(html, "html.parser")
        for a in soup.find_all("a"):
            href = a.get("href", "")
            if href.startswith("//"):
                href = "https:" + href
            if "repodatos" in href and href.lower().endswith(".csv"):
                urls.append(href)
        urls.extend(re.findall(r"https://repodatos[^\"'<>\s]+?\.csv", html))
    except Exception:
        pass

    clean = []
    seen = set()
    for url in urls + FALLBACK_PROFECO_URLS:
        if url not in seen:
            clean.append(url)
            seen.add(url)
    return clean


@st.cache_data(ttl=60 * 60 * 12, show_spinner=False)
def read_csv_flexible(source: object) -> pd.DataFrame:
    encodings = ["utf-8-sig", "utf-8", "latin1", "cp1252"]
    errors = []

    def rewind() -> None:
        if hasattr(source, "seek"):
            try:
                source.seek(0)
            except Exception:
                pass

    for enc in encodings:
        try:
            rewind()
            return pd.read_csv(source, encoding=enc, low_memory=False)
        except Exception as exc:
            errors.append(str(exc))

    # Segundo intento: separador autodetectado.
    for enc in encodings:
        try:
            rewind()
            return pd.read_csv(source, encoding=enc, sep=None, engine="python")
        except Exception as exc:
            errors.append(str(exc))

    raise ValueError("No se pudo leer el CSV. Revisa el archivo o la URL.")


def find_column(columns: List[str], candidates: List[str]) -> Optional[str]:
    normalized = {col: normalize_text(col).replace(" ", "") for col in columns}
    for candidate in candidates:
        cand = normalize_text(candidate).replace(" ", "")
        for col, norm in normalized.items():
            if norm == cand:
                return col
    for candidate in candidates:
        cand = normalize_text(candidate).replace(" ", "")
        for col, norm in normalized.items():
            if cand in norm or norm in cand:
                return col
    return None


def normalize_price_series(series: pd.Series) -> pd.Series:
    cleaned = (
        series.astype(str)
        .str.replace("$", "", regex=False)
        .str.replace(",", "", regex=False)
        .str.replace("MXN", "", regex=False)
        .str.replace(" ", "", regex=False)
    )
    return pd.to_numeric(cleaned, errors="coerce")


def normalize_price_data(raw: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, str]]:
    df = raw.copy()
    df.columns = [str(c).strip() for c in df.columns]
    columns = list(df.columns)

    mapping = {
        "product": find_column(columns, ["producto", "nombre producto", "descripcion producto", "articulo", "descripción", "descripcion"]),
        "presentation": find_column(columns, ["presentacion", "presentación", "empaque", "contenido"]),
        "brand": find_column(columns, ["marca", "fabricante"]),
        "category": find_column(columns, ["categoria", "categoría", "catalogo", "catálogo", "grupo", "linea"]),
        "price": find_column(columns, ["precio", "precio promedio", "precio minimo", "precio mínimo", "precio publico"]),
        "store": find_column(columns, ["cadena comercial", "cadenacomercial", "cadena", "establecimiento", "tienda", "proveedor", "nombre comercial", "nombrecomercial"]),
        "branch": find_column(columns, ["sucursal", "nombre sucursal", "razon social", "razón social", "nombre comercial", "nombrecomercial"]),
        "state": find_column(columns, ["estado", "entidad", "entidad federativa"]),
        "city": find_column(columns, ["municipio", "alcaldia", "alcaldía", "ciudad", "localidad"]),
        "address": find_column(columns, ["direccion", "dirección", "domicilio", "ubicacion", "ubicación"]),
        "date": find_column(columns, ["fecha", "fecha registro", "fecharegistro", "fecha de registro"]),
        "lat": find_column(columns, ["latitud", "latitude", "lat"]),
        "lon": find_column(columns, ["longitud", "longitude", "lon", "lng"]),
    }

    required = ["product", "price"]
    missing = [key for key in required if mapping.get(key) is None]
    if missing:
        raise ValueError(
            "El CSV no tiene columnas reconocibles de producto y precio. "
            "Revisa que venga de PROFECO o que tenga columnas como Producto y Precio."
        )

    out = pd.DataFrame()
    for key, col in mapping.items():
        if col is not None:
            out[key] = df[col]
        else:
            out[key] = ""

    out["product"] = out["product"].astype(str).str.strip()
    out["price"] = normalize_price_series(out["price"])
    out["presentation"] = out["presentation"].fillna("").astype(str).str.strip()
    out["brand"] = out["brand"].fillna("").astype(str).str.strip()
    out["category"] = out["category"].fillna("").astype(str).str.strip()
    out["store"] = out["store"].fillna("").astype(str).str.strip()
    out["branch"] = out["branch"].fillna("").astype(str).str.strip()
    out["state"] = out["state"].fillna("").astype(str).str.strip()
    out["city"] = out["city"].fillna("").astype(str).str.strip()
    out["address"] = out["address"].fillna("").astype(str).str.strip()
    out["date"] = out["date"].fillna("").astype(str).str.strip()
    out["lat"] = pd.to_numeric(out["lat"], errors="coerce")
    out["lon"] = pd.to_numeric(out["lon"], errors="coerce")

    out = out.dropna(subset=["price"])
    out = out[(out["price"] > 0) & (out["product"].str.len() > 1)].copy()

    out["product_norm"] = out["product"].map(normalize_text)
    out["store_norm"] = out["store"].map(normalize_text)
    out["city_norm"] = out["city"].map(normalize_text)
    out["state_norm"] = out["state"].map(normalize_text)

    out["display_product"] = out.apply(
        lambda r: " · ".join(
            [x for x in [r["product"], r["presentation"], r["brand"]] if str(x).strip()]
        ),
        axis=1,
    )
    out["display_store"] = out.apply(
        lambda r: " · ".join([x for x in [r["store"], r["branch"]] if str(x).strip()]),
        axis=1,
    )
    out["display_store"] = out["display_store"].replace("", "Establecimiento sin nombre")

    return out, {k: v for k, v in mapping.items() if v is not None}


def filter_data(df: pd.DataFrame, state: str, city: str, stores: List[str]) -> pd.DataFrame:
    filtered = df.copy()
    if state and state != "Todos":
        filtered = filtered[filtered["state"] == state]
    if city and city != "Todos":
        filtered = filtered[filtered["city"] == city]
    if stores:
        filtered = filtered[filtered["display_store"].isin(stores)]
    return filtered


def best_price_for_product(df: pd.DataFrame, product: str) -> Optional[pd.Series]:
    if df.empty:
        return None
    product_norm = normalize_text(product)
    exact = df[df["product_norm"] == product_norm]
    if exact.empty:
        exact = df[df["product_norm"].str.contains(re.escape(product_norm), na=False)]
    if exact.empty:
        return None
    return exact.sort_values("price", ascending=True).iloc[0]


def local_price_for_ingredient(df: pd.DataFrame, ingredient: str) -> Tuple[Optional[float], str]:
    aliases = INGREDIENT_ALIASES.get(ingredient, [ingredient])
    pattern = "|".join(re.escape(normalize_text(a)) for a in aliases)
    hits = df[df["product_norm"].str.contains(pattern, na=False, regex=True)]
    if hits.empty:
        return None, ""
    row = hits.sort_values("price").iloc[0]
    return float(row["price"]), str(row["display_product"])


def recipe_suggestions(df: pd.DataFrame, cart: List[Dict], budget_left: float) -> pd.DataFrame:
    cart_text = " ".join(normalize_text(item["producto"]) for item in cart)
    rows = []
    for recipe in RECIPES:
        covered = []
        missing = []
        missing_cost = 0.0
        missing_detail = []
        for ingredient in recipe["ingredients"]:
            aliases = INGREDIENT_ALIASES.get(ingredient, [ingredient])
            is_covered = any(normalize_text(a) in cart_text for a in aliases)
            if is_covered:
                covered.append(ingredient)
            else:
                price, local_product = local_price_for_ingredient(df, ingredient)
                missing.append(ingredient)
                if price is not None:
                    # No intenta calcular gramos exactos. Usa una compra mínima como referencia local.
                    missing_cost += min(price, price * 0.55)
                    missing_detail.append(f"{ingredient} ({currency(price)} ref.)")
                else:
                    missing_detail.append(f"{ingredient} (sin precio local)")
        score = len(covered) * 3 - len(missing)
        status = "Dentro del presupuesto" if missing_cost <= max(budget_left, 0) else "Puede salirse del presupuesto"
        rows.append(
            {
                "Platillo": recipe["name"],
                "Tipo": recipe["type"],
                "Ya tienes": ", ".join(covered) if covered else "Nada todavía",
                "Faltaría": ", ".join(missing_detail) if missing_detail else "Nada",
                "Extra estimado": missing_cost,
                "Estado": status,
                "Nota": recipe["note"],
                "score": score,
            }
        )
    result = pd.DataFrame(rows)
    return result.sort_values(["score", "Extra estimado"], ascending=[False, True]).drop(columns=["score"])


def build_meal_plan(suggestions: pd.DataFrame, days: int) -> pd.DataFrame:
    if suggestions.empty:
        return pd.DataFrame()
    plan_rows = []
    buckets = {
        "Desayuno": suggestions[suggestions["Tipo"] == "Desayuno"]["Platillo"].tolist(),
        "Comida": suggestions[suggestions["Tipo"] == "Comida"]["Platillo"].tolist(),
        "Cena": suggestions[suggestions["Tipo"] == "Cena"]["Platillo"].tolist(),
    }
    for meal_type in buckets:
        if not buckets[meal_type]:
            buckets[meal_type] = suggestions["Platillo"].tolist()
    for day in range(1, max(1, days) + 1):
        plan_rows.append(
            {
                "Día": day,
                "Desayuno": buckets["Desayuno"][(day - 1) % len(buckets["Desayuno"])],
                "Comida": buckets["Comida"][(day - 1) % len(buckets["Comida"])],
                "Cena": buckets["Cena"][(day - 1) % len(buckets["Cena"])],
            }
        )
    return pd.DataFrame(plan_rows)


def compare_stores_for_cart(df: pd.DataFrame, cart: List[Dict]) -> pd.DataFrame:
    if not cart or df.empty:
        return pd.DataFrame()

    products = [normalize_text(item["producto_base"]) for item in cart]
    rows = []
    for store, group in df.groupby("display_store"):
        total = 0.0
        found = 0
        missing = []
        for product_norm in products:
            hits = group[group["product_norm"] == product_norm]
            if hits.empty:
                hits = group[group["product_norm"].str.contains(re.escape(product_norm), na=False)]
            if hits.empty:
                missing.append(product_norm)
            else:
                found += 1
                total += float(hits["price"].min())
        rows.append(
            {
                "Tienda": store,
                "Productos encontrados": found,
                "Total si compras ahí": total if found else np.nan,
                "Faltantes": len(missing),
            }
        )
    result = pd.DataFrame(rows)
    if result.empty:
        return result
    return result.sort_values(["Faltantes", "Total si compras ahí"], ascending=[True, True])


def cart_to_dataframe(cart: List[Dict]) -> pd.DataFrame:
    if not cart:
        return pd.DataFrame(columns=["Producto", "Cantidad", "Precio ref.", "Subtotal", "Tienda sugerida"])
    return pd.DataFrame(
        [
            {
                "Producto": item["producto"],
                "Cantidad": item["cantidad"],
                "Precio ref.": item["precio"],
                "Subtotal": item["subtotal"],
                "Tienda sugerida": item["tienda"],
                "Dirección": item.get("direccion", ""),
            }
            for item in cart
        ]
    )


def reset_cart() -> None:
    st.session_state.cart = []


# -----------------------------
# UI
# -----------------------------
inject_css()
render_donation_button()

if "cart" not in st.session_state:
    st.session_state.cart = []

st.markdown(
    """
    <div class="hero">
      <div class="hero-title">AhorraDespensa</div>
      <div class="hero-subtitle">
        Arma una lista de despensa, estima cuánto gastarías en tu zona y recibe ideas de platillos sencillos según tu presupuesto.
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.subheader("Configuración")
    data_source = st.radio(
        "Fuente de precios",
        ["PROFECO automático", "Datos de ejemplo", "Pegar URL CSV", "Subir CSV"],
        help="PROFECO automático intenta leer el dataset abierto de Quién es Quién en los Precios. Si falla, puedes usar datos de ejemplo o subir un CSV.",
    )

    source_label = ""
    raw_df: Optional[pd.DataFrame] = None
    load_error = None

    try:
        if data_source == "PROFECO automático":
            with st.spinner("Buscando archivo CSV de PROFECO..."):
                urls = discover_profeco_csv_urls(PROFECO_DATASET_URL)
            chosen_url = st.selectbox("Archivo detectado", urls, index=0 if urls else None)
            source_label = chosen_url
            with st.spinner("Cargando precios..."):
                raw_df = read_csv_flexible(chosen_url)
        elif data_source == "Datos de ejemplo":
            source_label = "data/sample_precios.csv"
            raw_df = read_csv_flexible(SAMPLE_CSV)
        elif data_source == "Pegar URL CSV":
            custom_url = st.text_input("URL del CSV", value=FALLBACK_PROFECO_URLS[0])
            source_label = custom_url
            if custom_url:
                with st.spinner("Cargando CSV..."):
                    raw_df = read_csv_flexible(custom_url)
        else:
            uploaded = st.file_uploader("Sube tu CSV de precios", type=["csv"])
            if uploaded is not None:
                source_label = uploaded.name
                raw_df = read_csv_flexible(uploaded)
            else:
                raw_df = read_csv_flexible(SAMPLE_CSV)
                source_label = "Datos de ejemplo mientras subes un CSV"
    except Exception as exc:
        load_error = exc
        raw_df = read_csv_flexible(SAMPLE_CSV)
        source_label = "Datos de ejemplo por error al cargar la fuente"

    if load_error:
        st.warning(f"No pude cargar la fuente seleccionada. Usaré datos de ejemplo. Detalle: {load_error}")

try:
    prices_df, detected_columns = normalize_price_data(raw_df)
except Exception as exc:
    st.error(str(exc))
    st.stop()

with st.sidebar:
    st.caption(f"Fuente actual: {source_label}")
    with st.expander("Columnas detectadas"):
        st.json(detected_columns)

    st.divider()
    st.subheader("Tu presupuesto")
    budget = st.number_input("Presupuesto disponible", min_value=0.0, value=1200.0, step=50.0)
    days = st.number_input("¿Para cuántos días?", min_value=1, max_value=31, value=7, step=1)
    people = st.number_input("¿Para cuántas personas?", min_value=1, max_value=12, value=2, step=1)

states = ["Todos"] + sorted([x for x in prices_df["state"].dropna().unique().tolist() if str(x).strip()])
col1, col2, col3 = st.columns([1, 1, 1.2])
with col1:
    state = st.selectbox("Estado", states)

city_base = prices_df if state == "Todos" else prices_df[prices_df["state"] == state]
cities = ["Todos"] + sorted([x for x in city_base["city"].dropna().unique().tolist() if str(x).strip()])
with col2:
    city = st.selectbox("Municipio o ciudad", cities)

store_base = filter_data(prices_df, state, city, [])
stores_available = sorted([x for x in store_base["display_store"].dropna().unique().tolist() if str(x).strip()])
with col3:
    selected_stores = st.multiselect("Supermercados o tiendas", stores_available, placeholder="Todos")

local_df = filter_data(prices_df, state, city, selected_stores)

if local_df.empty:
    st.warning("No hay precios para esos filtros. Prueba con otro municipio, otra tienda o usa 'Todos'.")
    st.stop()

m1, m2, m3, m4 = st.columns(4)
with m1:
    st.markdown(f"<div class='metric-card'><div class='metric-label'>Productos</div><div class='metric-value'>{local_df['product'].nunique():,}</div></div>", unsafe_allow_html=True)
with m2:
    st.markdown(f"<div class='metric-card'><div class='metric-label'>Tiendas</div><div class='metric-value'>{local_df['display_store'].nunique():,}</div></div>", unsafe_allow_html=True)
with m3:
    st.markdown(f"<div class='metric-card'><div class='metric-label'>Precio mediano</div><div class='metric-value'>{currency(float(local_df['price'].median()))}</div></div>", unsafe_allow_html=True)
with m4:
    date_values = [x for x in local_df["date"].dropna().astype(str).unique().tolist() if x.strip()]
    date_label = date_values[0] if date_values else "Sin fecha"
    st.markdown(f"<div class='metric-card'><div class='metric-label'>Fecha ref.</div><div class='metric-value' style='font-size:1rem'>{date_label}</div></div>", unsafe_allow_html=True)

st.write("")
left, right = st.columns([1.05, 0.95], gap="large")

with left:
    st.markdown("<div class='soft-card'>", unsafe_allow_html=True)
    st.subheader("1. Arma tu lista")
    search = st.text_input("Buscar producto", placeholder="Ej. huevo, arroz, leche, pollo, tortilla...")

    searchable = local_df.copy()
    if search:
        terms = normalize_text(search)
        searchable = searchable[searchable["product_norm"].str.contains(re.escape(terms), na=False)]

    product_options = sorted(searchable["product"].dropna().unique().tolist())[:500]
    if not product_options:
        st.info("No encontré productos con esa búsqueda.")
    else:
        product = st.selectbox("Producto", product_options)
        best_row = best_price_for_product(local_df, product)
        qty_col, add_col = st.columns([1, 1])
        with qty_col:
            qty = st.number_input("Cantidad", min_value=0.1, value=1.0, step=0.5)
        with add_col:
            st.write("")
            st.write("")
            add_clicked = st.button("Agregar a mi lista", use_container_width=True)
        if best_row is not None:
            st.caption(
                f"Mejor referencia local: {currency(float(best_row['price']))} en {best_row['display_store']}"
            )
        if add_clicked and best_row is not None:
            st.session_state.cart.append(
                {
                    "producto_base": best_row["product"],
                    "producto": best_row["display_product"],
                    "cantidad": float(qty),
                    "precio": float(best_row["price"]),
                    "subtotal": float(best_row["price"]) * float(qty),
                    "tienda": best_row["display_store"],
                    "direccion": best_row["address"],
                }
            )
            st.success("Producto agregado.")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='soft-card'>", unsafe_allow_html=True)
    st.subheader("2. Tu lista estimada")
    cart_df = cart_to_dataframe(st.session_state.cart)
    if cart_df.empty:
        st.info("Agrega productos para ver el estimado de compra.")
    else:
        show_cart = cart_df.copy()
        show_cart["Precio ref."] = show_cart["Precio ref."].map(currency)
        show_cart["Subtotal"] = show_cart["Subtotal"].map(currency)
        st.dataframe(show_cart, use_container_width=True, hide_index=True)
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Vaciar lista", use_container_width=True):
                reset_cart()
                st.rerun()
        with c2:
            csv = cart_df.to_csv(index=False).encode("utf-8-sig")
            st.download_button("Descargar lista CSV", data=csv, file_name="mi_despensa.csv", mime="text/csv", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.markdown("<div class='soft-card'>", unsafe_allow_html=True)
    st.subheader("Resumen")
    total = sum(item["subtotal"] for item in st.session_state.cart)
    remaining = budget - total
    per_day = total / days if days else total
    per_person_day = total / (days * people) if days and people else total

    a, b = st.columns(2)
    with a:
        st.metric("Total estimado", currency(total))
        st.metric("Por día", currency(per_day))
    with b:
        st.metric("Presupuesto", currency(budget))
        st.metric("Por persona/día", currency(per_person_day))

    if total == 0:
        st.caption("Todavía no hay productos en la lista.")
    elif remaining >= 0:
        st.markdown(f"<p class='good'>Vas dentro del presupuesto. Te quedarían {currency(remaining)}.</p>", unsafe_allow_html=True)
    else:
        st.markdown(f"<p class='bad'>Te pasarías por {currency(abs(remaining))}.</p>", unsafe_allow_html=True)
    st.markdown("<p class='tiny-muted'>Los precios son referencias. Pueden variar por sucursal, fecha, presentación y disponibilidad.</p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='soft-card'>", unsafe_allow_html=True)
    st.subheader("Dónde conviene comprar")
    store_compare = compare_stores_for_cart(local_df, st.session_state.cart)
    if store_compare.empty:
        st.info("Agrega productos para comparar tiendas.")
    else:
        view = store_compare.head(8).copy()
        view["Total si compras ahí"] = view["Total si compras ahí"].map(lambda x: "-" if pd.isna(x) else currency(float(x)))
        st.dataframe(view, use_container_width=True, hide_index=True)
        best = store_compare.iloc[0]
        st.caption(f"Mejor opción aproximada: {best['Tienda']}")
    st.markdown("</div>", unsafe_allow_html=True)

    map_df = local_df.dropna(subset=["lat", "lon"])[["lat", "lon", "display_store", "address"]].drop_duplicates().head(250)
    if not map_df.empty:
        with st.expander("Ver tiendas en mapa"):
            st.map(map_df.rename(columns={"lat": "latitude", "lon": "longitude"}))

st.markdown("<div class='soft-card'>", unsafe_allow_html=True)
st.subheader("3. Ideas de platillos con tu presupuesto")
if not st.session_state.cart:
    st.info("Cuando agregues productos, aquí aparecerán platillos sugeridos y un plan por día.")
else:
    suggestions = recipe_suggestions(local_df, st.session_state.cart, remaining)
    top_suggestions = suggestions.head(10).copy()
    top_suggestions["Extra estimado"] = top_suggestions["Extra estimado"].map(currency)
    st.dataframe(top_suggestions, use_container_width=True, hide_index=True)

    plan = build_meal_plan(suggestions, int(days))
    st.write("Plan simple sugerido")
    st.dataframe(plan, use_container_width=True, hide_index=True)

    st.caption(
        "El costo por platillo es aproximado porque los datos públicos no siempre permiten convertir con precisión por gramo, kilo o pieza. La app lo usa como guía práctica, no como precio final garantizado."
    )
st.markdown("</div>", unsafe_allow_html=True)

with st.expander("Notas importantes"):
    st.markdown(
        """
        - Esta app usa precios de referencia. El precio final puede cambiar en tienda.
        - Si conectas un CSV de PROFECO, la app intenta detectar automáticamente columnas como producto, precio, tienda, estado, municipio y dirección.
        - Para producción, revisa cada mes el dataset más reciente o pega una nueva URL CSV.
        - La donación es voluntaria y está pensada como apoyo secundario para mantener la herramienta.
        """
    )
