# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError

MIN_BUY_PRICE = 100.0

MATERIAL_TYPES = [
    ('fabric', 'Fabric'),
    ('jeans', 'Jeans'),
    ('cotton', 'Cotton'),
]


class MaterialSupplier(models.Model):
    _name = 'material.supplier'
    _description = 'Material Supplier'
    _order = 'name'

    name = fields.Char(string='Supplier Name', required=True)
    material_ids = fields.One2many(
        'material.material', 'supplier_id', string='Materials')


class Material(models.Model):
    _name = 'material.material'
    _description = 'Material'
    _order = 'code'

    code = fields.Char(string='Material Code', required=True, index=True)
    name = fields.Char(string='Material Name', required=True)
    material_type = fields.Selection(
        MATERIAL_TYPES,
        string='Material Type',
        required=True,
    )
    buy_price = fields.Float(
        string='Material Buy Price', required=True, digits=(16, 2))
    supplier_id = fields.Many2one(
        'material.supplier',
        string='Related Supplier',
        required=True,
        ondelete='restrict',
    )

    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Material code must be unique.'),
    ]

    @api.constrains('code', 'name')
    def _check_not_blank(self):
        for rec in self:
            if not (rec.code or '').strip():
                raise ValidationError('Material code must not be blank.')
            if not (rec.name or '').strip():
                raise ValidationError('Material name must not be blank.')

    @api.constrains('buy_price')
    def _check_buy_price(self):
        for rec in self:
            if rec.buy_price < MIN_BUY_PRICE:
                raise ValidationError(
                    'Material buy price must be at least %s.' % MIN_BUY_PRICE)
