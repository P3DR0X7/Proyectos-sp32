
import tkinter as tk
from tkinter import ttk, messagebox
import serial
import serial.tools.list_ports
import time
from collections import deque


class ControlTemperatura:

    def __init__(self, ventana):
        self.ventana = ventana
        self.ventana.title("Control de temperatura ESP32")
        self.ventana.geometry("1000x780")
        self.ventana.configure(bg="#202936")

        self.ser = None
        self.conectado = False

        self.temperatura = 0.0
        self.humedad = 0.0
        self.setpoint = 40.0
        self.kp = 5.0
        self.error = 0.0
        self.salida = 0.0
        self.angulo = 0
        self.modo = "STOP"

        self.historial_temp = deque(maxlen=100)
        self.historial_sp = deque(maxlen=100)

        self.crear_interfaz()
        self.actualizar_puertos()
        self.actualizar_grafica()

        self.ventana.after(100, self.leer_serial)
        self.ventana.protocol("WM_DELETE_WINDOW", self.cerrar)

   
    def crear_interfaz(self):

        tk.Label(
            self.ventana,
            text="CONTROL AUTOMÁTICO DE TEMPERATURA",
            font=("Arial", 21, "bold"),
            bg="#202936",
            fg="white"
        ).pack(pady=15)

        conexion = tk.Frame(self.ventana, bg="#202936")
        conexion.pack(pady=8)

        tk.Label(
            conexion,
            text="Puerto COM:",
            bg="#202936",
            fg="white"
        ).pack(side="left", padx=5)

        self.combo_puertos = ttk.Combobox(
            conexion,
            width=15,
            state="readonly"
        )
        self.combo_puertos.pack(side="left", padx=5)

        tk.Button(
            conexion,
            text="Actualizar puertos",
            command=self.actualizar_puertos
        ).pack(side="left", padx=5)

        self.boton_conectar = tk.Button(
            conexion,
            text="CONECTAR",
            bg="#16803c",
            fg="white",
            width=13,
            command=self.conectar
        )
        self.boton_conectar.pack(side="left", padx=5)

        self.estado = tk.Label(
            self.ventana,
            text="DESCONECTADO",
            font=("Arial", 12, "bold"),
            bg="#202936",
            fg="#ff6464"
        )
        self.estado.pack(pady=5)

        panel = tk.Frame(self.ventana, bg="#202936")
        panel.pack(pady=12)

        self.lbl_temp = self.crear_lectura(
            panel, "TEMPERATURA", "0.0 °C", 0, 0
        )
        self.lbl_hum = self.crear_lectura(
            panel, "HUMEDAD", "0.0 %", 0, 1
        )
        self.lbl_sp = self.crear_lectura(
            panel, "TEMPERATURA DESEADA", "40.0 °C", 0, 2
        )
        self.lbl_error = self.crear_lectura(
            panel, "ERROR", "0.0 °C", 1, 0
        )
        self.lbl_salida = self.crear_lectura(
            panel, "SALIDA P", "0.0 %", 1, 1
        )
        self.lbl_servo = self.crear_lectura(
            panel, "ÁNGULO SERVO", "0°", 1, 2
        )

        config = tk.LabelFrame(
            self.ventana,
            text="CONFIGURACIÓN",
            font=("Arial", 12, "bold"),
            bg="#202936",
            fg="white",
            padx=15,
            pady=12
        )
        config.pack(fill="x", padx=35, pady=10)

        tk.Label(
            config,
            text="Temperatura deseada (°C):",
            bg="#202936",
            fg="white"
        ).grid(row=0, column=0, padx=8, pady=8)

        self.entry_sp = tk.Entry(
            config, width=12, font=("Arial", 12)
        )
        self.entry_sp.insert(0, "40")
        self.entry_sp.grid(row=0, column=1, padx=8)

        tk.Label(
            config,
            text="Ganancia Kp:",
            bg="#202936",
            fg="white"
        ).grid(row=0, column=2, padx=8)

        self.entry_kp = tk.Entry(
            config, width=12, font=("Arial", 12)
        )
        self.entry_kp.insert(0, "5")
        self.entry_kp.grid(row=0, column=3, padx=8)

        tk.Button(
            config,
            text="APLICAR",
            bg="#2878bd",
            fg="white",
            width=13,
            command=self.aplicar
        ).grid(row=0, column=4, padx=12)

        botones = tk.Frame(self.ventana, bg="#202936")
        botones.pack(pady=12)

        tk.Button(
            botones,
            text="INICIAR AUTOMÁTICO",
            bg="#16803c",
            fg="white",
            font=("Arial", 12, "bold"),
            width=22,
            height=2,
            command=self.iniciar
        ).pack(side="left", padx=10)

        tk.Button(
            botones,
            text="DETENER",
            bg="#bd3030",
            fg="white",
            font=("Arial", 12, "bold"),
            width=18,
            height=2,
            command=self.detener
        ).pack(side="left", padx=10)

        self.lbl_modo = tk.Label(
            self.ventana,
            text="MODO: STOP",
            font=("Arial", 13, "bold"),
            bg="#202936",
            fg="#ff6464"
        )
        self.lbl_modo.pack(pady=5)

        grafica_frame = tk.LabelFrame(
            self.ventana,
            text="GRÁFICA DE TEMPERATURA",
            font=("Arial", 12, "bold"),
            bg="#202936",
            fg="white"
        )
        grafica_frame.pack(
            fill="both", expand=True, padx=35, pady=10
        )

        self.canvas = tk.Canvas(
            grafica_frame,
            bg="#111820",
            height=250,
            highlightthickness=0
        )
        self.canvas.pack(
            fill="both", expand=True, padx=10, pady=10
        )

    def crear_lectura(self, padre, titulo, valor, fila, columna):

        cuadro = tk.Frame(
            padre,
            bg="#303d4e",
            padx=18,
            pady=12
        )
        cuadro.grid(row=fila, column=columna, padx=8, pady=8)

        tk.Label(
            cuadro,
            text=titulo,
            font=("Arial", 9, "bold"),
            bg="#303d4e",
            fg="#cbd5e1"
        ).pack()

        etiqueta = tk.Label(
            cuadro,
            text=valor,
            font=("Arial", 19, "bold"),
            bg="#303d4e",
            fg="white"
        )
        etiqueta.pack(pady=5)

        return etiqueta

   
    def actualizar_puertos(self):

        puertos = [
            p.device
            for p in serial.tools.list_ports.comports()
        ]

        self.combo_puertos["values"] = puertos

        if puertos:
            self.combo_puertos.current(0)

    
    def conectar(self):

        if self.conectado:
            return

        puerto = self.combo_puertos.get()

        if not puerto:
            messagebox.showwarning(
                "Puerto",
                "Selecciona un puerto COM."
            )
            return

        try:
            self.ser = serial.Serial(
                puerto,
                115200,
                timeout=0
            )

            time.sleep(2)
            self.ser.reset_input_buffer()

            self.conectado = True

            self.estado.config(
                text="CONECTADO",
                fg="#4ade80"
            )

            self.boton_conectar.config(
                text="CONECTADO",
                bg="#555555"
            )

        except Exception as e:
            messagebox.showerror(
                "Error de conexión",
                str(e)
            )

    def enviar(self, comando):

        if self.conectado and self.ser and self.ser.is_open:
            try:
                self.ser.write((comando + "\n").encode())
            except Exception:
                self.estado.config(
                    text="ERROR DE COMUNICACIÓN",
                    fg="#ff6464"
                )

    
    def aplicar(self):

        try:
            sp = float(self.entry_sp.get())
            kp = float(self.entry_kp.get())

            if not 0 <= sp <= 100:
                raise ValueError(
                    "La temperatura debe estar entre 0 y 100."
                )

            if not 0 <= kp <= 20:
                raise ValueError(
                    "Kp debe estar entre 0 y 20."
                )

            self.enviar(f"SP:{sp}")
            self.enviar(f"KP:{kp}")

        except ValueError as e:
            messagebox.showerror(
                "Dato incorrecto",
                str(e)
            )

    def iniciar(self):
        self.enviar("START")

    def detener(self):
        self.enviar("STOP")

   
    def leer_serial(self):

        if self.conectado and self.ser:

            try:
                while self.ser.in_waiting:

                    linea = self.ser.readline().decode(
                        "utf-8",
                        errors="ignore"
                    ).strip()

                    if linea.startswith("DATA,"):
                        self.procesar_datos(linea)

            except Exception:
                self.estado.config(
                    text="ERROR DE COMUNICACIÓN",
                    fg="#ff6464"
                )

        self.ventana.after(100, self.leer_serial)

    def procesar_datos(self, linea):

        try:
            datos = linea.split(",")

            if len(datos) != 9:
                return

            self.temperatura = float(datos[1])
            self.humedad = float(datos[2])
            self.setpoint = float(datos[3])
            self.kp = float(datos[4])
            self.error = float(datos[5])
            self.salida = float(datos[6])
            self.angulo = int(datos[7])
            self.modo = datos[8]

            self.lbl_temp.config(
                text=f"{self.temperatura:.1f} °C"
            )

            self.lbl_hum.config(
                text=f"{self.humedad:.1f} %"
            )

            self.lbl_sp.config(
                text=f"{self.setpoint:.1f} °C"
            )

            self.lbl_error.config(
                text=f"{self.error:.1f} °C"
            )

           
            self.lbl_salida.config(
                text=f"{self.salida:.1f} %"
            )

            
            self.lbl_servo.config(
                text=f"{self.angulo}°"
            )

            if self.modo == "AUTO":
                self.lbl_modo.config(
                    text="MODO: AUTOMÁTICO",
                    fg="#4ade80"
                )
            else:
                self.lbl_modo.config(
                    text="MODO: STOP",
                    fg="#ff6464"
                )

            self.historial_temp.append(self.temperatura)
            self.historial_sp.append(self.setpoint)

            self.actualizar_grafica()

        except (ValueError, IndexError):
            pass

    
    def actualizar_grafica(self):

        if not hasattr(self, "canvas"):
            return

        self.canvas.delete("all")

        ancho = max(self.canvas.winfo_width(), 800)
        alto = max(self.canvas.winfo_height(), 250)

        margen = 45
        ancho_util = ancho - 2 * margen
        alto_util = alto - 2 * margen

        maximo = max(
            50,
            self.setpoint + 10,
            max(self.historial_temp, default=0) + 10
        )

        self.canvas.create_line(
            margen, margen,
            margen, alto - margen,
            fill="white",
            width=2
        )

        self.canvas.create_line(
            margen, alto - margen,
            ancho - margen, alto - margen,
            fill="white",
            width=2
        )

        for i in range(6):

            valor = maximo * i / 5
            y = alto - margen - (
                valor / maximo
            ) * alto_util

            self.canvas.create_line(
                margen, y,
                ancho - margen, y,
                fill="#394554"
            )

            self.canvas.create_text(
                margen - 20, y,
                text=f"{valor:.0f}",
                fill="white"
            )

        def dibujar_linea(valores, color):

            if len(valores) < 2:
                return

            puntos = []

            for i, valor in enumerate(valores):

                x = margen + (
                    i / max(1, len(valores) - 1)
                ) * ancho_util

                y = alto - margen - (
                    valor / maximo
                ) * alto_util

                puntos.extend([x, y])

            self.canvas.create_line(
                *puntos,
                fill=color,
                width=2
            )

        dibujar_linea(
            self.historial_temp,
            "#38bdf8"
        )

        dibujar_linea(
            self.historial_sp,
            "#facc15"
        )

        self.canvas.create_text(
            ancho / 2, 15,
            text="Temperatura (°C)",
            fill="white",
            font=("Arial", 10, "bold")
        )

        self.canvas.create_text(
            ancho - 120, 25,
            text="Azul: real",
            fill="#38bdf8"
        )

        self.canvas.create_text(
            ancho - 120, 42,
            text="Amarillo: deseada",
            fill="#facc15"
        )

    
    def cerrar(self):

        if self.ser and self.ser.is_open:
            try:
                self.ser.close()
            except Exception:
                pass

        self.ventana.destroy()



if __name__ == "__main__":

    ventana = tk.Tk()
    aplicacion = ControlTemperatura(ventana)
    ventana.mainloop()
