import pymongo

# Conexión a tu base de datos de MongoDB Atlas
URI = "mongodb+srv://gianfrancomendoza125038_db_user:y3VFwnxubFRJq3YN@cluster0.bmxja09.mongodb.net/"
client = pymongo.MongoClient(URI)
db = client.mi_base_de_datos

print("Limpiando colecciones anteriores...")
db.usuarios.delete_many({})
db.plan_cuentas.delete_many({})
db.inventario.delete_many({})
db.clientes.delete_many({})
db.ventas.delete_many({})
db.comprobantes.delete_many({})

print("Insertando datos de la Juguetería...")

# 1. USUARIOS
usuarios = [
    {
        "nombres": "Gianfranco",
        "apellidos": "Mendoza",
        "correo": "admin@jugueteria.com",
        "celular": "77712345",
        "usuario": "admin",
        "rol": "Administrador",
        "password": "123"
    },
    {
        "nombres": "Ana",
        "apellidos": "López",
        "correo": "ventas@jugueteria.com",
        "celular": "77754321",
        "usuario": "vendedor",
        "rol": "Contador",
        "password": "123"
    }
]
db.usuarios.insert_many(usuarios)

# 2. PLAN DE CUENTAS
plan_cuentas = [
    {"codigo": "1000", "nombre": "ACTIVOS", "tipo": "Activo", "naturaleza": "Deudora"},
    {"codigo": "1100", "nombre": "Caja Moneda Nacional", "tipo": "Activo", "naturaleza": "Deudora"},
    {"codigo": "1110", "nombre": "Bancos", "tipo": "Activo", "naturaleza": "Deudora"},
    {"codigo": "1200", "nombre": "Inventario de Juguetes", "tipo": "Activo", "naturaleza": "Deudora"},
    {"codigo": "2000", "nombre": "PASIVOS", "tipo": "Pasivo", "naturaleza": "Acreedora"},
    {"codigo": "2100", "nombre": "Cuentas por Pagar (Proveedores)", "tipo": "Pasivo", "naturaleza": "Acreedora"},
    {"codigo": "3000", "nombre": "PATRIMONIO", "tipo": "Patrimonio", "naturaleza": "Acreedora"},
    {"codigo": "3100", "nombre": "Capital Social", "tipo": "Patrimonio", "naturaleza": "Acreedora"},
    {"codigo": "4000", "nombre": "INGRESOS", "tipo": "Ingreso", "naturaleza": "Acreedora"},
    {"codigo": "4100", "nombre": "Ventas de Juguetes", "tipo": "Ingreso", "naturaleza": "Acreedora"},
    {"codigo": "5000", "nombre": "EGRESOS", "tipo": "Egreso", "naturaleza": "Deudora"},
    {"codigo": "5100", "nombre": "Costo de Juguetes Vendidos", "tipo": "Egreso", "naturaleza": "Deudora"},
    {"codigo": "5200", "nombre": "Gastos de Alquiler y Servicios", "tipo": "Egreso", "naturaleza": "Deudora"}
]
db.plan_cuentas.insert_many(plan_cuentas)

# 3. INVENTARIO DE JUGUETES
inventario = [
    {"codigo": "JUG-001", "producto": "Oso de Peluche Gigante", "stock": 50, "precio": 120.0},
    {"codigo": "JUG-002", "producto": "Set de Bloques de Construcción", "stock": 150, "precio": 85.5},
    {"codigo": "JUG-003", "producto": "Auto a Control Remoto 4x4", "stock": 30, "precio": 250.0},
    {"codigo": "JUG-004", "producto": "Muñeca Articulada", "stock": 80, "precio": 90.0},
    {"codigo": "JUG-005", "producto": "Rompecabezas 1000 Piezas", "stock": 200, "precio": 45.0},
    {"codigo": "JUG-006", "producto": "Juego de Mesa Familiar", "stock": 60, "precio": 110.0}
]
db.inventario.insert_many(inventario)

# 4. CLIENTES
clientes = [
    {"nombre": "Juguetería El Recreo", "ci_nit": "102938475", "telefono": "22334455", "direccion": "Av. Principal 123"},
    {"nombre": "Distribuidora Kids", "ci_nit": "987654321", "telefono": "77889900", "direccion": "Calle Comercial 45"},
    {"nombre": "Familia Rodríguez", "ci_nit": "6543210", "telefono": "71122334", "direccion": "Zona Sur Alto"}
]
db.clientes.insert_many(clientes)

# 5. VENTAS (Simulando 2 ventas)
ventas = [
    {"producto": "Oso de Peluche Gigante", "cantidad": 2, "precio": 120.0, "total": 240.0, "fecha": "2026-05-10"},
    {"producto": "Auto a Control Remoto 4x4", "cantidad": 1, "precio": 250.0, "total": 250.0, "fecha": "2026-05-11"},
    {"producto": "Juego de Mesa Familiar", "cantidad": 3, "precio": 110.0, "total": 330.0, "fecha": "2026-05-11"}
]
db.ventas.insert_many(ventas)

# 6. COMPROBANTES CONTABLES (Reflejando el inicio de la empresa y las ventas)
comprobantes = [
    # Asiento de Apertura
    {"fecha": "2026-05-01", "cuenta": "1100 - Caja Moneda Nacional", "detalle": "Aporte inicial de socios", "debe": 10000.0, "haber": 0.0},
    {"fecha": "2026-05-01", "cuenta": "3100 - Capital Social", "detalle": "Aporte inicial de socios", "debe": 0.0, "haber": 10000.0},
    
    # Compra inicial de inventario
    {"fecha": "2026-05-02", "cuenta": "1200 - Inventario de Juguetes", "detalle": "Compra inicial de mercadería", "debe": 5000.0, "haber": 0.0},
    {"fecha": "2026-05-02", "cuenta": "1100 - Caja Moneda Nacional", "detalle": "Pago de mercadería inicial", "debe": 0.0, "haber": 5000.0},

    # Venta 1 (Oso de Peluche)
    {"fecha": "2026-05-10", "cuenta": "1100 - Caja Moneda Nacional", "detalle": "Venta de Osos de Peluche", "debe": 240.0, "haber": 0.0},
    {"fecha": "2026-05-10", "cuenta": "4100 - Ventas de Juguetes", "detalle": "Venta de Osos de Peluche", "debe": 0.0, "haber": 240.0},

    # Venta 2 (Auto a Control y Juegos)
    {"fecha": "2026-05-11", "cuenta": "1100 - Caja Moneda Nacional", "detalle": "Venta de Autos y Juegos de mesa", "debe": 580.0, "haber": 0.0},
    {"fecha": "2026-05-11", "cuenta": "4100 - Ventas de Juguetes", "detalle": "Venta de Autos y Juegos de mesa", "debe": 0.0, "haber": 580.0},

    # Costo de ventas (Estimación)
    {"fecha": "2026-05-11", "cuenta": "5100 - Costo de Juguetes Vendidos", "detalle": "Costo de la mercadería vendida", "debe": 400.0, "haber": 0.0},
    {"fecha": "2026-05-11", "cuenta": "1200 - Inventario de Juguetes", "detalle": "Salida de mercadería", "debe": 0.0, "haber": 400.0},
]
db.comprobantes.insert_many(comprobantes)

print("Exito! Base de datos poblada exitosamente con datos de la Jugueteria!")
print("   - Usuarios insertados: 2")
print("   - Cuentas creadas: 13")
print("   - Juguetes en inventario: 6")
print("   - Clientes registrados: 3")
print("   - Ventas realizadas: 3")
print("   - Comprobantes generados: 10")
