def main(page: ft.Page):
    page.title = "Escrutínio - Ourique"
    page.theme_mode = ft.ThemeMode.LIGHT
    
    # Estado da aplicação
    estado_app = {"mesa_autenticada": None}

    def render_login():
        page.clean()
        mesa_field = ft.TextField(label="Nome da Mesa", width=300)
        pass_field = ft.TextField(label="Password", password=True, width=300)
        status_text = ft.Text("")

        def on_login_click(e):
            # Usando a lógica de login que já tinhas
            if verificar_login(mesa_field.value, pass_field.value):
                estado_app["mesa_autenticada"] = mesa_field.value.strip()
                render_votacao() # Entra na votação
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
        # ... (aqui inseres o código da interface de votação que já tínhamos, 
        # garantindo que o carregar_tabela() é chamado aqui dentro)
        # ...
        carregar_tabela()
        page.update()

    # Iniciar a app pelo Login
    render_login()
