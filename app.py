from flask import Flask, render_template, request, redirect, url_for, session
import requests
import os
import uuid

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# Backend API URL
BACKEND_URL = os.getenv('BACKEND_URL', 'http://localhost:5000')

def get_session_id():
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    return session['session_id']

def api_request(method, endpoint, **kwargs):
    url = f"{BACKEND_URL}{endpoint}"
    headers = kwargs.pop('headers', {})
    headers['X-Session-ID'] = get_session_id()

    try:
        response = requests.request(method, url, headers=headers, **kwargs)
        return response
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        return None

@app.route('/')
def index():
    response = api_request('GET', '/api/products')

    if response and response.status_code == 200:
        products = response.json()
    else:
        products = []

    return render_template('index.html', products=products)

@app.route('/products')
def products():
    category = request.args.get('category')
    search = request.args.get('search')

    params = {}
    if category:
        params['category'] = category
    if search:
        params['search'] = search

    response = api_request('GET', '/api/products', params=params)

    if response and response.status_code == 200:
        products_list = response.json()
    else:
        products_list = []

    return render_template('products.html',
                         products=products_list,
                         category=category,
                         search=search)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    response = api_request('GET', f'/api/products/{product_id}')

    if response and response.status_code == 200:
        product = response.json()
        return render_template('product_detail.html', product=product)
    else:
        return "Product not found", 404

@app.route('/cart')
def cart():
    response = api_request('GET', '/api/cart')

    if response and response.status_code == 200:
        cart_data = response.json()
    else:
        cart_data = {'items': [], 'total': 0, 'item_count': 0}

    return render_template('cart.html', cart=cart_data)

@app.route('/add-to-cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    quantity = int(request.form.get('quantity', 1))

    response = api_request('POST', '/api/cart',
                          json={'product_id': product_id, 'quantity': quantity})

    return redirect(url_for('cart'))

@app.route('/remove-from-cart/<int:product_id>', methods=['POST'])
def remove_from_cart(product_id):
    api_request('DELETE', f'/api/cart/{product_id}')
    return redirect(url_for('cart'))

@app.route('/checkout')
def checkout():
    response = api_request('GET', '/api/cart')

    if response and response.status_code == 200:
        cart_data = response.json()
    else:
        cart_data = {'items': [], 'total': 0}

    if not cart_data['items']:
        return redirect(url_for('cart'))

    return render_template('checkout.html', cart=cart_data)

@app.route('/place-order', methods=['POST'])
def place_order():
    shipping_address = request.form.get('shipping_address')
    payment_method = request.form.get('payment_method')

    response = api_request('POST', '/api/checkout',
                          json={'shipping_address': shipping_address})

    if response and response.status_code == 200:
        order_data = response.json()
        return render_template('order_confirmation.html', order=order_data)
    else:
        return "Checkout failed", 400

@app.route('/order/<int:order_id>')
def order_detail(order_id):
    response = api_request('GET', f'/api/orders/{order_id}')

    if response and response.status_code == 200:
        order = response.json()
        return render_template('order_detail.html', order=order)
    else:
        return "Order not found", 404

@app.route('/health')
def health():
    return {'status': 'healthy', 'service': 'frontend'}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
