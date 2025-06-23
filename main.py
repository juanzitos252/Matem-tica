import flet as ft
from flet import (
    Page, Text, ElevatedButton, Row, Column, TextField, View, Container,
    MainAxisAlignment, CrossAxisAlignment, FontWeight, alignment,
    TextAlign, ScrollMode, padding, border, KeyboardType,
    Animation, AnimationCurve, ProgressBar # Margin removida
)
import random
import time

# --- Lógica do Quiz ---
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

def gerar_opcoes_quiz_invertido(multiplicacao_base_ref, todas_multiplicacoes_data_ref):
    resposta_correta_valor = multiplicacao_base_ref['fator1'] * multiplicacao_base_ref['fator2']
    opcao_correta_obj = {'texto': f"{multiplicacao_base_ref['fator1']} x {multiplicacao_base_ref['fator2']}", 'original_ref': multiplicacao_base_ref, 'is_correct': True}
    opcoes_geradas = [opcao_correta_obj]
    candidatos_embaralhados = random.sample(todas_multiplicacoes_data_ref, len(todas_multiplicacoes_data_ref))
    for item_candidato in candidatos_embaralhados:
        if len(opcoes_geradas) >= 4: break
        if item_candidato['fator1'] == multiplicacao_base_ref['fator1'] and item_candidato['fator2'] == multiplicacao_base_ref['fator2']: continue
        if item_candidato['fator1'] * item_candidato['fator2'] == resposta_correta_valor: continue
        opcoes_geradas.append({'texto': f"{item_candidato['fator1']} x {item_candidato['fator2']}", 'original_ref': item_candidato, 'is_correct': False})
    tentativas_fallback = 0
    while len(opcoes_geradas) < 4 and tentativas_fallback < 50:
        tentativas_fallback += 1
        f1, f2 = random.randint(1, 10), random.randint(1, 10)
        if (f1 == multiplicacao_base_ref['fator1'] and f2 == multiplicacao_base_ref['fator2']) or (f1 * f2 == resposta_correta_valor): continue
        existe = any((op['original_ref']['fator1'] == f1 and op['original_ref']['fator2'] == f2) or \
                     (op['original_ref']['fator1'] == f2 and op['original_ref']['fator2'] == f1) for op in opcoes_geradas)
        if existe: continue
        dummy_ref = {'fator1': f1, 'fator2': f2, 'peso': 10.0, 'historico_erros': [], 'vezes_apresentada': 0, 'vezes_correta': 0, 'ultima_vez_apresentada_ts': 0.0}
        opcoes_geradas.append({'texto': f"{f1} x {f2}", 'original_ref': dummy_ref, 'is_correct': False})
    random.shuffle(opcoes_geradas)
    return opcoes_geradas[:4]

def sugerir_tabuada_para_treino():
    global multiplicacoes_data
    if not multiplicacoes_data: return random.randint(1,10)
    pesos_por_tabuada = {i: 0.0 for i in range(1, 11)}
    contagem_por_tabuada = {i: 0 for i in range(1, 11)}
    for item in multiplicacoes_data:
        fator1, fator2, peso = item['fator1'], item['fator2'], item['peso']
        if fator1 in pesos_por_tabuada:
            pesos_por_tabuada[fator1] += peso; contagem_por_tabuada[fator1] += 1
        if fator2 in pesos_por_tabuada and fator1 != fator2:
            pesos_por_tabuada[fator2] += peso; contagem_por_tabuada[fator2] += 1
    media_pesos = { tab: pesos_por_tabuada[tab] / contagem_por_tabuada[tab] if contagem_por_tabuada[tab] > 0 else 0 for tab in pesos_por_tabuada }
    if not any(v > 0 for v in media_pesos.values()): return random.randint(1,10) # Verifica se algum peso é maior que 0
    return max(media_pesos, key=media_pesos.get)

def calcular_estatisticas_gerais():
    global multiplicacoes_data
    if not multiplicacoes_data: return {'total_respondidas': 0, 'percentual_acertos_geral': 0, 'top_3_dificeis': []}
    total_respondidas = sum(item['vezes_apresentada'] for item in multiplicacoes_data)
    total_acertos = sum(item['vezes_correta'] for item in multiplicacoes_data)
    percentual_acertos_geral = (total_acertos / total_respondidas * 100) if total_respondidas > 0 else 0
    top_dificeis_completo = sorted(multiplicacoes_data, key=lambda x: (x['peso'], -x['vezes_correta'], x['vezes_apresentada']), reverse=True)
    top_3_dificeis_objs = [item for item in top_dificeis_completo if item['vezes_apresentada'] > 0][:3]
    top_3_dificeis_formatado = [f"{item['fator1']} x {item['fator2']}" for item in top_3_dificeis_objs]
    return {'total_respondidas': total_respondidas, 'percentual_acertos_geral': round(percentual_acertos_geral, 1), 'top_3_dificeis': top_3_dificeis_formatado}

def calcular_proficiencia_tabuadas():
    global multiplicacoes_data
    proficiencia_por_tabuada = {i: 0.0 for i in range(1, 11)}
    if not multiplicacoes_data: return proficiencia_por_tabuada
    for t in range(1, 11):
        itens_tabuada_t, vistos_para_tabuada_t = [], set()
        for item_p in multiplicacoes_data:
            par_ordenado = tuple(sorted((item_p['fator1'], item_p['fator2'])))
            if (item_p['fator1'] == t or item_p['fator2'] == t) and par_ordenado not in vistos_para_tabuada_t:
                itens_tabuada_t.append(item_p); vistos_para_tabuada_t.add(par_ordenado)
        media_pesos = (sum(it['peso'] for it in itens_tabuada_t) / len(itens_tabuada_t)) if itens_tabuada_t else 100.0
        proficiencia_percentual = max(0, (100.0 - media_pesos) / (100.0 - 1.0)) * 100.0
        proficiencia_por_tabuada[t] = round(proficiencia_percentual, 1)
    return proficiencia_por_tabuada

inicializar_multiplicacoes()

# --- Temas e Gerenciamento de Tema ---
TEMAS = {
    "colorido": {"fundo_pagina": ft.Colors.PURPLE_50, "texto_titulos": ft.Colors.DEEP_PURPLE_700, "texto_padrao": ft.Colors.BLACK87, "botao_principal_bg": ft.Colors.DEEP_PURPLE_400, "botao_principal_texto": ft.Colors.WHITE, "botao_opcao_quiz_bg": ft.Colors.BLUE_300, "botao_opcao_quiz_texto": ft.Colors.WHITE, "botao_destaque_bg": ft.Colors.PINK_ACCENT_200, "botao_destaque_texto": ft.Colors.BLACK87, "feedback_acerto_texto": ft.Colors.GREEN_600, "feedback_erro_texto": ft.Colors.RED_500, "feedback_acerto_botao_bg": ft.Colors.GREEN_100, "feedback_erro_botao_bg": ft.Colors.RED_100, "container_treino_bg": ft.Colors.WHITE, "container_treino_borda": ft.Colors.DEEP_PURPLE_400, "progressbar_cor": ft.Colors.DEEP_PURPLE_400, "progressbar_bg_cor": ft.Colors.PURPLE_100},
    "claro": {"fundo_pagina": ft.Colors.GREY_100, "texto_titulos": ft.Colors.BLACK, "texto_padrao": ft.Colors.BLACK87, "botao_principal_bg": ft.Colors.BLUE_600, "botao_principal_texto": ft.Colors.WHITE, "botao_opcao_quiz_bg": ft.Colors.LIGHT_BLUE_200, "botao_opcao_quiz_texto": ft.Colors.BLACK87, "botao_destaque_bg": ft.Colors.CYAN_600, "botao_destaque_texto": ft.Colors.WHITE, "feedback_acerto_texto": ft.Colors.GREEN_700, "feedback_erro_texto": ft.Colors.RED_700, "feedback_acerto_botao_bg": ft.Colors.GREEN_100, "feedback_erro_botao_bg": ft.Colors.RED_100, "container_treino_bg": ft.Colors.WHITE, "container_treino_borda": ft.Colors.BLUE_600, "progressbar_cor": ft.Colors.BLUE_600, "progressbar_bg_cor": ft.Colors.BLUE_100},
    "escuro": {"fundo_pagina": ft.Colors.with_opacity(0.95, ft.Colors.BLACK), "texto_titulos": ft.Colors.PURPLE_ACCENT_100, "texto_padrao": ft.Colors.WHITE70, "botao_principal_bg": ft.Colors.PURPLE_ACCENT_200, "botao_principal_texto": ft.Colors.BLACK, "botao_opcao_quiz_bg": ft.Colors.BLUE_GREY_700, "botao_opcao_quiz_texto": ft.Colors.WHITE, "botao_destaque_bg": ft.Colors.TEAL_ACCENT_400, "botao_destaque_texto": ft.Colors.WHITE, "feedback_acerto_texto": ft.Colors.LIGHT_GREEN_ACCENT_400, "feedback_erro_texto": ft.Colors.RED_ACCENT_100, "feedback_acerto_botao_bg": ft.Colors.with_opacity(0.2, ft.Colors.LIGHT_GREEN_ACCENT_400), "feedback_erro_botao_bg": ft.Colors.with_opacity(0.2, ft.Colors.RED_ACCENT_100), "container_treino_bg": ft.Colors.BLUE_GREY_800, "container_treino_borda": ft.Colors.PURPLE_ACCENT_200, "progressbar_cor": ft.Colors.PURPLE_ACCENT_200, "progressbar_bg_cor": ft.Colors.BLUE_GREY_600}
}
tema_ativo_nome = "colorido"
def obter_cor_do_tema_ativo(nome_cor_semantica: str):
    tema_atual = TEMAS.get(tema_ativo_nome, TEMAS["colorido"])
    return tema_atual.get(nome_cor_semantica, ft.Colors.BLACK)

# --- Constantes de UI (Dimensões e Animações) ---
BOTAO_LARGURA_PRINCIPAL = 220
BOTAO_ALTURA_PRINCIPAL = 50
BOTAO_LARGURA_OPCAO_QUIZ = 150
BOTAO_ALTURA_OPCAO_QUIZ = 50
PADDING_VIEW = padding.symmetric(horizontal=25, vertical=20)
ESPACAMENTO_COLUNA_GERAL = 15
ESPACAMENTO_BOTOES_APRESENTACAO = 10
ANIMACAO_FADE_IN_LENTO = Animation(400, AnimationCurve.EASE_IN)
ANIMACAO_APARICAO_TEXTO_BOTAO = Animation(250, AnimationCurve.EASE_OUT)
ANIMACAO_FEEDBACK_OPACIDADE = Animation(200, AnimationCurve.EASE_IN_OUT)
ANIMACAO_FEEDBACK_ESCALA = Animation(300, AnimationCurve.EASE_OUT_BACK)

# --- Funções de Construção de Tela ---
def mudar_tema(page: Page, novo_tema_nome: str):
    global tema_ativo_nome
    if tema_ativo_nome == novo_tema_nome:
        return

    tema_ativo_nome = novo_tema_nome

    if page.client_storage:
        page.client_storage.set("tema_preferido_quiz_tabuada", novo_tema_nome)

    page.bgcolor = obter_cor_do_tema_ativo("fundo_pagina")

    current_route = page.route
    page.go(current_route)

def build_tela_apresentacao(page: Page):
    controles_botoes_tema = [
        Text("Escolha um Tema:", size=16, color=obter_cor_do_tema_ativo("texto_padrao")),
        Container(height=5),
        Row(
            [
                ElevatedButton(text="Colorido", on_click=lambda _: mudar_tema(page, "colorido"), width=BOTAO_LARGURA_PRINCIPAL/2 - 5, height=BOTAO_ALTURA_PRINCIPAL-10, bgcolor=obter_cor_do_tema_ativo("botao_destaque_bg"), color=obter_cor_do_tema_ativo("botao_destaque_texto")),
                ElevatedButton(text="Claro", on_click=lambda _: mudar_tema(page, "claro"), width=BOTAO_LARGURA_PRINCIPAL/2 - 5, height=BOTAO_ALTURA_PRINCIPAL-10, bgcolor=obter_cor_do_tema_ativo("botao_destaque_bg"), color=obter_cor_do_tema_ativo("botao_destaque_texto")),
                ElevatedButton(text="Escuro", on_click=lambda _: mudar_tema(page, "escuro"), width=BOTAO_LARGURA_PRINCIPAL/2 - 5, height=BOTAO_ALTURA_PRINCIPAL-10, bgcolor=obter_cor_do_tema_ativo("botao_destaque_bg"), color=obter_cor_do_tema_ativo("botao_destaque_texto")),
            ],
            alignment=MainAxisAlignment.CENTER,
            spacing = 10
        )
    ]
    conteudo_apresentacao = Column(
        controls=[
            Text("Quiz Mestre da Tabuada", size=32, weight=FontWeight.BOLD, text_align=TextAlign.CENTER, color=obter_cor_do_tema_ativo("texto_titulos")),
            Text("Aprenda e memorize a tabuada de forma divertida e adaptativa!", size=18, text_align=TextAlign.CENTER, color=obter_cor_do_tema_ativo("texto_padrao")),
            Container(height=20),
            ElevatedButton("Iniciar Quiz", width=BOTAO_LARGURA_PRINCIPAL, height=BOTAO_ALTURA_PRINCIPAL, on_click=lambda _: page.go("/quiz"), tooltip="Começar um novo quiz.", bgcolor=obter_cor_do_tema_ativo("botao_principal_bg"), color=obter_cor_do_tema_ativo("botao_principal_texto")),
            Container(height=ESPACAMENTO_BOTOES_APRESENTACAO),
            ElevatedButton("Quiz Invertido", width=BOTAO_LARGURA_PRINCIPAL, height=BOTAO_ALTURA_PRINCIPAL, on_click=lambda _: page.go("/quiz_invertido"), tooltip="Qual multiplicação resulta no número?", bgcolor=obter_cor_do_tema_ativo("botao_destaque_bg"), color=obter_cor_do_tema_ativo("botao_destaque_texto")),
            Container(height=ESPACAMENTO_BOTOES_APRESENTACAO),
            ElevatedButton("Modo Treino", width=BOTAO_LARGURA_PRINCIPAL, height=BOTAO_ALTURA_PRINCIPAL, on_click=lambda _: page.go("/treino"), tooltip="Treinar uma tabuada.", bgcolor=obter_cor_do_tema_ativo("botao_principal_bg"), color=obter_cor_do_tema_ativo("botao_principal_texto")),
            Container(height=ESPACAMENTO_BOTOES_APRESENTACAO),
            ElevatedButton("Estatísticas", width=BOTAO_LARGURA_PRINCIPAL, height=BOTAO_ALTURA_PRINCIPAL, on_click=lambda _: page.go("/estatisticas"), tooltip="Veja seu progresso.", bgcolor=obter_cor_do_tema_ativo("botao_opcao_quiz_bg"), color=obter_cor_do_tema_ativo("botao_opcao_quiz_texto")),
            Container(height=20, margin=ft.margin.only(top=10)),
        ] + controles_botoes_tema,
        alignment=MainAxisAlignment.CENTER, horizontal_alignment=CrossAxisAlignment.CENTER, spacing=ESPACAMENTO_COLUNA_GERAL
    )
    return Container(content=conteudo_apresentacao, alignment=alignment.center, expand=True, padding=PADDING_VIEW)

def build_tela_quiz(page: Page):
    texto_pergunta = Text(size=30, weight=FontWeight.BOLD, text_align=TextAlign.CENTER, color=obter_cor_do_tema_ativo("texto_titulos"), opacity=0, animate_opacity=ANIMACAO_APARICAO_TEXTO_BOTAO)
    botoes_opcoes = [ElevatedButton(width=BOTAO_LARGURA_OPCAO_QUIZ, height=BOTAO_ALTURA_OPCAO_QUIZ, opacity=0, animate_opacity=ANIMACAO_APARICAO_TEXTO_BOTAO) for _ in range(4)]
    texto_feedback = Text(size=18, weight=FontWeight.BOLD, text_align=TextAlign.CENTER, opacity=0, scale=0.8, animate_opacity=ANIMACAO_FEEDBACK_OPACIDADE, animate_scale=ANIMACAO_FEEDBACK_ESCALA)
    def handle_resposta(e, botao_clicado_ref, todos_botoes_opcoes_ref, txt_feedback_ctrl_ref, btn_proxima_ctrl_ref):
        dados_botao = botao_clicado_ref.data
        era_correta = dados_botao['correta']
        pergunta_original_ref = dados_botao['pergunta_original']
        registrar_resposta(pergunta_original_ref, era_correta)
        if era_correta:
            txt_feedback_ctrl_ref.value = "Correto!"
            txt_feedback_ctrl_ref.color = obter_cor_do_tema_ativo("feedback_acerto_texto")
            botao_clicado_ref.bgcolor = obter_cor_do_tema_ativo("feedback_acerto_botao_bg")
        else:
            resposta_certa_valor = pergunta_original_ref['fator1'] * pergunta_original_ref['fator2']
            txt_feedback_ctrl_ref.value = f"Errado! A resposta era {resposta_certa_valor}"
            txt_feedback_ctrl_ref.color = obter_cor_do_tema_ativo("feedback_erro_texto")
            botao_clicado_ref.bgcolor = obter_cor_do_tema_ativo("feedback_erro_botao_bg")
        for btn in todos_botoes_opcoes_ref: btn.disabled = True
        txt_feedback_ctrl_ref.opacity = 1; txt_feedback_ctrl_ref.scale = 1
        btn_proxima_ctrl_ref.visible = True; page.update()
    botao_proxima = ElevatedButton("Próxima Pergunta", on_click=None, visible=False, width=BOTAO_LARGURA_PRINCIPAL, height=BOTAO_ALTURA_PRINCIPAL, tooltip="Carregar próxima pergunta.", bgcolor=obter_cor_do_tema_ativo("botao_principal_bg"), color=obter_cor_do_tema_ativo("botao_principal_texto"))
    def carregar_nova_pergunta(page_ref, txt_pergunta_ctrl, btn_opcoes_ctrls, txt_feedback_ctrl, btn_proxima_ctrl):
        txt_feedback_ctrl.opacity = 0; txt_feedback_ctrl.scale = 0.8
        txt_pergunta_ctrl.opacity = 0
        for btn_opcao in btn_opcoes_ctrls: btn_opcao.opacity = 0
        pergunta_selecionada = selecionar_proxima_pergunta()
        if not pergunta_selecionada:
            txt_pergunta_ctrl.value = "Nenhuma pergunta disponível."; txt_pergunta_ctrl.opacity = 1
            for btn in btn_opcoes_ctrls: btn.visible = False
            txt_feedback_ctrl.value = ""; btn_proxima_ctrl.visible = False; page_ref.update(); return
        r_val = pergunta_selecionada['fator1'] * pergunta_selecionada['fator2']
        ops = gerar_opcoes(pergunta_selecionada['fator1'], pergunta_selecionada['fator2'], multiplicacoes_data)
        txt_pergunta_ctrl.value = f"{pergunta_selecionada['fator1']} x {pergunta_selecionada['fator2']} = ?"
        for i in range(4):
            btn_opcoes_ctrls[i].text = str(ops[i])
            btn_opcoes_ctrls[i].data = {'opcao': ops[i], 'correta': ops[i] == r_val, 'pergunta_original': pergunta_selecionada}
            btn_opcoes_ctrls[i].on_click = lambda e, btn=btn_opcoes_ctrls[i]: handle_resposta(page_ref, btn, btn_opcoes_ctrls, txt_feedback_ctrl, btn_proxima_ctrl)
            btn_opcoes_ctrls[i].bgcolor = obter_cor_do_tema_ativo("botao_opcao_quiz_bg")
            btn_opcoes_ctrls[i].color = obter_cor_do_tema_ativo("botao_opcao_quiz_texto")
            btn_opcoes_ctrls[i].disabled = False; btn_opcoes_ctrls[i].visible = True
        txt_feedback_ctrl.value = ""; btn_proxima_ctrl.visible = False
        txt_pergunta_ctrl.opacity = 1
        for btn_opcao in btn_opcoes_ctrls: btn_opcao.opacity = 1
        page_ref.update()
    botao_proxima.on_click = lambda _: carregar_nova_pergunta(page, texto_pergunta, botoes_opcoes, texto_feedback, botao_proxima)
    carregar_nova_pergunta(page, texto_pergunta, botoes_opcoes, texto_feedback, botao_proxima)
    botao_voltar = ElevatedButton("Voltar ao Menu", on_click=lambda _: page.go("/"), width=BOTAO_LARGURA_PRINCIPAL, height=BOTAO_ALTURA_PRINCIPAL, tooltip="Retornar à tela inicial.", bgcolor=obter_cor_do_tema_ativo("botao_principal_bg"), color=obter_cor_do_tema_ativo("botao_principal_texto"))
    layout_botoes = Column([Row(botoes_opcoes[0:2], alignment=MainAxisAlignment.CENTER, spacing=15), Container(height=10), Row(botoes_opcoes[2:4], alignment=MainAxisAlignment.CENTER, spacing=15)], horizontal_alignment=CrossAxisAlignment.CENTER, spacing=10)
    conteudo_quiz = Column([texto_pergunta, Container(height=15), layout_botoes, Container(height=15), texto_feedback, Container(height=20), botao_proxima, Container(height=10), botao_voltar], alignment=MainAxisAlignment.CENTER, horizontal_alignment=CrossAxisAlignment.CENTER, spacing=ESPACAMENTO_COLUNA_GERAL, scroll=ScrollMode.AUTO)
    return Container(content=conteudo_quiz, alignment=alignment.center, expand=True, padding=PADDING_VIEW)

def build_tela_quiz_invertido(page: Page):
    texto_pergunta_invertida = Text(size=30, weight=FontWeight.BOLD, text_align=TextAlign.CENTER, color=obter_cor_do_tema_ativo("texto_titulos"), opacity=0, animate_opacity=ANIMACAO_APARICAO_TEXTO_BOTAO)
    botoes_opcoes_invertidas = [ElevatedButton(width=BOTAO_LARGURA_OPCAO_QUIZ, height=BOTAO_ALTURA_OPCAO_QUIZ, opacity=0, animate_opacity=ANIMACAO_APARICAO_TEXTO_BOTAO) for _ in range(4)]
    texto_feedback_invertido = Text(size=18, weight=FontWeight.BOLD, text_align=TextAlign.CENTER, opacity=0, scale=0.8, animate_opacity=ANIMACAO_FEEDBACK_OPACIDADE, animate_scale=ANIMACAO_FEEDBACK_ESCALA)
    def handle_resposta_invertida(e, botao_clicado_ref, todos_botoes_opcoes_ref, txt_feedback_ctrl_ref, btn_proxima_ctrl_ref):
        dados_botao = botao_clicado_ref.data
        opcao_obj = dados_botao['opcao_obj']
        era_correta = opcao_obj['is_correct']
        pergunta_base_ref = dados_botao['pergunta_base_original_ref']
        registrar_resposta(pergunta_base_ref, era_correta)
        if era_correta:
            txt_feedback_ctrl_ref.value = "Correto!"
            txt_feedback_ctrl_ref.color = obter_cor_do_tema_ativo("feedback_acerto_texto")
            botao_clicado_ref.bgcolor = obter_cor_do_tema_ativo("feedback_acerto_botao_bg")
        else:
            resp_correta_txt = f"{pergunta_base_ref['fator1']} x {pergunta_base_ref['fator2']}"
            txt_feedback_ctrl_ref.value = f"Errado! A resposta era {resp_correta_txt}"
            txt_feedback_ctrl_ref.color = obter_cor_do_tema_ativo("feedback_erro_texto")
            botao_clicado_ref.bgcolor = obter_cor_do_tema_ativo("feedback_erro_botao_bg")
            for btn_op in todos_botoes_opcoes_ref:
                if btn_op.data['opcao_obj']['is_correct']: btn_op.bgcolor = obter_cor_do_tema_ativo("feedback_acerto_botao_bg"); break
        for btn in todos_botoes_opcoes_ref: btn.disabled = True
        txt_feedback_ctrl_ref.opacity = 1; txt_feedback_ctrl_ref.scale = 1
        btn_proxima_ctrl_ref.visible = True; page.update()
    botao_proxima_invertido = ElevatedButton("Próxima Pergunta", on_click=None, visible=False, width=BOTAO_LARGURA_PRINCIPAL, height=BOTAO_ALTURA_PRINCIPAL, tooltip="Carregar próxima pergunta.", bgcolor=obter_cor_do_tema_ativo("botao_principal_bg"), color=obter_cor_do_tema_ativo("botao_principal_texto"))
    def carregar_nova_pergunta_invertida(page_ref, txt_pergunta_ctrl, btn_opcoes_ctrls, txt_feedback_ctrl, btn_proxima_ctrl):
        txt_feedback_ctrl.opacity = 0; txt_feedback_ctrl.scale = 0.8
        txt_pergunta_ctrl.opacity = 0
        for btn_opcao in btn_opcoes_ctrls: btn_opcao.opacity = 0
        multiplicacao_base = selecionar_proxima_pergunta()
        if not multiplicacao_base:
            txt_pergunta_ctrl.value = "Nenhuma pergunta base disponível."; txt_pergunta_ctrl.opacity = 1
            for btn in btn_opcoes_ctrls: btn.visible = False
            txt_feedback_ctrl.value = ""; btn_proxima_ctrl.visible = False; page_ref.update(); return
        resultado_alvo = multiplicacao_base['fator1'] * multiplicacao_base['fator2']
        txt_pergunta_ctrl.value = f"Qual operação resulta em {resultado_alvo}?"
        opcoes_objs_geradas = gerar_opcoes_quiz_invertido(multiplicacao_base, multiplicacoes_data)
        for i in range(len(opcoes_objs_geradas)):
            btn_opcoes_ctrls[i].text = opcoes_objs_geradas[i]['texto']
            btn_opcoes_ctrls[i].data = {'opcao_obj': opcoes_objs_geradas[i], 'pergunta_base_original_ref': multiplicacao_base}
            btn_opcoes_ctrls[i].on_click = lambda e, btn=btn_opcoes_ctrls[i]: handle_resposta_invertida(page_ref, btn, btn_opcoes_ctrls, txt_feedback_ctrl, btn_proxima_ctrl)
            btn_opcoes_ctrls[i].bgcolor = obter_cor_do_tema_ativo("botao_opcao_quiz_bg")
            btn_opcoes_ctrls[i].color = obter_cor_do_tema_ativo("botao_opcao_quiz_texto")
            btn_opcoes_ctrls[i].disabled = False; btn_opcoes_ctrls[i].visible = True
        txt_feedback_ctrl.value = ""; btn_proxima_ctrl.visible = False
        txt_pergunta_ctrl.opacity = 1
        for btn_opcao in btn_opcoes_ctrls: btn_opcao.opacity = 1
        page_ref.update()
    botao_proxima_invertido.on_click = lambda _: carregar_nova_pergunta_invertida(page, texto_pergunta_invertida, botoes_opcoes_invertidas, texto_feedback_invertido, botao_proxima_invertido)
    carregar_nova_pergunta_invertida(page, texto_pergunta_invertida, botoes_opcoes_invertidas, texto_feedback_invertido, botao_proxima_invertido)
    botao_voltar_inv = ElevatedButton("Voltar ao Menu", on_click=lambda _: page.go("/"), width=BOTAO_LARGURA_PRINCIPAL, height=BOTAO_ALTURA_PRINCIPAL, tooltip="Retornar à tela inicial.", bgcolor=obter_cor_do_tema_ativo("botao_principal_bg"), color=obter_cor_do_tema_ativo("botao_principal_texto"))
    layout_botoes_inv = Column([Row(botoes_opcoes_invertidas[0:2], alignment=MainAxisAlignment.CENTER, spacing=15), Container(height=10), Row(botoes_opcoes_invertidas[2:4], alignment=MainAxisAlignment.CENTER, spacing=15)], horizontal_alignment=CrossAxisAlignment.CENTER, spacing=10)
    conteudo_quiz_inv = Column([texto_pergunta_invertida, Container(height=15), layout_botoes_inv, Container(height=15), texto_feedback_invertido, Container(height=20), botao_proxima_invertido, Container(height=10), botao_voltar_inv], alignment=MainAxisAlignment.CENTER, horizontal_alignment=CrossAxisAlignment.CENTER, spacing=ESPACAMENTO_COLUNA_GERAL, scroll=ScrollMode.AUTO)
    return Container(content=conteudo_quiz_inv, alignment=alignment.center, expand=True, padding=PADDING_VIEW)

def build_tela_treino(page: Page):
    tabuada_sugerida = sugerir_tabuada_para_treino()
    titulo_treino = Text(f"Treinando a Tabuada do {tabuada_sugerida}", size=28, weight=FontWeight.BOLD, text_align=TextAlign.CENTER, color=obter_cor_do_tema_ativo("texto_titulos"))
    campos_tabuada_refs = []
    coluna_itens_tabuada = Column(spacing=10, scroll=ScrollMode.AUTO, expand=True, horizontal_alignment=CrossAxisAlignment.CENTER)
    for i in range(1, 11):
        r_correta_val = tabuada_sugerida * i
        txt_mult = Text(f"{tabuada_sugerida} x {i} = ", size=18, color=obter_cor_do_tema_ativo("texto_padrao"))
        campo_resp = TextField(width=100, text_align=TextAlign.CENTER, data={'fator1': tabuada_sugerida, 'fator2': i, 'resposta_correta': r_correta_val}, keyboard_type=KeyboardType.NUMBER)
        campos_tabuada_refs.append(campo_resp)
        coluna_itens_tabuada.controls.append(Row([txt_mult, campo_resp], alignment=MainAxisAlignment.CENTER, spacing=10))
    txt_resumo = Text(size=18, weight=FontWeight.BOLD, text_align=TextAlign.CENTER, color=obter_cor_do_tema_ativo("texto_padrao"))
    btn_verificar = ElevatedButton("Verificar Respostas", width=BOTAO_LARGURA_PRINCIPAL, height=BOTAO_ALTURA_PRINCIPAL, tooltip="Corrigir respostas.", bgcolor=obter_cor_do_tema_ativo("botao_principal_bg"), color=obter_cor_do_tema_ativo("botao_principal_texto"))
    def handle_verificar_treino(e):
        acertos = 0
        for campo in campos_tabuada_refs:
            dados = campo.data
            f1, f2, resp_esperada = dados['fator1'], dados['fator2'], dados['resposta_correta']
            acertou = False
            try:
                if int(campo.value) == resp_esperada: acertos += 1; acertou = True; campo.border_color = obter_cor_do_tema_ativo("feedback_acerto_texto")
                else: campo.border_color = obter_cor_do_tema_ativo("feedback_erro_texto")
            except ValueError: campo.border_color = obter_cor_do_tema_ativo("feedback_erro_texto")
            campo.disabled = True
            pergunta_ref = next((p for p in multiplicacoes_data if (p['fator1'] == f1 and p['fator2'] == f2) or (p['fator1'] == f2 and p['fator2'] == f1)), None)
            if pergunta_ref: registrar_resposta(pergunta_ref, acertou)
        txt_resumo.value = f"Você acertou {acertos} de {len(campos_tabuada_refs)}!"; btn_verificar.disabled = True; page.update()
    btn_verificar.on_click = handle_verificar_treino
    btn_voltar = ElevatedButton("Voltar ao Menu", on_click=lambda _: page.go("/"), width=BOTAO_LARGURA_PRINCIPAL, height=BOTAO_ALTURA_PRINCIPAL, tooltip="Retornar à tela inicial.", bgcolor=obter_cor_do_tema_ativo("botao_principal_bg"), color=obter_cor_do_tema_ativo("botao_principal_texto"))
    cont_tabuada = Container(content=coluna_itens_tabuada, border=border.all(2, obter_cor_do_tema_ativo("container_treino_borda")), border_radius=8, padding=padding.all(15), width=360, height=420, bgcolor=obter_cor_do_tema_ativo("container_treino_bg"))
    conteudo_treino = Column([titulo_treino, Container(height=10), cont_tabuada, Container(height=10), btn_verificar, Container(height=10), txt_resumo, Container(height=15), btn_voltar], alignment=MainAxisAlignment.CENTER, horizontal_alignment=CrossAxisAlignment.CENTER, spacing=ESPACAMENTO_COLUNA_GERAL, scroll=ScrollMode.AUTO)
    return Container(content=conteudo_treino, alignment=alignment.center, expand=True, padding=PADDING_VIEW)

def build_tela_estatisticas(page: Page):
    stats_gerais = calcular_estatisticas_gerais()
    proficiencia_tabuadas = calcular_proficiencia_tabuadas()
    lista_proficiencia_controls = []
    for t in range(1, 11):
        progresso = proficiencia_tabuadas.get(t, 0) / 100.0
        cor_barra_semantica = "feedback_acerto_texto" # Default to green (high proficiency)
        if progresso < 0.4: # Low proficiency
            cor_barra_semantica = "feedback_erro_texto" # Red
        elif progresso < 0.7: # Medium proficiency
            cor_barra_semantica = "progressbar_cor" # Theme's progress bar color (e.g., purple/blue)

        cor_barra_dinamica = obter_cor_do_tema_ativo(cor_barra_semantica)
        progressbar_bg_color_dinamica = obter_cor_do_tema_ativo("progressbar_bg_cor")

        lista_proficiencia_controls.append(
            Row(
                [
                    Text(f"Tabuada do {t}: ", size=16, color=obter_cor_do_tema_ativo("texto_padrao"), width=130),
                    ProgressBar(value=progresso, width=150, color=cor_barra_dinamica, bgcolor=progressbar_bg_color_dinamica),
                    Text(f"{proficiencia_tabuadas.get(t, 0):.1f}%", size=16, color=obter_cor_do_tema_ativo("texto_padrao"), width=60, text_align=TextAlign.RIGHT)
                ],
                alignment=MainAxisAlignment.CENTER
            )
        )

    col_prof = Column(controls=lista_proficiencia_controls, spacing=8, horizontal_alignment=CrossAxisAlignment.CENTER)

    top_3_txt = [Text(item, size=16, color=obter_cor_do_tema_ativo("texto_padrao")) for item in stats_gerais['top_3_dificeis']]
    if not top_3_txt:
        top_3_txt = [Text("Nenhuma dificuldade registrada ainda!", size=16, color=obter_cor_do_tema_ativo("texto_padrao"))]

    col_dificuldades = Column(controls=top_3_txt, spacing=5, horizontal_alignment=CrossAxisAlignment.CENTER)

    conteudo_stats = Column(
        controls=[
            Text("Suas Estatísticas", size=32, weight=FontWeight.BOLD, color=obter_cor_do_tema_ativo("texto_titulos"), text_align=TextAlign.CENTER),
            Container(height=15),
            Text(f"Total de Perguntas Respondidas: {stats_gerais['total_respondidas']}", size=18, color=obter_cor_do_tema_ativo("texto_padrao")),
            Text(f"Percentual de Acertos Geral: {stats_gerais['percentual_acertos_geral']:.1f}%", size=18, color=obter_cor_do_tema_ativo("texto_padrao")),
            Container(height=10),
            Text("Proficiência por Tabuada:", size=22, weight=FontWeight.BOLD, color=obter_cor_do_tema_ativo("texto_titulos"), margin=ft.margin.only(top=20, bottom=10)),
            col_prof,
            Container(height=10),
            Text("Maiores Dificuldades Atuais:", size=22, weight=FontWeight.BOLD, color=obter_cor_do_tema_ativo("texto_titulos"), margin=ft.margin.only(top=20, bottom=10)),
            col_dificuldades,
            Container(height=25),
            ElevatedButton(
                "Voltar ao Menu",
                width=BOTAO_LARGURA_PRINCIPAL,
                height=BOTAO_ALTURA_PRINCIPAL,
                on_click=lambda _: page.go("/"),
                tooltip="Retornar à tela inicial.",
                bgcolor=obter_cor_do_tema_ativo("botao_principal_bg"),
                color=obter_cor_do_tema_ativo("botao_principal_texto")
            ), # <--- VÍRGULA ESTAVA FALTANDO AQUI, E FOI ADICIONADA NO PATCH ANTERIOR (subtarefa 18)
        ],
        scroll=ScrollMode.AUTO,
        alignment=MainAxisAlignment.CENTER,
        horizontal_alignment=CrossAxisAlignment.CENTER,
        spacing=ESPACAMENTO_COLUNA_GERAL
    )
    return Container(content=conteudo_stats, alignment=alignment.center, expand=True, padding=PADDING_VIEW)

# --- Configuração Principal da Página e Rotas ---
def main(page: Page):
    global tema_ativo_nome
    if page.client_storage:
        tema_salvo = page.client_storage.get("tema_preferido_quiz_tabuada")
        if tema_salvo and tema_salvo in TEMAS:
            tema_ativo_nome = tema_salvo

    page.title = "Quiz Mestre da Tabuada"
    page.vertical_alignment = MainAxisAlignment.CENTER
    page.horizontal_alignment = CrossAxisAlignment.CENTER
    page.bgcolor = obter_cor_do_tema_ativo("fundo_pagina")
    page.window_width = 480
    page.window_height = 800
    page.fonts = {"RobotoSlab": "https://github.com/google/fonts/raw/main/apache/robotoslab/RobotoSlab%5Bwght%5D.ttf"}

    def route_change(route_obj):
        page.bgcolor = obter_cor_do_tema_ativo("fundo_pagina")
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
            page.views.append(View("/quiz", [build_tela_quiz(page)], vertical_alignment=MainAxisAlignment.CENTER, horizontal_alignment=CrossAxisAlignment.CENTER))
        elif page.route == "/quiz_invertido":
            page.views.append(View("/quiz_invertido", [build_tela_quiz_invertido(page)], vertical_alignment=MainAxisAlignment.CENTER, horizontal_alignment=CrossAxisAlignment.CENTER))
        elif page.route == "/treino":
            page.views.append(View("/treino", [build_tela_treino(page)], vertical_alignment=MainAxisAlignment.CENTER, horizontal_alignment=CrossAxisAlignment.CENTER))
        elif page.route == "/estatisticas":
            page.views.append(View("/estatisticas", [build_tela_estatisticas(page)], vertical_alignment=MainAxisAlignment.CENTER, horizontal_alignment=CrossAxisAlignment.CENTER))

        page.update()

    def view_pop(view_instance):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.go("/")

ft.app(target=main)

[end of main.py]

[end of main.py]

[end of main.py]
