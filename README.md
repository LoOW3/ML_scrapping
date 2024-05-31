# ML_scrapping
Esta aplicación sirve para obtener información relevante acerca de los productos principales que coinciden con la búsqueda que realiza el usuario.
La información se almacena en un archivo con extensión csv para posterior análisis.

# Instalación de librerías
#### Crear entorno virtual
```
python -m venv venv
```
#### Instalar librerías
```
python -m pip install --upgrade pip
python -m pip install -r requirements.txt 
```
#### Correr app

```
python -m flask run --reload
```

# Uso
- Ingresar búsqueda
- Esperar a que se realizen todas las consultas (10 segundos máximo)
- Acceder al archivo .csv generado
