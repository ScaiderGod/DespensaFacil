# AhorraDespensa

App en Streamlit para estimar una lista de despensa, comparar precios por tienda/fuente y generar ideas simples de platillos según presupuesto, personas y días.

## Ejecutar localmente

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Donaciones

Edita la variable `PAYPAL_DONATION_LINK` en `app.py` o crea una variable de entorno con ese nombre.

## Precios

La app intenta usar recursos públicos de PROFECO. Si la fuente falla o no está disponible, usa datos de ejemplo para no romper la experiencia.

También puedes cargar un CSV propio con columnas como:

- producto
- precio
- tienda o cadena_comercial
- sucursal o nombre_comercial
- estado
- municipio
- fecha_registro o fechaRegistro
- marca
- presentacion
