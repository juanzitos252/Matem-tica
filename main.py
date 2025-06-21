import flet as ft
from flet import (
    Page, Text, ElevatedButton, Row, Column, TextField, View, Container,
    MainAxisAlignment, CrossAxisAlignment, FontWeight, alignment,
    TextAlign, ScrollMode, padding, border, KeyboardType
)
import random
import time

# --- Lógica do Quiz (sem alterações) ---
multiplicacoes_data = []
COOLDOWN_SEGUNDOS = 30

def inicializar_multiplicacoes():
    global multiplicacoes_data
    multiplicacoes_data = []
    for i in range(1, 11):
        for j in range(1, 11):
            multiplicacoes_data.append({
                'fator1': i, 'fator2': j, 'peso': 10.0, 'historico_erros': [],
                'vezes_apresentada': 0, 'vezes_correta': 0, 'ultima_vez_apresentada_ts': 0.0
            })

def selecionar_proxima_pergunta():
    global multiplicacoes_data
    agora_ts = time.time()
    perguntas_potenciais = [
        p for p in multiplicacoes_data if (agora_ts - p['ultima_vez_apresentada_ts']) > COOLDOWN_SEGUNDOS
    ]
    if not perguntas_potenciais:
        perguntas_potenciais = multiplicacoes_data
    if not perguntas_potenciais: return None
    perguntas_elegiveis_com_prioridade = []
    for pergunta_item in perguntas_potenciais:
        fator_peso = pergunta_item['peso']
        fator_erro_recente = 1.0
        if pergunta_item['historico_erros']:
            erros_recentes = sum(1 for erro in pergunta_item['historico_erros'] if erro)
            fator_erro_recente = 1 + (erros_recentes / len(pergunta_item['historico_erros']))
        fator_novidade = 1 / (1 + pergunta_item['vezes_apresentada'] * 0.05)
        prioridade = fator_peso * fator_erro_recente * fator_novidade
        perguntas_elegiveis_com_prioridade.append({'prioridade': prioridade, 'pergunta_original': pergunta_item})
    if not perguntas_elegiveis_com_prioridade:
        return random.choice(multiplicacoes_data) if multiplicacoes_data else None
    prioridades = [p['prioridade'] for p in perguntas_elegiveis_com_prioridade]
    perguntas_originais_refs = [p['pergunta_original'] for p in perguntas_elegiveis_com_prioridade]
    return random.choices(perguntas_originais_refs, weights=prioridades, k=1)[0]

def registrar_resposta(pergunta_selecionada_ref, acertou: bool):
    if not pergunta_selecionada_ref: return
    pergunta_selecionada_ref['vezes_apresentada'] += 1
    pergunta_selecionada_ref['ultima_vez_apresentada_ts'] = time.time()
    pergunta_selecionada_ref['historico_erros'].append(not acertou)
    pergunta_selecionada_ref['historico_erros'] = pergunta_selecionada_ref['historico_erros'][-5:]
    if acertou:
        pergunta_selecionada_ref['vezes_correta'] += 1
        pergunta_selecionada_ref['peso'] = max(1.0, pergunta_selecionada_ref['peso'] * 0.7)
    else:
        pergunta_selecionada_ref['peso'] = min(100.0, pergunta_selecionada_ref['peso'] * 1.6)

def gerar_opcoes(fator1: int, fator2: int, todas_multiplicacoes_data_ref):
    resposta_correta = fator1 * fator2
    opcoes = {resposta_correta}
    tentativas_max = 30
    count_tentativas = 0
    while len(opcoes) < 4 and count_tentativas < tentativas_max:
        count_tentativas += 1
        tipo_variacao = random.choice(['fator_adjacente', 'resultado_proximo', 'aleatorio_da_lista'])
        nova_opcao = -1
        if tipo_variacao == 'fator_adjacente':
            fator_modificado = random.choice([1, 2])
            if fator_modificado == 1:
                f1_mod = max(1, fator1 + random.choice([-2, -1, 1, 2]))
                nova_opcao = f1_mod * fator2
            else:
                f2_mod = max(1, fator2 + random.choice([-2, -1, 1, 2]))
                nova_opcao = fator1 * f2_mod
        elif tipo_variacao == 'resultado_proximo':
            offset_options = [-1, 1, -2, 2, -3, 3]
            if fator1 > 1: offset_options.extend([-fator1 // 2, fator1 // 2])
            if fator2 > 1: offset_options.extend([-fator2 // 2, fator2 // 2])
            if not offset_options: offset_options = [-1, 1]
            offset = random.choice(offset_options)
            if offset == 0: offset = random.choice([-1, 1]) if offset_options != [-1, 1] else 1
            nova_opcao = resposta_correta + offset
        elif tipo_variacao == 'aleatorio_da_lista':
            if todas_multiplicacoes_data_ref:
                pergunta_aleatoria = random.choice(todas_multiplicacoes_data_ref)
                nova_opcao = pergunta_aleatoria['fator1'] * pergunta_aleatoria['fator2']
        if nova_opcao == resposta_correta: continue
        if nova_opcao > 0: opcoes.add(nova_opcao)
    idx = 1
    while len(opcoes) < 4:
        alternativa = resposta_correta + idx
        if alternativa not in opcoes and alternativa > 0: opcoes.add(alternativa)
        if len(opcoes) < 4:
            alternativa_neg = resposta_correta - idx
            if alternativa_neg > 0 and alternativa_neg not in opcoes: opcoes.add(alternativa_neg)
        idx += 1
        if idx > max(fator1, fator2, 10) + 20: break
    while len(opcoes) < 4:
        rand_num = random.randint(1, max(100, resposta_correta + 30))
        if rand_num > 0 and rand_num not in opcoes: opcoes.add(rand_num)
    lista_opcoes = list(opcoes)
    random.shuffle(lista_opcoes)
    return lista_opcoes

def sugerir_tabuada_para_treino():
    global multiplicacoes_data
    if not multiplicacoes_data: return random.randint(1,10)
    pesos_por_tabuada = {i: 0.0 for i in range(1, 11)}
    contagem_por_tabuada = {i: 0 for i in range(1, 11)}
    for item in multiplicacoes_data:
        fator1, fator2, peso = item['fator1'], item['fator2'], item['peso']
        if fator1 in pesos_por_tabuada:
            pesos_por_tabuada[fator1] += peso
            contagem_por_tabuada[fator1] += 1
        if fator2 in pesos_por_tabuada and fator1 != fator2:
            pesos_por_tabuada[fator2] += peso
            contagem_por_tabuada[fator2] += 1
    media_pesos = { tab: pesos_por_tabuada[tab] / contagem_por_tabuada[tab] if contagem_por_tabuada[tab] > 0 else 0 for tab in pesos_por_tabuada }
    if not any(media_pesos.values()): return random.randint(1,10)
    return max(media_pesos, key=media_pesos.get)

inicializar_multiplicacoes()

# --- Constantes de UI ---
# Constantes de Dimensões e Espaçamento
BOTAO_LARGURA_PRINCIPAL = 220
BOTAO_ALTURA_PRINCIPAL = 50
BOTAO_LARGURA_OPCAO_QUIZ = 150
BOTAO_ALTURA_OPCAO_QUIZ = 50
PADDING_VIEW = padding.symmetric(horizontal=25, vertical=20)
ESPACAMENTO_COLUNA_GERAL = 20

# --- Novas Constantes de Cores (Paleta: Roxo, Azul, Rosa, Verde) ---
COR_ROXO_PRINCIPAL = ft.Colors.DEEP_PURPLE_400
COR_ROXO_ESCURO_TEXTO = ft.Colors.DEEP_PURPLE_700
COR_AZUL_BOTAO_OPCAO = ft.Colors.BLUE_300
COR_ROSA_DESTAQUE = ft.Colors.PINK_ACCENT_200 # Ou ft.Colors.PINK_300
COR_VERDE_ACERTO = ft.Colors.GREEN_600
COR_VERMELHO_ERRO = ft.Colors.RED_500 # Um pouco menos intenso que o RED_700 anterior
COR_TEXTO_SOBRE_ROXO = ft.Colors.WHITE
COR_TEXTO_SOBRE_AZUL = ft.Colors.WHITE # Ou BLACK87 se o azul for muito claro
COR_TEXTO_SOBRE_ROSA = ft.Colors.BLACK87 # Geralmente rosa claro pede texto escuro
COR_TEXTO_PADRAO_ESCURO = ft.Colors.BLACK87 # Para textos gerais sobre fundos claros
COR_TEXTO_TITULOS = COR_ROXO_ESCURO_TEXTO # Usar um roxo escuro para títulos
COR_FUNDO_PAGINA = ft.Colors.PURPLE_50 # Um roxo bem claro para o fundo geral
COR_FUNDO_CONTAINER_TREINO = ft.Colors.WHITE # Manter branco para clareza na área de treino
COR_BORDA_CONTAINER_TREINO = COR_ROXO_PRINCIPAL
COR_BOTAO_FEEDBACK_ACERTO_BG = ft.Colors.GREEN_100 # Fundo do botão de opção correto
COR_BOTAO_FEEDBACK_ERRO_BG = ft.Colors.RED_100   # Fundo do botão de opção errado

# --- Funções de Construção de Tela ---
def build_tela_apresentacao(page: Page):
    conteudo_apresentacao = Column(
        controls=[
            Text(
                "Quiz Mestre da Tabuada",
                size=32,
                weight=FontWeight.BOLD,
                text_align=TextAlign.CENTER,
                color=COR_TEXTO_TITULOS
            ),
            Text(
                "Aprenda e memorize a tabuada de forma divertida e adaptativa!",
                size=18,
                text_align=TextAlign.CENTER,
                color=COR_TEXTO_PADRAO_ESCURO
            ),
            Container(height=25),
            ElevatedButton(
                "Iniciar Quiz",
                width=BOTAO_LARGURA_PRINCIPAL, height=BOTAO_ALTURA_PRINCIPAL,
                on_click=lambda _: page.go("/quiz"),
                tooltip="Começar um novo quiz com perguntas aleatórias.",
                bgcolor=COR_ROXO_PRINCIPAL,
                color=COR_TEXTO_SOBRE_ROXO
            ),
            Container(height=15),
            ElevatedButton(
                "Modo Treino",
                width=BOTAO_LARGURA_PRINCIPAL, height=BOTAO_ALTURA_PRINCIPAL,
                on_click=lambda _: page.go("/treino"),
                tooltip="Treinar uma tabuada específica ou uma sugerida.",
                bgcolor=COR_ROXO_PRINCIPAL,
                color=COR_TEXTO_SOBRE_ROXO
            ),
        ],
        alignment=MainAxisAlignment.CENTER,
        horizontal_alignment=CrossAxisAlignment.CENTER,
        spacing=ESPACAMENTO_COLUNA_GERAL
    )
    return Container(content=conteudo_apresentacao, alignment=alignment.center, expand=True, padding=PADDING_VIEW)

def build_tela_quiz(page: Page):
    texto_pergunta = Text(
        size=30,
        weight=FontWeight.BOLD,
        text_align=TextAlign.CENTER,
        color=COR_TEXTO_TITULOS
    )
    botoes_opcoes = [
        ElevatedButton(
            width=BOTAO_LARGURA_OPCAO_QUIZ, height=BOTAO_ALTURA_OPCAO_QUIZ,
            # bgcolor e color serão definidos em carregar_nova_pergunta
        ) for _ in range(4)
    ]
    texto_feedback = Text(size=18, weight=FontWeight.BOLD, text_align=TextAlign.CENTER) # Cor definida dinamicamente

    def handle_resposta(e, botao_clicado_ref, todos_botoes_opcoes_ref, txt_feedback_ctrl_ref, btn_proxima_ctrl_ref):
        dados_botao = botao_clicado_ref.data
        era_correta = dados_botao['correta']
        pergunta_original_ref = dados_botao['pergunta_original']
        registrar_resposta(pergunta_original_ref, era_correta)
        if era_correta:
            txt_feedback_ctrl_ref.value = "Correto!"
            txt_feedback_ctrl_ref.color = COR_VERDE_ACERTO
            botao_clicado_ref.bgcolor = COR_BOTAO_FEEDBACK_ACERTO_BG
            # botao_clicado_ref.color = COR_VERDE_ACERTO # Opcional, se o texto precisar mudar
        else:
            resposta_certa_valor = pergunta_original_ref['fator1'] * pergunta_original_ref['fator2']
            txt_feedback_ctrl_ref.value = f"Errado! A resposta era {resposta_certa_valor}"
            txt_feedback_ctrl_ref.color = COR_VERMELHO_ERRO
            botao_clicado_ref.bgcolor = COR_BOTAO_FEEDBACK_ERRO_BG
            # botao_clicado_ref.color = COR_VERMELHO_ERRO # Opcional
        for btn in todos_botoes_opcoes_ref: btn.disabled = True
        btn_proxima_ctrl_ref.visible = True
        page.update()

    botao_proxima = ElevatedButton(
        "Próxima Pergunta",
        on_click=None, visible=False,
        width=BOTAO_LARGURA_PRINCIPAL, height=BOTAO_ALTURA_PRINCIPAL,
        tooltip="Carregar a próxima pergunta do quiz.",
        bgcolor=COR_ROXO_PRINCIPAL,
        color=COR_TEXTO_SOBRE_ROXO
    )

    def carregar_nova_pergunta(page_ref, txt_pergunta_ctrl_ref, btn_opcoes_ctrls_ref, txt_feedback_ctrl_ref, btn_proxima_ctrl_ref):
        pergunta_selecionada = selecionar_proxima_pergunta()
        if not pergunta_selecionada:
            txt_pergunta_ctrl_ref.value = "Nenhuma pergunta disponível."
            for btn in btn_opcoes_ctrls_ref: btn.visible = False
            txt_feedback_ctrl_ref.value = ""
            btn_proxima_ctrl_ref.visible = False
            page_ref.update()
            return
        resposta_correta_valor = pergunta_selecionada['fator1'] * pergunta_selecionada['fator2']
        opcoes = gerar_opcoes(pergunta_selecionada['fator1'], pergunta_selecionada['fator2'], multiplicacoes_data)
        txt_pergunta_ctrl_ref.value = f"{pergunta_selecionada['fator1']} x {pergunta_selecionada['fator2']} = ?"
        for i in range(4):
            btn_opcoes_ctrls_ref[i].text = str(opcoes[i])
            btn_opcoes_ctrls_ref[i].data = {'opcao': opcoes[i], 'correta': opcoes[i] == resposta_correta_valor, 'pergunta_original': pergunta_selecionada}
            current_button = btn_opcoes_ctrls_ref[i]
            btn_opcoes_ctrls_ref[i].on_click = lambda e, btn=current_button: handle_resposta(page_ref, btn, btn_opcoes_ctrls_ref, txt_feedback_ctrl_ref, btn_proxima_ctrl_ref)
            btn_opcoes_ctrls_ref[i].bgcolor = COR_AZUL_BOTAO_OPCAO # Estado normal
            btn_opcoes_ctrls_ref[i].color = COR_TEXTO_SOBRE_AZUL   # Estado normal
            btn_opcoes_ctrls_ref[i].disabled = False
            btn_opcoes_ctrls_ref[i].visible = True
        txt_feedback_ctrl_ref.value = ""
        btn_proxima_ctrl_ref.visible = False
        page_ref.update()

    botao_proxima.on_click = lambda _: carregar_nova_pergunta(page, texto_pergunta, botoes_opcoes, texto_feedback, botao_proxima)
    carregar_nova_pergunta(page, texto_pergunta, botoes_opcoes, texto_feedback, botao_proxima)

    botao_voltar = ElevatedButton(
        "Voltar ao Menu",
        on_click=lambda _: page.go("/"),
        width=BOTAO_LARGURA_PRINCIPAL, height=BOTAO_ALTURA_PRINCIPAL,
        tooltip="Retornar à tela inicial.",
        bgcolor=COR_ROXO_PRINCIPAL,
        color=COR_TEXTO_SOBRE_ROXO
    )

    layout_botoes_opcoes = Column(
        [
            Row(botoes_opcoes[0:2], alignment=MainAxisAlignment.CENTER, spacing=15),
            Container(height=10),
            Row(botoes_opcoes[2:4], alignment=MainAxisAlignment.CENTER, spacing=15),
        ],
        horizontal_alignment=CrossAxisAlignment.CENTER, spacing=10
    )

    conteudo_quiz = Column(
        controls=[
            texto_pergunta,
            Container(height=15),
            layout_botoes_opcoes,
            Container(height=15),
            texto_feedback,
            Container(height=20),
            botao_proxima,
            Container(height=10),
            botao_voltar
        ],
        alignment=MainAxisAlignment.CENTER,
        horizontal_alignment=CrossAxisAlignment.CENTER,
        spacing=ESPACAMENTO_COLUNA_GERAL,
        scroll=ScrollMode.AUTO
    )
    return Container(content=conteudo_quiz, alignment=alignment.center, expand=True, padding=PADDING_VIEW)

def build_tela_treino(page: Page):
    tabuada_sugerida = sugerir_tabuada_para_treino()
    titulo_treino = Text(
        f"Treinando a Tabuada do {tabuada_sugerida}",
        size=28,
        weight=FontWeight.BOLD,
        text_align=TextAlign.CENTER,
        color=COR_TEXTO_TITULOS
    )
    campos_tabuada_refs = []
    coluna_itens_tabuada = Column(spacing=10, scroll=ScrollMode.AUTO, expand=True, horizontal_alignment=CrossAxisAlignment.CENTER)

    for i in range(1, 11):
        resposta_correta_val = tabuada_sugerida * i
        texto_multiplicacao = Text(
            f"{tabuada_sugerida} x {i} = ",
            size=18,
            color=COR_TEXTO_PADRAO_ESCURO
        )
        campo_resposta = TextField(
            width=100, text_align=TextAlign.CENTER,
            data={'fator1': tabuada_sugerida, 'fator2': i, 'resposta_correta': resposta_correta_val},
            keyboard_type=KeyboardType.NUMBER # Corrigido para ft.KeyboardType
        )
        campos_tabuada_refs.append(campo_resposta)
        coluna_itens_tabuada.controls.append(Row([texto_multiplicacao, campo_resposta], alignment=MainAxisAlignment.CENTER, spacing=10))

    texto_resumo_treino = Text(
        size=18,
        weight=FontWeight.BOLD,
        text_align=TextAlign.CENTER,
        color=COR_TEXTO_PADRAO_ESCURO
    )

    botao_verificar = ElevatedButton(
        "Verificar Respostas",
        width=BOTAO_LARGURA_PRINCIPAL, height=BOTAO_ALTURA_PRINCIPAL,
        tooltip="Corrigir as respostas da tabuada.",
        bgcolor=COR_ROXO_PRINCIPAL,
        color=COR_TEXTO_SOBRE_ROXO
    )

    def handle_verificar_treino(e):
        acertos = 0
        total_questoes = len(campos_tabuada_refs)
        for campo in campos_tabuada_refs:
            dados_campo = campo.data
            fator1, fator2, resposta_correta_esperada = dados_campo['fator1'], dados_campo['fator2'], dados_campo['resposta_correta']
            resposta_usuario_str = campo.value
            acertou_questao = False
            try:
                resposta_usuario_int = int(resposta_usuario_str)
                if resposta_usuario_int == resposta_correta_esperada:
                    acertos += 1
                    acertou_questao = True
                    campo.border_color = COR_VERDE_ACERTO
                else:
                    campo.border_color = COR_VERMELHO_ERRO
            except ValueError:
                campo.border_color = COR_VERMELHO_ERRO
            campo.disabled = True
            pergunta_ref = next((p for p in multiplicacoes_data if (p['fator1'] == fator1 and p['fator2'] == fator2) or (p['fator1'] == fator2 and p['fator2'] == fator1)), None)
            if pergunta_ref:
                registrar_resposta(pergunta_ref, acertou_questao)
        texto_resumo_treino.value = f"Você acertou {acertos} de {total_questoes}!"
        botao_verificar.disabled = True
        page.update()

    botao_verificar.on_click = handle_verificar_treino
    botao_voltar_menu = ElevatedButton(
        "Voltar ao Menu",
        on_click=lambda _: page.go("/"),
        width=BOTAO_LARGURA_PRINCIPAL, height=BOTAO_ALTURA_PRINCIPAL,
        tooltip="Retornar à tela inicial.",
        bgcolor=COR_ROXO_PRINCIPAL,
        color=COR_TEXTO_SOBRE_ROXO
    )

    container_tabuada = Container(
        content=coluna_itens_tabuada,
        border=border.all(2, COR_BORDA_CONTAINER_TREINO), # Aumentei a espessura da borda para 2
        border_radius=8,
        padding=padding.all(15),
        width=360,
        height=420,
        bgcolor=COR_FUNDO_CONTAINER_TREINO
    )

    conteudo_treino = Column(
        controls=[
            titulo_treino,
            Container(height=10),
            container_tabuada,
            Container(height=10),
            botao_verificar,
            Container(height=10),
            texto_resumo_treino,
            Container(height=15),
            botao_voltar_menu
        ],
        alignment=MainAxisAlignment.CENTER,
        horizontal_alignment=CrossAxisAlignment.CENTER,
        spacing=ESPACAMENTO_COLUNA_GERAL,
        scroll=ScrollMode.AUTO
    )
    return Container(content=conteudo_treino, alignment=alignment.center, expand=True, padding=PADDING_VIEW)

# --- Configuração Principal da Página e Rotas ---
def main(page: Page):
    page.title = "Quiz Mestre da Tabuada"
    page.vertical_alignment = MainAxisAlignment.CENTER
    page.horizontal_alignment = CrossAxisAlignment.CENTER
    page.bgcolor = COR_FUNDO_PAGINA # Aplicando a nova cor de fundo da página
    page.window_width = 480
    page.window_height = 800
    page.fonts = {
        "RobotoSlab": "https://github.com/google/fonts/raw/main/apache/robotoslab/RobotoSlab%5Bwght%5D.ttf"
    }
    # page.theme = ft.Theme(font_family="RobotoSlab") # Ativar a fonte (opcional)

    def route_change(route):
        page.views.clear()
        page.views.append(
            View(
                route="/",
                controls=[build_tela_apresentacao(page)],
                vertical_alignment=MainAxisAlignment.CENTER,
                horizontal_alignment=CrossAxisAlignment.CENTER
            )
        )
        if page.route == "/quiz":
            page.views.append(
                View(
                    route="/quiz",
                    controls=[build_tela_quiz(page)],
                    vertical_alignment=MainAxisAlignment.CENTER,
                    horizontal_alignment=CrossAxisAlignment.CENTER
                )
            )
        elif page.route == "/treino":
            page.views.append(
                View(
                    route="/treino",
                    controls=[build_tela_treino(page)],
                    vertical_alignment=MainAxisAlignment.CENTER,
                    horizontal_alignment=CrossAxisAlignment.CENTER
                )
            )
        page.update()

    def view_pop(view_instance):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.go("/")

ft.app(target=main)
