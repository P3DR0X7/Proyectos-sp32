import tkinter as tk
from tkinter import ttk, messagebox

import serial
import serial.tools.list_ports


arduino = None
estados = [False, False, False]
automatico = False


def buscar_puertos():
    puertos = [
        puerto.device
        for puerto in serial.tools.list_ports.comports()
    ]

    combo_puerto["values"] = puertos

    if puertos and not combo_puerto.get():
        combo_puerto.set(puertos[0])


def enviar(comando):
    if arduino and arduino.is_open:
        try:
            arduino.write((comando + "\n").encode("utf-8"))
        except (serial.SerialException, OSError) as error:
            messagebox.showerror("Error de comunicación", str(error))
    else:
        messagebox.showwarning("Aviso", "Conecta primero el ESP32.")


def conectar():
    global arduino

    puerto = combo_puerto.get()

    if not puerto:
        messagebox.showwarning("Aviso", "Selecciona un puerto COM.")
        return

    try:
        if arduino and arduino.is_open:
            arduino.close()

        arduino = serial.Serial(puerto, 115200, timeout=0.05)
        ventana.after(1800, conexion_lista)

    except (serial.SerialException, OSError) as error:
        arduino = None
        messagebox.showerror("Error de conexión", str(error))


def conexion_lista():
    if arduino and arduino.is_open:
        etiqueta_conexion.config(
            text="Conectado al ESP32",
            fg="green"
        )
        boton_conectar.config(state="disabled")
        combo_puerto.config(state="disabled")


def iniciar_ciclo():
    global automatico

    if not arduino or not arduino.is_open:
        messagebox.showwarning("Aviso", "Conecta primero el ESP32.")
        return

    enviar("AUTO")
    automatico = True
    actualizar_interfaz()


def detener_ciclo():
    global automatico

    enviar("STOPAUTO")
    automatico = False
    actualizar_interfaz()


def cambiar_rele(numero):
    if automatico:
        messagebox.showinfo(
            "Ciclo automático",
            "Detén el ciclo automático para controlar los relés manualmente."
        )
        return

    nuevo_estado = not estados[numero]
    comando = f"{numero + 1}{'ON' if nuevo_estado else 'OFF'}"
    enviar(comando)


def actualizar_interfaz():
    for indice, boton in enumerate(botones):
        if estados[indice]:
            boton.config(
                text=f"RELÉ {indice + 1}: ENCENDIDO",
                bg="green",
                fg="white"
            )
        else:
            boton.config(
                text=f"RELÉ {indice + 1}: APAGADO",
                bg="lightgray",
                fg="black"
            )

    if automatico:
        etiqueta_modo.config(
            text="CICLO AUTOMÁTICO ACTIVO",
            fg="green"
        )
        boton_inicio.config(state="disabled")
        boton_detener.config(state="normal")
    else:
        etiqueta_modo.config(
            text="CONTROL MANUAL",
            fg="blue"
        )
        boton_inicio.config(state="normal")
        boton_detener.config(state="disabled")


def leer_serial():
    if arduino and arduino.is_open:
        try:
            while arduino.in_waiting:
                linea = arduino.readline().decode(
                    "utf-8",
                    errors="ignore"
                ).strip()

                if linea.startswith("TEMP:"):
                    valor = linea.split(":", 1)[1]
                    etiqueta_temp.config(text=f"{valor} °C")

                elif linea.startswith("LOW:"):
                    valor = linea.split(":", 1)[1]
                    etiqueta_low.config(text=f"LOW: {valor} °C")

                elif linea.startswith("HIGH:"):
                    valor = linea.split(":", 1)[1]
                    etiqueta_high.config(text=f"HIGH: {valor} °C")

                elif linea.startswith("RELES:"):
                    valores = linea.split(":", 1)[1].split(",")

                    if len(valores) == 3:
                        for indice, valor in enumerate(valores):
                            estados[indice] = (valor == "1")

                        actualizar_interfaz()

        except (serial.SerialException, OSError):
            desconectar()

    ventana.after(100, leer_serial)


def desconectar():
    global arduino, automatico

    if arduino and arduino.is_open:
        try:
            arduino.close()
        except (serial.SerialException, OSError):
            pass

    arduino = None
    automatico = False

    etiqueta_conexion.config(text="Desconectado", fg="red")
    boton_conectar.config(state="normal")
    combo_puerto.config(state="readonly")

    actualizar_interfaz()


def cerrar():
    if arduino and arduino.is_open:
        try:
            arduino.write(b"STOPAUTO\n")
        except (serial.SerialException, OSError):
            pass

    desconectar()
    ventana.destroy()


ventana = tk.Tk()
ventana.title("ESP32 - Potenciómetros y LM35")
ventana.geometry("460x570")
ventana.resizable(False, False)

tk.Label(
    ventana,
    text="CONTROL DE TEMPERATURA",
    font=("Arial", 15, "bold")
).pack(pady=12)

marco_puerto = ttk.Frame(ventana)
marco_puerto.pack(pady=4)

tk.Label(marco_puerto, text="Puerto COM:").grid(
    row=0, column=0, padx=5
)

combo_puerto = ttk.Combobox(
    marco_puerto,
    width=12,
    state="readonly"
)
combo_puerto.grid(row=0, column=1, padx=5)

ttk.Button(
    marco_puerto,
    text="Buscar",
    command=buscar_puertos
).grid(row=0, column=2, padx=5)

boton_conectar = ttk.Button(
    ventana,
    text="Conectar",
    command=conectar
)
boton_conectar.pack(pady=5)

etiqueta_conexion = tk.Label(
    ventana,
    text="Desconectado",
    fg="red"
)
etiqueta_conexion.pack()

marco_limites = ttk.LabelFrame(
    ventana,
    text="Límites ajustados con potenciómetros"
)
marco_limites.pack(fill="x", padx=20, pady=12)

etiqueta_low = tk.Label(marco_limites, text="LOW: --.- °C")
etiqueta_low.pack(pady=4)

etiqueta_high = tk.Label(marco_limites, text="HIGH: --.- °C")
etiqueta_high.pack(pady=4)

tk.Label(
    ventana,
    text="TEMPERATURA ACTUAL",
    font=("Arial", 11, "bold")
).pack(pady=4)

etiqueta_temp = tk.Label(
    ventana,
    text="--.- °C",
    font=("Arial", 27, "bold"),
    fg="blue"
)
etiqueta_temp.pack()

marco_ciclo = ttk.Frame(ventana)
marco_ciclo.pack(pady=10)

boton_inicio = ttk.Button(
    marco_ciclo,
    text="Iniciar ciclo",
    command=iniciar_ciclo
)
boton_inicio.grid(row=0, column=0, padx=6)

boton_detener = ttk.Button(
    marco_ciclo,
    text="Detener ciclo",
    command=detener_ciclo,
    state="disabled"
)
boton_detener.grid(row=0, column=1, padx=6)

etiqueta_modo = tk.Label(
    ventana,
    text="CONTROL MANUAL",
    font=("Arial", 10, "bold"),
    fg="blue"
)
etiqueta_modo.pack(pady=4)

botones = []

for i in range(3):
    boton = tk.Button(
        ventana,
        text=f"RELÉ {i + 1}: APAGADO",
        width=28,
        height=2,
        bg="lightgray",
        command=lambda n=i: cambiar_rele(n)
    )
    boton.pack(pady=4)
    botones.append(boton)

buscar_puertos()
actualizar_interfaz()

ventana.after(100, leer_serial)
ventana.protocol("WM_DELETE_WINDOW", cerrar)
ventana.mainloop()
