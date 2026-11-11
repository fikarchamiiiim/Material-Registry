# -*- coding: utf-8 -*-
import json

from psycopg2 import IntegrityError
from werkzeug.wrappers import Response

from odoo import http
from odoo.exceptions import ValidationError
from odoo.http import request

REQUIRED_FIELDS = ['code', 'name', 'material_type', 'buy_price', 'supplier_id']
ALLOWED_FIELDS = set(REQUIRED_FIELDS)
VALID_TYPES = ('fabric', 'jeans', 'cotton')
MIN_BUY_PRICE = 100


def json_response(payload, status=200):
    return Response(
        json.dumps(payload),
        status=status,
        content_type='application/json',
    )


def error_response(message, status=400, details=None):
    body = {'error': message}
    if details:
        body['details'] = details
    return json_response(body, status)


def serialize(rec):
    return {
        'id': rec.id,
        'code': rec.code,
        'name': rec.name,
        'material_type': rec.material_type,
        'buy_price': rec.buy_price,
        'supplier': {
            'id': rec.supplier_id.id,
            'name': rec.supplier_id.name,
        },
    }


def parse_body():
    try:
        data = json.loads(request.httprequest.data or b'{}')
    except ValueError:
        return None
    return data if isinstance(data, dict) else None


def validate_payload(data, partial=False):
    errors = {}

    for key in data:
        if key not in ALLOWED_FIELDS:
            errors[key] = 'unknown field'

    if not partial:
        for field in REQUIRED_FIELDS:
            if field not in data:
                errors[field] = 'required'

    for field in ('code', 'name'):
        if field in data:
            value = data[field]
            if not isinstance(value, str) or not value.strip():
                errors[field] = 'must be a non-empty string'

    if 'material_type' in data and data['material_type'] not in VALID_TYPES:
        errors['material_type'] = 'must be one of: %s' % ', '.join(VALID_TYPES)

    if 'buy_price' in data:
        price = data['buy_price']
        if isinstance(price, bool) or not isinstance(price, (int, float)):
            errors['buy_price'] = 'must be a number'
        elif price < MIN_BUY_PRICE:
            errors['buy_price'] = 'must be >= %s' % MIN_BUY_PRICE

    if 'supplier_id' in data:
        supplier_id = data['supplier_id']
        if isinstance(supplier_id, bool) or not isinstance(supplier_id, int):
            errors['supplier_id'] = 'must be an integer id'
        elif not request.env['material.supplier'].browse(supplier_id).exists():
            errors['supplier_id'] = 'supplier not found'

    return errors


class MaterialController(http.Controller):

    @http.route('/api/materials', type='http', auth='user',
                methods=['GET'], csrf=False)
    def list_materials(self, material_type=None, **kwargs):
        if material_type and material_type not in VALID_TYPES:
            return error_response(
                'Invalid material_type',
                400,
                {'material_type': 'must be one of: %s' % ', '.join(VALID_TYPES)},
            )
        domain = [('material_type', '=', material_type)] if material_type else []
        records = request.env['material.material'].search(domain)
        return json_response({
            'count': len(records),
            'data': [serialize(rec) for rec in records],
        })

    @http.route('/api/materials/<int:material_id>', type='http', auth='user',
                methods=['GET'], csrf=False)
    def get_material(self, material_id, **kwargs):
        rec = request.env['material.material'].browse(material_id).exists()
        if not rec:
            return error_response('Material not found', 404)
        return json_response(serialize(rec))

    @http.route('/api/materials', type='http', auth='user',
                methods=['POST'], csrf=False)
    def create_material(self, **kwargs):
        data = parse_body()
        if data is None:
            return error_response('Body must be a JSON object')

        errors = validate_payload(data)
        if errors:
            return error_response('Validation failed', 400, errors)

        try:
            with request.env.cr.savepoint():
                rec = request.env['material.material'].create(data)
        except ValidationError as exc:
            return error_response('Validation failed', 400, {'detail': str(exc)})
        except IntegrityError:
            return error_response(
                'Database constraint violated (is the code already used?)', 409)

        return json_response(serialize(rec), 201)

    @http.route('/api/materials/<int:material_id>', type='http', auth='user',
                methods=['PUT', 'PATCH'], csrf=False)
    def update_material(self, material_id, **kwargs):
        rec = request.env['material.material'].browse(material_id).exists()
        if not rec:
            return error_response('Material not found', 404)

        data = parse_body()
        if not data:
            return error_response('Body must be a non-empty JSON object')

        errors = validate_payload(data, partial=True)
        if errors:
            return error_response('Validation failed', 400, errors)

        try:
            with request.env.cr.savepoint():
                rec.write(data)
        except ValidationError as exc:
            return error_response('Validation failed', 400, {'detail': str(exc)})
        except IntegrityError:
            return error_response(
                'Database constraint violated (is the code already used?)', 409)

        return json_response(serialize(rec))

    @http.route('/api/materials/<int:material_id>', type='http', auth='user',
                methods=['DELETE'], csrf=False)
    def delete_material(self, material_id, **kwargs):
        rec = request.env['material.material'].browse(material_id).exists()
        if not rec:
            return error_response('Material not found', 404)
        rec.unlink()
        return json_response({'deleted': True, 'id': material_id})

    @http.route('/api/suppliers', type='http', auth='user',
                methods=['GET'], csrf=False)
    def list_suppliers(self, **kwargs):
        suppliers = request.env['material.supplier'].search([])
        return json_response({
            'count': len(suppliers),
            'data': [{'id': supplier.id, 'name': supplier.name}
                     for supplier in suppliers],
        })
