import sys
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import tkinter as tk
import os
import requests
import threading
from PIL import Image, ImageTk
from views.tela_cadastro import abrir_tela_cadastro
from views.tela_agenda import abrir_tela_agenda
from views.tela_espera import abrir_tela_espera

# ==================================================
# CAMINHOS COMPATÍVEIS COM PYTHON E EXE
# ==================================================
def caminho_base():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def caminho_recurso(pasta, arquivo):
    return os.path.join(caminho_base(), pasta, arquivo)

# ==================================================

def abrir_tela_principal():
    janela = ttk.Window(themename="flatly")
    janela.title("Sistema de Agendamento UBS")
    janela.state('zoomed')

    # CORREÇÃO DOS CAMINHOS AQUI 👇
    caminho_icone = caminho_recurso("assets", "icone.ico")
    
    # ATENÇÃO: Confirme se o nome do seu arquivo de imagem é "tela_principal.png" mesmo
    caminho_fundo = caminho_recurso("assets", "tela_principal.png") 

    if os.path.exists(caminho_icone):
        janela.iconbitmap(caminho_icone)

    def abrir_e_esconder(funcao_abrir):
        janela.withdraw()
        funcao_abrir(janela)

    # --- PLANO DE FUNDO ---
    label_fundo = None
    imagem_original = None

    if os.path.exists(caminho_fundo):
        try:
            imagem_original = Image.open(caminho_fundo)
            label_fundo = tk.Label(janela)
            label_fundo.place(x=0, y=0, relwidth=1, relheight=1)
        except Exception as e:
            print(f"Erro no fundo: {e}")

    def redimensionar_fundo(event):
        nonlocal imagem_original, label_fundo
        if event.widget == janela and imagem_original and label_fundo:
            largura = event.width
            altura = event.height
            if largura > 100 and altura > 100:
                img_redimensionada = imagem_original.resize((largura, altura), Image.Resampling.LANCZOS)
                foto_tk = ImageTk.PhotoImage(img_redimensionada)
                label_fundo.configure(image=foto_tk)
                label_fundo.image = foto_tk

    janela.bind('<Configure>', redimensionar_fundo)

    # --- WIDGET DE CLIMA (Canto Superior Direito) ---
    frame_clima = tk.Frame(janela, bg="#1B365D", padx=31, pady=19)
    frame_clima.place(relx=0.98, rely=0.03, anchor=NE)

    label_clima = tk.Label(frame_clima, text="⏳ Buscando clima...", font=("Helvetica", 10, "bold"), bg="#1B365D", fg="white")
    label_clima.pack()

    def buscar_clima():
        try:
            url = "https://api.open-meteo.com/v1/forecast?latitude=-16.4419&longitude=-51.1186&current_weather=true"
            resposta = requests.get(url, timeout=5)
            
            if resposta.status_code == 200:
                dados = resposta.json()
                temp = round(dados['current_weather']['temperature'])
                codigo = dados['current_weather']['weathercode']
                
                if codigo == 0:
                    emoji, desc = "☀️", "Céu limpo"
                elif codigo in [1, 2, 3]:
                    emoji, desc = "⛅", "Nublado"
                elif codigo in [45, 48]:
                    emoji, desc = "🌫️", "Nevoeiro"
                elif codigo in [51, 53, 55, 61, 63, 65, 80, 81, 82]:
                    emoji, desc = "🌧️", "Chuva"
                elif codigo in [95, 96, 99]:
                    emoji, desc = "⛈️", "Tempestade"
                else:
                    emoji, desc = "☁️", "Tempo variável"
                
                texto_final = f"{emoji} Arenópolis: {temp}°C | {desc}"
                
                janela.after(0, lambda: label_clima.config(text=texto_final))
            else:
                janela.after(0, lambda: label_clima.config(text="☁️ Clima indisponível no momento"))
        except Exception:
            janela.after(0, lambda: label_clima.config(text="☁️ Modo Offline"))

    threading.Thread(target=buscar_clima, daemon=True).start()

    # --- CARD CENTRAL GIGANTE ---
    card_central = ttk.Frame(janela, padding=60, bootstyle=LIGHT)
    card_central.place(relx=0.5, rely=0.5, anchor=CENTER)

    ttk.Label(
        card_central, 
        text="SISTEMA DE AGENDAMENTO UBS", 
        font=("Helvetica", 24, "bold"), 
        bootstyle=PRIMARY
    ).pack(pady=(0, 40))

    estilo = ttk.Style()
    estilo.configure('Grande.TButton', font=('Helvetica', 13, 'bold'))

    ttk.Button(
        card_central, text="➕ Cadastrar Paciente", bootstyle=SUCCESS, width=35,
        style='Grande.TButton', command=lambda: abrir_e_esconder(abrir_tela_cadastro)
    ).pack(pady=15)

    ttk.Button(
        card_central, text="🗓️ Visualizar Agenda", bootstyle=INFO, width=35,
        style='Grande.TButton', command=lambda: abrir_e_esconder(abrir_tela_agenda)
    ).pack(pady=15)

    ttk.Button(
        card_central, text="⏳ Gerenciar Fila de Espera", bootstyle=WARNING, width=35,
        style='Grande.TButton', command=lambda: abrir_e_esconder(abrir_tela_espera)
    ).pack(pady=15)

    ttk.Label(card_central, text="Fase Beta - Gestão Unificada", font=("Helvetica", 11), bootstyle=SECONDARY).pack(pady=(30, 0))

    janela.mainloop()