from flask import Flask, render_template, request, redirect, url_for, session
from flask import make_response
from pymongo import MongoClient
from bson.objectid import ObjectId
from reportlab.pdfgen import canvas
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter

app = Flask(__name__)
app.secret_key = 'sistema_contable_secreto'

# MONGODB
client = MongoClient("mongodb+srv://gianfrancomendoza125038_db_user:y3VFwnxubFRJq3YN@cluster0.bmxja09.mongodb.net/")
db = client.mi_base_de_datos # Nombre de la base de datos

# LOGIN
@app.route('/')
def login():
    return render_template('index.html')

# REGISTRO
@app.route('/registro')
def registro():
    return render_template('registro.html')

# GUARDAR USUARIO
@app.route('/guardar_usuario', methods=['POST'])
def guardar_usuario():

    nombres = request.form['nombres']
    apellidos = request.form['apellidos']
    correo = request.form['correo']
    celular = request.form['celular']
    usuario = request.form['usuario']
    rol = request.form['rol']
    password = request.form['password']

    db.usuarios.insert_one({
        'nombres': nombres,
        'apellidos': apellidos,
        'correo': correo,
        'celular': celular,
        'usuario': usuario,
        'rol': rol,
        'password': password
    })

    return "Usuario registrado correctamente"

# VALIDAR LOGIN
@app.route('/validar_login', methods=['POST'])
def validar_login():

    usuario = request.form['usuario']
    password = request.form['password']

    cuenta = db.usuarios.find_one({'usuario': usuario, 'password': password})

    if cuenta:
        session['usuario'] = usuario
        session['rol'] = cuenta.get('rol', '')
     
        return render_template('dashboard.html')
    else:
        return "Usuario o contraseña incorrectos"

# DASHBOARD
@app.route('/dashboard')
def dashboard():

    if 'usuario' in session:
        return render_template('dashboard.html')

    return redirect(url_for('login'))   

# CERRAR SESIÓN
@app.route('/logout')
def logout():

    session.clear()

    return redirect(url_for('login')) 

# MOSTRAR USUARIOS
@app.route('/usuarios')
def usuarios():

    if 'usuario' in session:

        if session['rol'] != 'Administrador':
          return "Acceso denegado"

        usuarios = list(db.usuarios.find())

        return render_template('usuarios.html', usuarios=usuarios)

    return redirect(url_for('login'))

# EDITAR USUARIO
@app.route('/editar_usuario/<id>')
def editar_usuario(id):

    if 'usuario' in session:

        usuario = db.usuarios.find_one({'_id': ObjectId(id)})

        return render_template('editar_usuario.html', usuario=usuario)

    return redirect(url_for('login'))

# ACTUALIZAR USUARIO
@app.route('/actualizar_usuario/<id>', methods=['POST'])
def actualizar_usuario(id):

    nombres = request.form['nombres']
    apellidos = request.form['apellidos']
    correo = request.form['correo']
    usuario = request.form['usuario']
    rol = request.form['rol']

    db.usuarios.update_one({'_id': ObjectId(id)}, {'$set': {
        'nombres': nombres,
        'apellidos': apellidos,
        'correo': correo,
        'usuario': usuario,
        'rol': rol
    }})

    return redirect(url_for('usuarios'))

# ELIMINAR USUARIO
@app.route('/eliminar_usuario/<id>')
def eliminar_usuario(id):

    if 'usuario' in session:

        db.usuarios.delete_one({'_id': ObjectId(id)})

        return redirect(url_for('usuarios'))

    return redirect(url_for('login'))

# PLAN DE CUENTAS
@app.route('/plan_cuentas')
def plan_cuentas():

    if 'usuario' in session:

        cuentas = list(db.plan_cuentas.find().sort('codigo', 1))

        return render_template('plan_cuentas.html', cuentas=cuentas)

    return redirect(url_for('login'))

# GUARDAR CUENTA
@app.route('/guardar_cuenta', methods=['POST'])
def guardar_cuenta():

    codigo = request.form['codigo']
    nombre = request.form['nombre']
    tipo = request.form['tipo']
    naturaleza = request.form['naturaleza']

    db.plan_cuentas.insert_one({
        'codigo': codigo,
        'nombre': nombre,
        'tipo': tipo,
        'naturaleza': naturaleza
    })

    return redirect(url_for('plan_cuentas'))

# COMPROBANTES
@app.route('/comprobantes')
def comprobantes():

    if 'usuario' in session:

        comprobantes = list(db.comprobantes.find())
        cuentas = list(db.plan_cuentas.find())

        return render_template(
            'comprobantes.html',
            comprobantes=comprobantes,
            cuentas=cuentas
        )

    return redirect(url_for('login'))

# GUARDAR COMPROBANTE
@app.route('/guardar_comprobante', methods=['POST'])
def guardar_comprobante():

    fecha = request.form['fecha']
    cuenta = request.form['cuenta']
    detalle = request.form['detalle']
    debe = request.form['debe']
    haber = request.form['haber']

    db.comprobantes.insert_one({
        'fecha': fecha,
        'cuenta': cuenta,
        'detalle': detalle,
        'debe': float(debe) if debe else 0.0,
        'haber': float(haber) if haber else 0.0
    })

    return redirect(url_for('comprobantes'))

# LIBRO DIARIO
@app.route('/libro_diario')
def libro_diario():

    if 'usuario' in session:

        movimientos = list(db.comprobantes.find())

        total_debe = sum(mov.get('debe', 0) for mov in movimientos)
        total_haber = sum(mov.get('haber', 0) for mov in movimientos)

        return render_template(
            'libro_diario.html',
            movimientos=movimientos,
            total_debe=total_debe,
            total_haber=total_haber
        )

    return redirect(url_for('login'))

# BALANCE GENERAL
@app.route('/balance_general')
def balance_general():

    if 'usuario' in session:

        comprobantes = list(db.comprobantes.find())

        activos = sum((mov.get('debe', 0) - mov.get('haber', 0)) for mov in comprobantes if str(mov.get('cuenta', '')).startswith('1'))
        pasivos = sum((mov.get('haber', 0) - mov.get('debe', 0)) for mov in comprobantes if str(mov.get('cuenta', '')).startswith('2'))
        patrimonio = sum((mov.get('haber', 0) - mov.get('debe', 0)) for mov in comprobantes if str(mov.get('cuenta', '')).startswith('3'))

        return render_template(
            'balance_general.html',
            activos=activos or 0,
            pasivos=pasivos or 0,
            patrimonio=patrimonio or 0
        )

    return redirect(url_for('login'))

# EXPORTAR LIBRO DIARIO PDF
@app.route('/pdf_libro_diario')
def pdf_libro_diario():

    if 'usuario' in session:

        movimientos = list(db.comprobantes.find())

        buffer = BytesIO()

        pdf = canvas.Canvas(buffer)

        pdf.setTitle("Libro Diario")

        y = 800

        pdf.drawString(50, y, "LIBRO DIARIO")

        y -= 40

        for movimiento in movimientos:

            texto = f"""
Fecha: {movimiento.get('fecha', '')} |
Cuenta: {movimiento.get('cuenta', '')} |
Debe: {movimiento.get('debe', 0)} |
Haber: {movimiento.get('haber', 0)}
"""

            pdf.drawString(50, y, texto)

            y -= 20

        pdf.save()

        buffer.seek(0)

        response = make_response(buffer.getvalue())

        response.headers['Content-Type'] = 'application/pdf'

        response.headers['Content-Disposition'] = \
            'inline; filename=libro_diario.pdf'

        return response

    return redirect(url_for('login'))

# ESTADO DE RESULTADOS
@app.route('/estado_resultados')
def estado_resultados():

    if 'usuario' in session:

        comprobantes = list(db.comprobantes.find())

        ingresos = sum((mov.get('haber', 0) - mov.get('debe', 0)) for mov in comprobantes if str(mov.get('cuenta', '')).startswith('4'))
        gastos = sum((mov.get('debe', 0) - mov.get('haber', 0)) for mov in comprobantes if str(mov.get('cuenta', '')).startswith('5'))

        utilidad = ingresos - gastos

        return render_template(
            'estado_resultados.html',
            ingresos=ingresos,
            gastos=gastos,
            utilidad=utilidad
        )

    return redirect(url_for('login'))

# GRAFICOS FINANCIEROS
@app.route('/graficos')
def graficos():

    if 'usuario' in session:

        comprobantes = list(db.comprobantes.find())

        ingresos = sum((mov.get('haber', 0) - mov.get('debe', 0)) for mov in comprobantes if str(mov.get('cuenta', '')).startswith('4'))
        gastos = sum((mov.get('debe', 0) - mov.get('haber', 0)) for mov in comprobantes if str(mov.get('cuenta', '')).startswith('5'))

        return render_template(
            'graficos.html',
            ingresos=ingresos,
            gastos=gastos
        )

    return redirect(url_for('login'))

# INVENTARIO
@app.route('/inventario')
def inventario():

    if 'usuario' in session:

        productos = list(db.inventario.find())

        return render_template(
            'inventario.html',
            productos=productos
        )

    return redirect(url_for('login'))

# GUARDAR PRODUCTO
@app.route('/guardar_producto', methods=['POST'])
def guardar_producto():

    codigo = request.form['codigo']
    producto = request.form['producto']
    stock = request.form['stock']
    precio = request.form['precio']

    db.inventario.insert_one({
        'codigo': codigo,
        'producto': producto,
        'stock': int(stock) if stock else 0,
        'precio': float(precio) if precio else 0.0
    })

    return redirect(url_for('inventario'))

# VENTAS
@app.route('/ventas')
def ventas():

    if 'usuario' in session:

        ventas = list(db.ventas.find())
        productos = list(db.inventario.find())

        return render_template(
            'ventas.html',
            ventas=ventas,
            productos=productos
        )

    return redirect(url_for('login'))

# GUARDAR VENTA
@app.route('/guardar_venta', methods=['POST'])
def guardar_venta():

    producto = request.form['producto']
    cantidad = int(request.form['cantidad'])
    precio = float(request.form['precio'])
    fecha = request.form['fecha']

    total = cantidad * precio

    db.ventas.insert_one({
        'producto': producto,
        'cantidad': cantidad,
        'precio': precio,
        'total': total,
        'fecha': fecha
    })

    db.inventario.update_one(
        {'producto': producto},
        {'$inc': {'stock': -cantidad}}
    )

    return redirect(url_for('ventas'))
# CLIENTES
@app.route('/clientes')
def clientes():

    if 'usuario' in session:

        clientes = list(db.clientes.find())

        return render_template(
            'clientes.html',
            clientes=clientes
        )

    return redirect(url_for('login'))

# GUARDAR CLIENTE
@app.route('/guardar_cliente', methods=['POST'])
def guardar_cliente():

    nombre = request.form['nombre']
    ci_nit = request.form['ci_nit']
    telefono = request.form['telefono']
    direccion = request.form['direccion']

    db.clientes.insert_one({
        'nombre': nombre,
        'ci_nit': ci_nit,
        'telefono': telefono,
        'direccion': direccion
    })

    return redirect(url_for('clientes'))

# FACTURA PDF
@app.route('/factura_pdf/<id_venta>')
def factura_pdf(id_venta):

    if 'usuario' in session:

        venta = db.ventas.find_one({'_id': ObjectId(id_venta)})

        buffer = BytesIO()

        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=28
        )

        elementos = []

        estilos = getSampleStyleSheet()

        # TITULO
        titulo = Paragraph(
            "<font size=20><b>FACTURA EMPRESARIAL</b></font>",
            estilos['Title']
        )

        elementos.append(titulo)

        elementos.append(Spacer(1, 20))

        # DATOS EMPRESA
        empresa = Paragraph(
            """
            <b>SISTEMAS CONTABLES GYAM</b><br/>
            Dirección: La Paz - Bolivia<br/>
            Teléfono: 77777777<br/>
            NIT: 123456789
            """,
            estilos['BodyText']
        )

        elementos.append(empresa)

        elementos.append(Spacer(1, 20))

        # TABLA FACTURA
        datos = [
            ['ID', 'Producto', 'Cantidad', 'Precio', 'Total'],
            [
                str(venta.get('_id', '')),
                venta.get('producto', ''),
                venta.get('cantidad', 0),
                f"Bs. {venta.get('precio', 0)}",
                f"Bs. {venta.get('total', 0)}"
            ]
        ]

        tabla = Table(datos, colWidths=[60, 180, 80, 80, 80])

        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.darkblue),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('BACKGROUND', (0,1), (-1,-1), colors.beige),
            ('GRID', (0,0), (-1,-1), 1, colors.black)
        ]))

        elementos.append(tabla)

        elementos.append(Spacer(1, 30))
        doc.build(elementos)
        buffer.seek(0)
        response = make_response(buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename=factura_{id_venta}.pdf'
        return response
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)