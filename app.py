from flask import Flask, request, send_file, render_template
import requests
from bs4 import BeautifulSoup
import csv
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO, TextIOWrapper
from datetime import datetime

app = Flask(__name__)

def get_product_data(product_url):
    response = requests.get(product_url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')

        shipping_info = soup.find('div', class_='ui-pdp-color--BLACK ui-pdp-size--SMALL ui-pdp-family--REGULAR ui-pdp-media__title + andes-money-amount__fraction')
        full_svg = soup.find('svg', class_='ui-pdp-icon ui-pdp-icon--full ui-pdp-color--GREEN')
        seller_name = soup.find('div', class_='ui-pdp-seller__header__title').text.strip().replace('Vendido por', '').replace('Tienda oficial', '')

        breadcrumb_items = soup.find('ol', class_='andes-breadcrumb').find_all('a', class_='andes-breadcrumb__link')
        breadcrumb_values = [item.text.strip() for item in breadcrumb_items]
        tipo_factura = soup.find('p', class_='ui-pdp-color--GRAY ui-pdp-size--XXSMALL ui-pdp-family--REGULAR ui-pdp-seller__header__subtitle')

        sales_info = soup.find('ul', class_='ui-pdp-seller__list-description')
        sales_data = {}
        if sales_info:
            sales_items = sales_info.find_all('li', class_='ui-pdp-seller__item-description')
            for item in sales_items:
                strong_tag = item.find('strong', class_='ui-pdp-seller__sales-description')
                p_tag = item.find('p', class_='ui-pdp-seller__text-description')
                if strong_tag and p_tag:
                    sales_data[p_tag.text.strip()] = strong_tag.text.strip()

        attention_info = soup.find('p', class_='ui-pdp-seller__text-description')

        rating_value = soup.find('ul', class_='ui-thermometer').get('value') if soup.find('ul', class_='ui-thermometer') else None
        if not rating_value:
            rating_value = soup.find('ul', class_='ui-seller-data-status__thermometer').get('value') if soup.find('ul', class_='ui-seller-data-status__thermometer') else None

        shipping_text = shipping_info.text.strip() if shipping_info else ''
        is_full = True if full_svg else False
        attention_text = attention_info.text.strip() if attention_info else ''
        factura_type = tipo_factura.text.strip() if tipo_factura else ''
        return {
            'ENVIO': shipping_text,
            'FULL': is_full,
            'TIENDA': seller_name,
            **sales_data,
            'ATENCION': attention_text,
            'VALORACION (igual al value)': rating_value,
            'RUTA': breadcrumb_values,
            "FACTURACIÓN": factura_type
        }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    search_query = request.form['search']
    mercado_libre = 'https://listado.mercadolibre.com.ar/'
    clean_search = search_query.replace(" ", "-").strip()
    response = requests.get(mercado_libre + clean_search)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        product_containers = soup.find_all('div', class_='ui-search-result__content-wrapper')

        csv_data = BytesIO()
        text_io = TextIOWrapper(csv_data, encoding='utf-8', newline='')
        writer = csv.writer(text_io)
        writer.writerow(['PRODUCT', 'BRAND', 'RATING', 'PRECIO', 'DISCOUNT', 'Shipping text', 'FULL', 'NOMBRE VENDEDOR', 'VENTAS', 'ATENCIÓN', 'OFERTA DEL DÍA', 'MÁS VENDIDO', 'RECOMENDADO', "FACTURACIÓN",'CATEGORIA', 'URL'])

        def process_product(container):
            title_tag = container.find('a', class_='ui-search-link')
            brand_tag = container.find('span', class_='ui-search-item__brand-discoverability ui-search-item__group__element')
            rating_tag = container.find('span', class_='ui-search-reviews__rating-number')
            price_tag = container.find('span', class_='andes-money-amount ui-search-price__part ui-search-price__part--medium andes-money-amount--cents-superscript')
            price_label_tag = container.find('span', class_='ui-search-price__second-line__label')
            offer_of_day_tag = container.find('div', class_='ui-search-item__highlight-label ui-search-item__highlight-label--deal_of_the_day')
            most_selled_tag = container.find('div', class_='ui-search-item__highlight-label ui-search-item__highlight-label--best_seller')
            meli_choice_tag = container.find('div', class_='ui-search-item__highlight-label ui-search-item__highlight-label--meli_choice')

            title = title_tag.text.strip() if title_tag else ''
            brand = brand_tag.text.strip() if brand_tag else ''
            rating = rating_tag.text.strip() if rating_tag else ''
            price = price_tag.text.strip() if price_tag else ''
            price_label = price_label_tag.text.strip() if price_label_tag else ''
            product_url = title_tag['href'] if title_tag else ''
            offer_of_day = True if offer_of_day_tag else False
            most_selled = True if most_selled_tag else False
            meli_choice = True if meli_choice_tag else False

            product_data = get_product_data(product_url)
            shipping_text = product_data.get('ENVIO', '')
            is_full = product_data.get('FULL', '')
            seller_name = product_data.get('TIENDA', '')
            sales_description = product_data.get('Ventas concretadas', '')
            attention_value = product_data.get('VALORACION (igual al value)', '')
            breadcrumb_values = product_data.get('RUTA', '')
            factura_tipo = product_data.get('FACTURACIÓN', '')

            return [title, brand, rating, price, price_label, shipping_text, is_full, seller_name, sales_description, attention_value, offer_of_day, most_selled, meli_choice, factura_tipo, breadcrumb_values, product_url]

        with ThreadPoolExecutor(max_workers=5) as executor:
            results = list(executor.map(process_product, product_containers))
            writer.writerows(results)

        text_io.flush()
        csv_data.seek(0)
        
        # Generate filename
        date_str = datetime.now().strftime("%d%m%Y")
        filename = f"{clean_search}_{date_str}.csv"
        
        return send_file(BytesIO(csv_data.getvalue()), as_attachment=True, download_name=filename, mimetype='text/csv')
    else:
        return f"Error en la solicitud: {response.status_code}"

if __name__ == '__main__':
    app.run(debug=True)
