
import tkinter as tk
from tkinter import ttk, messagebox
import serial
import threading

PUERTO = "COM12"
BAUDIOS = 115200

try:
    esp32 = serial.Serial(PUERTO, BAUDIOS, timeout=1)
except serial.SerialException as error:
    esp32 = None
    print("Error de conexión:", error)

datos = {
    "DIST": "24.0",
    "PCT": "0.0",
    "LITROS": "0.00",
    "HIGH": "80",
    "LOW": "20",
    "ESTADO": "INICIANDO",
    "M1": "0",
    "M2": "0"
}

ciclo_activo = True


def enviar_comando(comando):
    if esp32 and esp32.is_open:
        try:
            esp32.write((comando + "\n").encode("utf-8"))
        except (serial.SerialException, OSError):
            conexion_label.config(text="Error de comunicación")


def aplicar_limites():
    try:
        high = int(campo_high.get())
        low = int(campo_low.get())

        if not 5 <= high <= 100:
            raise ValueError("HIGH debe estar entre 5 y 100.")

        if not 0 <= low <= 95:
            raise ValueError("LOW debe estar entre 0 y 95.")

        if low >= high:
            raise ValueError("LOW debe ser menor que HIGH.")

    except ValueError as error:
        messagebox.showerror("Configuración inválida", str(error))
        return

    enviar_comando(f"HIGH={high}")
    enviar_comando(f"LOW={low}")

    datos["HIGH"] = str(high)
    datos["LOW"] = str(low)

    configuracion_label.config(
        text=f"Ciclo configurado: {low}% a {high}%"
    )


def alternar_ciclo():
    global ciclo_activo

    ciclo_activo = not ciclo_activo

    if ciclo_activo:
        enviar_comando("AUTO=1")
        boton_ciclo.config(text="Pausar ciclo")
        ciclo_label.config(text="Ciclo: ACTIVADO")
    else:
        enviar_comando("AUTO=0")
        boton_ciclo.config(text="Reanudar ciclo")
        ciclo_label.config(text="Ciclo: PAUSADO")


def actualizar_interfaz():
    distancia_label.config(
        text=f"Distancia: {datos['DIST']} cm"
    )

    porcentaje = float(datos["PCT"])
    litros = float(datos["LITROS"])

    nivel_label.config(
        text=f"Nivel de agua: {porcentaje:.1f}%"
    )

    barra["value"] = porcentaje

    litros_label.config(
        text=f"Volumen: {litros:.2f} / 2.00 litros"
    )

    estado_label.config(
        text=f"Estado: {datos['ESTADO']}"
    )

    limites_label.config(
        text=f"Límite inferior: {datos['LOW']}% | "
             f"Límite superior: {datos['HIGH']}%"
    )

    bomba1_label.config(
        text="Bomba de llenado: " +
        ("ENCENDIDA" if datos["M1"] == "1" else "APAGADA")
    )

    bomba2_label.config(
        text="Bomba de vaciado: " +
        ("ENCENDIDA" if datos["M2"] == "1" else "APAGADA")
    )


def leer_serial():
    while esp32 and esp32.is_open:
        try:
            linea = esp32.readline().decode(
                "utf-8", errors="ignore"
            ).strip()

            if not linea:
                continue

            nuevos = {}

            for parte in linea.split(","):
                if "=" in parte:
                    clave, valor = parte.split("=", 1)
                    nuevos[clave.strip()] = valor.strip()

            if "PCT" in nuevos:
                datos.update(nuevos)
                ventana.after(0, actualizar_interfaz)

        except (serial.SerialException, OSError):
            break


def cerrar():
    if esp32 and esp32.is_open:
        esp32.close()

    ventana.destroy()


ventana = tk.Tk()
ventana.title("Control cíclico del agua")
ventana.geometry("440x560")
ventana.resizable(False, False)

tk.Label(
    ventana,
    text="CONTROL AUTOMÁTICO DE AGUA",
    font=("Arial", 15, "bold")
).pack(pady=12)

distancia_label = tk.Label(
    ventana,
    text="Distancia: -- cm"
)
distancia_label.pack(pady=3)

nivel_label = tk.Label(
    ventana,
    text="Nivel de agua: --%",
    font=("Arial", 14, "bold")
)
nivel_label.pack(pady=3)

barra = ttk.Progressbar(
    ventana,
    orient="horizontal",
    length=340,
    maximum=100,
    mode="determinate"
)
barra.pack(pady=7)

litros_label = tk.Label(
    ventana,
    text="Volumen: -- litros"
)
litros_label.pack(pady=3)

ttk.Separator(ventana).pack(
    fill="x",
    padx=20,
    pady=10
)

tk.Label(
    ventana,
    text="Configurar límites del ciclo",
    font=("Arial", 12, "bold")
).pack(pady=4)

tk.Label(
    ventana,
    text="Límite superior HIGH (%)"
).pack()

campo_high = tk.Entry(
    ventana,
    justify="center",
    width=10
)
campo_high.insert(0, "80")
campo_high.pack(pady=3)

tk.Label(
    ventana,
    text="Límite inferior LOW (%)"
).pack()

campo_low = tk.Entry(
    ventana,
    justify="center",
    width=10
)
campo_low.insert(0, "20")
campo_low.pack(pady=3)

tk.Button(
    ventana,
    text="Aplicar límites",
    command=aplicar_limites
).pack(pady=7)

configuracion_label = tk.Label(
    ventana,
    text="Ciclo configurado: 20% a 80%"
)
configuracion_label.pack(pady=2)

ciclo_label = tk.Label(
    ventana,
    text="Ciclo: ACTIVADO",
    font=("Arial", 11, "bold")
)
ciclo_label.pack(pady=4)

boton_ciclo = tk.Button(
    ventana,
    text="Pausar ciclo",
    command=alternar_ciclo
)
boton_ciclo.pack(pady=4)

estado_label = tk.Label(
    ventana,
    text="Estado: INICIANDO"
)
estado_label.pack(pady=4)

limites_label = tk.Label(
    ventana,
    text="Límite inferior: 20% | Límite superior: 80%"
)
limites_label.pack(pady=3)

bomba1_label = tk.Label(
    ventana,
    text="Bomba de llenado: APAGADA"
)
bomba1_label.pack(pady=3)

bomba2_label = tk.Label(
    ventana,
    text="Bomba de vaciado: APAGADA"
)
bomba2_label.pack(pady=3)

conexion_label = tk.Label(
    ventana,
    text=f"Puerto: {PUERTO} | 115200 baudios",
    font=("Arial", 9)
)
conexion_label.pack(pady=8)

if esp32 and esp32.is_open:
    hilo = threading.Thread(
        target=leer_serial,
        daemon=True
    )
    hilo.start()
else:
    conexion_label.config(
        text=f"Sin conexión: revisa el puerto {PUERTO}"
    )

ventana.protocol("WM_DELETE_WINDOW", cerrar)
ventana.mainloop()
