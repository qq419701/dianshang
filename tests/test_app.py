import json
import pytest
from app import create_app
from app.extensions import db as _db
from app.models.user import User, UserShopPermission
from app.models.shop import Shop
from app.models.order import Order
from app.models.notification_log import NotificationLog
from config import TestConfig


@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def db(app):
    return _db


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def admin_user(db):
    user = User(username='admin', name='Admin', role='admin',
                can_view_order=1, can_deliver=1, can_refund=1)
    user.set_password('admin123')
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def operator_user(db):
    user = User(username='operator', name='Operator', role='operator',
                can_view_order=1, can_deliver=1, can_refund=0)
    user.set_password('op123')
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def shop(db):
    s = Shop(shop_name='测试店铺', shop_code='TEST001', shop_type=1,
             is_enabled=1, notify_enabled=0)
    db.session.add(s)
    db.session.commit()
    return s


@pytest.fixture
def shop_with_notify(db):
    s = Shop(shop_name='通知店铺', shop_code='NOTIFY001', shop_type=1,
             is_enabled=1, notify_enabled=1,
             dingtalk_webhook='https://oapi.dingtalk.com/robot/send?access_token=test',
             dingtalk_secret='test_secret')
    db.session.add(s)
    db.session.commit()
    return s


@pytest.fixture
def order(db, shop):
    o = Order(order_no='ORD001', jd_order_no='JD001', shop_id=shop.id,
              shop_type=1, order_type=1, amount=10000, quantity=1,
              product_info='测试商品', produce_account='13800138000')
    db.session.add(o)
    db.session.commit()
    return o


@pytest.fixture
def card_order(db, shop):
    o = Order(order_no='ORD002', jd_order_no='JD002', shop_id=shop.id,
              shop_type=1, order_type=2, amount=20000, quantity=2,
              product_info='卡密商品')
    db.session.add(o)
    db.session.commit()
    return o


def login(client, username, password):
    return client.post('/login', data={'username': username, 'password': password},
                       follow_redirects=True)


# ---- Model Tests ----

class TestUserModel:
    def test_password_hashing(self, app, db):
        user = User(username='test', role='operator')
        user.set_password('mypassword')
        assert user.check_password('mypassword')
        assert not user.check_password('wrongpassword')

    def test_is_admin(self, app, admin_user):
        assert admin_user.is_admin is True

    def test_is_not_admin(self, app, operator_user):
        assert operator_user.is_admin is False

    def test_is_active(self, app, admin_user):
        assert admin_user.is_active is True

    def test_get_permitted_shop_ids_admin(self, app, admin_user):
        assert admin_user.get_permitted_shop_ids() is None

    def test_get_permitted_shop_ids_operator(self, app, db, operator_user, shop):
        perm = UserShopPermission(user_id=operator_user.id, shop_id=shop.id)
        db.session.add(perm)
        db.session.commit()
        ids = operator_user.get_permitted_shop_ids()
        assert shop.id in ids

    def test_has_shop_permission_admin(self, app, admin_user):
        assert admin_user.has_shop_permission(999) is True

    def test_has_shop_permission_operator(self, app, db, operator_user, shop):
        assert operator_user.has_shop_permission(shop.id) is False
        perm = UserShopPermission(user_id=operator_user.id, shop_id=shop.id)
        db.session.add(perm)
        db.session.commit()
        assert operator_user.has_shop_permission(shop.id) is True


class TestShopModel:
    def test_shop_type_label(self, app, shop):
        assert shop.shop_type_label == '游戏点卡'
        shop.shop_type = 2
        assert shop.shop_type_label == '通用交易'

    def test_to_dict(self, app, shop):
        d = shop.to_dict()
        assert d['shop_name'] == '测试店铺'
        assert d['shop_code'] == 'TEST001'


class TestOrderModel:
    def test_order_status_label(self, app, order):
        assert order.order_status_label == '待支付'
        order.order_status = 2
        assert order.order_status_label == '已完成'

    def test_amount_yuan(self, app, order):
        assert order.amount_yuan == '100.00'

    def test_card_info_parsed(self, app, card_order):
        assert card_order.card_info_parsed == []
        card_order.card_info = json.dumps([{'cardNo': '111', 'cardPwd': 'aaa'}])
        assert len(card_order.card_info_parsed) == 1

    def test_to_dict(self, app, order):
        d = order.to_dict()
        assert d['order_no'] == 'ORD001'
        assert d['amount'] == 10000


# ---- Auth Tests ----

class TestAuth:
    def test_login_page(self, client):
        resp = client.get('/login')
        assert resp.status_code == 200

    def test_login_success(self, client, admin_user):
        resp = client.post('/login', data={'username': 'admin', 'password': 'admin123'},
                           follow_redirects=True)
        assert resp.status_code == 200

    def test_login_fail(self, client, admin_user):
        resp = client.post('/login', data={'username': 'admin', 'password': 'wrong'},
                           follow_redirects=True)
        assert resp.status_code == 200
        assert '用户名或密码错误'.encode() in resp.data

    def test_logout(self, client, admin_user):
        login(client, 'admin', 'admin123')
        resp = client.get('/logout', follow_redirects=True)
        assert resp.status_code == 200

    def test_redirect_unauthenticated(self, client):
        resp = client.get('/order/')
        assert resp.status_code == 302


# ---- Order Route Tests ----

class TestOrderRoutes:
    def test_order_list(self, client, admin_user, order):
        login(client, 'admin', 'admin123')
        resp = client.get('/order/')
        assert resp.status_code == 200
        assert b'JD001' in resp.data

    def test_order_detail(self, client, admin_user, order):
        login(client, 'admin', 'admin123')
        resp = client.get(f'/order/detail/{order.id}')
        assert resp.status_code == 200

    def test_notify_success(self, client, admin_user, order):
        login(client, 'admin', 'admin123')
        resp = client.post(f'/order/notify-success/{order.id}',
                           content_type='application/json', data='{}')
        data = json.loads(resp.data)
        assert data['success'] is True
        assert order.order_status == 2

    def test_notify_refund(self, client, admin_user, order):
        login(client, 'admin', 'admin123')
        resp = client.post(f'/order/notify-refund/{order.id}',
                           content_type='application/json', data='{}')
        data = json.loads(resp.data)
        assert data['success'] is True
        assert order.order_status == 3

    def test_deliver_card(self, client, admin_user, card_order):
        login(client, 'admin', 'admin123')
        cards = [{'cardNo': '111', 'cardPwd': 'aaa'}, {'cardNo': '222', 'cardPwd': 'bbb'}]
        resp = client.post(f'/order/deliver-card/{card_order.id}',
                           content_type='application/json',
                           data=json.dumps({'cards': cards}))
        data = json.loads(resp.data)
        assert data['success'] is True
        assert card_order.order_status == 2

    def test_deliver_card_wrong_count(self, client, admin_user, card_order):
        login(client, 'admin', 'admin123')
        cards = [{'cardNo': '111', 'cardPwd': 'aaa'}]
        resp = client.post(f'/order/deliver-card/{card_order.id}',
                           content_type='application/json',
                           data=json.dumps({'cards': cards}))
        data = json.loads(resp.data)
        assert data['success'] is False

    def test_self_debug(self, client, admin_user, order):
        login(client, 'admin', 'admin123')
        resp = client.post(f'/order/self-debug/{order.id}',
                           content_type='application/json',
                           data=json.dumps({'status': 'success'}))
        data = json.loads(resp.data)
        assert data['success'] is True
        assert order.order_status == 2

    def test_self_debug_processing(self, client, admin_user, order):
        login(client, 'admin', 'admin123')
        resp = client.post(f'/order/self-debug/{order.id}',
                           content_type='application/json',
                           data=json.dumps({'status': 'processing'}))
        data = json.loads(resp.data)
        assert data['success'] is True
        assert order.order_status == 1

    def test_self_debug_failed(self, client, admin_user, order):
        login(client, 'admin', 'admin123')
        resp = client.post(f'/order/self-debug/{order.id}',
                           content_type='application/json',
                           data=json.dumps({'status': 'failed'}))
        data = json.loads(resp.data)
        assert data['success'] is True
        assert order.order_status == 3

    def test_order_filter_by_shop(self, client, admin_user, order, shop):
        login(client, 'admin', 'admin123')
        resp = client.get(f'/order/?shop_id={shop.id}')
        assert resp.status_code == 200
        assert b'JD001' in resp.data

    def test_operator_no_permission(self, client, db, operator_user, order):
        login(client, 'operator', 'op123')
        resp = client.post(f'/order/notify-refund/{order.id}',
                           content_type='application/json', data='{}')
        data = json.loads(resp.data)
        assert data['success'] is False


# ---- Shop Route Tests ----

class TestShopRoutes:
    def test_shop_list_admin(self, client, admin_user, shop):
        login(client, 'admin', 'admin123')
        resp = client.get('/shop/')
        assert resp.status_code == 200

    def test_shop_list_operator_forbidden(self, client, operator_user):
        login(client, 'operator', 'op123')
        resp = client.get('/shop/', follow_redirects=True)
        assert resp.status_code == 200  # redirected

    def test_shop_create(self, client, admin_user):
        login(client, 'admin', 'admin123')
        resp = client.post('/shop/create', data={
            'shop_name': '新店铺',
            'shop_code': 'NEW001',
            'shop_type': '1',
            'is_enabled': '1',
            'notify_enabled': '0',
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert Shop.query.filter_by(shop_code='NEW001').first() is not None

    def test_shop_edit(self, client, admin_user, shop):
        login(client, 'admin', 'admin123')
        resp = client.post(f'/shop/edit/{shop.id}', data={
            'shop_name': '修改后店铺',
            'shop_type': '2',
            'is_enabled': '1',
            'notify_enabled': '1',
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert shop.shop_name == '修改后店铺'

    def test_shop_delete(self, client, admin_user, shop):
        login(client, 'admin', 'admin123')
        resp = client.post(f'/shop/delete/{shop.id}', follow_redirects=True)
        assert resp.status_code == 200
        assert Shop.query.get(shop.id) is None


# ---- User Route Tests ----

class TestUserRoutes:
    def test_user_list(self, client, admin_user):
        login(client, 'admin', 'admin123')
        resp = client.get('/user/')
        assert resp.status_code == 200

    def test_user_create(self, client, admin_user):
        login(client, 'admin', 'admin123')
        resp = client.post('/user/create', data={
            'username': 'newuser',
            'password': 'newpass123',
            'name': 'New User',
            'role': 'operator',
            'can_view_order': '1',
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert User.query.filter_by(username='newuser').first() is not None


# ---- API Tests ----

class TestAPI:
    def test_create_order_api(self, client, shop):
        resp = client.post('/api/order/create',
                           content_type='application/json',
                           data=json.dumps({
                               'shop_code': 'TEST001',
                               'jd_order_no': 'JD_API_001',
                               'order_type': 1,
                               'amount': 5000,
                               'quantity': 1,
                               'product_info': 'API测试商品',
                               'produce_account': '13900139000',
                           }))
        data = json.loads(resp.data)
        assert data['success'] is True
        assert 'order_no' in data

    def test_create_order_invalid_shop(self, client):
        resp = client.post('/api/order/create',
                           content_type='application/json',
                           data=json.dumps({
                               'shop_code': 'INVALID',
                               'jd_order_no': 'JD_FAIL',
                               'amount': 1000,
                           }))
        data = json.loads(resp.data)
        assert data['success'] is False


# ---- Notification Service Tests ----

class TestNotificationService:
    def test_build_order_message(self, app, order, shop):
        from app.services.notification import build_order_message
        msg = build_order_message(order, shop)
        assert '新订单通知' in msg
        assert 'JD001' in msg
        assert '测试店铺' in msg

    def test_send_order_notification_disabled(self, app, db, order, shop):
        from app.services.notification import send_order_notification
        # shop.notify_enabled == 0, should not send
        send_order_notification(order, shop)
        assert NotificationLog.query.count() == 0
