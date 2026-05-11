from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
from flask import make_response
from reportlab.pdfgen import canvas
from io import BytesIO
from flask import make_response
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
from io import BytesIO

app = Flask(__name__)
app.secret_key = 'sistema_contable_secreto'

# MYSQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'sistema_contable'

mysql = MySQL(app)

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

    cursor = mysql.connection.cursor()

    cursor.execute("""
        INSERT INTO usuarios
        (nombres, apellidos, correo, celular, usuario, rol, password)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (nombres, apellidos, correo, celular, usuario, rol, password))

    mysql.connection.commit()

    cursor.close()

    return "Usuario registrado correctamente"

# VALIDAR LOGIN
@app.route('/validar_login', methods=['POST'])
def validar_login():

    usuario = request.form['usuario']
    password = request.form['password']

    cursor = mysql.connection.cursor()

    cursor.execute("""
        SELECT * FROM usuarios
        WHERE usuario=%s AND password=%s
    """, (usuario, password))

    cuenta = cursor.fetchone()

    cursor.close()

    if cuenta:

        session['usuario'] = usuario
        session['rol'] = cuenta[6]
     
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

        cursor = mysql.connection.cursor()

        cursor.execute("SELECT * FROM usuarios")

        usuarios = cursor.fetchall()

        cursor.close()

        return render_template('usuarios.html', usuarios=usuarios)

    return redirect(url_for('login'))

# EDITAR USUARIO
@app.route('/editar_usuario/<int:id>')
def editar_usuario(id):

    if 'usuario' in session:

        cursor = mysql.connection.cursor()

        cursor.execute("SELECT * FROM usuarios WHERE id=%s", (id,))

        usuario = cursor.fetchone()

        cursor.close()

        return render_template('editar_usuario.html', usuario=usuario)

    return redirect(url_for('login'))

# ACTUALIZAR USUARIO
@app.route('/actualizar_usuario/<int:id>', methods=['POST'])
def actualizar_usuario(id):

    nombres = request.form['nombres']
    apellidos = request.form['apellidos']
    correo = request.form['correo']
    usuario = request.form['usuario']
    rol = request.form['rol']

    cursor = mysql.connection.cursor()

    cursor.execute("""
        UPDATE usuarios
        SET nombres=%s,
            apellidos=%s,
            correo=%s,
            usuario=%s,
            rol=%s
        WHERE id=%s
    """, (nombres, apellidos, correo, usuario, rol, id))

    mysql.connection.commit()

    cursor.close()

    return redirect(url_for('usuarios'))

# ELIMINAR USUARIO
@app.route('/eliminar_usuario/<int:id>')
def eliminar_usuario(id):

    if 'usuario' in session:

        cursor = mysql.connection.cursor()

        cursor.execute("DELETE FROM usuarios WHERE id=%s", (id,))

        mysql.connection.commit()

        cursor.close()

        return redirect(url_for('usuarios'))

    return redirect(url_for('login'))

# PLAN DE CUENTAS
@app.route('/plan_cuentas')
def plan_cuentas():

    if 'usuario' in session:

        cursor = mysql.connection.cursor()

        cursor.execute("""
    SELECT * FROM plan_cuentas
    ORDER BY codigo ASC
""")

        cuentas = cursor.fetchall()

        cursor.close()

        return render_template('plan_cuentas.html', cuentas=cuentas)

    return redirect(url_for('login'))

# GUARDAR CUENTA
@app.route('/guardar_cuenta', methods=['POST'])
def guardar_cuenta():

    codigo = request.form['codigo']
    nombre = request.form['nombre']
    tipo = request.form['tipo']
    naturaleza = request.form['naturaleza']

    cursor = mysql.connection.cursor()

    cursor.execute("""
        INSERT INTO plan_cuentas
        (codigo, nombre, tipo, naturaleza)
        VALUES (%s, %s, %s, %s)
    """, (codigo, nombre, tipo, naturaleza))

    mysql.connection.commit()

    cursor.close()

    return redirect(url_for('plan_cuentas'))

# COMPROBANTES
@app.route('/comprobantes')
def comprobantes():

    if 'usuario' in session:

        cursor = mysql.connection.cursor()

        # OBTENER COMPROBANTES
        cursor.execute("SELECT * FROM comprobantes")
        comprobantes = cursor.fetchall()

        # OBTENER CUENTAS
        cursor.execute("SELECT * FROM plan_cuentas")
        cuentas = cursor.fetchall()

        cursor.close()

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

    cursor = mysql.connection.cursor()

    cursor.execute("""
        INSERT INTO comprobantes
        (fecha, cuenta, detalle, debe, haber)
        VALUES (%s, %s, %s, %s, %s)
    """, (fecha, cuenta, detalle, debe, haber))

    mysql.connection.commit()

    cursor.close()

    return redirect(url_for('comprobantes'))

# LIBRO DIARIO
@app.route('/libro_diario')
def libro_diario():

    if 'usuario' in session:

        cursor = mysql.connection.cursor()

        cursor.execute("SELECT * FROM comprobantes")

        movimientos = cursor.fetchall()

        # TOTAL DEBE
        cursor.execute("""
            SELECT SUM(debe)
            FROM comprobantes
        """)

        total_debe = cursor.fetchone()[0]

        # TOTAL HABER
        cursor.execute("""
            SELECT SUM(haber)
            FROM comprobantes
        """)

        total_haber = cursor.fetchone()[0]

        cursor.close()

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

        cursor = mysql.connection.cursor()

        # ACTIVOS
        cursor.execute("""
            SELECT SUM(debe - haber)
            FROM comprobantes
            WHERE cuenta LIKE '1%'
        """)

        activos = cursor.fetchone()[0]

        # PASIVOS
        cursor.execute("""
            SELECT SUM(haber - debe)
            FROM comprobantes
            WHERE cuenta LIKE '2%'
        """)

        pasivos = cursor.fetchone()[0]

        # PATRIMONIO
        cursor.execute("""
            SELECT SUM(haber - debe)
            FROM comprobantes
            WHERE cuenta LIKE '3%'
        """)

        patrimonio = cursor.fetchone()[0]

        cursor.close()

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

        cursor = mysql.connection.cursor()

        cursor.execute("SELECT * FROM comprobantes")

        movimientos = cursor.fetchall()

        cursor.close()

        buffer = BytesIO()

        pdf = canvas.Canvas(buffer)

        pdf.setTitle("Libro Diario")

        y = 800

        pdf.drawString(50, y, "LIBRO DIARIO")

        y -= 40

        for movimiento in movimientos:

            texto = f"""
Fecha: {movimiento[1]} |
Cuenta: {movimiento[2]} |
Debe: {movimiento[4]} |
Haber: {movimiento[5]}
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

        cursor = mysql.connection.cursor()

        # INGRESOS
        cursor.execute("""
            SELECT SUM(haber - debe)
            FROM comprobantes
            WHERE cuenta LIKE '4%'
        """)

        ingresos = cursor.fetchone()[0] or 0

        # GASTOS
        cursor.execute("""
            SELECT SUM(debe - haber)
            FROM comprobantes
            WHERE cuenta LIKE '5%'
        """)

        gastos = cursor.fetchone()[0] or 0

        utilidad = ingresos - gastos

        cursor.close()

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

        cursor = mysql.connection.cursor()

        # INGRESOS
        cursor.execute("""
            SELECT SUM(haber - debe)
            FROM comprobantes
            WHERE cuenta LIKE '4%'
        """)

        ingresos = cursor.fetchone()[0] or 0

        # GASTOS
        cursor.execute("""
            SELECT SUM(debe - haber)
            FROM comprobantes
            WHERE cuenta LIKE '5%'
        """)

        gastos = cursor.fetchone()[0] or 0

        cursor.close()

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

        cursor = mysql.connection.cursor()

        cursor.execute("SELECT * FROM inventario")

        productos = cursor.fetchall()

        cursor.close()

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

    cursor = mysql.connection.cursor()

    cursor.execute("""
        INSERT INTO inventario
        (codigo, producto, stock, precio)
        VALUES (%s, %s, %s, %s)
    """, (codigo, producto, stock, precio))

    mysql.connection.commit()

    cursor.close()

    return redirect(url_for('inventario'))

# VENTAS
@app.route('/ventas')
def ventas():

    if 'usuario' in session:

        cursor = mysql.connection.cursor()

        # OBTENER VENTAS
        cursor.execute("SELECT * FROM ventas")
        ventas = cursor.fetchall()

        # OBTENER PRODUCTOS
        cursor.execute("SELECT * FROM inventario")
        productos = cursor.fetchall()

        cursor.close()

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

    cursor = mysql.connection.cursor()

    # GUARDAR VENTA
    cursor.execute("""
        INSERT INTO ventas
        (producto, cantidad, precio, total, fecha)
        VALUES (%s, %s, %s, %s, %s)
    """, (producto, cantidad, precio, total, fecha))

    # DESCONTAR STOCK
    cursor.execute("""
        UPDATE inventario
        SET stock = stock - %s
        WHERE producto = %s
    """, (cantidad, producto))

    mysql.connection.commit()

    cursor.close()

    return redirect(url_for('ventas'))
# CLIENTES
@app.route('/clientes')
def clientes():

    if 'usuario' in session:

        cursor = mysql.connection.cursor()

        cursor.execute("SELECT * FROM clientes")

        clientes = cursor.fetchall()

        cursor.close()

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

    cursor = mysql.connection.cursor()

    cursor.execute("""
        INSERT INTO clientes
        (nombre, ci_nit, telefono, direccion)
        VALUES (%s, %s, %s, %s)
    """, (nombre, ci_nit, telefono, direccion))

    mysql.connection.commit()

    cursor.close()

    return redirect(url_for('clientes'))

# FACTURA PDF
@app.route('/factura_pdf/<int:id_venta>')
def factura_pdf(id_venta):

    if 'usuario' in session:

        cursor = mysql.connection.cursor()

        cursor.execute("SELECT * FROM ventas WHERE id = %s", (id_venta,))

        venta = cursor.fetchone()

        cursor.close()

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
                venta[0],
                venta[1],
                venta[2],
                f"Bs. {venta[3]}",
                f"Bs. {venta[4]}"
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
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)