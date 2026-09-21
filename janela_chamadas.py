import os
import subprocess
import tkinter as tk
from ctypes import POINTER, WINFUNCTYPE, Structure, byref, c_int, windll
from ctypes.wintypes import BOOL, DWORD, HMONITOR, LPARAM, RECT

import socketio


SERVIDOR = os.environ.get("CHAMADAS_SERVIDOR", "http://127.0.0.1:5000")
COR_TRANSPARENTE = "#010101"


class MonitorInfo(Structure):
    _fields_ = [
        ("cbSize", DWORD),
        ("rcMonitor", RECT),
        ("rcWork", RECT),
        ("dwFlags", DWORD),
    ]


def listar_monitores():
    monitores = []
    callback = WINFUNCTYPE(BOOL, HMONITOR, c_int, POINTER(RECT), LPARAM)

    def registrar_monitor(handle, _dc, _rect, _data):
        info = MonitorInfo()
        info.cbSize = ctypes_sizeof(MonitorInfo)
        windll.user32.GetMonitorInfoW(handle, byref(info))
        area = info.rcMonitor
        monitores.append((area.left, area.top, area.right - area.left, area.bottom - area.top))
        return True

    callback_registro = callback(registrar_monitor)
    windll.user32.EnumDisplayMonitors(None, None, callback_registro, 0)
    return monitores


def ctypes_sizeof(tipo):
    import ctypes

    return ctypes.sizeof(tipo)


def selecionar_monitor(monitores):
    if not monitores:
        return None

    selecao = tk.Tk()
    selecao.title("Escolher tela do painel")
    selecao.resizable(False, False)
    selecao.attributes("-topmost", True)

    tk.Label(
        selecao,
        text="Em qual tela deseja abrir o painel de chamadas?",
        padx=20,
        pady=15,
    ).pack()

    lista = tk.Listbox(selecao, height=len(monitores), width=42, exportselection=False)
    for indice, (_x, _y, largura, altura) in enumerate(monitores, start=1):
        lista.insert(tk.END, f"Tela {indice} - {largura} x {altura}")
    lista.selection_set(0)
    lista.pack(padx=20, pady=(0, 15))

    resultado = {"monitor": None}

    def confirmar():
        selecao_atual = lista.curselection()
        if selecao_atual:
            resultado["monitor"] = monitores[selecao_atual[0]]
        selecao.destroy()

    tk.Button(selecao, text="Abrir painel", command=confirmar, width=18).pack(pady=(0, 20))
    selecao.protocol("WM_DELETE_WINDOW", selecao.destroy)
    selecao.bind("<Return>", lambda _evento: confirmar())
    selecao.mainloop()
    return resultado["monitor"]


class JanelaChamadas:
    def __init__(self):
        monitor = selecionar_monitor(listar_monitores())
        if monitor is None:
            self.root = None
            return

        x, y, largura, altura = monitor
        self.root = tk.Tk()
        self.root.title("Painel de Chamadas")
        self.root.geometry(f"{largura}x{altura}+{x}+{y}")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.configure(bg=COR_TRANSPARENTE)
        self.root.wm_attributes("-transparentcolor", COR_TRANSPARENTE)
        self.root.bind("<Escape>", lambda _evento: self.fechar())
        self.root.protocol("WM_DELETE_WINDOW", self.fechar)

        self.canvas = tk.Canvas(
            self.root,
            bg=COR_TRANSPARENTE,
            highlightthickness=0,
        )
        self.canvas.pack(fill="both", expand=True)
        self.timer_ocultar = None

        self.socket = socketio.Client(reconnection=True)
        self.socket.on("nova_chamada", self.nova_chamada)
        self.root.after(100, self.conectar)

    def conectar(self):
        try:
            self.socket.connect(SERVIDOR)
        except Exception as erro:
            print(f"Nao foi possivel conectar ao servidor: {erro}")
            self.root.after(5000, self.conectar)

    def nova_chamada(self, dados):
        self.root.after(0, self.mostrar_chamada, dados)

    def mostrar_chamada(self, dados):
        senha = str(dados.get("senha", "--"))
        origem = dados.get("sala_origem")
        nomes = {
            "triagem": ("COMPARECER A TRIAGEM", "Triagem"),
            "A": ("CONSULTORIO 01", "Consultorio um"),
            "B": ("CONSULTORIO 02", "Consultorio dois"),
        }
        nome_sala, nome_fala = nomes.get(
            origem,
            (str(dados.get("sala_nome", "Sala de atendimento")), str(dados.get("sala_nome", "Sala de atendimento"))),
        )

        largura = self.root.winfo_screenwidth()
        altura = self.root.winfo_screenheight()
        caixa_largura = min(1100, largura - 80)
        caixa_altura = 430
        esquerda = (largura - caixa_largura) // 2
        topo = (altura - caixa_altura) // 2

        self.canvas.delete("chamada")
        self.canvas.create_rectangle(
            esquerda,
            topo,
            esquerda + caixa_largura,
            topo + caixa_altura,
            fill="#e74c3c",
            outline="white",
            width=5,
            tags="chamada",
        )
        self.canvas.create_text(
            largura // 2,
            topo + 85,
            text=nome_sala,
            fill="white",
            font=("Segoe UI", 32, "bold"),
            tags="chamada",
        )
        self.canvas.create_text(
            largura // 2,
            topo + 260,
            text=senha,
            fill="white",
            font=("Segoe UI", 150, "bold"),
            tags="chamada",
        )

        self.falar(f"Senha {senha}. Comparecer a {nome_fala}")
        if self.timer_ocultar:
            self.root.after_cancel(self.timer_ocultar)
        self.timer_ocultar = self.root.after(12000, self.ocultar_chamada)

    def ocultar_chamada(self):
        self.canvas.delete("chamada")
        self.timer_ocultar = None

    @staticmethod
    def falar(texto):
        texto_seguro = texto.replace("'", "''")
        comando = (
            "Add-Type -AssemblyName System.Speech; "
            "$voz = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
            f"$voz.Speak('{texto_seguro}');"
        )
        subprocess.Popen(
            ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", comando],
            creationflags=subprocess.CREATE_NO_WINDOW,
        )

    def fechar(self):
        if self.root is None:
            return
        if self.socket.connected:
            self.socket.disconnect()
        self.root.destroy()

    def iniciar(self):
        if self.root is None:
            return
        self.root.mainloop()


if __name__ == "__main__":
    JanelaChamadas().iniciar()
