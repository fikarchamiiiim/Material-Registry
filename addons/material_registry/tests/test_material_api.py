# -*- coding: utf-8 -*-
import json

from odoo import tools
from odoo.tests.common import HOST, HttpCase, tagged
from odoo.tools import mute_logger


@tagged('post_install', '-at_install')
class TestMaterialApi(HttpCase):

    def setUp(self):
        super().setUp()
        self.supplier = self.env['material.supplier'].create(
            {'name': 'PT Kain Jaya'})
        self.env['res.users'].create({
            'name': 'API Tester',
            'login': 'api_tester',
            'password': 'api_tester',
            'groups_id': [(6, 0, [self.env.ref('base.group_user').id])],
        })
        self.authenticate('api_tester', 'api_tester')
        self.payload = {
            'code': 'MAT-001',
            'name': 'Katun Premium',
            'material_type': 'cotton',
            'buy_price': 150,
            'supplier_id': self.supplier.id,
        }

    def url(self, path):
        return 'http://%s:%s%s' % (HOST, tools.config['http_port'], path)

    def call(self, method, path, payload=None):
        kwargs = {}
        if payload is not None:
            kwargs['data'] = json.dumps(payload)
            kwargs['headers'] = {'Content-Type': 'text/plain'}
        return self.opener.request(method, self.url(path), timeout=10, **kwargs)

    def create_material(self, **overrides):
        return self.call('POST', '/api/materials', dict(self.payload, **overrides))

    def test_create_success(self):
        res = self.create_material()
        self.assertEqual(res.status_code, 201)
        body = res.json()
        self.assertEqual(body['code'], 'MAT-001')
        self.assertEqual(body['supplier']['id'], self.supplier.id)

    def test_create_price_below_100_returns_400(self):
        res = self.create_material(buy_price=99)
        self.assertEqual(res.status_code, 400)
        self.assertIn('buy_price', res.json()['details'])

    def test_create_missing_field_returns_400(self):
        payload = dict(self.payload)
        del payload['name']
        res = self.call('POST', '/api/materials', payload)
        self.assertEqual(res.status_code, 400)
        self.assertIn('name', res.json()['details'])

    def test_create_invalid_type_returns_400(self):
        res = self.create_material(material_type='silk')
        self.assertEqual(res.status_code, 400)

    def test_create_unknown_supplier_returns_400(self):
        res = self.create_material(supplier_id=999999)
        self.assertEqual(res.status_code, 400)

    @mute_logger('odoo.sql_db')
    def test_create_duplicate_code_returns_409(self):
        self.assertEqual(self.create_material().status_code, 201)
        res = self.create_material(name='Lain')
        self.assertEqual(res.status_code, 409)

    def test_failed_create_leaves_no_record(self):
        self.create_material(buy_price=99)
        count = self.env['material.material'].search_count([])
        self.assertEqual(count, 0)

    def test_list_and_filter_by_type(self):
        self.create_material(code='A', material_type='fabric')
        self.create_material(code='B', material_type='jeans')
        self.create_material(code='C', material_type='jeans')

        all_res = self.call('GET', '/api/materials').json()
        self.assertEqual(all_res['count'], 3)

        jeans = self.call('GET', '/api/materials?material_type=jeans').json()
        self.assertEqual(jeans['count'], 2)
        self.assertTrue(
            all(material['material_type'] == 'jeans' for material in jeans['data']))

    def test_filter_invalid_type_returns_400(self):
        res = self.call('GET', '/api/materials?material_type=silk')
        self.assertEqual(res.status_code, 400)

    def test_get_one_and_not_found(self):
        created = self.create_material().json()
        ok = self.call('GET', '/api/materials/%d' % created['id'])
        self.assertEqual(ok.status_code, 200)
        self.assertEqual(ok.json()['code'], 'MAT-001')

        missing = self.call('GET', '/api/materials/999999')
        self.assertEqual(missing.status_code, 404)

    def test_update_success(self):
        material_id = self.create_material().json()['id']
        res = self.call('PUT', '/api/materials/%d' % material_id,
                        {'name': 'Katun Super', 'buy_price': 300})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['name'], 'Katun Super')
        self.assertEqual(res.json()['buy_price'], 300)

    def test_update_price_below_100_returns_400_and_keeps_old_value(self):
        material_id = self.create_material().json()['id']
        res = self.call('PUT', '/api/materials/%d' % material_id, {'buy_price': 50})
        self.assertEqual(res.status_code, 400)
        rec = self.env['material.material'].browse(material_id)
        rec.invalidate_cache()
        self.assertEqual(rec.buy_price, 150)

    def test_update_not_found_returns_404(self):
        res = self.call('PUT', '/api/materials/999999', {'name': 'X'})
        self.assertEqual(res.status_code, 404)

    def test_delete_success_and_not_found(self):
        material_id = self.create_material().json()['id']
        res = self.call('DELETE', '/api/materials/%d' % material_id)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(
            self.call('GET', '/api/materials/%d' % material_id).status_code, 404)
        self.assertEqual(
            self.call('DELETE', '/api/materials/%d' % material_id).status_code, 404)
