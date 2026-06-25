import flet as ft
from supabase import create_client
import os
import time
import threading
import unicodedata
from dotenv import load_dotenv
from datetime import datetime

# Carregar variáveis de ambiente
load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# Função para remover acentos
def remover_acentos(texto):
    if not texto: return ""
    nfkd_form = unicodedata.normalize('NFKD', texto)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

def main(page: ft.Page):
    page.title = "Escrutínio - Ourique"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 800
    page.window_height = 900
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    # Campo de pesquisa global
    campo_pesquisa = ft.TextField(label="Pesquisar Eleitor", width=400, on_change=lambda e: carregar_tabela(e.control.value))

    lbl_inscritos = ft.Text("0", size=20, weight="bold")
    lbl_votantes = ft.Text("0", size=20, weight="bold", color=ft.Colors.GREEN)
    lbl_abstencao = ft.Text("0%", size=20, weight="bold", color=ft.Colors.RED)
    
    txt_confirmacao = ft.Text("", size=16)

    def processar_voto(e):
        id_eleitor = bs.data 
        try:
            supabase.table("eleitores").update({"Votou": True, "data_voto": datetime.now().isoformat()}).eq("id", id_eleitor).execute()
            
            # Limpar o campo e recarregar
            bs.open = False
            campo_pesquisa.value = "" 
            campo_pesquisa.update()
            
            carregar_tabela(campo_pesquisa.value) 
            
            page.snack_bar = ft.SnackBar(ft.Text("Voto registado com sucesso!"))
            page.snack_bar.open = True
        except Exception as ex:
            print(f"ERRO: {ex}")
        page.update()

    bs = ft.BottomSheet(
        content=ft.Container(
            padding=20,
            content=ft.Column([
                ft.Text("Confirmação de Voto", size=20, weight="bold"),
                txt_confirmacao,
                ft.Row([
                    ft.TextButton("Cancelar", on_click=lambda e: (setattr(bs, "open", False), page.update())),
                    ft.FilledButton("CONFIRMAR VOTO", on_click=processar_voto),
                ], alignment=ft.MainAxisAlignment.CENTER),
            ], tight=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        ),
    )
    page.overlay.append(bs)

    def abrir_confirmacao(id_eleitor, nome):
        bs.data = id_eleitor  
        txt_confirmacao.value = f"Deseja confirmar o voto de: {nome}?"
        bs.open = True
        page.update()

    tabela = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Sócio")),
            ft.DataColumn(ft.Text("Nome")),
            ft.DataColumn(ft.Text("NIF")),
            ft.DataColumn(ft.Text("Ação")),
        ],
        rows=[]
    )

    def carregar_tabela(termo=""):
        try:
            todos = supabase.table("eleitores").select("*").execute()
            lista_total = todos.data
            total = len(lista_total)
            votantes = len([e for e in lista_total if e.get("Votou") is True])
            abstencao = ((total - votantes) / total * 100) if total > 0 else 0
            
            lbl_inscritos.value = str(total)
            lbl_votantes.value = str(votantes)
            lbl_abstencao.value = f"{abstencao:.1f}%"
            
            response = supabase.table("eleitores").select("*").is_("Votou", "false").execute()
            lista_eleitores = response.data
            
            termo_limpo = remover_acentos(termo).lower()
            
            tabela.rows.clear()
            for item in lista_eleitores:
                nome_limpo = remover_acentos(item.get("Nome", "")).lower()
                nif_str = str(item.get("NIF", ""))
                socio_str = str(item.get("Num_Socio", ""))
                
                if termo_limpo in nome_limpo or termo_limpo in nif_str or termo_limpo in socio_str:
                    id_e = item["id"]
                    tabela.rows.append(
                        ft.DataRow(cells=[
                            ft.DataCell(ft.Text(socio_str)),
                            ft.DataCell(ft.Text(item.get("Nome", "N/A"))),
                            ft.DataCell(ft.Text(nif_str)),
                            ft.DataCell(ft.FilledButton("VOTAR", on_click=lambda e, i=id_e, n=item.get("Nome"): abrir_confirmacao(i, n))),
                        ])
                    )
            page.update()
        except Exception as ex:
            print(f"Erro ao carregar: {ex}")

    def auto_refresh():
        while True:
            time.sleep(5)
            carregar_tabela(campo_pesquisa.value)

    threading.Thread(target=auto_refresh, daemon=True).start()

    lista_scroll = ft.ListView(controls=[tabela], expand=True, spacing=10, padding=20)
    container_tabela = ft.Container(
        content=lista_scroll,
        height=450,
        border=ft.Border(
            left=ft.BorderSide(1, ft.Colors.OUTLINE),
            top=ft.BorderSide(1, ft.Colors.OUTLINE),
            right=ft.BorderSide(1, ft.Colors.OUTLINE),
            bottom=ft.BorderSide(1, ft.Colors.OUTLINE)
        ),
        border_radius=10,
    )

    page.add(
        ft.Column([
            ft.Text("Eleições dos Órgãos da Casa do Pessoal da CMO (2026 - 2029)", size=22, weight="bold", text_align=ft.TextAlign.CENTER),
            ft.Text("Escrutínio Digital", size=18, color=ft.Colors.BLUE),
            ft.Row([
                ft.Card(content=ft.Container(ft.Column([ft.Text("Total Inscritos"), lbl_inscritos], horizontal_alignment=ft.CrossAxisAlignment.CENTER), padding=10)),
                ft.Card(content=ft.Container(ft.Column([ft.Text("Total Votantes"), lbl_votantes], horizontal_alignment=ft.CrossAxisAlignment.CENTER), padding=10)),
                ft.Card(content=ft.Container(ft.Column([ft.Text("Abstenção"), lbl_abstencao], horizontal_alignment=ft.CrossAxisAlignment.CENTER), padding=10)),
            ], alignment=ft.MainAxisAlignment.CENTER),
            campo_pesquisa,
            container_tabela
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    )
    
    carregar_tabela()

if __name__ == "__main__":
    # Configuração de porta dinâmica para Cloud
    port = int(os.environ.get("PORT", 8080))
    ft.app(target=main, port=port, view=ft.AppView.WEB_BROWSER)