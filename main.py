import os
import unicodedata
import flet as ft
from dotenv import load_dotenv
from supabase import create_client
from datetime import datetime
import asyncio

# --- CONFIGURAÇÃO ---
load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

def remover_acentos(texto):
    if not texto: return ""
    nfkd_form = unicodedata.normalize('NFKD', texto)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

def main(page: ft.Page):
    page.title = "Escrutínio - Ourique"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    # Elementos de UI globais
    lbl_inscritos = ft.Text("0", size=20, weight="bold")
    lbl_votantes = ft.Text("0", size=20, weight="bold", color=ft.Colors.GREEN)
    lbl_abstencao = ft.Text("0%", size=20, weight="bold", color=ft.Colors.RED)
    tabela = ft.DataTable(columns=[
        ft.DataColumn(ft.Text("Sócio")), ft.DataColumn(ft.Text("Nome")), 
        ft.DataColumn(ft.Text("NIF")), ft.DataColumn(ft.Text("Ação"))
    ])
    
    txt_confirmacao = ft.Text("", size=16, weight="bold")
    bs = ft.BottomSheet(content=ft.Container(padding=20, content=ft.Column([
        ft.Text("Confirmação de Voto", size=20, weight="bold"), txt_confirmacao,
        ft.Row([ft.TextButton("Cancelar", on_click=lambda e: setattr(bs, "open", False) or page.update()), 
                ft.FilledButton("CONFIRMAR", on_click=lambda e: processar_voto())], alignment=ft.MainAxisAlignment.CENTER)
    ])))
    page.overlay.append(bs)

    def carregar_tabela(termo=""):
        dados = supabase.table("eleitores").select("*").execute().data
        total = len(dados)
        votantes = len([d for d in dados if d.get("Votou")])
        lbl_inscritos.value, lbl_votantes.value = str(total), str(votantes)
        lbl_abstencao.value = f"{((total - votantes) / total * 100):.1f}%" if total > 0 else "0%"
        
        tabela.rows.clear()
        for item in sorted([d for d in dados if not d.get("Votou")], key=lambda x: int(x.get("Num_Socio") or 0)):
            if remover_acentos(termo).lower() in remover_acentos(item.get("Nome", "")).lower():
                tabela.rows.append(ft.DataRow(cells=[
                    ft.DataCell(ft.Text(str(item.get("Num_Socio", "")))),
                    ft.DataCell(ft.Text(item.get("Nome", ""))),
                    ft.DataCell(ft.Text(str(item.get("NIF", "")))),
                    ft.DataCell(ft.FilledButton("VOTAR", on_click=lambda e, i=item["id"], n=item["Nome"]: 
                        setattr(bs, "data", i) or setattr(txt_confirmacao, "value", f"Confirmar voto de {n}?") or setattr(bs, "open", True) or page.update()))
                ]))
        page.update()

    def processar_voto():
        supabase.table("eleitores").update({"Votou": True, "data_voto": datetime.now().isoformat()}).eq("id", bs.data).execute()
        bs.open = False
        page.snack_bar = ft.SnackBar(ft.Text("Voto registado com sucesso!"))
        page.snack_bar.open = True
        carregar_tabela()

    # Loop de atualização assíncrono (Web Friendly)
    async def auto_refresh():
        while True:
            await asyncio.sleep(10)
            carregar_tabela(campo_pesquisa.value)

    campo_pesquisa = ft.TextField(label="Pesquisar Eleitor", width=400, on_change=lambda e: carregar_tabela(e.control.value))
    
    page.add(
        ft.Text("Eleições Casa do Pessoal da CMO (2026-2029)", size=22, weight="bold"),
        ft.Row([ft.Card(ft.Container(ft.Column([ft.Text("Total"), lbl_inscritos]), padding=10)),
                ft.Card(ft.Container(ft.Column([ft.Text("Votantes"), lbl_votantes]), padding=10)),
                ft.Card(ft.Container(ft.Column([ft.Text("Abstenção"), lbl_abstencao]), padding=10))], alignment=ft.MainAxisAlignment.CENTER),
        campo_pesquisa, ft.ListView([tabela], expand=True, height=400)
    )
    
    carregar_tabela()
    page.run_task(auto_refresh) # Forma correta de rodar background tasks no Flet web

if __name__ == "__main__":
    ft.app(target=main, port=int(os.environ.get("PORT", 8080)), view=ft.AppView.WEB_BROWSER)
