# AhorraDespensa

App en Streamlit para estimar una lista de despensa, comparar precios por ubicación y proponer platillos sencillos según presupuesto.

## Ejecutar localmente

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Donaciones

Cambia el enlace de PayPal en `app.py`:

```python
PAYPAL_DONATION_LINK = "https://www.paypal.com/donate/?hosted_button_id=TU_ID_REAL"
```

También puedes usar variable de entorno:

```bash
PAYPAL_DONATION_LINK="https://www.paypal.me/tuusuario" streamlit run app.py
```

## CSV esperado

La app intenta detectar nombres de columnas comunes. Como mínimo necesita:

- producto
- precio

Recomendado:

- presentacion
- marca
- categoria
- cadena_comercial o tienda
- nombre_comercial o sucursal
- estado
- municipio
- fechaRegistro o fecha
- url, si es un precio en línea

## Nota importante

Los precios son estimados. Pueden variar por fecha, sucursal, promoción, disponibilidad, código postal o método de entrega.
