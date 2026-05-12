# AhorraDespensa

App en Streamlit para armar una lista de despensa, estimar costo local y sugerir platillos sencillos según presupuesto.

## Cómo correrla localmente

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Cómo cambiar el botón de donación

En `app.py`, reemplaza esta línea:

```python
PAYPAL_DONATION_LINK = os.getenv(
    "PAYPAL_DONATION_LINK",
    "https://www.paypal.com/donate/?hosted_button_id=REEMPLAZA_ESTO",
)
```

Por tu enlace real de PayPal, por ejemplo:

```python
PAYPAL_DONATION_LINK = "https://www.paypal.me/tuusuario"
```

O configura una variable de entorno llamada `PAYPAL_DONATION_LINK` en Streamlit Cloud.

## Fuente de datos

La app intenta conectarse al dataset público de PROFECO, `Quién es Quién en los Precios`, desde datos.gob.mx. También incluye datos de ejemplo para que puedas probarla aunque la fuente pública falle o cambie.

## Recomendación para publicar

1. Sube estos archivos a un repositorio de GitHub.
2. Entra a Streamlit Community Cloud.
3. Crea una nueva app apuntando a `app.py`.
4. Configura tu link de PayPal en Secrets o como variable de entorno.

## Limitaciones

Los precios son referencias. Pueden variar por fecha, sucursal, presentación, disponibilidad y promociones.
