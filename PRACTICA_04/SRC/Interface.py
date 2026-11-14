import tkinter as tk
from tkinter import ttk, messagebox
import serial
import serial.tools.list_ports
import time

esp32 = None

def actualizar_puertos():
    puertos = [p.device for p in serial.tools.list_ports.comports()]
    selector["values"] = puertos
    if puertos:
        selector.current(0)
    else:
        selector.set("")

def conectar():
    global esp32
    puerto = selector.get()

    if not puerto:
        messagebox.showerror("Error", "No se encontró ningún puerto COM.")
        return

    try:
        esp32 = serial.Serial(puerto, 115200, timeout=1)
        time.sleep(2)
        estado.config(text=f"Conectado a {puerto}")
        boton_conectar.config(state="disabled")
        boton_desconectar.config(state="normal")
        slider.config(state="normal")
    except serial.SerialException as error:
        messagebox.showerror("Error al conectar", str(error))

def desconectar():
    global esp32
    if esp32 and esp32.is_open:
        esp32.close()
    esp32 = None
    estado.config(text="Desconectado")
    boton_conectar.config(state="normal")
    boton_desconectar.config(state="disabled")
    slider.config(state="disabled")

def mover_servo(valor):
    if esp32 and esp32.is_open:
        angulo = int(float(valor))
        esp32.write(f"{angulo}\n".encode())

ventana = tk.Tk()
ventana.title("Control del servo ESP32")
ventana.resizable(False, False)

tk.Label(ventana, text="Selecciona el puerto COM:").pack(padx=15, pady=(15, 5))

fila = tk.Frame(ventana)
fila.pack(padx=15)

selector = ttk.Combobox(fila, state="readonly", width=15)
selector.pack(side="left")

tk.Button(fila, text="Actualizar", command=actualizar_puertos).pack(side="left", padx=5)

boton_conectar = tk.Button(ventana, text="Conectar", command=conectar)
boton_conectar.pack(pady=10)

boton_desconectar = tk.Button(
    ventana, text="Desconectar", command=desconectar, state="disabled"
)
boton_desconectar.pack()

estado = tk.Label(ventana, text="Desconectado")
estado.pack(pady=8)

slider = tk.Scale(
    ventana,
    from_=0,
    to=180,
    orient="horizontal",
    length=350,
    label="Ángulo del servo",
    command=mover_servo,
    state="disabled"
)
slider.pack(padx=15, pady=10)

actualizar_puertos()

def cerrar_ventana():
    desconectar()
    ventana.destroy()

ventana.protocol("WM_DELETE_WINDOW", cerrar_ventana)
ventana.mainloop()
