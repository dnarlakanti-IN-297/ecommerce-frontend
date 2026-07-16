"""Unit tests for the frontend's server-rendered routes.

Each route proxies to the backend via api_request(); the mock_backend
fixture (conftest.py) stubs that call so these tests never need a live
backend service.
"""
from conftest import FakeResponse


SAMPLE_PRODUCT = {
    'id': 1,
    'name': 'Running Shoes',
    'description': 'Lightweight trainers',
    'price': 89.99,
    'category': 'running-shoes',
    'stock': 10,
    'rating': 4.5,
}

SAMPLE_CART = {
    'items': [{
        'product_id': 1,
        'name': 'Running Shoes',
        'price': 89.99,
        'quantity': 2,
        'image_url': None,
    }],
    'total': 179.98,
    'item_count': 2,
}


# --- health -------------------------------------------------------------

def test_health(client):
    resp = client.get('/health')
    assert resp.status_code == 200
    assert resp.get_json() == {'status': 'healthy', 'service': 'frontend'}


# --- index ----------------------------------------------------------------

def test_index_renders_products(client, mock_backend):
    mock_backend.response = FakeResponse(200, [SAMPLE_PRODUCT])
    resp = client.get('/')
    assert resp.status_code == 200
    assert b'Running Shoes' in resp.data


def test_index_falls_back_to_empty_when_backend_unavailable(client, mock_backend):
    mock_backend.response = FakeResponse(500, {})
    resp = client.get('/')
    assert resp.status_code == 200
    assert b'Running Shoes' not in resp.data


# --- products ---------------------------------------------------------------

def test_products_page_lists_products(client, mock_backend):
    mock_backend.response = FakeResponse(200, [SAMPLE_PRODUCT])
    resp = client.get('/products')
    assert resp.status_code == 200
    assert b'Running Shoes' in resp.data


def test_products_page_shows_empty_state_when_no_products(client, mock_backend):
    mock_backend.response = FakeResponse(200, [])
    resp = client.get('/products')
    assert resp.status_code == 200
    assert b'No products found' in resp.data


def test_products_page_passes_category_filter_to_backend(client, mock_backend):
    mock_backend.response = FakeResponse(200, [])
    client.get('/products?category=running-shoes')
    assert mock_backend.calls[-1]['kwargs']['params'] == {'category': 'running-shoes'}


def test_products_page_passes_search_filter_to_backend(client, mock_backend):
    mock_backend.response = FakeResponse(200, [])
    client.get('/products?search=running')
    assert mock_backend.calls[-1]['kwargs']['params'] == {'search': 'running'}


# --- product detail -------------------------------------------------------

def test_product_detail_found(client, mock_backend):
    mock_backend.response = FakeResponse(200, SAMPLE_PRODUCT)
    resp = client.get('/product/1')
    assert resp.status_code == 200
    assert b'Running Shoes' in resp.data


def test_product_detail_not_found(client, mock_backend):
    mock_backend.response = FakeResponse(404, {})
    resp = client.get('/product/9999')
    assert resp.status_code == 404


# --- cart -----------------------------------------------------------------

def test_cart_page_renders_backend_cart(client, mock_backend):
    mock_backend.response = FakeResponse(200, SAMPLE_CART)
    resp = client.get('/cart')
    assert resp.status_code == 200
    assert b'Running Shoes' in resp.data


def test_cart_page_falls_back_to_empty_cart_when_backend_unavailable(client, mock_backend):
    mock_backend.response = FakeResponse(500, {})
    resp = client.get('/cart')
    assert resp.status_code == 200
    assert b'Your cart is empty' in resp.data


def test_add_to_cart_redirects_to_cart_and_forwards_quantity(client, mock_backend):
    mock_backend.response = FakeResponse(200, {'success': True})
    resp = client.post('/add-to-cart/1', data={'quantity': '2'})
    assert resp.status_code == 302
    assert resp.headers['Location'].endswith('/cart')
    assert mock_backend.calls[-1]['kwargs']['json'] == {'product_id': 1, 'quantity': 2}


def test_remove_from_cart_redirects_to_cart(client, mock_backend):
    mock_backend.response = FakeResponse(200, {'success': True})
    resp = client.post('/remove-from-cart/1')
    assert resp.status_code == 302
    assert resp.headers['Location'].endswith('/cart')


# --- checkout / orders -----------------------------------------------------

def test_checkout_redirects_to_cart_when_empty(client, mock_backend):
    mock_backend.response = FakeResponse(200, {'items': [], 'total': 0})
    resp = client.get('/checkout')
    assert resp.status_code == 302
    assert resp.headers['Location'].endswith('/cart')


def test_checkout_renders_when_cart_has_items(client, mock_backend):
    mock_backend.response = FakeResponse(200, SAMPLE_CART)
    resp = client.get('/checkout')
    assert resp.status_code == 200


def test_place_order_success_renders_confirmation(client, mock_backend):
    mock_backend.response = FakeResponse(200, {'order_id': 42, 'success': True, 'status': 'confirmed', 'total': 89.99})
    resp = client.post('/place-order', data={'shipping_address': '123 Main St', 'payment_method': 'card'})
    assert resp.status_code == 200
    assert b'ORD-42' in resp.data


def test_place_order_failure_returns_400(client, mock_backend):
    mock_backend.response = FakeResponse(400, {'error': 'out of stock'})
    resp = client.post('/place-order', data={'shipping_address': '123 Main St'})
    assert resp.status_code == 400


def test_order_detail_found(client, mock_backend):
    mock_backend.response = FakeResponse(200, {
        'id': 42,
        'created_at': '2026-07-16T10:00:00',
        'status': 'confirmed',
        'items': [{'product_id': 1, 'quantity': 2, 'price': 89.99}],
        'total_amount': 179.98,
        'shipping_address': '123 Main St',
    })
    resp = client.get('/order/42')
    assert resp.status_code == 200
    assert b'ORD-42' in resp.data


def test_order_detail_not_found(client, mock_backend):
    mock_backend.response = FakeResponse(404, {})
    resp = client.get('/order/9999')
    assert resp.status_code == 404
