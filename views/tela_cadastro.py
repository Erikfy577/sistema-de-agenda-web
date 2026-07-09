import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import tkinter as tk
from tkinter import messagebox
import sqlite3
import os
import sys
import requests 
from PIL import Image, ImageTk

# ==================================================
# CAMINHOS COMPATÍVEIS COM PYTHON E EXE
# ==================================================

def caminho_base():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def caminho_recurso(pasta, arquivo):
    return os.path.join(caminho_base(), pasta, arquivo)

def obter_caminho_banco():
    return caminho_recurso("database", "banco.db")

# ==================================================
# TELA DE CADASTRO
# ==================================================

def abrir_tela_cadastro(janela_principal):
    cadastro = ttk.Toplevel(master=janela_principal)
    cadastro.title("Cadastro de Paciente - Fila de Espera")
    cadastro.state("zoomed")

    caminho_icone = caminho_recurso("assets", "icone.ico")
    caminho_fundo = caminho_recurso("assets", "tela_cadastro.png")

    if os.path.exists(caminho_icone):
        cadastro.iconbitmap(caminho_icone)

    def voltar():
        cadastro.destroy()
        janela_principal.deiconify()
        janela_principal.state("zoomed")

    cadastro.protocol("WM_DELETE_WINDOW", voltar)

    # ==================================================
    # CABEÇALHO
    # ==================================================

    frame_header = tk.Frame(cadastro, bg="#1B365D", height=70)
    frame_header.pack(fill=X, side=TOP)
    frame_header.pack_propagate(False)

    ttk.Button(frame_header, text="← Menu Principal", command=voltar, bootstyle=LIGHT).pack(side=LEFT, padx=20, pady=18)
    
    tk.Label(frame_header, text="NOVO CADASTRO DE PACIENTE", font=("Helvetica", 14, "bold"), bg="#1B365D", fg="white").pack(side=RIGHT, padx=20)

    # ==================================================
    # FUNDO
    # ==================================================

    frame_fundo = tk.Frame(cadastro, bg="#F8FAFC")
    frame_fundo.pack(fill=BOTH, expand=True)

    imagem_original = None
    label_imagem = None

    if os.path.exists(caminho_fundo):
        try:
            imagem_original = Image.open(caminho_fundo)
            label_imagem = tk.Label(frame_fundo)
            label_imagem.place(x=0, y=0, relwidth=1, relheight=1)
        except Exception as erro:
            print("Erro imagem:", erro)

    def redimensionar(event):
        nonlocal imagem_original, label_imagem
        if imagem_original and label_imagem:
            imagem = imagem_original.resize((event.width, event.height), Image.Resampling.LANCZOS)
            foto = ImageTk.PhotoImage(imagem)
            label_imagem.configure(image=foto)
            label_imagem.image = foto

    frame_fundo.bind("<Configure>", redimensionar)

    # ==================================================
    # CARD
    # ==================================================

    COR = "#EBF4F6"
    card = tk.Frame(frame_fundo, bg=COR)
    card.place(relx=0.74, rely=0.55, anchor=CENTER)

    tk.Label(card, text="Informações do Paciente", font=("Helvetica", 18, "bold"), bg=COR, fg="#1B365D").pack(pady=15)

    tk.Label(card, text="Nome Completo:", bg=COR).pack(anchor=W)
    entrada_nome = ttk.Entry(card, width=38)
    entrada_nome.pack(pady=10)

    tk.Label(card, text="Telefone / WhatsApp:", bg=COR).pack(anchor=W)
    entrada_telefone = ttk.Entry(card, width=38)
    entrada_telefone.pack(pady=10)

    tk.Label(card, text="Profissional:", bg=COR).pack(anchor=W)
    
    profissionais = ["Dra. Jamile", "Dra. Laurice", "Dr. Gerlando", "Jadson"]
    combo_medico = ttk.Combobox(card, values=profissionais, state="readonly", width=36)
    combo_medico.pack(pady=10)
    combo_medico.set(profissionais[0])

    tk.Label(card, text="Prioridade:", bg=COR).pack(anchor=W)
    combo_prioridade = ttk.Combobox(card, values=["Eletivo", "Prioritário", "Urgente"], state="readonly", width=36)
    combo_prioridade.pack(pady=10)
    combo_prioridade.set("Eletivo")

    tk.Label(card, text="Tipo de Atendimento:", bg=COR).pack(anchor=W)
    combo_atendimento = ttk.Combobox(card, values=["Primeira Vez", "Retorno"], state="readonly", width=36)
    combo_atendimento.pack(pady=10)
    combo_atendimento.set("Primeira Vez")

    # ==================================================
    # SALVAR
    # ==================================================

    def salvar():
        nome = entrada_nome.get().strip()
        telefone = entrada_telefone.get().strip()
        medico = combo_medico.get()
        prioridade = combo_prioridade.get()
        atendimento = combo_atendimento.get()

        if not nome or not telefone:
            messagebox.showwarning("Aviso", "Preencha todos os campos")
            return

        try:
            banco = obter_caminho_banco()
            conexao = sqlite3.connect(banco)
            cursor = conexao.cursor()
            
            cursor.execute("""
                INSERT INTO pacientes (nome, telefone, profissional, status, prioridade, atendimento_tipo)
                VALUES (?, ?, ?, 'Aguardando', ?, ?)
            """, (nome, telefone, medico, prioridade, atendimento))

            conexao.commit()
            conexao.close()

            # --- INTEGRAÇÃO MAKE ---
            url_do_webhook = "https://hook.us2.make.com/v90f1fet2o1i2hwsk2arkvxssl8zucy8"
            dados_paciente = {
                "nome": nome,
                "telefone": telefone,
                "profissional": medico,
                "prioridade": prioridade,
                "atendimento_tipo": atendimento,
                "status": "Aguardando"
            }
            
            try:
                requests.post(url_do_webhook, json=dados_paciente, timeout=3)
            except:
                pass 

            messagebox.showinfo("Sucesso", "Paciente cadastrado!")
            entrada_nome.delete(0, tk.END)
            entrada_telefone.delete(0, tk.END)

        except Exception as erro:
            messagebox.showerror("Erro no Banco", str(erro))

    ttk.Button(card, text="Salvar na Fila", bootstyle=SUCCESS, command=salvar).pack(pady=20)