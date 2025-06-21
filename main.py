import flet as ft
from flet import (
    Page, Text, ElevatedButton, Row, Column, TextField, View, Container,
    MainAxisAlignment, CrossAxisAlignment, FontWeight, alignment,
    TextAlign, ScrollMode, padding, border, KeyboardType,
    Animation, AnimationCurve, Margin, ProgressBar
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

    opcao_correta_obj = {
        'texto': f"{multiplicacao_base_ref['fator1']} x {multiplicacao_base_ref['fator2']}",
        'original_ref': multiplicacao_base_ref, # Referência ao item original em multiplicacoes_data
        'is_correct': True
    }
    opcoes_geradas = [opcao_correta_obj]

    candidatos_embaralhados = random.sample(todas_multiplicacoes_data_ref, len(todas_multiplicacoes_data_ref))

    for item_candidato in candidatos_embaralhados:
        if len(opcoes_geradas) >= 4:
            break

        # Pular se for exatamente a mesma multiplicação base (mesmos fatores)
        if item_candidato['fator1'] == multiplicacao_base_ref['fator1'] and \
           item_candidato['fator2'] == multiplicacao_base_ref['fator2']:
            continue

        # Pular se o resultado for o mesmo da pergunta base, mas os fatores são diferentes
        # Isso evita ter múltiplas opções que levam ao mesmo resultado, ex: 2x6 e 3x4 para a pergunta "Qual operação resulta em 12?"
        # se a pergunta base (a correta) for 2x6.
        if item_candidato['fator1'] * item_candidato['fator2'] == resposta_correta_valor:
            continue

        opcoes_geradas.append({
            'texto': f"{item_candidato['fator1']} x {item_candidato['fator2']}",
            'original_ref': item_candidato, # Referência ao item original
            'is_correct': False
        })

    # Fallback: se ainda não tem 4 opções (altamente improvável com 100 itens)
    # Gera fatores aleatórios que não resultem em `resposta_correta_valor`
    # e que não sejam os fatores da `multiplicacao_base_ref`.
    tentativas_fallback = 0
    while len(opcoes_geradas) < 4 and tentativas_fallback < 50:
        tentativas_fallback += 1
        f1 = random.randint(1, 10)
        f2 = random.randint(1, 10)

        # Verifica se já existe uma opção com estes fatores ou se resulta no mesmo valor da resposta correta
        # ou se são os mesmos fatores da pergunta base
        if (f1 == multiplicacao_base_ref['fator1'] and f2 == multiplicacao_base_ref['fator2']) or \
           (f1 * f2 == resposta_correta_valor):
            continue

        # Verifica se a combinação de fatores já está nas opções geradas
        existe = False
        for op_existente in opcoes_geradas:
            ref_existente = op_existente['original_ref']
            if (ref_existente['fator1'] == f1 and ref_existente['fator2'] == f2) or \
               (ref_existente['fator1'] == f2 and ref_existente['fator2'] == f1):
                existe = True
                break
        if existe:
            continue

        # Cria um "dummy" ref para o fallback, já que não vem de multiplicacoes_data diretamente
        dummy_ref = {'fator1': f1, 'fator2': f2, 'peso': 10.0, 'historico_erros': [],
                     'vezes_apresentada': 0, 'vezes_correta': 0, 'ultima_vez_apresentada_ts': 0.0}

        opcoes_geradas.append({
            'texto': f"{f1} x {f2}",
            'original_ref': dummy_ref,
            'is_correct': False
        })

    random.shuffle(opcoes_geradas)
    return opcoes_geradas[:4] # Garante que apenas 4 opções sejam retornadas


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

def calcular_estatisticas_gerais():
    global multiplicacoes_data
    if not multiplicacoes_data:
        return {'total_respondidas': 0, 'percentual_acertos_geral': 0, 'top_3_dificeis': []}
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
        itens_tabuada_t = []
        vistos_para_tabuada_t = set()
        for item_p in multiplicacoes_data:
            par_ordenado = tuple(sorted((item_p['fator1'], item_p['fator2'])))
            if (item_p['fator1'] == t or item_p['fator2'] == t) and par_ordenado not in vistos_para_tabuada_t :
                if item_p['fator1'] == t or item_p['fator2'] == t:
                     itens_tabuada_t.append(item_p)
                     vistos_para_tabuada_t.add(par_ordenado)
        if not itens_tabuada_t: media_pesos = 100.0
        else:
            soma_pesos_tabuada_t = sum(item_t['peso'] for item_t in itens_tabuada_t)
            media_pesos = soma_pesos_tabuada_t / len(itens_tabuada_t)
        proficiencia_percentual = max(0, (100.0 - media_pesos) / (100.0 - 1.0)) * 100.0
        proficiencia_por_tabuada[t] = round(proficiencia_percentual, 1)
    return proficiencia_por_tabuada

inicializar_multiplicacoes()

# --- Constantes de UI ---
BOTAO_LARGURA_PRINCIPAL = 220
BOTAO_ALTURA_PRINCIPAL = 50
BOTAO_LARGURA_OPCAO_QUIZ = 150
BOTAO_ALTURA_OPCAO_QUIZ = 50
PADDING_VIEW = padding.symmetric(horizontal=25, vertical=20)
ESPACAMENTO_COLUNA_GERAL = 15 # Reduzido para acomodar mais botões na tela inicial
ESPACAMENTO_BOTOES_APRESENTACAO = 10

COR_ROXO_PRINCIPAL = ft.Colors.DEEP_PURPLE_400
COR_ROXO_ESCURO_TEXTO = ft.Colors.DEEP_PURPLE_700
COR_AZUL_BOTAO_OPCAO = ft.Colors.BLUE_300
COR_ROSA_DESTAQUE = ft.Colors.PINK_ACCENT_200
COR_VERDE_ACERTO = ft.Colors.GREEN_600
COR_VERMELHO_ERRO = ft.Colors.RED_500
COR_TEXTO_SOBRE_ROXO = ft.Colors.WHITE
COR_TEXTO_SOBRE_AZUL = ft.Colors.WHITE
COR_TEXTO_SOBRE_ROSA = ft.Colors.BLACK87
COR_TEXTO_PADRAO_ESCURO = ft.Colors.BLACK87
COR_TEXTO_TITULOS = COR_ROXO_ESCURO_TEXTO
COR_FUNDO_PAGINA = ft.Colors.PURPLE_50
COR_FUNDO_CONTAINER_TREINO = ft.Colors.WHITE
COR_BORDA_CONTAINER_TREINO = COR_ROXO_PRINCIPAL
COR_BOTAO_FEEDBACK_ACERTO_BG = ft.Colors.GREEN_100
COR_BOTAO_FEEDBACK_ERRO_BG = ft.Colors.RED_100

ANIMACAO_FADE_IN_LENTO = Animation(400, AnimationCurve.EASE_IN)
ANIMACAO_APARICAO_TEXTO_BOTAO = Animation(250, AnimationCurve.EASE_OUT)
ANIMACAO_FEEDBACK_OPACIDADE = Animation(200, AnimationCurve.EASE_IN_OUT)
ANIMACAO_FEEDBACK_ESCALA = Animation(300, AnimationCurve.EASE_OUT_BACK)

# --- Funções de Construção de Tela ---
def build_tela_apresentacao(page: Page):
    conteudo_apresentacao = Column(
        controls=[
            Text("Quiz Mestre da Tabuada", size=32, weight=FontWeight.BOLD, text_align=TextAlign.CENTER, color=COR_TEXTO_TITULOS),
            Text("Aprenda e memorize a tabuada de forma divertida e adaptativa!", size=18, text_align=TextAlign.CENTER, color=COR_TEXTO_PADRAO_ESCURO),
            Container(height=20),
            ElevatedButton("Iniciar Quiz", width=BOTAO_LARGURA_PRINCIPAL, height=BOTAO_ALTURA_PRINCIPAL, on_click=lambda _: page.go("/quiz"), tooltip="Começar um novo quiz com perguntas aleatórias.", bgcolor=COR_ROXO_PRINCIPAL, color=COR_TEXTO_SOBRE_ROXO),
            Container(height=ESPACAMENTO_BOTOES_APRESENTACAO),
            ElevatedButton("Quiz Invertido", width=BOTAO_LARGURA_PRINCIPAL, height=BOTAO_ALTURA_PRINCIPAL, on_click=lambda _: page.go("/quiz_invertido"), tooltip="Descubra qual multiplicação resulta no número dado.", bgcolor=COR_ROSA_DESTAQUE, color=COR_TEXTO_SOBRE_ROSA),
            Container(height=ESPACAMENTO_BOTOES_APRESENTACAO),
            ElevatedButton("Modo Treino", width=BOTAO_LARGURA_PRINCIPAL, height=BOTAO_ALTURA_PRINCIPAL, on_click=lambda _: page.go("/treino"), tooltip="Treinar uma tabuada específica ou uma sugerida.", bgcolor=COR_ROXO_PRINCIPAL, color=COR_TEXTO_SOBRE_ROXO),
            Container(height=ESPACAMENTO_BOTOES_APRESENTACAO),
            ElevatedButton("Estatísticas", width=BOTAO_LARGURA_PRINCIPAL, height=BOTAO_ALTURA_PRINCIPAL, on_click=lambda _: page.go("/estatisticas"), tooltip="Veja seu progresso e dificuldades.", bgcolor=COR_AZUL_BOTAO_OPCAO, color=COR_TEXTO_SOBRE_AZUL),
        ],
        alignment=MainAxisAlignment.CENTER,
        horizontal_alignment=CrossAxisAlignment.CENTER,
        spacing=ESPACAMENTO_COLUNA_GERAL
    )
    return Container(content=conteudo_apresentacao, alignment=alignment.center, expand=True, padding=PADDING_VIEW)

def build_tela_quiz(page: Page):
    # ... (código da tela de quiz normal, sem alterações nesta etapa) ...
    texto_pergunta = Text(size=30, weight=FontWeight.BOLD, text_align=TextAlign.CENTER, color=COR_TEXTO_TITULOS, opacity=0, animate_opacity=ANIMACAO_APARICAO_TEXTO_BOTAO)
    botoes_opcoes = [ElevatedButton(width=BOTAO_LARGURA_OPCAO_QUIZ, height=BOTAO_ALTURA_OPCAO_QUIZ, opacity=0, animate_opacity=ANIMACAO_APARICAO_TEXTO_BOTAO) for _ in range(4)]
    texto_feedback = Text(size=18, weight=FontWeight.BOLD, text_align=TextAlign.CENTER, opacity=0, scale=0.8, animate_opacity=ANIMACAO_FEEDBACK_OPACIDADE, animate_scale=ANIMACAO_FEEDBACK_ESCALA)
    def handle_resposta(e, botao_clicado_ref, todos_botoes_opcoes_ref, txt_feedback_ctrl_ref, btn_proxima_ctrl_ref):
        dados_botao = botao_clicado_ref.data
        era_correta = dados_botao['correta']
        pergunta_original_ref = dados_botao['pergunta_original']
        registrar_resposta(pergunta_original_ref, era_correta)
        if era_correta:
            txt_feedback_ctrl_ref.value = "Correto!"
            txt_feedback_ctrl_ref.color = COR_VERDE_ACERTO
            botao_clicado_ref.bgcolor = COR_BOTAO_FEEDBACK_ACERTO_BG
        else:
            resposta_certa_valor = pergunta_original_ref['fator1'] * pergunta_original_ref['fator2']
            txt_feedback_ctrl_ref.value = f"Errado! A resposta era {resposta_certa_valor}"
            txt_feedback_ctrl_ref.color = COR_VERMELHO_ERRO
            botao_clicado_ref.bgcolor = COR_BOTAO_FEEDBACK_ERRO_BG
        for btn in todos_botoes_opcoes_ref: btn.disabled = True
        txt_feedback_ctrl_ref.opacity = 1
        txt_feedback_ctrl_ref.scale = 1
        btn_proxima_ctrl_ref.visible = True
        page.update()
    botao_proxima = ElevatedButton("Próxima Pergunta", on_click=None, visible=False, width=BOTAO_LARGURA_PRINCIPAL, height=BOTAO_ALTURA_PRINCIPAL, tooltip="Carregar a próxima pergunta do quiz.", bgcolor=COR_ROXO_PRINCIPAL, color=COR_TEXTO_SOBRE_ROXO)
    def carregar_nova_pergunta(page_ref, txt_pergunta_ctrl_ref, btn_opcoes_ctrls_ref, txt_feedback_ctrl_ref, btn_proxima_ctrl_ref):
        txt_feedback_ctrl_ref.opacity = 0
        txt_feedback_ctrl_ref.scale = 0.8
        txt_pergunta_ctrl_ref.opacity = 0
        for btn_opcao in btn_opcoes_ctrls_ref: btn_opcao.opacity = 0
        pergunta_selecionada = selecionar_proxima_pergunta()
        if not pergunta_selecionada:
            txt_pergunta_ctrl_ref.value = "Nenhuma pergunta disponível."
            txt_pergunta_ctrl_ref.opacity = 1
            for btn in btn_opcoes_ctrls_ref: btn.visible = False
            txt_feedback_ctrl_ref.value = ""
            btn_proxima_ctrl_ref.visible = False
            page_ref.update()
            return
        resposta_correta_valor = pergunta_selecionada['fator1'] * pergunta_selecionada['fator2']
        opcoes_geradas = gerar_opcoes(pergunta_selecionada['fator1'], pergunta_selecionada['fator2'], multiplicacoes_data)
        txt_pergunta_ctrl_ref.value = f"{pergunta_selecionada['fator1']} x {pergunta_selecionada['fator2']} = ?"
        for i in range(4):
            btn_opcoes_ctrls_ref[i].text = str(opcoes_geradas[i])
            btn_opcoes_ctrls_ref[i].data = {'opcao': opcoes_geradas[i], 'correta': opcoes_geradas[i] == resposta_correta_valor, 'pergunta_original': pergunta_selecionada}
            current_button = btn_opcoes_ctrls_ref[i]
            btn_opcoes_ctrls_ref[i].on_click = lambda e, btn=current_button: handle_resposta(page_ref, btn, btn_opcoes_ctrls_ref, txt_feedback_ctrl_ref, btn_proxima_ctrl_ref)
            btn_opcoes_ctrls_ref[i].bgcolor = COR_AZUL_BOTAO_OPCAO
            btn_opcoes_ctrls_ref[i].color = COR_TEXTO_SOBRE_AZUL
            btn_opcoes_ctrls_ref[i].disabled = False
            btn_opcoes_ctrls_ref[i].visible = True
        txt_feedback_ctrl_ref.value = ""
        btn_proxima_ctrl_ref.visible = False
        txt_pergunta_ctrl_ref.opacity = 1
        for btn_opcao in btn_opcoes_ctrls_ref: btn_opcao.opacity = 1
        page_ref.update()
    botao_proxima.on_click = lambda _: carregar_nova_pergunta(page, texto_pergunta, botoes_opcoes, texto_feedback, botao_proxima)
    carregar_nova_pergunta(page, texto_pergunta, botoes_opcoes, texto_feedback, botao_proxima)
    botao_voltar = ElevatedButton("Voltar ao Menu", on_click=lambda _: page.go("/"), width=BOTAO_LARGURA_PRINCIPAL, height=BOTAO_ALTURA_PRINCIPAL, tooltip="Retornar à tela inicial.", bgcolor=COR_ROXO_PRINCIPAL, color=COR_TEXTO_SOBRE_ROXO)
    layout_botoes_opcoes = Column([Row(botoes_opcoes[0:2], alignment=MainAxisAlignment.CENTER, spacing=15), Container(height=10), Row(botoes_opcoes[2:4], alignment=MainAxisAlignment.CENTER, spacing=15)], horizontal_alignment=CrossAxisAlignment.CENTER, spacing=10)
    conteudo_quiz = Column(controls=[texto_pergunta, Container(height=15), layout_botoes_opcoes, Container(height=15), texto_feedback, Container(height=20), botao_proxima, Container(height=10), botao_voltar], alignment=MainAxisAlignment.CENTER, horizontal_alignment=CrossAxisAlignment.CENTER, spacing=ESPACAMENTO_COLUNA_GERAL, scroll=ScrollMode.AUTO)
    return Container(content=conteudo_quiz, alignment=alignment.center, expand=True, padding=PADDING_VIEW)

def build_tela_quiz_invertido(page: Page):
    texto_pergunta_invertida = Text(size=30, weight=FontWeight.BOLD, text_align=TextAlign.CENTER, color=COR_TEXTO_TITULOS, opacity=0, animate_opacity=ANIMACAO_APARICAO_TEXTO_BOTAO)
    botoes_opcoes_invertidas = [ElevatedButton(width=BOTAO_LARGURA_OPCAO_QUIZ, height=BOTAO_ALTURA_OPCAO_QUIZ, opacity=0, animate_opacity=ANIMACAO_APARICAO_TEXTO_BOTAO) for _ in range(4)]
    texto_feedback_invertido = Text(size=18, weight=FontWeight.BOLD, text_align=TextAlign.CENTER, opacity=0, scale=0.8, animate_opacity=ANIMACAO_FEEDBACK_OPACIDADE, animate_scale=ANIMACAO_FEEDBACK_ESCALA)

    def handle_resposta_invertida(e, botao_clicado_ref, todos_botoes_opcoes_ref, txt_feedback_ctrl_ref, btn_proxima_ctrl_ref):
        dados_botao = botao_clicado_ref.data
        opcao_selecionada_obj = dados_botao['opcao_obj']
        era_correta = opcao_selecionada_obj['is_correct']
        # No quiz invertido, a "pergunta original" que deve ter seu peso atualizado é a que foi usada para gerar o resultado (a opção correta).
        # Se o usuário escolheu a opção correta, `opcao_selecionada_obj['original_ref']` é a referência certa.
        # Se o usuário escolheu uma incorreta, `opcao_selecionada_obj['original_ref']` é a referência da multiplicação incorreta.
        # No entanto, o aprendizado deve ser sobre a multiplicação que gerou o resultado alvo.
        # Então, `pergunta_base_original_ref` (que é a multiplicação correta que gerou o resultado) é o que deve ser atualizado.
        pergunta_base_ref = dados_botao['pergunta_base_original_ref']

        registrar_resposta(pergunta_base_ref, era_correta)

        if era_correta:
            txt_feedback_ctrl_ref.value = "Correto!"
            txt_feedback_ctrl_ref.color = COR_VERDE_ACERTO
            botao_clicado_ref.bgcolor = COR_BOTAO_FEEDBACK_ACERTO_BG
        else:
            resposta_correta_texto = f"{pergunta_base_ref['fator1']} x {pergunta_base_ref['fator2']}"
            txt_feedback_ctrl_ref.value = f"Errado! A resposta era {resposta_correta_texto}"
            txt_feedback_ctrl_ref.color = COR_VERMELHO_ERRO
            botao_clicado_ref.bgcolor = COR_BOTAO_FEEDBACK_ERRO_BG
            # Destacar a opção correta
            for btn_opcao in todos_botoes_opcoes_ref:
                if btn_opcao.data['opcao_obj']['is_correct']:
                    btn_opcao.bgcolor = COR_BOTAO_FEEDBACK_ACERTO_BG # Mostra qual era a certa
                    break

        for btn in todos_botoes_opcoes_ref: btn.disabled = True
        txt_feedback_ctrl_ref.opacity = 1
        txt_feedback_ctrl_ref.scale = 1
        btn_proxima_ctrl_ref.visible = True
        page.update()

    botao_proxima_invertido = ElevatedButton("Próxima Pergunta", on_click=None, visible=False, width=BOTAO_LARGURA_PRINCIPAL, height=BOTAO_ALTURA_PRINCIPAL, tooltip="Carregar a próxima pergunta do quiz invertido.", bgcolor=COR_ROXO_PRINCIPAL, color=COR_TEXTO_SOBRE_ROXO)

    def carregar_nova_pergunta_invertida(page_ref, txt_pergunta_ctrl, btn_opcoes_ctrls, txt_feedback_ctrl, btn_proxima_ctrl):
        txt_feedback_ctrl.opacity = 0
        txt_feedback_ctrl.scale = 0.8
        txt_pergunta_ctrl.opacity = 0
        for btn_opcao in btn_opcoes_ctrls: btn_opcao.opacity = 0

        multiplicacao_selecionada_base = selecionar_proxima_pergunta()
        if not multiplicacao_selecionada_base:
            txt_pergunta_ctrl.value = "Nenhuma pergunta base disponível."
            txt_pergunta_ctrl.opacity = 1
            for btn in btn_opcoes_ctrls: btn.visible = False
            txt_feedback_ctrl.value = ""
            btn_proxima_ctrl.visible = False
            page_ref.update()
            return

        resultado_para_exibir = multiplicacao_selecionada_base['fator1'] * multiplicacao_selecionada_base['fator2']
        txt_pergunta_ctrl.value = f"Qual operação resulta em {resultado_para_exibir}?"

        opcoes_objs = gerar_opcoes_quiz_invertido(multiplicacao_selecionada_base, multiplicacoes_data)

        for i in range(len(opcoes_objs)): # Usar len(opcoes_objs) que deve ser 4
            btn_opcoes_ctrls[i].text = opcoes_objs[i]['texto']
            # Armazena o objeto da opção e também a referência da pergunta base (a correta que gerou o resultado)
            btn_opcoes_ctrls[i].data = {'opcao_obj': opcoes_objs[i], 'pergunta_base_original_ref': multiplicacao_selecionada_base}
            current_button = btn_opcoes_ctrls[i]
            btn_opcoes_ctrls[i].on_click = lambda e, btn=current_button: handle_resposta_invertida(page_ref, btn, btn_opcoes_ctrls, txt_feedback_ctrl, btn_proxima_ctrl)
            btn_opcoes_ctrls[i].bgcolor = COR_AZUL_BOTAO_OPCAO
            btn_opcoes_ctrls[i].color = COR_TEXTO_SOBRE_AZUL
            btn_opcoes_ctrls[i].disabled = False
            btn_opcoes_ctrls[i].visible = True

        txt_feedback_ctrl.value = ""
        btn_proxima_ctrl.visible = False
        txt_pergunta_ctrl.opacity = 1
        for btn_opcao in btn_opcoes_ctrls: btn_opcao.opacity = 1
        page_ref.update()

    botao_proxima_invertido.on_click = lambda _: carregar_nova_pergunta_invertida(page, texto_pergunta_invertida, botoes_opcoes_invertidas, texto_feedback_invertido, botao_proxima_invertido)
    carregar_nova_pergunta_invertida(page, texto_pergunta_invertida, botoes_opcoes_invertidas, texto_feedback_invertido, botao_proxima_invertido)

    botao_voltar_menu_invertido = ElevatedButton("Voltar ao Menu", on_click=lambda _: page.go("/"), width=BOTAO_LARGURA_PRINCIPAL, height=BOTAO_ALTURA_PRINCIPAL, tooltip="Retornar à tela inicial.", bgcolor=COR_ROXO_PRINCIPAL, color=COR_TEXTO_SOBRE_ROXO)
    layout_botoes_opcoes_inv = Column([Row(botoes_opcoes_invertidas[0:2], alignment=MainAxisAlignment.CENTER, spacing=15), Container(height=10), Row(botoes_opcoes_invertidas[2:4], alignment=MainAxisAlignment.CENTER, spacing=15)], horizontal_alignment=CrossAxisAlignment.CENTER, spacing=10)

    conteudo_quiz_invertido = Column(
        controls=[
            texto_pergunta_invertida, Container(height=15),
            layout_botoes_opcoes_inv, Container(height=15),
            texto_feedback_invertido, Container(height=20),
            botao_proxima_invertido, Container(height=10),
            botao_voltar_menu_invertido
        ],
        alignment=MainAxisAlignment.CENTER, horizontal_alignment=CrossAxisAlignment.CENTER,
        spacing=ESPACAMENTO_COLUNA_GERAL, scroll=ScrollMode.AUTO
    )
    return Container(content=conteudo_quiz_invertido, alignment=alignment.center, expand=True, padding=PADDING_VIEW)


def build_tela_treino(page: Page):
    # ... (código da tela de treino permanece o mesmo) ...
    tabuada_sugerida = sugerir_tabuada_para_treino()
    titulo_treino = Text(f"Treinando a Tabuada do {tabuada_sugerida}", size=28, weight=FontWeight.BOLD, text_align=TextAlign.CENTER, color=COR_TEXTO_TITULOS)
    campos_tabuada_refs = []
    coluna_itens_tabuada = Column(spacing=10, scroll=ScrollMode.AUTO, expand=True, horizontal_alignment=CrossAxisAlignment.CENTER)
    for i in range(1, 11):
        resposta_correta_val = tabuada_sugerida * i
        texto_multiplicacao = Text(f"{tabuada_sugerida} x {i} = ", size=18, color=COR_TEXTO_PADRAO_ESCURO)
        campo_resposta = TextField(width=100, text_align=TextAlign.CENTER, data={'fator1': tabuada_sugerida, 'fator2': i, 'resposta_correta': resposta_correta_val}, keyboard_type=KeyboardType.NUMBER)
        campos_tabuada_refs.append(campo_resposta)
        coluna_itens_tabuada.controls.append(Row([texto_multiplicacao, campo_resposta], alignment=MainAxisAlignment.CENTER, spacing=10))
    texto_resumo_treino = Text(size=18, weight=FontWeight.BOLD, text_align=TextAlign.CENTER, color=COR_TEXTO_PADRAO_ESCURO)
    botao_verificar = ElevatedButton("Verificar Respostas", width=BOTAO_LARGURA_PRINCIPAL, height=BOTAO_ALTURA_PRINCIPAL, tooltip="Corrigir as respostas da tabuada.", bgcolor=COR_ROXO_PRINCIPAL, color=COR_TEXTO_SOBRE_ROXO)
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
    botao_voltar_menu = ElevatedButton("Voltar ao Menu", on_click=lambda _: page.go("/"), width=BOTAO_LARGURA_PRINCIPAL, height=BOTAO_ALTURA_PRINCIPAL, tooltip="Retornar à tela inicial.", bgcolor=COR_ROXO_PRINCIPAL, color=COR_TEXTO_SOBRE_ROXO)
    container_tabuada = Container(content=coluna_itens_tabuada, border=border.all(2, COR_BORDA_CONTAINER_TREINO), border_radius=8, padding=padding.all(15), width=360, height=420, bgcolor=COR_FUNDO_CONTAINER_TREINO)
    conteudo_treino = Column(controls=[titulo_treino, Container(height=10), container_tabuada, Container(height=10), botao_verificar, Container(height=10), texto_resumo_treino, Container(height=15), botao_voltar_menu], alignment=MainAxisAlignment.CENTER, horizontal_alignment=CrossAxisAlignment.CENTER, spacing=ESPACAMENTO_COLUNA_GERAL, scroll=ScrollMode.AUTO)
    return Container(content=conteudo_treino, alignment=alignment.center, expand=True, padding=PADDING_VIEW)

def build_tela_estatisticas(page: Page):
    # ... (código da tela de estatísticas permanece o mesmo) ...
    stats_gerais = calcular_estatisticas_gerais()
    proficiencia_tabuadas = calcular_proficiencia_tabuadas()
    lista_proficiencia_controls = []
    for t in range(1, 11):
        progresso = proficiencia_tabuadas.get(t, 0) / 100.0
        cor_barra = COR_VERDE_ACERTO if progresso >= 0.7 else (COR_ROXO_PRINCIPAL if progresso >= 0.4 else COR_VERMELHO_ERRO)
        lista_proficiencia_controls.append(Row([Text(f"Tabuada do {t}: ", size=16, color=COR_TEXTO_PADRAO_ESCURO, width=130), ProgressBar(value=progresso, width=150, color=cor_barra, bgcolor=ft.Colors.with_opacity(0.2, cor_barra)), Text(f"{proficiencia_tabuadas.get(t, 0):.1f}%", size=16, color=COR_TEXTO_PADRAO_ESCURO, width=60, text_align=TextAlign.RIGHT)], alignment=MainAxisAlignment.CENTER))
    coluna_proficiencia = Column(controls=lista_proficiencia_controls, spacing=8, horizontal_alignment=CrossAxisAlignment.CENTER)
    top_3_texts = [Text(item, size=16, color=COR_TEXTO_PADRAO_ESCURO) for item in stats_gerais['top_3_dificeis']]
    if not top_3_texts: top_3_texts = [Text("Nenhuma dificuldade registrada ainda!", size=16, color=COR_TEXTO_PADRAO_ESCURO)]
    coluna_dificuldades = Column(controls=top_3_texts, spacing=5, horizontal_alignment=CrossAxisAlignment.CENTER)
    conteudo_estatisticas = Column(controls=[Text("Suas Estatísticas", size=32, weight=FontWeight.BOLD, color=COR_TEXTO_TITULOS, text_align=TextAlign.CENTER), Container(height=15), Text(f"Total de Perguntas Respondidas: {stats_gerais['total_respondidas']}", size=18, color=COR_TEXTO_PADRAO_ESCURO), Text(f"Percentual de Acertos Geral: {stats_gerais['percentual_acertos_geral']:.1f}%", size=18, color=COR_TEXTO_PADRAO_ESCURO), Container(height=10), Text("Proficiência por Tabuada:", size=22, weight=FontWeight.SEMI_BOLD, color=COR_TEXTO_TITULOS, margin=Margin(top=20, bottom=10)), coluna_proficiencia, Container(height=10), Text("Maiores Dificuldades Atuais:", size=22, weight=FontWeight.SEMI_BOLD, color=COR_TEXTO_TITULOS, margin=Margin(top=20, bottom=10)), coluna_dificuldades, Container(height=25), ElevatedButton("Voltar ao Menu", width=BOTAO_LARGURA_PRINCIPAL, height=BOTAO_ALTURA_PRINCIPAL, on_click=lambda _: page.go("/"), tooltip="Retornar à tela inicial.", bgcolor=COR_ROXO_PRINCIPAL, color=COR_TEXTO_SOBRE_ROXO)], scroll=ScrollMode.AUTO, alignment=MainAxisAlignment.CENTER, horizontal_alignment=CrossAxisAlignment.CENTER, spacing=ESPACAMENTO_COLUNA_GERAL)
    return Container(content=conteudo_estatisticas, alignment=alignment.center, expand=True, padding=PADDING_VIEW)

# --- Configuração Principal da Página e Rotas ---
def main(page: Page):
    page.title = "Quiz Mestre da Tabuada"
    page.vertical_alignment = MainAxisAlignment.CENTER
    page.horizontal_alignment = CrossAxisAlignment.CENTER
    page.bgcolor = COR_FUNDO_PAGINA
    page.window_width = 480
    page.window_height = 800
    page.fonts = {"RobotoSlab": "https://github.com/google/fonts/raw/main/apache/robotoslab/RobotoSlab%5Bwght%5D.ttf"}

    def route_change(route):
        page.views.clear()
        page.views.append(View("/", [build_tela_apresentacao(page)], vertical_alignment=MainAxisAlignment.CENTER, horizontal_alignment=CrossAxisAlignment.CENTER))
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
