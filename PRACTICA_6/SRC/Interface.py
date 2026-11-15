
import tkinter as tk
from tkinter import ttk, messagebox
import serial
import serial.tools.list_ports

arduino = None

ventana = tk.Tk()
ventana.title("Control de temperatura ESP32")
ventana.geometry("600x650")
ventana.resizable(False, False)


tk.Label(
    ventana,
    text="CONTROL AUTOMATICO ESP32",
    font=("Arial", 18, "bold")
).pack(pady=12)


marco = ttk.LabelFrame(ventana, text="Conexion con ESP32", padding=12)
marco.pack(fill="x", padx=15, pady=8)

tk.Label(marco, text="Puerto COM:").grid(row=0, column=0, padx=5)

puerto_var = tk.StringVar()
combo = ttk.Combobox(
    marco,
    textvariable=puerto_var,
    width=15,
    state="readonly"
)
combo.grid(row=0, column=1, padx=5)

def listar_puertos():
    puertos = [
        p.device for p in serial.tools.list_ports.comports()
    ]
    combo["values"] = puertos
    if puertos:
        combo.current(0)

ttk.Button(
    marco,
    text="ACTUALIZAR PUERTOS",
    command=listar_puertos
).grid(row=0, column=2, padx=5)

marco_botones = tk.Frame(ventana)
marco_botones.pack(pady=10)

def conectar():
    global arduino

    if arduino is not None:
        return

    puerto = puerto_var.get()

    if not puerto:
        messagebox.showwarning(
            "Aviso",
            "Selecciona el puerto COM del ESP32"
        )
        return

    try:
        arduino = serial.Serial(
            puerto,
            115200,
            timeout=0.1
        )

        estado_conexion.config(
            text="CONECTADO AL ESP32",
            fg="green"
        )

        ventana.after(100, leer_serial)

    except Exception as e:
        arduino = None
        messagebox.showerror("Error", str(e))

def desconectar():
    global arduino

    if arduino is not None:
        try:
            arduino.close()
        except:
            pass

        arduino = None

    estado_conexion.config(
        text="DESCONECTADO",
        fg="red"
    )

boton_conectar = tk.Button(
    marco_botones,
    text="CONECTAR AL ESP32",
    font=("Arial", 12, "bold"),
    bg="green",
    fg="white",
    width=20,
    height=2,
    command=conectar
)
boton_conectar.grid(row=0, column=0, padx=10)

boton_desconectar = tk.Button(
    marco_botones,
    text="DESCONECTAR",
    font=("Arial", 12, "bold"),
    bg="red",
    fg="white",
    width=15,
    height=2,
    command=desconectar
)
boton_desconectar.grid(row=0, column=1, padx=10)

estado_conexion = tk.Label(
    ventana,
    text="DESCONECTADO",
    fg="red",
    font=("Arial", 12, "bold")
)
estado_conexion.pack(pady=5)


marco_sensor = ttk.LabelFrame(
    ventana,
    text="Sensor DHT11",
    padding=15
)
marco_sensor.pack(fill="x", padx=15, pady=8)

temperatura_label = tk.Label(
    marco_sensor,
    text="Temperatura: -- °C",
    font=("Arial", 22, "bold"),
    fg="red"
)
temperatura_label.pack(pady=8)

humedad_label = tk.Label(
    marco_sensor,
    text="Humedad: -- %",
    font=("Arial", 18)
)
humedad_label.pack(pady=5)


marco_limites = ttk.LabelFrame(
    ventana,
    text="Limites",
    padding=12
)
marco_limites.pack(fill="x", padx=15, pady=8)

low_label = tk.Label(
    marco_limites,
    text="LOW: 20 °C",
    font=("Arial", 14)
)
low_label.pack(pady=4)

high_label = tk.Label(
    marco_limites,
    text="HIGH: 30 °C",
    font=("Arial", 14)
)
high_label.pack(pady=4)


marco_estado = ttk.LabelFrame(
    ventana,
    text="Estado de componentes",
    padding=12
)
marco_estado.pack(fill="x", padx=15, pady=8)

estado_label = tk.Label(
    marco_estado,
    text="Estado: LOW",
    font=("Arial", 14, "bold")
)
estado_label.pack(pady=4)

servo_label = tk.Label(
    marco_estado,
    text="Servo: 180 grados",
    font=("Arial", 13)
)
servo_label.pack(pady=4)

reles_label = tk.Label(
    marco_estado,
    text="Rele 2: OFF | Rele 3: OFF",
    font=("Arial", 13)
)
reles_label.pack(pady=4)

modo_label = tk.Label(
    marco_estado,
    text="Modo: AUTOMATICO",
    font=("Arial", 13)
)
modo_label.pack(pady=4)

mensaje_label = tk.Label(
    ventana,
    text="Esperando conexion...",
    font=("Arial", 10)
)
mensaje_label.pack(pady=8)


def procesar_dato(dato):
    dato = dato.strip()

    if dato.startswith("TEMP:"):
        valor = dato.replace("TEMP:", "")
        temperatura_label.config(
            text=f"Temperatura: {valor} °C"
        )

    elif dato.startswith("HUM:"):
        valor = dato.replace("HUM:", "")
        humedad_label.config(
            text=f"Humedad: {valor} %"
        )

    elif dato.startswith("LIMITES:"):
        valores = dato.replace("LIMITES:", "").split(",")
        if len(valores) == 2:
            low_label.config(text=f"LOW: {valores[0]} °C")
            high_label.config(text=f"HIGH: {valores[1]} °C")

    elif dato == "ESTADO:HIGH":
        estado_label.config(text="Estado: HIGH")

    elif dato == "ESTADO:LOW":
        estado_label.config(text="Estado: LOW")

    elif dato == "ESTADO:DETENIDO":
        estado_label.config(text="Estado: DETENIDO")

    elif dato.startswith("ANGULO_OBJETIVO:"):
        valor = dato.split(":")[1]
        servo_label.config(text=f"Servo: {valor} grados")

    elif dato.startswith("RELES:"):
        valores = dato.replace("RELES:", "").split(",")
        if len(valores) == 2:
            reles_label.config(
                text=f"Rele 2: {valores[0]} | Rele 3: {valores[1]}"
            )

    elif dato == "MODO_AUTO":
        modo_label.config(text="Modo: AUTOMATICO")

    elif dato == "MODO_DETENIDO":
        modo_label.config(text="Modo: DETENIDO")

    elif dato == "ERROR_SENSOR":
        mensaje_label.config(
            text="ERROR: Revisar sensor DHT11",
            fg="red"
        )

    elif dato == "SISTEMA_INICIADO":
        mensaje_label.config(
            text="ESP32 iniciado correctamente",
            fg="green"
        )


def leer_serial():
    global arduino

    if arduino is None:
        return

    try:
        while arduino.in_waiting:
            dato = arduino.readline().decode(
                "utf-8",
                errors="ignore"
            ).strip()

            if dato:
                procesar_dato(dato)

    except Exception as e:
        desconectar()
        messagebox.showerror("Error de comunicacion", str(e))
        return

    ventana.after(100, leer_serial)

def cerrar():
    desconectar()
    ventana.destroy()

ventana.protocol("WM_DELETE_WINDOW", cerrar)

listar_puertos()
ventana.mainloop()
