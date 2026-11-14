
import tkinter as tk
from tkinter import ttk, messagebox
import serial
import serial.tools.list_ports

arduino = None
estados = [False, False, False]
automatico = False


def buscar_puertos():
    puertos = [
        p.device for p in serial.tools.list_ports.comports()
    ]
    combo_puerto["values"] = puertos

    if puertos and not combo_puerto.get():
        combo_puerto.set(puertos[0])


def enviar(comando):
    if arduino and arduino.is_open:
        try:
            arduino.write((comando + "\n").encode("utf-8"))
        except (serial.SerialException, OSError) as error:
            messagebox.showerror("Error", str(error))
    else:
        messagebox.showwarning(
            "Aviso", "Conecta primero el ESP32."
        )


def conectar():
    global arduino

    puerto = combo_puerto.get()

    if not puerto:
        messagebox.showwarning(
            "Aviso", "Selecciona un puerto COM."
        )
        return

    try:
        if arduino and arduino.is_open:
            arduino.close()

        arduino = serial.Serial(
            puerto, 115200, timeout=0.05
        )

        ventana.after(1800, conexion_lista)

    except (serial.SerialException, OSError) as error:
        arduino = None
        messagebox.showerror("Conexión", str(error))


def conexion_lista():
    etiqueta_conexion.config(
        text="Conectado al ESP32", fg="green"
    )
    boton_conectar.config(state="disabled")
    combo_puerto.config(state="disabled")


def aplicar_limites():
    try:
        low = float(entrada_low.get())
        high = float(entrada_high.get())

        if not (0 <= low < high <= 150):
            raise ValueError(
                "LOW debe ser menor que HIGH y ambos "
                "deben estar entre 0 y 150 °C."
            )

        enviar(f"SET:{low},{high}")

    except ValueError as error:
        messagebox.showerror("Límites incorrectos", str(error))


def iniciar_ciclo():
    global automatico

    try:
        low = float(entrada_low.get())
        high = float(entrada_high.get())

        if not (0 <= low < high <= 150):
            raise ValueError(
                "LOW debe ser menor que HIGH."
            )

    except ValueError as error:
        messagebox.showerror("Error", str(error))
        return

    if not arduino or not arduino.is_open:
        messagebox.showwarning(
            "Aviso", "Conecta primero el ESP32."
        )
        return

    enviar(f"SET:{low},{high}")
    enviar("AUTO")

    automatico = True
    actualizar_interfaz()


def detener_ciclo():
    global automatico

    enviar("STOPAUTO")
    automatico = False
    actualizar_interfaz()


def cambiar_rele(numero):
    if automatico and numero in (0, 1, 2):
        messagebox.showinfo(
            "Ciclo automático",
            "Detén el ciclo automático para controlar "
            "los relés manualmente."
        )
        return

    nuevo_estado = not estados[numero]
    comando = (
        f"{numero + 1}{'ON' if nuevo_estado else 'OFF'}"
    )

    enviar(comando)


def actualizar_interfaz():
    for i, boton in enumerate(botones):
        if estados[i]:
            boton.config(
                text=f"RELÉ {i + 1}: ENCENDIDO",
                bg="green", fg="white"
            )
        else:
            boton.config(
                text=f"RELÉ {i + 1}: APAGADO",
                bg="lightgray", fg="black"
            )

    if automatico:
        etiqueta_modo.config(
            text="CICLO AUTOMÁTICO ACTIVO", fg="green"
        )
        boton_inicio.config(state="disabled")
        boton_detener.config(state="normal")
    else:
        etiqueta_modo.config(
            text="CONTROL MANUAL", fg="blue"
        )
        boton_inicio.config(state="normal")
        boton_detener.config(state="disabled")


def leer_serial():
    if arduino and arduino.is_open:
        try:
            while arduino.in_waiting:
                linea = arduino.readline().decode(
                    "utf-8", errors="ignore"
                ).strip()

                if linea.startswith("TEMP:"):
                    valor = linea.split(":", 1)[1]
                    etiqueta_temp.config(text=f"{valor} °C")

                elif linea.startswith("RELES:"):
                    valores = linea.split(":")[1].split(",")

                    if len(valores) == 3:
                        for i, valor in enumerate(valores):
                            estados[i] = (valor == "1")

                        actualizar_interfaz()

                elif linea == "LIMITES_OK":
                    etiqueta_estado.config(
                        text="Límites aplicados correctamente",
                        fg="green"
                    )

                elif linea == "ERROR_LIMITES":
                    etiqueta_estado.config(
                        text="Error en los límites", fg="red"
                    )

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

    etiqueta_conexion.config(
        text="Desconectado", fg="red"
    )
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
ventana.title("ESP32 - HIGH / LOW y LM35")
ventana.geometry("480x620")
ventana.resizable(False, False)

tk.Label(
    ventana,
    text="CONTROL DE TEMPERATURA",
    font=("Arial", 15, "bold")
).pack(pady=12)

marco_puerto = ttk.Frame(ventana)
marco_puerto.pack(pady=4)

tk.Label(
    marco_puerto, text="Puerto COM:"
).grid(row=0, column=0, padx=5)

combo_puerto = ttk.Combobox(
    marco_puerto, width=12, state="readonly"
)
combo_puerto.grid(row=0, column=1, padx=5)

ttk.Button(
    marco_puerto, text="Buscar",
    command=buscar_puertos
).grid(row=0, column=2, padx=5)

boton_conectar = ttk.Button(
    ventana, text="Conectar", command=conectar
)
boton_conectar.pack(pady=5)

etiqueta_conexion = tk.Label(
    ventana, text="Desconectado", fg="red"
)
etiqueta_conexion.pack()


marco_limites = ttk.LabelFrame(
    ventana, text="Temperaturas en °C"
)
marco_limites.pack(fill="x", padx=20, pady=12)

tk.Label(
    marco_limites, text="LOW:"
).grid(row=0, column=0, padx=8, pady=10)

entrada_low = ttk.Entry(marco_limites, width=10)
entrada_low.insert(0, "20")
entrada_low.grid(row=0, column=1, padx=5)

tk.Label(
    marco_limites, text="HIGH:"
).grid(row=0, column=2, padx=8)

entrada_high = ttk.Entry(marco_limites, width=10)
entrada_high.insert(0, "30")
entrada_high.grid(row=0, column=3, padx=5)

ttk.Button(
    marco_limites, text="Aplicar límites",
    command=aplicar_limites
).grid(row=1, column=0, columnspan=4, pady=8)


tk.Label(
    ventana, text="TEMPERATURA ACTUAL",
    font=("Arial", 11, "bold")
).pack(pady=4)

etiqueta_temp = tk.Label(
    ventana, text="--.- °C",
    font=("Arial", 27, "bold"), fg="blue"
)
etiqueta_temp.pack()


marco_ciclo = ttk.Frame(ventana)
marco_ciclo.pack(pady=10)

boton_inicio = ttk.Button(
    marco_ciclo, text="Iniciar ciclo",
    command=iniciar_ciclo
)
boton_inicio.grid(row=0, column=0, padx=6)

boton_detener = ttk.Button(
    marco_ciclo, text="Detener ciclo",
    command=detener_ciclo, state="disabled"
)
boton_detener.grid(row=0, column=1, padx=6)

etiqueta_modo = tk.Label(
    ventana, text="CONTROL MANUAL",
    font=("Arial", 10, "bold"), fg="blue"
)
etiqueta_modo.pack(pady=4)


botones = []

for i in range(3):
    boton = tk.Button(
        ventana,
        text=f"RELÉ {i + 1}: APAGADO",
        width=28, height=2,
        bg="lightgray",
        command=lambda n=i: cambiar_rele(n)
    )
    boton.pack(pady=4)
    botones.append(boton)

etiqueta_estado = tk.Label(
    ventana, text="Listo", fg="gray"
)
etiqueta_estado.pack(pady=5)

buscar_puertos()
actualizar_interfaz()

ventana.after(100, leer_serial)
ventana.protocol("WM_DELETE_WINDOW", cerrar)
ventana.mainloop()
