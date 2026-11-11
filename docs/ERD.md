# ERD — Modul Registrasi Material

## Mermaid

```mermaid
erDiagram
    MATERIAL_SUPPLIER ||--|{ MATERIAL_MATERIAL : "supplies"

    MATERIAL_SUPPLIER {
        int id PK
        varchar name "NOT NULL"
    }

    MATERIAL_MATERIAL {
        int id PK
        varchar code "NOT NULL, UNIQUE"
        varchar name "NOT NULL"
        varchar material_type "NOT NULL, fabric|jeans|cotton"
        numeric buy_price "NOT NULL, >= 100"
        int supplier_id FK "NOT NULL"
    }
```

## Gambar

![ERD Material Registry](erd.png)

## Keterangan

| Tabel | Kolom | Key / Constraint |
|---|---|---|
| `material_supplier` | `id`, `name` | `id` PK |
| `material_material` | `id`, `code`, `name`, `material_type`, `buy_price`, `supplier_id` | `id` PK, `code` UNIQUE, `supplier_id` FK → `material_supplier.id` |

- Relasi: satu supplier memiliki banyak material (1:N); satu material dimiliki tepat satu supplier.
- `material_type` hanya berisi `fabric`, `jeans`, atau `cotton`.
- `buy_price` tidak boleh kurang dari 100.
- Semua kolom wajib terisi (`NOT NULL`).
