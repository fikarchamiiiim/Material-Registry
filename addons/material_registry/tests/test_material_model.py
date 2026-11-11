# -*- coding: utf-8 -*-
from psycopg2 import IntegrityError

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase, tagged
from odoo.tools import mute_logger


@tagged('post_install', '-at_install')
class TestMaterialModel(TransactionCase):

    def setUp(self):
        super().setUp()
        self.Material = self.env['material.material']
        self.supplier = self.env['material.supplier'].create(
            {'name': 'PT Kain Jaya'})
        self.vals = {
            'code': 'MAT-001',
            'name': 'Katun Premium',
            'material_type': 'cotton',
            'buy_price': 150.0,
            'supplier_id': self.supplier.id,
        }

    def test_create_valid_material(self):
        rec = self.Material.create(self.vals)
        self.assertEqual(rec.code, 'MAT-001')
        self.assertEqual(rec.material_type, 'cotton')
        self.assertEqual(rec.supplier_id, self.supplier)

    def test_buy_price_below_100_rejected(self):
        with self.assertRaises(ValidationError):
            self.Material.create(dict(self.vals, buy_price=99.99))

    def test_buy_price_exactly_100_accepted(self):
        rec = self.Material.create(dict(self.vals, buy_price=100.0))
        self.assertEqual(rec.buy_price, 100.0)

    def test_update_price_below_100_rejected(self):
        rec = self.Material.create(self.vals)
        with self.assertRaises(ValidationError):
            rec.write({'buy_price': 50})

    def test_blank_name_rejected(self):
        with self.assertRaises(ValidationError):
            self.Material.create(dict(self.vals, name='   '))

    def test_blank_code_rejected(self):
        with self.assertRaises(ValidationError):
            self.Material.create(dict(self.vals, code=''))

    @mute_logger('odoo.sql_db')
    def test_missing_supplier_rejected(self):
        vals = dict(self.vals)
        del vals['supplier_id']
        with self.assertRaises(IntegrityError):
            self.Material.create(vals)

    @mute_logger('odoo.sql_db')
    def test_missing_material_type_rejected(self):
        vals = dict(self.vals)
        del vals['material_type']
        with self.assertRaises(IntegrityError):
            self.Material.create(vals)

    def test_invalid_material_type_rejected(self):
        with self.assertRaises(ValueError):
            self.Material.create(dict(self.vals, material_type='silk'))

    def test_all_three_types_accepted(self):
        for index, material_type in enumerate(('fabric', 'jeans', 'cotton')):
            rec = self.Material.create(
                dict(self.vals, code='MAT-T%d' % index, material_type=material_type))
            self.assertEqual(rec.material_type, material_type)

    @mute_logger('odoo.sql_db')
    def test_duplicate_code_rejected(self):
        self.Material.create(self.vals)
        with self.assertRaises(IntegrityError):
            self.Material.create(dict(self.vals, name='Lain'))

    def test_search_filter_by_type(self):
        self.Material.create(dict(self.vals, code='A', material_type='fabric'))
        self.Material.create(dict(self.vals, code='B', material_type='jeans'))
        self.Material.create(dict(self.vals, code='C', material_type='jeans'))
        jeans = self.Material.search([('material_type', '=', 'jeans')])
        self.assertEqual(len(jeans), 2)
        self.assertTrue(all(rec.material_type == 'jeans' for rec in jeans))

    def test_update_material(self):
        rec = self.Material.create(self.vals)
        rec.write({'name': 'Katun Super', 'buy_price': 300})
        self.assertEqual(rec.name, 'Katun Super')
        self.assertEqual(rec.buy_price, 300)

    def test_delete_material(self):
        rec = self.Material.create(self.vals)
        rec.unlink()
        self.assertFalse(rec.exists())

    def test_supplier_with_materials_cannot_be_deleted(self):
        self.Material.create(self.vals)
        with mute_logger('odoo.sql_db'), self.assertRaises(IntegrityError):
            self.supplier.unlink()
