import sys
sys.path.append("libs")

import tkinter as tk
from tkinter import ttk, scrolledtext
from tkcalendar import DateEntry
from datetime import datetime, timedelta
from selenium import webdriver
from bs4 import BeautifulSoup
import threading

def extrair_conteudo(checkin, checkout, total_pessoas, cupom=None):
    link = f'https://hbook.hsystem.com.br/Booking?companyId=632b188de819f634133fd526&checkin={checkin}&checkout={checkout}&adults={total_pessoas}'
    if cupom:
        link += f'&promocode={cupom}'

    opcoes = webdriver.ChromeOptions()
    opcoes.add_argument('--headless')
    opcoes.add_argument('--no-sandbox')
    opcoes.add_argument('--disable-dev-shm-usage')
    opcoes.add_argument('--disable-gpu')
    opcoes.add_argument('--disable-extensions')

    with webdriver.Chrome(options=opcoes) as driver:
        driver.get(link)
        driver.implicitly_wait(5)  # Definir um tempo de espera implícita

        html = driver.page_source

    soup = BeautifulSoup(html, 'html.parser')
    section_body = soup.find('div', class_='section-body')
    
    if section_body:
        quartos_info = section_body.find_all('div', class_='room-item')
        nome_quartos = []
        nome_tarifas = []
        valor_quarto = []
        quantidade_noites = []
        disponibilidade = []

        for quarto in quartos_info:
            nome_quarto = quarto.find('span', class_='room-name').get_text(strip=True).upper()
            nome_tarifa = quarto.find('span', class_='rate-name').get_text(strip=True)
            valor = quarto.find('span', class_='item-value').get_text(strip=True)
            noites = quarto.find('span', attrs={'data-bind': 'text: $root.RoomNights'}).get_text(strip=True)
            disponivel = quarto.find('span', attrs={'data-bind': 'text:Availability'}).get_text(strip=True)

            nome_quartos.append(nome_quarto)
            nome_tarifas.append(nome_tarifa)
            valor_quarto.append(valor)
            quantidade_noites.append(noites)
            disponibilidade.append(disponivel)

        return nome_quartos, nome_tarifas, valor_quarto, quantidade_noites, disponibilidade
    
    return None

def construir_links(nome_quartos):
    quartos = {
        "QUARTO DUPLO COM VENTILADOR": "duplo-standard",
        "QUARTO TRIPLO COM VENTILADOR": "standard-triplo",
        "QUARTO DUPLO SUPERIOR": "executivo-duplo",
        "QUARTO COM CAMA QUEEN-SIZE - ACESSÍVEL PARA HÓSPEDES COM MOBILIDADE REDUZIDA": "executivo-acessivel",
        "QUARTO QUÁDRUPLO SUPERIOR": "executivo-quadruplo",
        "QUARTO DUPLO DELUXE MASTER COM VISTA DO MAR": "deluxe-duplo-35",
        "QUARTO DUPLO DELUXE COM VISTA DO MAR": "deluxe-duplo-50"
    }
    
    links = []
    for quarto in nome_quartos:
        links.append("https://peixegordohotel.com/rooms/" + quartos.get(quarto, "Link não encontrado para este quarto"))
    return links

def buscar_quartos():
    def realizar_busca():
        progress_window = tk.Toplevel(root)
        progress_window.title("Buscando...")
        progress_window.grab_set()

        progress_bar = ttk.Progressbar(progress_window, orient='horizontal', length=300, mode='indeterminate')
        progress_bar.pack(padx=10, pady=10)
        progress_bar.start()

        contador_label = tk.Label(progress_window, text="Tempo decorrido: 0 segundos")
        contador_label.pack(pady=(0, 10))

        segundos = 0

        def atualizar_contador():
            nonlocal segundos
            segundos += 1
            contador_label.config(text=f"Tempo decorrido: {segundos} segundos")
            contador_label.after(1000, atualizar_contador)

        atualizar_contador()

        try:
            total_pessoas = int(adultos_combobox.get()) + int(criancas_combobox.get())
            cupom = cupom_entry.get()  # Novo: Obter o valor do cupom
            resultados = extrair_conteudo(checkin_cal.get_date().strftime('%d/%m/%Y'),
                                          checkout_cal.get_date().strftime('%d/%m/%Y'),
                                          total_pessoas,
                                          cupom)

            progress_bar.stop()
            progress_window.destroy()

            if resultados:
                nome_quartos, nome_tarifas, valor_quarto, quantidade_noites, disponibilidade = resultados
                resultado_text.delete(1.0, tk.END)

                links = construir_links(nome_quartos)
                for nome_quarto, nome_tarifa, valor, noites, disponivel, link in zip(nome_quartos, nome_tarifas, valor_quarto, quantidade_noites, disponibilidade, links):
                    if disponivel != '0':
                        resultado_text.insert(tk.END, f"🏨 *{nome_quarto}*\n{nome_tarifa}\n💲 {valor}\n👥 {total_pessoas} adultos\n📅 {checkin_cal.get_date().strftime('%d/%m/%Y')} até {checkout_cal.get_date().strftime('%d/%m/%Y')} - {noites}\n🔗 [Link]({link})\n\n")

                while resultado_text.get("end-2c", "end-1c") == '\n':
                    resultado_text.delete("end-2c", "end-1c")
            else:
                resultado_text.delete(1.0, tk.END)
                resultado_text.insert(tk.END, "Em caso de indisponibilidade, nosso WhatsApp é (84) 31911103, faremos o possível para recebê-lo!")

        except Exception as e:
            pass

    threading.Thread(target=realizar_busca).start()

def copiar_texto():
    root.clipboard_clear()
    root.clipboard_append(resultado_text.get(1.0, tk.END))
    copied_label = tk.Label(frame, text="O texto foi copiado para a área de transferência.", fg="green")
    copied_label.grid(row=3, columnspan=11, padx=5, pady=5, sticky="nsew")
    root.after(5000, lambda: copied_label.grid_forget())

root = tk.Tk()
root.title("Busca de Quartos")
root.resizable(False, False)

frame = tk.Frame(root)
frame.pack(padx=10, pady=10)

# Labels e widgets para entrada de data e número de pessoas
tk.Label(frame, text="Check-In:").grid(row=0, column=0, padx=5, pady=5)
checkin_cal = DateEntry(frame, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='dd/MM/yyyy')
checkin_cal.grid(row=0, column=1, padx=5, pady=5)
checkin_cal.set_date(datetime.now())

tk.Label(frame, text="Check-Out:").grid(row=0, column=2, padx=5, pady=5)
checkout_cal = DateEntry(frame, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='dd/MM/yyyy')
checkout_cal.grid(row=0, column=3, padx=5, pady=5)
checkout_cal.set_date(datetime.now() + timedelta(days=1))

tk.Label(frame, text="Adultos:").grid(row=0, column=4, padx=5, pady=5)
adultos_combobox = ttk.Combobox(frame, values=[str(i) for i in range(1, 5)], width=2)
adultos_combobox.grid(row=0, column=5, padx=5, pady=5)
adultos_combobox.set('2')

tk.Label(frame, text="Crianças:").grid(row=0, column=6, padx=5, pady=5)
criancas_combobox = ttk.Combobox(frame, values=[str(i) for i in range(4)], width=2)
criancas_combobox.grid(row=0, column=7, padx=5, pady=5)
criancas_combobox.set('0')

# Novo: Label e Entry para inserir o cupom
tk.Label(frame, text="Cupom:").grid(row=0, column=8, padx=5, pady=5)
cupom_entry = ttk.Entry(frame, width=10)
cupom_entry.grid(row=0, column=9, padx=5, pady=5)

# Botão de busca
tk.Button(frame, text="Buscar", command=buscar_quartos, cursor="hand2").grid(row=0, column=10, padx=5, pady=5)

# Área de texto para exibição dos resultados
resultado_text = scrolledtext.ScrolledText(frame, width=80, height=20)
resultado_text.grid(row=1, columnspan=11, padx=5, pady=5, sticky="nsew")
resultado_text.tag_configure('center', justify='center')
resultado_text.tag_add('center', '1.0', 'end')

# Botão para copiar texto
tk.Button(frame, text="Copiar", command=copiar_texto, cursor="hand2").grid(row=2, columnspan=11, padx=5, pady=5)

root.mainloop()
