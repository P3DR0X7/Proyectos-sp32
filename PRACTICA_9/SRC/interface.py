
import tkinter as tk
from tkinter import ttk, messagebox
import serial
import serial.tools.list_ports
import threading
import queue
import time
from collections import deque


class ControlTemperatura:

    def __init__(self, root):

        self.root = root
        self.root.title("Control PID de Temperatura - ESP32")
        self.root.geometry("1050x750")
        self.root.configure(bg="#eeeeee")

        self.ser = None
        self.conectado = False
        self.hilo = None
        self.cola = queue.Queue()

        self.datos_temp = deque(maxlen=300)
        self.datos_ref = deque(maxlen=300)
        self.tiempos = deque(maxlen=300)

        self.inicio_grafica = time.time()

        self.temperatura = 0
        self.humedad = 0
        self.error = 0
        self.p = 0
        self.i = 0
        self.d = 0
        self.salida = 0
        self.angulo = 90
        self.modo = "STOP"

        self.crear_interfaz()
        self.buscar_puertos()

        self.root.after(100, self.actualizar_interfaz)
        self.root.protocol("WM_DELETE_WINDOW", self.cerrar)

 

    def crear_interfaz(self):

        titulo = tk.Label(
            self.root,
            text="CONTROL PID DE TEMPERATURA",
            font=("Arial", 20, "bold"),
            bg="#eeeeee"
        )
        titulo.pack(pady=10)

        conexion = tk.LabelFrame(
            self.root,
            text="Conexión ESP32",
            font=("Arial", 11, "bold"),
            padx=10,
            pady=10
        )
        conexion.pack(fill="x", padx=15, pady=5)

        self.combo_puertos = ttk.Combobox(
            conexion,
            width=18,
            state="readonly"
        )
        self.combo_puertos.pack(side="left", padx=5)

        ttk.Button(
            conexion,
            text="Buscar puertos",
            command=self.buscar_puertos
        ).pack(side="left", padx=5)

        ttk.Button(
            conexion,
            text="Conectar",
            command=self.conectar
        ).pack(side="left", padx=5)

        ttk.Button(
            conexion,
            text="Desconectar",
            command=self.desconectar
        ).pack(side="left", padx=5)

        self.lbl_conexion = tk.Label(
            conexion,
            text="Desconectado",
            fg="red",
            font=("Arial", 11, "bold")
        )
        self.lbl_conexion.pack(side="left", padx=15)

   

        parametros = tk.LabelFrame(
            self.root,
            text="Configuración PID",
            font=("Arial", 11, "bold"),
            padx=10,
            pady=10
        )
        parametros.pack(fill="x", padx=15, pady=5)

        self.entrada_sp = self.crear_campo(
            parametros, "Temperatura deseada (°C)", "40"
        )

        self.entrada_kp = self.crear_campo(
            parametros, "Kp", "5.0"
        )

        self.entrada_ki = self.crear_campo(
            parametros, "Ki", "0.05"
        )

        self.entrada_kd = self.crear_campo(
            parametros, "Kd", "0.0"
        )

        ttk.Button(
            parametros,
            text="Enviar parámetros",
            command=self.enviar_parametros
        ).pack(side="left", padx=10, pady=5)

      

        botones = tk.Frame(self.root, bg="#eeeeee")
        botones.pack(pady=10)

        tk.Button(
            botones,
            text="INICIAR PID",
            bg="#28a745",
            fg="white",
            font=("Arial", 12, "bold"),
            width=16,
            command=self.iniciar
        ).pack(side="left", padx=10)

        tk.Button(
            botones,
            text="DETENER",
            bg="#dc3545",
            fg="white",
            font=("Arial", 12, "bold"),
            width=16,
            command=self.detener
        ).pack(side="left", padx=10)

 

        lecturas = tk.LabelFrame(
            self.root,
            text="Lecturas del sistema",
            font=("Arial", 11, "bold"),
            padx=10,
            pady=10
        )
        lecturas.pack(fill="x", padx=15, pady=5)

        self.lbl_temp = self.crear_lectura(
            lecturas, "Temperatura", "0 °C"
        )

        self.lbl_hum = self.crear_lectura(
            lecturas, "Humedad", "0 %"
        )

        self.lbl_error = self.crear_lectura(
            lecturas, "Error", "0 °C"
        )

        self.lbl_salida = self.crear_lectura(
            lecturas, "Salida PID", "0 %"
        )

        self.lbl_servo = self.crear_lectura(
            lecturas, "Servo", "90°"
        )

        self.lbl_modo = self.crear_lectura(
            lecturas, "Modo", "STOP"
        )

        

        datos_pid = tk.LabelFrame(
            self.root,
            text="Componentes del PID",
            font=("Arial", 11, "bold"),
            padx=10,
            pady=10
        )
        datos_pid.pack(fill="x", padx=15, pady=5)

        self.lbl_p = self.crear_lectura(datos_pid, "P", "0")
        self.lbl_i = self.crear_lectura(datos_pid, "I", "0")
        self.lbl_d = self.crear_lectura(datos_pid, "D", "0")

      

        grafica = tk.LabelFrame(
            self.root,
            text="Gráfica de temperatura",
            font=("Arial", 11, "bold"),
            padx=10,
            pady=10
        )
        grafica.pack(fill="both", expand=True, padx=15, pady=10)

        self.canvas = tk.Canvas(
            grafica,
            bg="white",
            height=300
        )
        self.canvas.pack(fill="both", expand=True)

        leyenda = tk.Frame(grafica)
        leyenda.pack(pady=5)

        tk.Label(
            leyenda,
            text="● Temperatura real",
            fg="blue",
            font=("Arial", 10, "bold")
        ).pack(side="left", padx=15)

        tk.Label(
            leyenda,
            text="● Temperatura deseada",
            fg="red",
            font=("Arial", 10, "bold")
        ).pack(side="left", padx=15)

    def crear_campo(self, padre, nombre, valor):

        marco = tk.Frame(padre)
        marco.pack(side="left", padx=8)

        tk.Label(
            marco,
            text=nombre,
            font=("Arial", 9, "bold")
        ).pack()

        entrada = ttk.Entry(marco, width=9)
        entrada.insert(0, valor)
        entrada.pack()

        return entrada

    def crear_lectura(self, padre, nombre, valor):

        marco = tk.Frame(padre)
        marco.pack(side="left", padx=12)

        tk.Label(
            marco,
            text=nombre,
            font=("Arial", 9, "bold")
        ).pack()

        etiqueta = tk.Label(
            marco,
            text=valor,
            font=("Arial", 13, "bold"),
            fg="#174a8b"
        )
        etiqueta.pack()

        return etiqueta

  

    def buscar_puertos(self):

        puertos = [
            puerto.device
            for puerto in serial.tools.list_ports.comports()
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
                "Aviso",
                "Selecciona un puerto COM."
            )
            return

        try:
            self.ser = serial.Serial(
                puerto,
                115200,
                timeout=1
            )

            time.sleep(2)

            self.conectado = True

            self.lbl_conexion.config(
                text="Conectado",
                fg="green"
            )

            self.hilo = threading.Thread(
                target=self.leer_serial,
                daemon=True
            )
            self.hilo.start()

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def desconectar(self):

        self.conectado = False

        if self.ser:
            try:
                self.ser.close()
            except:
                pass

        self.ser = None

        self.lbl_conexion.config(
            text="Desconectado",
            fg="red"
        )

    def leer_serial(self):

        while self.conectado and self.ser:

            try:
                linea = self.ser.readline().decode(
                    "utf-8",
                    errors="ignore"
                ).strip()

                if linea.startswith("DATA,"):
                    self.cola.put(linea)

            except:
                break

 

    def enviar_comando(self, comando):

        if not self.conectado or not self.ser:
            messagebox.showwarning(
                "Aviso",
                "Primero conecta el ESP32."
            )
            return

        try:
            self.ser.write((comando + "\n").encode())

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def enviar_parametros(self):

        try:
            sp = float(self.entrada_sp.get())
            kp = float(self.entrada_kp.get())
            ki = float(self.entrada_ki.get())
            kd = float(self.entrada_kd.get())

            if not (0 <= sp <= 100):
                raise ValueError("La referencia debe estar entre 0 y 100.")

            if not (0 <= kp <= 100):
                raise ValueError("Kp debe estar entre 0 y 100.")

            if not (0 <= ki <= 20):
                raise ValueError("Ki debe estar entre 0 y 20.")

            if not (0 <= kd <= 100):
                raise ValueError("Kd debe estar entre 0 y 100.")

            self.enviar_comando(f"SP:{sp}")
            self.enviar_comando(f"KP:{kp}")
            self.enviar_comando(f"KI:{ki}")
            self.enviar_comando(f"KD:{kd}")

        except ValueError as e:
            messagebox.showerror("Parámetros incorrectos", str(e))

    def iniciar(self):
        self.enviar_comando("START")

    def detener(self):
        self.enviar_comando("STOP")

    

    def procesar_datos(self, linea):

        try:
            partes = linea.split(",")

            if len(partes) != 14:
                return

            self.temperatura = float(partes[1])
            self.humedad = float(partes[2])
            referencia = float(partes[3])

            self.error = float(partes[7])
            self.p = float(partes[8])
            self.i = float(partes[9])
            self.d = float(partes[10])

            self.salida = float(partes[11])
            self.angulo = int(float(partes[12]))
            self.modo = partes[13]

            self.lbl_temp.config(
                text=f"{self.temperatura:.1f} °C"
            )

            self.lbl_hum.config(
                text=f"{self.humedad:.1f} %"
            )

            self.lbl_error.config(
                text=f"{self.error:.2f} °C"
            )

            self.lbl_salida.config(
                text=f"{self.salida:.1f} %"
            )

            self.lbl_servo.config(
                text=f"{self.angulo}°"
            )

            self.lbl_modo.config(text=self.modo)

            self.lbl_p.config(text=f"{self.p:.2f}")
            self.lbl_i.config(text=f"{self.i:.2f}")
            self.lbl_d.config(text=f"{self.d:.2f}")

            tiempo = time.time() - self.inicio_grafica

            self.tiempos.append(tiempo)
            self.datos_temp.append(self.temperatura)
            self.datos_ref.append(referencia)

        except (ValueError, IndexError):
            pass

    

    def actualizar_interfaz(self):

        while not self.cola.empty():

            linea = self.cola.get()

            self.procesar_datos(linea)

        self.dibujar_grafica()

        self.root.after(100, self.actualizar_interfaz)

    

    def dibujar_grafica(self):

        canvas = self.canvas

        canvas.delete("all")

        ancho = canvas.winfo_width()
        alto = canvas.winfo_height()

        if ancho < 100 or alto < 100:
            return

        margen_izq = 55
        margen_der = 20
        margen_sup = 20
        margen_inf = 35

        x1 = margen_izq
        x2 = ancho - margen_der
        y1 = margen_sup
        y2 = alto - margen_inf

        canvas.create_rectangle(
            x1, y1, x2, y2,
            outline="black"
        )

        if not self.datos_temp:
            canvas.create_text(
                ancho / 2,
                alto / 2,
                text="Esperando datos del ESP32...",
                fill="gray",
                font=("Arial", 12)
            )
            return

        minimo = min(
            min(self.datos_temp),
            min(self.datos_ref)
        ) - 5

        maximo = max(
            max(self.datos_temp),
            max(self.datos_ref)
        ) + 5

        if maximo - minimo < 10:
            maximo = minimo + 10

        

        for n in range(6):

            valor = minimo + (
                (maximo - minimo) * n / 5
            )

            y = y2 - (y2 - y1) * n / 5

            canvas.create_line(
                x1, y, x2, y,
                fill="#dddddd"
            )

            canvas.create_text(
                x1 - 25,
                y,
                text=f"{valor:.0f}",
                font=("Arial", 8)
            )

        

        cantidad = len(self.datos_temp)

        def calcular_puntos(datos):

            puntos = []

            for indice, valor in enumerate(datos):

                if cantidad <= 1:
                    x = x1
                else:
                    x = x1 + (
                        (x2 - x1) * indice / (cantidad - 1)
                    )

                y = y2 - (
                    (valor - minimo) /
                    (maximo - minimo)
                ) * (y2 - y1)

                puntos.extend([x, y])

            return puntos

        puntos_temp = calcular_puntos(self.datos_temp)
        puntos_ref = calcular_puntos(self.datos_ref)

        if len(puntos_temp) >= 4:
            canvas.create_line(
                *puntos_temp,
                fill="blue",
                width=2
            )

        if len(puntos_ref) >= 4:
            canvas.create_line(
                *puntos_ref,
                fill="red",
                width=2
            )

        canvas.create_text(
            ancho / 2,
            alto - 10,
            text="Tiempo (últimas lecturas)",
            font=("Arial", 9)
        )

   

    def cerrar(self):

        if self.conectado:
            try:
                self.enviar_comando("STOP")
                time.sleep(0.1)
            except:
                pass

        self.desconectar()
        self.root.destroy()




if __name__ == "__main__":

    ventana = tk.Tk()

    aplicacion = ControlTemperatura(ventana)

    ventana.mainloop()
