import flet as ft
from flet import (
    Page, Text, ElevatedButton, Row, Column, TextField, View, Container,
    MainAxisAlignment, CrossAxisAlignment, FontWeight, colors, alignment,
    TextAlign, ScrollMode, padding, border
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
COR_FUNDO_PAGINA = colors.BLUE_GREY_50 # Mais suave
BOTAO_LARGURA_PRINCIPAL = 220
BOTAO_ALTURA_PRINCIPAL = 50
BOTAO_LARGURA_OPCAO_QUIZ = 150
BOTAO_ALTURA_OPCAO_QUIZ = 50
PADDING_VIEW = padding.symmetric(horizontal=25, vertical=20)
ESPACAMENTO_COLUNA_GERAL = 20

# --- Funções de Construção de Tela ---
def build_tela_apresentacao(page: Page):
    conteudo_apresentacao = Column(
        controls=[
            Text("Quiz Mestre da Tabuada", size=32, weight=FontWeight.BOLD, text_align=TextAlign.CENTER), # Ajuste leve no tamanho
            Text("Aprenda e memorize a tabuada de forma divertida e adaptativa!", size=18, text_align=TextAlign.CENTER),
            Container(height=25), # Aumentar espaçamento
            ElevatedButton(
                "Iniciar Quiz",
                width=BOTAO_LARGURA_PRINCIPAL, height=BOTAO_ALTURA_PRINCIPAL,
                on_click=lambda _: page.go("/quiz"),
                tooltip="Começar um novo quiz com perguntas aleatórias."
            ),
            Container(height=15),
            ElevatedButton(
                "Modo Treino",
                width=BOTAO_LARGURA_PRINCIPAL, height=BOTAO_ALTURA_PRINCIPAL,
                on_click=lambda _: page.go("/treino"),
                tooltip="Treinar uma tabuada específica ou uma sugerida."
            ),
        ],
        alignment=MainAxisAlignment.CENTER,
        horizontal_alignment=CrossAxisAlignment.CENTER,
        spacing=ESPACAMENTO_COLUNA_GERAL # Usar constante
    )
    return Container(content=conteudo_apresentacao, alignment=alignment.center, expand=True, padding=PADDING_VIEW)

def build_tela_quiz(page: Page):
    texto_pergunta = Text(size=30, weight=FontWeight.BOLD, text_align=TextAlign.CENTER) # Ajuste leve
    botoes_opcoes = [ElevatedButton(width=BOTAO_LARGURA_OPCAO_QUIZ, height=BOTAO_ALTURA_OPCAO_QUIZ) for _ in range(4)]
    texto_feedback = Text(size=18, weight=FontWeight.BOLD, text_align=TextAlign.CENTER) # Consistente com subtitulo

    def handle_resposta(e, botao_clicado_ref, todos_botoes_opcoes_ref, txt_feedback_ctrl_ref, btn_proxima_ctrl_ref):
        dados_botao = botao_clicado_ref.data
        era_correta = dados_botao['correta']
        pergunta_original_ref = dados_botao['pergunta_original']
        registrar_resposta(pergunta_original_ref, era_correta)
        if era_correta:
            txt_feedback_ctrl_ref.value = "Correto!"
            txt_feedback_ctrl_ref.color = colors.GREEN_700 # Ajuste para verde mais padrão
            botao_clicado_ref.bgcolor = colors.GREEN_100
        else:
            resposta_certa_valor = pergunta_original_ref['fator1'] * pergunta_original_ref['fator2']
            txt_feedback_ctrl_ref.value = f"Errado! A resposta era {resposta_certa_valor}"
            txt_feedback_ctrl_ref.color = colors.RED_700 # Ajuste para vermelho mais padrão
            botao_clicado_ref.bgcolor = colors.RED_100
        for btn in todos_botoes_opcoes_ref: btn.disabled = True
        btn_proxima_ctrl_ref.visible = True
        page.update()

    botao_proxima = ElevatedButton(
        "Próxima Pergunta",
        on_click=None, visible=False,
        width=BOTAO_LARGURA_PRINCIPAL, height=BOTAO_ALTURA_PRINCIPAL,
        tooltip="Carregar a próxima pergunta do quiz."
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
            btn_opcoes_ctrls_ref[i].bgcolor = None
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
        tooltip="Retornar à tela inicial."
    )

    layout_botoes_opcoes = Column(
        [
            Row(botoes_opcoes[0:2], alignment=MainAxisAlignment.CENTER, spacing=15), # Aumentar espaçamento
            Container(height=10),
            Row(botoes_opcoes[2:4], alignment=MainAxisAlignment.CENTER, spacing=15), # Aumentar espaçamento
        ],
        horizontal_alignment=CrossAxisAlignment.CENTER, spacing=10
    )

    conteudo_quiz = Column(
        controls=[
            texto_pergunta,
            Container(height=15), # Ajuste de espaçamento
            layout_botoes_opcoes,
            Container(height=15),
            texto_feedback,
            Container(height=20), # Aumentar antes do botão próxima
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
    titulo_treino = Text(f"Treinando a Tabuada do {tabuada_sugerida}", size=28, weight=FontWeight.BOLD, text_align=TextAlign.CENTER)
    campos_tabuada_refs = []
    coluna_itens_tabuada = Column(spacing=10, scroll=ScrollMode.AUTO, expand=True, horizontal_alignment=CrossAxisAlignment.CENTER) # spacing 10

    for i in range(1, 11):
        resposta_correta_val = tabuada_sugerida * i
        texto_multiplicacao = Text(f"{tabuada_sugerida} x {i} = ", size=18)
        campo_resposta = TextField(
            width=100, text_align=TextAlign.CENTER,
            data={'fator1': tabuada_sugerida, 'fator2': i, 'resposta_correta': resposta_correta_val},
            keyboard_type=ft.KeyboardType.NUMBER
        )
        campos_tabuada_refs.append(campo_resposta)
        coluna_itens_tabuada.controls.append(Row([texto_multiplicacao, campo_resposta], alignment=MainAxisAlignment.CENTER, spacing=10))

    texto_resumo_treino = Text(size=18, weight=FontWeight.BOLD, text_align=TextAlign.CENTER)

    botao_verificar = ElevatedButton(
        "Verificar Respostas",
        width=BOTAO_LARGURA_PRINCIPAL, height=BOTAO_ALTURA_PRINCIPAL,
        tooltip="Corrigir as respostas da tabuada."
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
                    campo.border_color = colors.GREEN_700
                else:
                    campo.border_color = colors.RED_700
            except ValueError:
                campo.border_color = colors.RED_700
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
        tooltip="Retornar à tela inicial."
    )

    container_tabuada = Container(
        content=coluna_itens_tabuada,
        border=border.all(1, colors.BLACK26),
        border_radius=8, # Aumentar border_radius
        padding=padding.all(15), # Aumentar padding interno
        width=360, # Aumentar largura
        height=420 # Aumentar altura
    )

    conteudo_treino = Column(
        controls=[
            titulo_treino,
            Container(height=10), # Ajuste
            container_tabuada,
            Container(height=10), # Ajuste
            botao_verificar,
            Container(height=10),
            texto_resumo_treino,
            Container(height=15), # Aumentar antes do botão voltar
            botao_voltar_menu
        ],
        alignment=MainAxisAlignment.CENTER, # Centralizar todo o conteúdo da tela de treino
        horizontal_alignment=CrossAxisAlignment.CENTER,
        spacing=ESPACAMENTO_COLUNA_GERAL, # Usar constante
        scroll=ScrollMode.AUTO
    )
    return Container(content=conteudo_treino, alignment=alignment.center, expand=True, padding=PADDING_VIEW)

# --- Configuração Principal da Página e Rotas ---
def main(page: Page):
    page.title = "Quiz Mestre da Tabuada"
    page.vertical_alignment = MainAxisAlignment.CENTER
    page.horizontal_alignment = CrossAxisAlignment.CENTER
    page.bgcolor = COR_FUNDO_PAGINA
    page.window_width = 480 # Aumentar um pouco a largura
    page.window_height = 800 # Aumentar um pouco a altura
    page.fonts = { # Exemplo de como adicionar uma fonte personalizada (se desejado e disponível no ambiente)
        "RobotoSlab": "https://github.com/google/fonts/raw/main/apache/robotoslab/RobotoSlab%5Bwght%5D.ttf"
    }
    # page.theme = ft.Theme(font_family="RobotoSlab") # Ativar a fonte (opcional)


    def route_change(route):
        page.views.clear()
        # Adiciona a view da rota raiz (Tela de Apresentação)
        page.views.append(
            View(
                route="/",
                controls=[build_tela_apresentacao(page)],
                vertical_alignment=MainAxisAlignment.CENTER, # Centraliza o container da tela
                horizontal_alignment=CrossAxisAlignment.CENTER
            )
        )
        if page.route == "/quiz":
            page.views.append(
                View(
                    route="/quiz",
                    controls=[build_tela_quiz(page)],
                    vertical_alignment=MainAxisAlignment.CENTER, # Centraliza o container da tela
                    horizontal_alignment=CrossAxisAlignment.CENTER
                )
            )
        elif page.route == "/treino":
            page.views.append(
                View(
                    route="/treino",
                    controls=[build_tela_treino(page)],
                    vertical_alignment=MainAxisAlignment.CENTER, # Centraliza o container da tela
                    horizontal_alignment=CrossAxisAlignment.CENTER
                )
            )
        page.update()

    def view_pop(view_instance): # Renomeado para clareza
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.go("/")

ft.app(target=main)
