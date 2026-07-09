import sys
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import tkinter as tk
from tkinter import messagebox
from tkcalendar import Calendar
import sqlite3
import os
import webbrowser
from urllib.parse import quote
from PIL import Image, ImageTk
import pyautogui
import time
import threading

# ==================================================
# CAMINHOS COMPATÍVEIS COM PYTHON E EXE
# ==================================================

def caminho_base():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)

    return os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )

def caminho_recurso(pasta, arquivo):
    return os.path.join(caminho_base(), pasta, arquivo)

def obter_caminho_banco():
    return caminho_recurso("database", "banco.db")

# ==================================================

def abrir_tela_agenda(janela_principal):
    agenda = ttk.Toplevel(master=janela_principal)
    agenda.title("Agenda Mensal e Sincronização")
    agenda.state('zoomed')

    caminho_icone = caminho_recurso("assets", "icone.ico")
    caminho_fundo = caminho_recurso("assets", "tela_agenda.png")

    if os.path.exists(caminho_icone): agenda.iconbitmap(caminho_icone)

    def voltar():
        agenda.destroy()
        janela_principal.deiconify()
        janela_principal.state('zoomed')

    agenda.protocol("WM_DELETE_WINDOW", voltar)

    # -------------------------------------------------------------------------
    # BARRA SUPERIOR
    # -------------------------------------------------------------------------
    frame_header = tk.Frame(agenda, bg="#1B365D", height=70)
    frame_header.pack(fill=X, side=TOP, anchor=N)
    frame_header.pack_propagate(False)
    ttk.Button(frame_header, text="← Menu Principal", command=voltar, bootstyle=LIGHT).pack(side=LEFT, padx=20, pady=18)
    tk.Label(frame_header, text="CENTRAL DE AGENDAMENTOS E NOTIFICAÇÃO", font=("Helvetica", 14, "bold"), bg="#1B365D", fg="white").pack(side=RIGHT, padx=20, pady=18)

    # -------------------------------------------------------------------------
    # FUNDO
    # -------------------------------------------------------------------------
    frame_fundo = tk.Frame(agenda, bg="#F8FAFC")
    frame_fundo.pack(fill=BOTH, expand=YES)
    label_imagem_fundo = tk.Label(frame_fundo)
    imagem_original = Image.open(caminho_fundo) if os.path.exists(caminho_fundo) else None
    if imagem_original: label_imagem_fundo.place(x=0, y=0, relwidth=1, relheight=1)

    def redimensionar_fundo(event):
        if event.widget == agenda and imagem_original:
            img_redimensionada = imagem_original.resize((event.width, event.height), Image.Resampling.LANCZOS)
            foto_tk = ImageTk.PhotoImage(img_redimensionada)
            label_imagem_fundo.configure(image=foto_tk)
            label_imagem_fundo.image = foto_tk

    agenda.bind('<Configure>', redimensionar_fundo)

    # -------------------------------------------------------------------------
    # CARD CENTRAL
    # -------------------------------------------------------------------------
    card_agenda = tk.Frame(frame_fundo, bg="white", padx=20, pady=20)
    card_agenda.place(relx=0.5, rely=0.53, relwidth=0.9, relheight=0.8, anchor=CENTER)

    # -------------------------------------------------------------------------
    # COLUNA ESQUERDA (Filtros e Calendário)
    # -------------------------------------------------------------------------
    col_esquerda = tk.Frame(card_agenda, bg="white")
    col_esquerda.pack(side=LEFT, fill=BOTH, padx=10, expand=False)

    tk.Label(col_esquerda, text="1. Filtrar Profissional", font=("Helvetica", 12, "bold"), bg="white", fg="#1B365D").pack(anchor=W, pady=5)
    
    profissionais = ["Dra. Jamile", "Dra. Laurice", "Dr. Gerlando", "Jadson"]
    
    combo_filtro = ttk.Combobox(col_esquerda, values=profissionais, state="readonly", font=("Helvetica", 12))
    combo_filtro.pack(fill=X, pady=(0, 20))
    combo_filtro.set(profissionais[0])

    tk.Label(col_esquerda, text="2. Selecione a Data", font=("Helvetica", 12, "bold"), bg="white", fg="#1B365D").pack(anchor=W, pady=5)
    calendario = Calendar(col_esquerda, selectmode='day', date_pattern='dd/mm/yyyy', locale='pt_BR', background="#2C3E50", foreground="white", selectbackground="#18BC9C")
    calendario.pack(pady=10, fill=BOTH, expand=YES)

    # -------------------------------------------------------------------------
    # COLUNA DIREITA (Tabela e Controles)
    # -------------------------------------------------------------------------
    col_direita = tk.Frame(card_agenda, bg="white")
    col_direita.pack(side=RIGHT, fill=BOTH, expand=YES, padx=10)

    tk.Label(col_direita, text="3. Pacientes Agendados", font=("Helvetica", 12, "bold"), bg="white", fg="#1B365D").pack(anchor=W, pady=5)
    
    # Botão de selecionar todos
    def toggle_todas_caixinhas():
        itens = tabela_dia.get_children()
        if not itens: return
        todos_marcados = all(tabela_dia.item(i, 'values')[0] == '☑' for i in itens)
        novo_valor = '☐' if todos_marcados else '☑'
        for i in itens:
            valores = list(tabela_dia.item(i, 'values'))
            valores[0] = novo_valor
            tabela_dia.item(i, values=valores)
            
    ttk.Button(col_direita, text="☑ Marcar/Desmarcar Todos", bootstyle=(INFO, OUTLINE), cursor="hand2", command=toggle_todas_caixinhas).pack(anchor=W, pady=(0, 5))

    # Tabela com as colunas Sel e Aviso adicionadas
    colunas = ("Sel", "ID", "Nome", "Telefone", "Prioridade", "Retorno", "Aviso")
    tabela_dia = ttk.Treeview(col_direita, columns=colunas, show="headings", bootstyle=INFO)
    for col in colunas: 
        tabela_dia.heading(col, text=col)
        tabela_dia.column(col, anchor=CENTER)
    
    tabela_dia.column("Sel", width=40)
    tabela_dia.column("ID", width=50)
    tabela_dia.column("Retorno", width=60) 
    tabela_dia.column("Aviso", width=60) 
    tabela_dia.pack(fill=BOTH, expand=YES, pady=5)

    def alternar_caixinha(event):
        if tabela_dia.identify("region", event.x, event.y) == "cell" and tabela_dia.identify_column(event.x) == '#1':
            item = tabela_dia.focus()
            if item:
                valores = list(tabela_dia.item(item, 'values'))
                valores[0] = '☑' if valores[0] == '☐' else '☐'
                tabela_dia.item(item, values=valores)

    tabela_dia.bind('<ButtonRelease-1>', alternar_caixinha)

    # -------------------------------------------------------------------------
    # CONTROLES DE API (WhatsApp e Google Calendar)
    # -------------------------------------------------------------------------
    frame_controles = ttk.Labelframe(col_direita, text=" 4. Disparo Automático (API) ", padding=15, bootstyle=PRIMARY)
    frame_controles.pack(fill=X, pady=15)
    
    ttk.Label(frame_controles, text="Período da Consulta:").grid(row=0, column=0, padx=5, sticky=W)
    combo_periodo = ttk.Combobox(frame_controles, values=["Manhã", "Tarde", "Noite"], state="readonly", width=30)
    combo_periodo.grid(row=0, column=1, padx=5, sticky=W)
    combo_periodo.set("Manhã")

    def disparar_mensagens(tipo_aviso):
        itens_marcados = [item for item in tabela_dia.get_children() if tabela_dia.item(item)['values'][0] == '☑']
        if not itens_marcados: 
            return messagebox.showwarning("Aviso", "Selecione pelo menos um paciente nas caixinhas.")

        resposta = messagebox.askyesno(
            "Confirmação de Disparo", 
            f"Você está prestes a enviar {tipo_aviso} para {len(itens_marcados)} paciente(s).\n\n"
            "⚠️ IMPORTANTE: O sistema assumirá o controle do teclado para enviar.\n"
            "NÃO mexa no computador até o aviso de sucesso aparecer.\n\n"
            "Deseja iniciar o disparo?"
        )
        if not resposta: return
        
        btn_conf.config(state=DISABLED)
        btn_lemb.config(state=DISABLED)

        def rotina_envio():
            try:
                conexao = sqlite3.connect(obter_caminho_banco())
                cursor = conexao.cursor()
                
                for item in itens_marcados:
                    valores = tabela_dia.item(item)['values']
                    id_paciente = valores[1]
                    nome = valores[2]
                    tel = "".join(filter(str.isdigit, str(valores[3])))
                    if not tel.startswith("55"): tel = f"55{tel}"
                    
                    periodo = combo_periodo.get()
                    if periodo == "Manhã": horario = "das 07:00 às 10:00"
                    elif periodo == "Tarde": horario = "das 13:00 às 16:00"
                    else: horario = "das 17:00 às 19:30"
                    
                    if tipo_aviso == "Confirmação":
                        msg = f"Aviso Importante para você *{nome}*\n\nDando continuidade ao cuidado com a saúde, estamos entrando em contato para confirmar seu agendamento com *{combo_filtro.get()}*\n\n📅 *Data:* {calendario.get_date()}\n🌤️ *Período:* {periodo}\n🕛 *Horário:* {horario}\n📍 *Local:* Unidade Básica de Saúde Maria Divina Monteiro \n\nPodemos confirmar sua presença?\n\nCaso não possa comparecer, pedimos que entre em contato:\n📞 (64) 98131-1988\n\nCuidar da saúde hoje é um passo importante para o seu bem-estar. 💛"
                    else:
                        msg = f"Olá *{nome}*!\n\nPassando para *LEMBRAR* da sua consulta agendada para AMANHÃ com *{combo_filtro.get()}*.\n\n🌤️ *Período:* {periodo}\n🕛 *Horário:* {horario}\n📍 *Local:* Unidade Básica de Saúde Maria Divina Monteiro \n\nContamos com a sua presença! 💛\n\nSe houver algum imprevisto, avise-nos o quanto antes:\n📞 (64) 98131-1988"

                    # Abre o app do WhatsApp no Windows
                    webbrowser.open(f"whatsapp://send?phone={tel}&text={quote(msg)}")
                    
                    # Pausa para o WhatsApp Desktop carregar e focar a tela
                    time.sleep(4) 
                    
                    # Simula o aperto do Enter
                    pyautogui.press('enter')
                    time.sleep(1)
                    
                    # Salva no banco de dados que o aviso foi enviado
                    cursor.execute("UPDATE pacientes SET status_aviso = ? WHERE id = ?", (tipo_aviso, id_paciente))
                    conexao.commit()
                        
                conexao.close()
            except Exception as e:
                print(f"Erro na automação: {e}")
            
            # Devolve o controle para a interface após finalizar
            agenda.after(0, finalizar_envio)

        def finalizar_envio():
            atualizar_tabela()
            btn_conf.config(state=NORMAL)
            btn_lemb.config(state=NORMAL)
            messagebox.showinfo("Sucesso", "Todos os disparos foram concluídos!")

        # Roda a automação em segundo plano para não travar a tela
        threading.Thread(target=rotina_envio, daemon=True).start()

    def acao_api_google():
        itens = [item for item in tabela_dia.get_children() if tabela_dia.item(item)['values'][0] == '☑']
        if not itens: return messagebox.showwarning("Aviso", "Selecione um paciente para sincronizar.")
        
        item_valores = tabela_dia.item(itens[0])['values']
        data_br = calendario.get_date()
        dia, mes, ano = data_br.split('/')
        data_google = f"{ano}{mes}{dia}"
        
        profissional = combo_filtro.get()
        titulo = quote(f"Consulta: {item_valores[2]} ({profissional})")
        detalhes = quote(f"Paciente: {item_valores[2]}\nTelefone: {item_valores[3]}\nProfissional: {profissional}\nPeríodo: {combo_periodo.get()}")
        
        hora_inicio = "080000"
        hora_fim = "090000"
        if combo_periodo.get() == "Tarde":
            hora_inicio = "130000"; hora_fim = "140000"
        elif combo_periodo.get() == "Noite":
            hora_inicio = "170000"; hora_fim = "180000"
        
        url_google = f"https://calendar.google.com/calendar/render?action=TEMPLATE&text={titulo}&dates={data_google}T{hora_inicio}/{data_google}T{hora_fim}&details={detalhes}"
        webbrowser.open(url_google)

    btn_frame = ttk.Frame(frame_controles)
    btn_frame.grid(row=1, column=0, columnspan=2, pady=15, sticky=W)
    
    btn_conf = ttk.Button(btn_frame, text="📩 Enviar Confirmação", command=lambda: disparar_mensagens("Confirmação"), bootstyle=SUCCESS, width=22)
    btn_conf.pack(side=LEFT, padx=5)
    
    btn_lemb = ttk.Button(btn_frame, text="🔔 Enviar Lembrete", command=lambda: disparar_mensagens("Lembrete"), bootstyle=WARNING, width=22)
    btn_lemb.pack(side=LEFT, padx=5)
    
    ttk.Button(btn_frame, text="🗓️ Google Calendar", command=acao_api_google, bootstyle=INFO, width=20).pack(side=LEFT, padx=5)

    # -------------------------------------------------------------------------
    # CARREGAMENTO DE DADOS
    # -------------------------------------------------------------------------
    def atualizar_tabela(*args):
        for item in tabela_dia.get_children(): tabela_dia.delete(item)
        try:
            conexao = sqlite3.connect(obter_caminho_banco())
            cursor = conexao.cursor()
            
            # Puxa também a coluna status_aviso que foi adicionada
            query = """
                SELECT id, nome, telefone, prioridade, atendimento_tipo, status_aviso 
                FROM pacientes 
                WHERE status = 'Agendado' AND profissional = ? AND data_consulta = ?
                ORDER BY CASE prioridade WHEN 'Urgente' THEN 1 WHEN 'Prioritário' THEN 2 ELSE 3 END, id ASC
            """
            
            # Caso a coluna não exista (banco desatualizado), previne o crash
            try:
                cursor.execute(query, (combo_filtro.get(), calendario.get_date()))
            except sqlite3.OperationalError:
                query_fallback = "SELECT id, nome, telefone, prioridade, atendimento_tipo, 'Nenhum' FROM pacientes WHERE status = 'Agendado' AND profissional = ? AND data_consulta = ? ORDER BY CASE prioridade WHEN 'Urgente' THEN 1 WHEN 'Prioritário' THEN 2 ELSE 3 END, id ASC"
                cursor.execute(query_fallback, (combo_filtro.get(), calendario.get_date()))
            
            for linha in cursor.fetchall(): 
                simbolo_retorno = "✅" if linha[4] == "Retorno" else ""
                
                status_bd = linha[5]
                simbolo_aviso = "📩" if status_bd == "Confirmação" else "🔔" if status_bd == "Lembrete" else ""
                
                valores_formatados = ('☐', linha[0], linha[1], linha[2], linha[3], simbolo_retorno, simbolo_aviso)
                tabela_dia.insert("", END, values=valores_formatados)
            
            conexao.close()
        except Exception as e: 
            print(f"Erro ao atualizar tabela: {e}")

    calendario.bind("<<CalendarSelected>>", atualizar_tabela)
    combo_filtro.bind("<<ComboboxSelected>>", atualizar_tabela)
    atualizar_tabela()