import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog, colorchooser
import json, csv, os, datetime
from PIL import Image, ImageTk

BASE_PATH = os.path.dirname(__file__)
IMG_PATH = os.path.join(BASE_PATH, "img")
PROD_PATH = os.path.join(BASE_PATH, "productos.json")
EMP_PATH = os.path.join(BASE_PATH, "empleados.json")
VENTAS_PATH = os.path.join(BASE_PATH, "ventas.csv")
CATS_PATH = os.path.join(BASE_PATH, "categorias_colores.json")

def cargar_colores_categoria():
    if os.path.exists(CATS_PATH):
        with open(CATS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def guardar_colores_categoria():
    with open(CATS_PATH, "w", encoding="utf-8") as f:
        json.dump(cat_colors, f, indent=4)

cat_colors = cargar_colores_categoria()

def login():
    with open(EMP_PATH, "r", encoding="utf-8") as f:
        empleados = json.load(f)
    usuario = simpledialog.askstring("Login", "Usuario:")
    password = simpledialog.askstring("Login", "Contraseña:", show="*")
    for emp in empleados:
        if emp["usuario"] == usuario and emp["password"] == password:
            return emp["usuario"]
    messagebox.showerror("Acceso denegado", "Credenciales incorrectas")
    return login()

with open(PROD_PATH, "r", encoding="utf-8") as f:
    productos = json.load(f)

def agrupar_categorias():
    cats = {}
    for p in productos:
        cats.setdefault(p["categoria"], []).append(p)
    return cats

categorias = agrupar_categorias()
carrito = {}
usuario_actual = login()

def agregar_nuevo_producto():
    nombre = simpledialog.askstring("Agregar", "Nombre del nuevo producto:")
    if not nombre:
        return
    try:
        precio = float(simpledialog.askstring("Agregar", "Precio del producto:"))
        stock = int(simpledialog.askstring("Agregar", "Stock disponible:"))
        categoria = simpledialog.askstring("Agregar", "Categoría del producto:")
        imagen = "default.png"
        nuevo = {"nombre": nombre, "precio": precio, "stock": stock, "categoria": categoria, "imagen": imagen}
        productos.append(nuevo)
        with open(PROD_PATH, "w", encoding="utf-8") as f:
            json.dump(productos, f, indent=4)
        messagebox.showinfo("Producto agregado", "Producto guardado. Reinicia para verlo en la interfaz.")
    except:
        messagebox.showerror("Error", "Datos inválidos")

def agregar_producto(prod):
    if prod["stock"] <= 0:
        messagebox.showwarning("Sin stock", f"No hay stock para {prod['nombre']}")
        return
    nombre = prod["nombre"]
    if nombre in carrito:
        if carrito[nombre]["cantidad"] >= prod["stock"]:
            messagebox.showwarning("Stock limitado", "Has alcanzado el máximo disponible")
            return
        carrito[nombre]["cantidad"] += 1
    else:
        carrito[nombre] = {"precio": prod["precio"], "cantidad": 1}
    actualizar_carrito()


def actualizar_carrito():
    tree.delete(*tree.get_children())
    subtotal = 0
    for nombre, datos in carrito.items():
        total = datos["precio"] * datos["cantidad"]
        subtotal += total
        tree.insert("", "end", values=(nombre, datos["cantidad"], f"${datos['precio']:.2f}", f"${total:.2f}"))
    iva = subtotal * 0.16
    total = subtotal + iva
    var_sub.set(f"${subtotal:.2f}")
    var_iva.set(f"${iva:.2f}")
    var_total.set(f"${total:.2f}")

def cobrar():
    if not carrito:
        messagebox.showinfo("Vacío", "No hay productos.")
        return
    productos_vendidos = []
    for nombre, datos in carrito.items():
        for p in productos:
            if p["nombre"] == nombre:
                p["stock"] -= datos["cantidad"]
        productos_vendidos.append(f"{nombre}x{datos['cantidad']}")
    total = var_total.get().replace("$", "")
    with open(VENTAS_PATH, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([datetime.datetime.now(), usuario_actual, ", ".join(productos_vendidos), total])
    with open(PROD_PATH, "w", encoding="utf-8") as f:
        json.dump(productos, f, indent=4)
    messagebox.showinfo("Éxito", f"Venta realizada por {usuario_actual}")
    carrito.clear()
    actualizar_carrito()

def aplicar_descuento_total():
    try:
        porcentaje = simpledialog.askfloat("Descuento Global", "Porcentaje de descuento (ej. 10 para 10%)")
        if porcentaje is None: return
        for datos in carrito.values():
            datos["precio"] *= (1 - porcentaje / 100)
        actualizar_carrito()
    except:
        messagebox.showerror("Error", "Ingresa un número válido")

def aplicar_descuento_producto():
    producto = simpledialog.askstring("Descuento por Producto", "Nombre exacto del producto del carrito:")
    if not producto or producto not in carrito:
        messagebox.showerror("No encontrado", "Ese producto no está en el carrito")
        return
    try:
        porcentaje = simpledialog.askfloat("Descuento", f"Descuento para {producto} (%)")
        if porcentaje is None: return
        carrito[producto]["precio"] *= (1 - porcentaje / 100)
        actualizar_carrito()
    except:
        messagebox.showerror("Error", "Ingresa un número válido")
ventana = tk.Tk()
ventana.title("Punto de Venta")
ventana.geometry("1200x680")
ventana.configure(bg="#2c2f33")

style = ttk.Style()
style.theme_use("default")
style.configure("Treeview", background="#1e2124", foreground="white", fieldbackground="#1e2124", rowheight=28)
style.configure("Treeview.Heading", background="#4a4e54", foreground="white", font=("Arial", 10, "bold"))

frame_izq = tk.Frame(ventana, bg="#2c2f33")
frame_izq.pack(side="left", fill="y", padx=10, pady=10)

frame_der = tk.Frame(ventana, bg="#2c2f33")
frame_der.pack(side="right", fill="both", expand=True, padx=10, pady=10)

def imprimir_ticket():
    if not carrito:
        messagebox.showwarning("Carrito vacío", "No hay productos para imprimir.")
        return
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("ticket.txt", "w", encoding="utf-8") as f:
        f.write("******** TICKET DE COMPRA ********\n")
        f.write(f"Empleado: {usuario_actual}\nFecha: {now}\n\n")
        f.write("Producto\tCant.\tPrecio\tTotal\n")
        for nombre, datos in carrito.items():
            total_linea = datos["cantidad"] * datos["precio"]
            f.write(f"{nombre}\t{datos['cantidad']}\t${datos['precio']:.2f}\t${total_linea:.2f}\n")
        f.write("\n")
        f.write(f"Subtotal: {var_sub.get()}\n")
        f.write(f"IVA 16% : {var_iva.get()}\n")
        f.write(f"Total   : {var_total.get()}\n")
        f.write("*******************************\n")
    messagebox.showinfo("Ticket generado", "Archivo ticket.txt creado correctamente.")

def cambiar_color_categoria():
    categoria = simpledialog.askstring("Cambiar color", "Escribe el nombre de la categoría:")
    if not categoria or categoria not in categorias:
        messagebox.showerror("Error", "Categoría no válida")
        return
    color = colorchooser.askcolor(title="Selecciona color")[1]
    if color:
        cat_colors[categoria] = color
        guardar_colores_categoria()
        messagebox.showinfo("Guardado", f"Color actualizado para {categoria}. Reinicia para aplicar cambios.")

# Botones cuadrados tipo cubo en grid
frame_botones = tk.Frame(frame_izq, bg="#2c2f33")
frame_botones.pack(pady=(0, 10))

def modificar_producto():
    nombres = [p["nombre"] for p in productos]
    nombre = simpledialog.askstring("Modificar", "Nombre del producto a modificar:")
    if not nombre or nombre not in nombres:
        messagebox.showerror("Error", "Producto no encontrado")
        return

    for p in productos:
        if p["nombre"] == nombre:
            nuevo_nombre = simpledialog.askstring("Modificar", f"Nuevo nombre (actual: {p['nombre']}):", initialvalue=p["nombre"])
            nuevo_precio = simpledialog.askfloat("Modificar", f"Nuevo precio (actual: {p['precio']}):", initialvalue=p["precio"])
            nuevo_stock = simpledialog.askinteger("Modificar", f"Nuevo stock (actual: {p['stock']}):", initialvalue=p["stock"])
            nueva_cat = simpledialog.askstring("Modificar", f"Nueva categoría (actual: {p['categoria']}):", initialvalue=p["categoria"])
            nueva_imagen = filedialog.askopenfilename(title="Selecciona nueva imagen", filetypes=[("Imagen PNG", "*.png")])
            if nueva_imagen:
                imagen_guardada = os.path.basename(nueva_imagen)
                destino = os.path.join(IMG_PATH, imagen_guardada)
                if not os.path.exists(destino):
                    from shutil import copyfile
                    copyfile(nueva_imagen, destino)
                p["imagen"] = imagen_guardada

            p["nombre"] = nuevo_nombre
            p["precio"] = nuevo_precio
            p["stock"] = nuevo_stock
            p["categoria"] = nueva_cat

            with open(PROD_PATH, "w", encoding="utf-8") as f:
                json.dump(productos, f, indent=4)

            messagebox.showinfo("Modificado", "Producto actualizado. Reinicia para ver los cambios.")
            return


botones = [
    ("💰 Cobrar", cobrar, "#17a2b8"),
    ("🖨 Imprimir Ticket", imprimir_ticket, "#6c757d"),
    ("➕ Agregar Producto", agregar_nuevo_producto, "#6f42c1"),
    ("🎨 Color Categoría", cambiar_color_categoria, "#ffc107"),
    ("% Descuento Total", aplicar_descuento_total, "#20c997"),
    ("% Descuento Producto", aplicar_descuento_producto, "#fd7e14"),
    ("✏️ Modificar Producto", modificar_producto, "#007bff"),
]

for i, (texto, comando, color) in enumerate(botones):
    btn = tk.Button(frame_botones, text=texto, command=comando,
                    width=18, height=3, bg=color, fg="white",
                    font=("Arial", 10, "bold"), relief="raised", bd=2)
    btn.grid(row=i // 4, column=i % 4, padx=10, pady=10)  # Distribución 4 columnas

# Usuario actual y título del carrito
tk.Label(frame_izq, text=f"👤 {usuario_actual}", font=("Arial", 12),
         bg="#2c2f33", fg="white").pack(anchor="w")
tk.Label(frame_izq, text="🛒 Carrito", font=("Arial", 16, "bold"),
         bg="#2c2f33", fg="white").pack()
cols = ("Producto", "Cantidad", "Precio", "Total")
tree = ttk.Treeview(frame_izq, columns=cols, show="headings", height=20)
for col in cols:
    tree.heading(col, text=col)
    tree.column(col, anchor="center")
tree.pack()

var_sub, var_iva, var_total = tk.StringVar(), tk.StringVar(), tk.StringVar()

def etiqueta_total(lbl, var):
    tk.Label(frame_izq, text=lbl, bg="#2c2f33", fg="white", anchor="w").pack(anchor="w")
    tk.Label(frame_izq, textvariable=var, bg="#2c2f33", fg="white", font=("Arial", 12)).pack(anchor="w")

etiqueta_total("Subtotal:", var_sub)
etiqueta_total("IVA (16%):", var_iva)
etiqueta_total("Total:", var_total)

notebook = ttk.Notebook(frame_der)
notebook.pack(fill="both", expand=True)

imagenes_tk = {}
categorias = agrupar_categorias()

for cat, items in categorias.items():
    f = tk.Frame(notebook, bg="#2c2f33")
    notebook.add(f, text=cat)
    color = cat_colors.get(cat, "#6C757D")
    for i, p in enumerate(items):
        path = os.path.join(IMG_PATH, p["imagen"])
        if not os.path.exists(path):
            path = os.path.join(IMG_PATH, "default.png")
        img = Image.open(path).resize((70, 70))
        tk_img = ImageTk.PhotoImage(img)
        imagenes_tk[p["nombre"]] = tk_img
        b = tk.Button(f, image=tk_img, text=f"{p['nombre']}\n${p['precio']:.2f}\nStock: {p['stock']}", compound="top",
                     bg=color, fg="white", font=("Arial", 9, "bold"), width=140, height=140,
                     command=lambda p=p: agregar_producto(p))
        b.grid(row=i // 4, column=i % 4, padx=10, pady=10)

ventana.mainloop()
