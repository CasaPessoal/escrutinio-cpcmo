import os
import unicodedata
import bcrypt
import flet as ft
from dotenv import load_dotenv
from supabase import create_client
from datetime import datetime

# --- CONFIGURAÇÃO ---
load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

estado_app = {"mesa_autenticada": None}

def remover_acentos(texto):
    if not texto: return ""
    nfkd_form = unicodedata.normalize('NFKD', texto)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

def verificar_login(nome_mesa, password_tentativa):
    try:
        response = supabase.table("mesas").select("password_hash").eq("nome_mesa", nome_mesa.strip()).execute()
        if not response.data: return False
        hash_guardado = response.data[0]['password_hash'].encode('utf-8')
        return bcrypt.checkpw(password_tentativa.encode('utf-8'), hash_guardado)
    except: return False

def registar_log(id_eleitor, mesa_id):
    try:
        log_data = {"eleitor_id": id_eleitor, "mesa_id": mesa_id, "timestamp": datetime.now().isoformat()}
        supabase.table("logs_votos").insert(log_data).execute()
    except Exception as e: print(f"Erro ao registar log: {e}")

def main(page: ft.Page):
    page.title = "Escrutínio - Ourique"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    # Sintaxe de borda universal
    borda_padrao = ft.Border(
        left=ft.BorderSide(1, ft.Colors.GREY_300),
        top=ft.BorderSide(1, ft.Colors.GREY_300),
        right=ft.BorderSide(1, ft.Colors.GREY_300),
        bottom=ft.BorderSide(1, ft.Colors.GREY_300)
    )

    def render_login():
        page.clean()
        mesa_field = ft.TextField(label="Nome da Mesa", width=300)
        pass_field = ft.TextField(label="Password", password=True, width=300)
        status_text = ft.Text("")

        def on_login_click(e):
            if verificar_login(mesa_field.value, pass_field.value):
                estado_app["mesa_autenticada"] = mesa_field.value.strip()
                render_votacao()
            else:
                status_text.value = "Credenciais inválidas!"
                page.update()

        page.add(ft.Column([
            ft.Text("Login de Acesso", size=20, weight="bold"),
            mesa_field, pass_field,
            ft.FilledButton("Entrar", on_click=on_login_click),
            status_text
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER))

    def render_votacao():
        page.clean()
        
        lbl_inscritos = ft.Text("0", size=20, weight="bold")
        lbl_votantes = ft.Text("0", size=20, weight="bold", color=ft.Colors.GREEN)
        lbl_abstencao = ft.Text("0%", size=20, weight="bold", color=ft.Colors.RED)
        row_progresso_mesas = ft.Row(alignment=ft.MainAxisAlignment.CENTER, wrap=True)
        lista_linhas = ft.Column(scroll=ft.ScrollMode.AUTO, height=400)
        txt_confirmacao = ft.Text("", size=16, weight="bold")
        
        bs = ft.BottomSheet(content=ft.Container(padding=20, content=ft.Column([
            ft.Text("Confirmação de Voto", size=20, weight="bold"), 
            txt_confirmacao, 
            ft.Row([ft.TextButton("Cancelar", on_click=lambda e: (setattr(bs, "open", False), page.update())), 
                    ft.FilledButton("CONFIRMAR VOTO", on_click=lambda e: processar_voto())], alignment=ft.MainAxisAlignment.CENTER)
        ])))
        page.overlay.append(bs)

        def processar_voto():
            supabase.table("eleitores").update({"Votou": True, "data_voto": datetime.now().isoformat()}).eq("id", bs.data).execute()
            registar_log(bs.data, estado_app["mesa_autenticada"])
            bs.open = False
            carregar_tabela("")
            page.snack_bar = ft.SnackBar(ft.Text("Voto registado com sucesso!"))
            page.snack_bar.open = True
            page.update()

        def carregar_tabela(termo=""):
            dados = supabase.table("eleitores").select("*").execute().data
            logs = supabase.table("logs_votos").select("mesa_id").execute().data
            total = len(dados)
            vot_count = len(logs)
            lbl_inscritos.value = str(total)
            lbl_votantes.value = str(vot_count)
            lbl_abstencao.value = f"{((total - vot_count) / total * 100):.1f}%" if total > 0 else "0%"
            
            votos_por_mesa = {}
            for log in logs: votos_por_mesa[log['mesa_id']] = votos_por_mesa.get(log['mesa_id'], 0) + 1
            row_progresso_mesas.controls.clear()
            for mesa, qtd in votos_por_mesa.items():
                row_progresso_mesas.controls.append(ft.Container(content=ft.Text(f"{mesa}: {(qtd/total*100):.1f}%", size=11), padding=5, bgcolor=ft.Colors.BLUE_50, border_radius=5))
            
            lista_ordenada = sorted([d for d in dados if not d.get("Votou")], key=lambda x: int(x.get("Num_Socio", 0)) if str(x.get("Num_Socio", 0)).isdigit() else 0)
            lista_linhas.controls.clear()
            for item in lista_ordenada:
                nome = item.get("Nome", "N/A")
                if remover_acentos(termo).lower() in remover_acentos(nome).lower():
                    lista_linhas.controls.append(ft.Container(content=ft.Row([
                        ft.Text(str(item.get("Num_Socio", "")), width=60), 
                        ft.Text(nome, expand=True), 
                        ft.Text(str(item.get("NIF", "")), width=100), 
                        ft.FilledButton("VOTAR", on_click=lambda e, i=item["id"], n=nome: (
                            setattr(bs, "data", i), setattr(txt_confirmacao, "value", f"Confirmar voto de: \"{n}\"?"), setattr(bs, "open", True), page.update()
                        ))
                    ]), padding=5, border=borda_padrao))
            page.update()

        page.add(ft.Column([
            ft.Text("Eleições Casa do Pessoal da CMO (2026-2029)", size=22, weight="bold"),
            ft.Row([
                ft.Card(ft.Container(ft.Column([ft.Text("Total"), lbl_inscritos], horizontal_alignment=ft.CrossAxisAlignment.CENTER), padding=20)),
                ft.Card(ft.Container(ft.Column([ft.Text("Votantes"), lbl_votantes], horizontal_alignment=ft.CrossAxisAlignment.CENTER), padding=20)),
                ft.Card(ft.Container(ft.Column([ft.Text("Abstenção"), lbl_abstencao], horizontal_alignment=ft.CrossAxisAlignment.CENTER), padding=20)),
                ft.Container(content=ft.Column([ft.Text("Afluência Por Mesa"), row_progresso_mesas], horizontal_alignment=ft.CrossAxisAlignment.CENTER), padding=10, border=borda_padrao, border_radius=10)
            ], alignment=ft.MainAxisAlignment.CENTER),
            ft.TextField(label="Pesquisar Eleitor", width=400, on_change=lambda e: carregar_tabela(e.control.value)),
            ft.Container(content=ft.Row([ft.Text("Sócio", weight="bold", width=60), ft.Text("Nome", weight="bold", expand=True), ft.Text("NIF", weight="bold", width=100), ft.Text("Ação", weight="bold", width=80)]), padding=10, bgcolor=ft.Colors.GREY_200),
            lista_linhas
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER))
        carregar_tabela()

    render_login()

if __name__ == "__main__":
    ft.app(target=main, port=int(os.environ.get("PORT", 8080)))
