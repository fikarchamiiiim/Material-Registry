# Material Registry — Odoo 14 Backend Test

## Setup

### 1. Run PostgreSQL

```bash
docker compose up -d db
```

### 2. Inisialisasi database dan install modul

```bash
docker compose run --rm odoo odoo -d material_db -i base \
    --stop-after-init --without-demo=all

docker compose run --rm odoo odoo -d material_db -i material_registry \
    --stop-after-init --without-demo=all
```

### 3. Jalankan Odoo

```bash
docker compose up -d odoo
```

Buka `http://localhost:8069`.

- Login: `admin`
- Password: `admin`

## Dokumentasi API

### Autentikasi

```bash
curl -i -c cookies.txt -X POST http://localhost:8069/web/session/authenticate \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","params":{"db":"material_db","login":"admin","password":"admin"}}'
```

Semua request berikutnya menggunakan cookie tersebut (`-b cookies.txt`). Jika belum login, Odoo akan mengalihkan ke halaman login (bukan 401 JSON).

### Endpoint

| Method | Endpoint | Sukses | Error |
|---|---|---|---|
| GET | `/api/materials` | 200 | 400 (material_type invalid) |
| GET | `/api/materials?material_type=jeans` | 200 | 400 |
| GET | `/api/materials/<id>` | 200 | 404 |
| POST | `/api/materials` | 201 | 400 (validasi), 409 (kode kembar) |
| PUT/PATCH | `/api/materials/<id>` | 200 | 400, 404, 409 |
| DELETE | `/api/materials/<id>` | 200 | 404 |
| GET | `/api/suppliers` | 200 | - |

### Payload create

```json
{
  "code": "MAT-001",
  "name": "Katun Premium",
  "material_type": "cotton",
  "buy_price": 150.0,
  "supplier_id": 1
}
```

`material_type` hanya `fabric`, `jeans`, atau `cotton`.

### Response sukses

```json
{
  "id": 1,
  "code": "OBJ-001",
  "name": "Katun",
  "material_type": "cotton",
  "buy_price": 150.0,
  "supplier": {"id": 1, "name": "PT Kain"}
}
```

### Response error

```json
{
  "error": "Validation failed",
  "details": {"buy_price": "must be >= 100"}
}
```

### Contoh curl

```bash
# Daftar supplier (untuk mendapatkan supplier_id)
curl -b cookies.txt http://localhost:8069/api/suppliers

# Create
curl -b cookies.txt -X POST http://localhost:8069/api/materials \
  -H 'Content-Type: text/plain' \
  -d '{"code":"MAT-001","name":"Katun Premium","material_type":"cotton","buy_price":150,"supplier_id":1}'

# List semua
curl -b cookies.txt http://localhost:8069/api/materials

# Filter by type
curl -b cookies.txt "http://localhost:8069/api/materials?material_type=cotton"

# Detail
curl -b cookies.txt http://localhost:8069/api/materials/1

# Update parsial
curl -b cookies.txt -X PUT http://localhost:8069/api/materials/1 \
  -H 'Content-Type: text/plain' \
  -d '{"buy_price":175}'

# Delete
curl -b cookies.txt -X DELETE http://localhost:8069/api/materials/1

# Validasi: harga 99 harus 400
curl -b cookies.txt -X POST http://localhost:8069/api/materials \
  -H 'Content-Type: text/plain' \
  -d '{"code":"MAT-002","name":"X","material_type":"jeans","buy_price":99,"supplier_id":1}'
```

## Menjalankan Test

```bash
docker compose run --rm odoo odoo -d test_db -i material_registry \
    --test-enable --test-tags /material_registry \
    --stop-after-init --log-level=test --without-demo=all
```

## ERD

![ERD Material Registry](docs/erd.png)

Sumber: [`docs/ERD.md`](docs/ERD.md) (Mermaid + DBML).

Relasi: satu supplier memiliki banyak material (1:N); satu material dimiliki tepat satu supplier.
