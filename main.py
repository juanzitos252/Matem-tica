import flet as ft
from flet import (
    Page, Text, ElevatedButton, Row, Column, TextField, View, Container,
    MainAxisAlignment, CrossAxisAlignment, FontWeight, alignment,
    TextAlign, ScrollMode, padding, border, KeyboardType,
    Animation, AnimationCurve, ProgressBar # Margin removida
)
import random
import time
import requests
from packaging import version
import subprocess
import threading
import os # Adicionado para manipulação de caminhos

# --- Definições das Fórmulas Notáveis (Integrado de formula_definitions.py) ---

# --- Funções de Cálculo para Fórmulas Notáveis ---

def calc_quadrado_soma(a: int, b: int) -> int:
    """Calcula (a+b)^2."""
    return (a + b) ** 2

def calc_quadrado_diferenca(a: int, b: int) -> int:
    """Calcula (a-b)^2."""
    return (a - b) ** 2

def calc_produto_soma_diferenca(a: int, b: int) -> int:
    """Calcula a^2 - b^2."""
    return a**2 - b**2

def calc_raiz_soma_diferenca(val_a: int, val_b: int) -> int:
    """Calcula a - b, onde val_a e val_b são os números DENTRO das raízes na pergunta."""
    return val_a - val_b

# --- Definições da Lista de Fórmulas Notáveis ---
FORMULAS_NOTAVEIS = [
    {
        'id': "quadrado_soma",
        'display_name': "Quadrado da Soma: (a+b)^2",
        'variables': ['a', 'b'],
        'calculation_function': calc_quadrado_soma,
        'question_template': "Se a={a} e b={b}, qual o valor de (a+b)^2?",
        'reminder_template': "(x+y)^2 = x^2 + 2xy + y^2",
        'range_constraints': {},
        'variable_labels': {'a': "Valor de 'a'", 'b': "Valor de 'b'"}
    },
    {
        'id': "quadrado_diferenca",
        'display_name': "Quadrado da Diferença: (a-b)^2",
        'variables': ['a', 'b'],
        'calculation_function': calc_quadrado_diferenca,
        'question_template': "Se a={a} e b={b}, qual o valor de (a-b)^2?",
        'reminder_template': "(x-y)^2 = x^2 - 2xy + y^2",
        'range_constraints': {},
        'variable_labels': {'a': "Valor de 'a'", 'b': "Valor de 'b'"}
    },
    {
        'id': "produto_soma_diferenca",
        'display_name': "Produto da Soma pela Diferença: (a+b)(a-b)",
        'variables': ['a', 'b'],
        'calculation_function': calc_produto_soma_diferenca,
        'question_template': "Se a={a} e b={b}, qual o valor de (a+b)(a-b)?",
        'reminder_template': "(x+y)(x-y) = x^2 - y^2",
        'range_constraints': {'b': 'less_than_equal_a'},
        'variable_labels': {'a': "Valor de 'a'", 'b': "Valor de 'b' (b <= a)"}
    },
    {
        'id': "raiz_soma_diferenca",
        'display_name': "Diferença de Quadrados (Raízes): (sqrt(a)+sqrt(b))(sqrt(a)-sqrt(b))",
        'variables': ['a', 'b'],
        'calculation_function': calc_raiz_soma_diferenca,
        'question_template': "Qual o valor de (sqrt({a}) + sqrt({b})) * (sqrt({a}) - sqrt({b}))?",
        'reminder_template': "(sqrt(x) + sqrt(y))(sqrt(x) - sqrt(y)) = x - y",
        'range_constraints': {
            'a': {'min': 2},
            'b': {'less_than_a': True, 'min': 1}
        },
        'variable_labels': {
            'a': "Valor de 'a' (dentro da sqrt, a > b)",
            'b': "Valor de 'b' (dentro da sqrt, b < a)"
        }
    },
]

def get_formula_definition(formula_id: str):
    for formula in FORMULAS_NOTAVEIS:
        if formula['id'] == formula_id:
            return formula
    return None

# --- Fim das Definições das Fórmulas Notáveis ---

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
        itens_tabuada_t_apresentados, vistos_para_tabuada_t = [], set()
        for item_p in multiplicacoes_data:
            par_ordenado = tuple(sorted((item_p['fator1'], item_p['fator2'])))
            # Considerar apenas itens que foram apresentados
            if (item_p['fator1'] == t or item_p['fator2'] == t) and \
               par_ordenado not in vistos_para_tabuada_t and \
               item_p['vezes_apresentada'] > 0:
                itens_tabuada_t_apresentados.append(item_p)
                vistos_para_tabuada_t.add(par_ordenado)

        if not itens_tabuada_t_apresentados:
            # Se nenhum item da tabuada foi apresentado, a proficiência é 0
            proficiencia_por_tabuada[t] = 0.0
        else:
            # Calcular a média dos pesos apenas dos itens apresentados
            media_pesos = sum(it['peso'] for it in itens_tabuada_t_apresentados) / len(itens_tabuada_t_apresentados)
            # A fórmula de proficiência permanece a mesma, mas baseada em dados relevantes
            proficiencia_percentual = max(0, (100.0 - media_pesos) / (100.0 - 1.0)) * 100.0
            proficiencia_por_tabuada[t] = round(proficiencia_percentual, 1)

    return proficiencia_por_tabuada

inicializar_multiplicacoes()

# --- Armazenamento de Fórmulas Personalizadas ---
custom_formulas_data = [] # Lista para armazenar as fórmulas personalizadas
current_custom_formula_for_quiz = None # Armazena a fórmula selecionada para o quiz personalizado

# --- Constantes e Lógica de Atualização ---
GITHUB_REPO_URL = "https://api.github.com/repos/desenvolvedorXXX/quiz_app_flet/releases/latest" # Substitua pelo seu URL
APP_CURRENT_VERSION = "0.1.0" # Defina a versão atual do seu aplicativo

# Variáveis globais para status da atualização
update_available = False
latest_version_tag = ""
update_check_status_message = "Verificando atualizações..."

def get_local_git_commit_hash():
    """Obtém o hash do commit local."""
    try:
        # Verifica se é um repositório git
        if not os.path.exists(".git"):
            return "Não é um repositório git"

        result = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Erro ao obter hash do commit local: {e}")
        return "Erro ao obter commit"
    except FileNotFoundError:
        print("Git não encontrado. Certifique-se de que está instalado e no PATH.")
        return "Git não encontrado"

local_git_commit = get_local_git_commit_hash()

def check_for_updates():
    global update_available, latest_version_tag, update_check_status_message, APP_CURRENT_VERSION
    try:
        response = requests.get(GITHUB_REPO_URL, timeout=10)
        response.raise_for_status()
        release_info = response.json()
        latest_version_tag = release_info['tag_name']

        # Remove 'v' prefixo se existir (ex: v1.0.1 -> 1.0.1)
        parsed_latest_version = latest_version_tag.lstrip('v')
        parsed_current_version = APP_CURRENT_VERSION.lstrip('v')

        if version.parse(parsed_latest_version) > version.parse(parsed_current_version):
            update_available = True
            update_check_status_message = f"Nova versão {latest_version_tag} disponível!"
            print(f"Atualização disponível: {latest_version_tag}")
        else:
            update_available = False
            update_check_status_message = "Você está na versão mais recente."
            print("Nenhuma atualização encontrada.")
    except requests.exceptions.RequestException as e:
        update_check_status_message = "Erro ao verificar atualizações."
        print(f"Erro ao verificar atualizações: {e}")
    except Exception as e:
        update_check_status_message = "Erro inesperado na verificação."
        print(f"Erro inesperado ao verificar atualizações: {e}")

# --- Temas e Gerenciamento de Tema ---
TEMAS = {
    "colorido": {"fundo_pagina": ft.Colors.PURPLE_50, "texto_titulos": ft.Colors.DEEP_PURPLE_700, "texto_padrao": ft.Colors.BLACK87, "botao_principal_bg": ft.Colors.DEEP_PURPLE_400, "botao_principal_texto": ft.Colors.WHITE, "botao_opcao_quiz_bg": ft.Colors.BLUE_300, "botao_opcao_quiz_texto": ft.Colors.WHITE, "botao_destaque_bg": ft.Colors.PINK_ACCENT_200, "botao_destaque_texto": ft.Colors.BLACK87, "botao_tema_bg": ft.Colors.PINK_ACCENT_100, "botao_tema_texto": ft.Colors.BLACK, "feedback_acerto_texto": ft.Colors.GREEN_600, "feedback_erro_texto": ft.Colors.RED_500, "feedback_acerto_botao_bg": ft.Colors.GREEN_100, "feedback_erro_botao_bg": ft.Colors.RED_100, "container_treino_bg": ft.Colors.WHITE, "container_treino_borda": ft.Colors.DEEP_PURPLE_400, "textfield_border_color": ft.Colors.DEEP_PURPLE_400, "dropdown_border_color": ft.Colors.DEEP_PURPLE_400,"progressbar_cor": ft.Colors.DEEP_PURPLE_400, "progressbar_bg_cor": ft.Colors.PURPLE_100, "update_icon_color_available": ft.Colors.AMBER_700, "update_icon_color_uptodate": ft.Colors.GREEN_700, "update_icon_color_error": ft.Colors.RED_700},
    "claro": {"fundo_pagina": ft.Colors.GREY_100, "texto_titulos": ft.Colors.BLACK, "texto_padrao": ft.Colors.BLACK87, "botao_principal_bg": ft.Colors.BLUE_600, "botao_principal_texto": ft.Colors.WHITE, "botao_opcao_quiz_bg": ft.Colors.LIGHT_BLUE_200, "botao_opcao_quiz_texto": ft.Colors.BLACK87, "botao_destaque_bg": ft.Colors.CYAN_600, "botao_destaque_texto": ft.Colors.WHITE, "botao_tema_bg": ft.Colors.CYAN_200, "botao_tema_texto": ft.Colors.BLACK87,"feedback_acerto_texto": ft.Colors.GREEN_700, "feedback_erro_texto": ft.Colors.RED_700, "feedback_acerto_botao_bg": ft.Colors.GREEN_100, "feedback_erro_botao_bg": ft.Colors.RED_100, "container_treino_bg": ft.Colors.WHITE, "container_treino_borda": ft.Colors.BLUE_600, "textfield_border_color": ft.Colors.BLUE_600, "dropdown_border_color": ft.Colors.BLUE_600, "progressbar_cor": ft.Colors.BLUE_600, "progressbar_bg_cor": ft.Colors.BLUE_100, "update_icon_color_available": ft.Colors.ORANGE_ACCENT_700, "update_icon_color_uptodate": ft.Colors.GREEN_800, "update_icon_color_error": ft.Colors.RED_800},
    "escuro_moderno": {
        "fundo_pagina": ft.Colors.TEAL_900, # Fallback for page.bgcolor
        "gradient_page_bg": ft.LinearGradient(
            begin=alignment.top_center, # Changed from top_left
            end=alignment.bottom_center,  # Changed from bottom_right
            colors=[ft.Colors.INDIGO_900, ft.Colors.PURPLE_800, ft.Colors.TEAL_800], # Slightly adjusted shades for harmony
            stops=[0.1, 0.6, 1.0]
        ),
        "texto_titulos": ft.Colors.CYAN_ACCENT_200,
        "texto_padrao": ft.Colors.WHITE,
        "botao_principal_bg": ft.Colors.PINK_ACCENT_400,
        "botao_principal_texto": ft.Colors.WHITE,
        "botao_opcao_quiz_bg": ft.Colors.BLUE_GREY_700,
        "botao_opcao_quiz_texto": ft.Colors.WHITE,
        "botao_destaque_bg": ft.Colors.TEAL_ACCENT_400,
        "botao_destaque_texto": ft.Colors.WHITE,
        "botao_tema_bg": ft.Colors.with_opacity(0.2, ft.Colors.WHITE), # For theme selection buttons
        "botao_tema_texto": ft.Colors.CYAN_ACCENT_100,                 # For theme selection buttons text
        "feedback_acerto_texto": ft.Colors.GREEN_ACCENT_200,
        "feedback_erro_texto": ft.Colors.RED_ACCENT_100,
        "feedback_acerto_botao_bg": ft.Colors.with_opacity(0.3, ft.Colors.GREEN_ACCENT_100),
        "feedback_erro_botao_bg": ft.Colors.with_opacity(0.3, ft.Colors.RED_ACCENT_100),
        "container_treino_bg": ft.Colors.with_opacity(0.1, ft.Colors.WHITE), # Slightly more subtle frosted glass
        "container_treino_borda": ft.Colors.CYAN_ACCENT_700,
        "textfield_border_color": ft.Colors.CYAN_ACCENT_700,
        "dropdown_border_color": ft.Colors.CYAN_ACCENT_700,
        "progressbar_cor": ft.Colors.CYAN_ACCENT_400,
        "progressbar_bg_cor": ft.Colors.with_opacity(0.2, ft.Colors.WHITE),
        "update_icon_color_available": ft.Colors.YELLOW_ACCENT_400,
        "update_icon_color_uptodate": ft.Colors.GREEN_ACCENT_400,
        "update_icon_color_error": ft.Colors.RED_ACCENT_400
    }
}
tema_ativo_nome = "colorido" # Default theme
def obter_cor_do_tema_ativo(nome_cor_semantica: str, fallback_color=ft.Colors.BLACK): # Added fallback_color param
    # Se o tema ativo for o novo escuro e a cor pedida for 'gradient_page_bg', retorna o objeto Gradient.
    if tema_ativo_nome == "escuro_moderno" and nome_cor_semantica == "gradient_page_bg":
        return TEMAS["escuro_moderno"]["gradient_page_bg"]

    tema_atual = TEMAS.get(tema_ativo_nome, TEMAS["colorido"])
    return tema_atual.get(nome_cor_semantica, fallback_color) # Use provided fallback

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

    # Store current route
    current_route_val = page.route

    # Clear existing views
    page.views.clear()

    # Re-populate views directly, ensuring all build_... functions use the new theme.
    # This logic is similar to what's in route_change.

    # Base view (always present, typically the home screen)
    page.views.append(
        View(
            route="/",
            controls=[build_tela_apresentacao(page)],
            vertical_alignment=MainAxisAlignment.CENTER,
            horizontal_alignment=CrossAxisAlignment.CENTER
        )
    )

    # Append the specific view for the current_route_val if it's not the base view.
    # If current_route_val is "/", the base view is already the top view.
    if current_route_val == "/quiz":
        page.views.append(View("/quiz", [build_tela_quiz(page)], vertical_alignment=MainAxisAlignment.CENTER, horizontal_alignment=CrossAxisAlignment.CENTER))
    elif current_route_val == "/quiz_invertido":
        page.views.append(View("/quiz_invertido", [build_tela_quiz_invertido(page)], vertical_alignment=MainAxisAlignment.CENTER, horizontal_alignment=CrossAxisAlignment.CENTER))
    elif current_route_val == "/treino":
        page.views.append(View("/treino", [build_tela_treino(page)], vertical_alignment=MainAxisAlignment.CENTER, horizontal_alignment=CrossAxisAlignment.CENTER))
    elif current_route_val == "/estatisticas":
        page.views.append(View("/estatisticas", [build_tela_estatisticas(page)], vertical_alignment=MainAxisAlignment.CENTER, horizontal_alignment=CrossAxisAlignment.CENTER))
    elif current_route_val == "/formula_quiz_setup":
        page.views.append(View("/formula_quiz_setup", [build_tela_formula_quiz_setup(page)], vertical_alignment=MainAxisAlignment.CENTER, horizontal_alignment=CrossAxisAlignment.CENTER))
    elif current_route_val == "/custom_quiz":
        page.views.append(View("/custom_quiz", [build_tela_custom_quiz(page)], vertical_alignment=MainAxisAlignment.CENTER, horizontal_alignment=CrossAxisAlignment.CENTER))

    page.update()
    # We avoid calling page.go() here as we've manually rebuilt the view stack.
    # Calling page.go() would trigger route_change again, which is now redundant for this theme update.

# --- Funções Auxiliares para Fórmulas ---
# (parse_variable_ranges pode ser mantido se for útil para os ranges de 'a' e 'b' das fórmulas notáveis)
def parse_variable_ranges(range_str: str, default_min=1, default_max=10):
    """Converte uma string como '1-10' em {'min': 1, 'max': 10}. Limita ao intervalo 1-100."""
    try:
        parts = range_str.split('-')
        min_val = int(parts[0].strip())
        max_val = int(parts[1].strip())

        # Garante min <= max
        if min_val > max_val:
            min_val, max_val = max_val, min_val

        # Limita os valores para estar entre 1 e 10 (ou outro limite superior se necessário no futuro)
        # Para as variáveis base das fórmulas notáveis, vamos manter o limite de 1-10.
        min_val = max(1, min(min_val, 10))
        max_val = max(1, min(max_val, 10))

        # Garante min <= max novamente após o clipping
        if min_val > max_val:
            min_val = max_val # Se min_val era 11 e max_val era 5, ambos se tornam 10, depois min é ajustado.

        return {'min': min_val, 'max': max_val}
    except:
        # Retorna o padrão, mas também limitado
        return {'min': max(1, min(default_min, 10)), 'max': max(1, min(default_max, 10))}

# (A linha "from formula_definitions import FORMULAS_NOTAVEIS, get_formula_definition" foi removida pois as definições estão agora neste arquivo)

# --- Tela de Configuração de Quiz com Fórmula Notável ---
def build_tela_formula_quiz_setup(page: Page):
    # Campo para nomear esta configuração de quiz (opcional, mas útil se salvarmos)
    quiz_config_name_field = TextField(
        label="Nome para esta Configuração de Quiz (Ex: Treino Quadrado da Soma)",
        width=350,
        color=obter_cor_do_tema_ativo("texto_padrao"),
        border_color=obter_cor_do_tema_ativo("textfield_border_color")
    )

    # Dropdown para selecionar o tipo de fórmula notável
    formula_type_dropdown_options = [
        ft.dropdown.Option(key=f['id'], text=f['display_name']) for f in FORMULAS_NOTAVEIS
    ]
    formula_type_dropdown = Dropdown(
        label="Selecione o Tipo de Fórmula",
        width=350,
        options=formula_type_dropdown_options,
        border_color=obter_cor_do_tema_ativo("dropdown_border_color"),
        color=obter_cor_do_tema_ativo("texto_padrao")
    )

    # Campos para os ranges das variáveis (inicialmente para 'a' e 'b')
    # Labels serão atualizados com base na fórmula selecionada
    var_a_range_field = TextField(
        label="Range para 'a' (1-10)", # Label genérico inicial
        width=170,
        color=obter_cor_do_tema_ativo("texto_padrao"),
        border_color=obter_cor_do_tema_ativo("textfield_border_color"),
        value="1-10" # Valor padrão
    )
    var_b_range_field = TextField(
        label="Range para 'b' (1-10)", # Label genérico inicial
        width=170,
        color=obter_cor_do_tema_ativo("texto_padrao"),
        border_color=obter_cor_do_tema_ativo("textfield_border_color"),
        value="1-10", # Valor padrão
        visible=True # A maioria das fórmulas usará 'b'
    )

    feedback_text = Text("", color=obter_cor_do_tema_ativo("texto_padrao"))

    # Dropdown para listar configurações de quiz salvas
    # (Anteriormente 'formulas_dropdown', agora 'saved_quiz_configs_dropdown')
    saved_quiz_configs_dropdown = Dropdown(
        label="Ou selecione uma configuração de quiz salva",
        width=350,
        options=[ft.dropdown.Option(key=cfg['name'], text=cfg['name']) for cfg in custom_formulas_data], # custom_formulas_data será adaptado
        border_color=obter_cor_do_tema_ativo("dropdown_border_color"),
        color=obter_cor_do_tema_ativo("texto_padrao")
    )

    def update_variable_fields(selected_formula_id: str):
        """Atualiza a visibilidade e labels dos campos de range das variáveis."""
        definition = get_formula_definition(selected_formula_id)
        if not definition:
            var_a_range_field.visible = False
            var_b_range_field.visible = False
        else:
            variables = definition.get('variables', [])
            labels = definition.get('variable_labels', {})

            if 'a' in variables:
                var_a_range_field.label = labels.get('a', "Range para 'a' (1-10)")
                var_a_range_field.visible = True
            else:
                var_a_range_field.visible = False

            if 'b' in variables:
                var_b_range_field.label = labels.get('b', "Range para 'b' (1-10)")
                var_b_range_field.visible = True
            else:
                var_b_range_field.visible = False
        page.update()

    def on_formula_type_change(e):
        if formula_type_dropdown.value:
            update_variable_fields(formula_type_dropdown.value)
        else: # Nenhum tipo selecionado, esconde campos de range
            var_a_range_field.visible = False
            var_b_range_field.visible = False
            page.update()

    formula_type_dropdown.on_change = on_formula_type_change
    # Inicializar visibilidade dos campos de range (nenhuma fórmula selecionada inicialmente)
    var_a_range_field.visible = False
    var_b_range_field.visible = False


    def update_saved_quiz_configs_dropdown():
        # custom_formulas_data agora armazena configurações de quiz notável
        saved_quiz_configs_dropdown.options = [
            ft.dropdown.Option(key=cfg['name'], text=cfg['name']) for cfg in custom_formulas_data
        ]
        current_selection = saved_quiz_configs_dropdown.value
        if custom_formulas_data:
            if not any(opt.key == current_selection for opt in saved_quiz_configs_dropdown.options):
                saved_quiz_configs_dropdown.value = custom_formulas_data[-1]['name']
        else:
            saved_quiz_configs_dropdown.value = None
        saved_quiz_configs_dropdown.update()

    # Handler para SALVAR uma CONFIGURAÇÃO de quiz com fórmula notável
    # (Adaptado de save_custom_formula_handler)
    def save_quiz_config_handler(e):
        global custom_formulas_data # Esta lista agora armazena configs de quiz notável

        config_name = quiz_config_name_field.value.strip()
        selected_formula_id = formula_type_dropdown.value

        if not config_name:
            feedback_text.value = "Por favor, dê um nome para esta configuração de quiz."
            feedback_text.color = obter_cor_do_tema_ativo("feedback_erro_texto")
            page.update()
            return

        if not selected_formula_id:
            feedback_text.value = "Por favor, selecione um tipo de fórmula."
            feedback_text.color = obter_cor_do_tema_ativo("feedback_erro_texto")
            page.update()
            return

        if any(cfg['name'] == config_name for cfg in custom_formulas_data):
            feedback_text.value = f"Uma configuração de quiz com o nome '{config_name}' já existe."
            feedback_text.color = obter_cor_do_tema_ativo("feedback_erro_texto")
            page.update()
            return

        # Obter ranges das variáveis visíveis
        ranges = {}
        definition = get_formula_definition(selected_formula_id)
        if definition:
            if 'a' in definition.get('variables', []):
                ranges['a'] = parse_variable_ranges(var_a_range_field.value)
            if 'b' in definition.get('variables', []):
                ranges['b'] = parse_variable_ranges(var_b_range_field.value)

        # Validar ranges com base nas constraints da fórmula (a ser feito na Etapa 5 ao gerar pergunta)
        # Por ex, para raiz_soma_diferenca, b deve ser < a.
        # Esta validação pode ser mais complexa e talvez melhor no momento da geração da pergunta
        # ou com feedback mais dinâmico na UI. Por agora, salvamos os ranges como dados.

        quiz_config_entry = {
            'name': config_name,
            'formula_id': selected_formula_id,
            'ranges': ranges
            # 'reminder_template' e 'question_template' virão da definição da fórmula ao gerar o quiz
        }
        custom_formulas_data.append(quiz_config_entry)
        feedback_text.value = f"Configuração de Quiz '{config_name}' salva!"
        feedback_text.color = obter_cor_do_tema_ativo("feedback_acerto_texto")

        update_saved_quiz_configs_dropdown()
        quiz_config_name_field.value = ""
        formula_type_dropdown.value = None # Resetar dropdown de tipo
        var_a_range_field.visible = False # Esconder ranges
        var_b_range_field.visible = False
        page.update()

    # Handler para INICIAR um quiz com uma CONFIGURAÇÃO SALVA
    def start_quiz_with_saved_config_handler(e):
        global current_custom_formula_for_quiz # Esta var global será usada para passar a config do quiz

        selected_config_name = saved_quiz_configs_dropdown.value
        if not selected_config_name:
            feedback_text.value = "Nenhuma configuração de quiz salva selecionada."
            feedback_text.color = obter_cor_do_tema_ativo("feedback_erro_texto")
            page.update()
            return

        # Encontra a configuração salva
        quiz_config_to_run = next((cfg for cfg in custom_formulas_data if cfg['name'] == selected_config_name), None)

        if quiz_config_to_run:
            # `current_custom_formula_for_quiz` agora armazena a *configuração do quiz* selecionada,
            # que inclui o formula_id e os ranges.
            current_custom_formula_for_quiz = quiz_config_to_run
            page.go("/custom_quiz") # A tela /custom_quiz precisará ser adaptada
        else:
            feedback_text.value = f"Configuração de Quiz '{selected_config_name}' não encontrada."
            feedback_text.color = obter_cor_do_tema_ativo("feedback_erro_texto")
            page.update()

    update_saved_quiz_configs_dropdown() # Atualizar dropdown de configs salvas na carga inicial

    save_button = ElevatedButton("Salvar Configuração do Quiz", on_click=save_quiz_config_handler, width=BOTAO_LARGURA_PRINCIPAL, height=BOTAO_ALTURA_PRINCIPAL, bgcolor=obter_cor_do_tema_ativo("botao_principal_bg"), color=obter_cor_do_tema_ativo("botao_principal_texto"))
    start_quiz_button = ElevatedButton("Iniciar Quiz com Config. Salva", on_click=start_quiz_with_saved_config_handler, width=BOTAO_LARGURA_PRINCIPAL, height=BOTAO_ALTURA_PRINCIPAL, bgcolor=obter_cor_do_tema_ativo("botao_destaque_bg"), color=obter_cor_do_tema_ativo("botao_destaque_texto"))
    back_button = ElevatedButton("Voltar ao Menu", on_click=lambda _: page.go("/"), width=BOTAO_LARGURA_PRINCIPAL, height=BOTAO_ALTURA_PRINCIPAL, bgcolor=obter_cor_do_tema_ativo("botao_principal_bg"), color=obter_cor_do_tema_ativo("botao_principal_texto"))

    content = Column(
        controls=[
            Text("Configurar Quiz com Fórmula Notável", size=28, weight=FontWeight.BOLD, color=obter_cor_do_tema_ativo("texto_titulos")),
            Container(height=10),
            Text("1. Configure um novo Quiz:", size=18, weight=FontWeight.BOLD, color=obter_cor_do_tema_ativo("texto_padrao")),
            quiz_config_name_field,
            formula_type_dropdown, # Novo dropdown para tipo de fórmula
            Container(height=5),
            Text("Defina os ranges para as variáveis (1-10):", color=obter_cor_do_tema_ativo("texto_padrao"), size=12),
            Row([var_a_range_field, var_b_range_field], spacing=10, alignment=MainAxisAlignment.CENTER),
            Container(height=10),
            save_button, # Agora salva a configuração do quiz
            Container(height=15, border=ft.border.only(bottom=ft.BorderSide(1, obter_cor_do_tema_ativo("texto_padrao"))), margin=ft.margin.symmetric(vertical=10)),
            Text("2. Ou inicie um Quiz com uma Configuração Salva:", size=18, weight=FontWeight.BOLD, color=obter_cor_do_tema_ativo("texto_padrao")),
            saved_quiz_configs_dropdown, # Lista configurações salvas
            Container(height=10),
            start_quiz_button, # Inicia com config salva
            Container(height=10),
            feedback_text,
            Container(height=15),
            back_button,
        ],
        scroll=ScrollMode.AUTO,
        alignment=MainAxisAlignment.CENTER,
        horizontal_alignment=CrossAxisAlignment.CENTER,
        spacing=ESPACAMENTO_COLUNA_GERAL
    )

    view_container = Container(content=content, alignment=alignment.center, expand=True, padding=PADDING_VIEW)
    if tema_ativo_nome == "escuro_moderno":
        view_container.gradient = obter_cor_do_tema_ativo("gradient_page_bg")
        view_container.bgcolor = None
    else:
        view_container.bgcolor = obter_cor_do_tema_ativo("fundo_pagina")
        view_container.gradient = None
    return view_container


def build_tela_apresentacao(page: Page):
    controles_botoes_tema = [
        Text("Escolha um Tema:", size=16, color=obter_cor_do_tema_ativo("texto_padrao")),
        Container(height=5),
        Row(
            [
                ElevatedButton(text="Colorido", on_click=lambda _: mudar_tema(page, "colorido"), width=BOTAO_LARGURA_PRINCIPAL/2 - 5, height=BOTAO_ALTURA_PRINCIPAL-10, bgcolor=obter_cor_do_tema_ativo("botao_tema_bg"), color=obter_cor_do_tema_ativo("botao_tema_texto")),
                ElevatedButton(text="Claro", on_click=lambda _: mudar_tema(page, "claro"), width=BOTAO_LARGURA_PRINCIPAL/2 - 5, height=BOTAO_ALTURA_PRINCIPAL-10, bgcolor=obter_cor_do_tema_ativo("botao_tema_bg"), color=obter_cor_do_tema_ativo("botao_tema_texto")),
                ElevatedButton(text="Escuro Moderno", on_click=lambda _: mudar_tema(page, "escuro_moderno"), width=BOTAO_LARGURA_PRINCIPAL/2 - 5, height=BOTAO_ALTURA_PRINCIPAL-10, bgcolor=obter_cor_do_tema_ativo("botao_tema_bg"), color=obter_cor_do_tema_ativo("botao_tema_texto")),
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
            Container(height=ESPACAMENTO_BOTOES_APRESENTACAO),
            ElevatedButton("Quiz com Fórmulas", width=BOTAO_LARGURA_PRINCIPAL, height=BOTAO_ALTURA_PRINCIPAL, on_click=lambda _: page.go("/formula_quiz_setup"), tooltip="Crie ou selecione um quiz baseado em fórmulas notáveis.", bgcolor=obter_cor_do_tema_ativo("botao_destaque_bg"), color=obter_cor_do_tema_ativo("botao_destaque_texto")), # Rota e texto atualizados
            Container(height=20, margin=ft.margin.only(top=10)),
        ] + controles_botoes_tema + [
            Container(height=10),
            update_action_button, # Adiciona o botão de "Atualizar Agora" se visível
            Container(height=5),
            # Removido o texto de status daqui, pois está na AppBar
            # Row([update_status_icon, Container(width=5), update_status_text], alignment=MainAxisAlignment.CENTER, vertical_alignment=CrossAxisAlignment.CENTER)
        ],
        alignment=MainAxisAlignment.CENTER, horizontal_alignment=CrossAxisAlignment.CENTER, spacing=ESPACAMENTO_COLUNA_GERAL,
        # Adicionar scroll caso o conteúdo fique muito grande com os botões de tema
        scroll=ScrollMode.AUTO
    )

    view_container = Container(
        content=conteudo_apresentacao,
        alignment=alignment.center,
        expand=True,
        padding=PADDING_VIEW
    )

    if tema_ativo_nome == "escuro_moderno":
        view_container.gradient = obter_cor_do_tema_ativo("gradient_page_bg")
        view_container.bgcolor = None # Gradiente tem precedência
    else:
        view_container.bgcolor = obter_cor_do_tema_ativo("fundo_pagina")
        view_container.gradient = None

    return view_container

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

    view_container = Container(content=conteudo_quiz, alignment=alignment.center, expand=True, padding=PADDING_VIEW)
    if tema_ativo_nome == "escuro_moderno":
        view_container.gradient = obter_cor_do_tema_ativo("gradient_page_bg")
        view_container.bgcolor = None
    else:
        view_container.bgcolor = obter_cor_do_tema_ativo("fundo_pagina")
        view_container.gradient = None
    return view_container

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

    view_container = Container(content=conteudo_quiz_inv, alignment=alignment.center, expand=True, padding=PADDING_VIEW)
    if tema_ativo_nome == "escuro_moderno":
        view_container.gradient = obter_cor_do_tema_ativo("gradient_page_bg")
        view_container.bgcolor = None
    else:
        view_container.bgcolor = obter_cor_do_tema_ativo("fundo_pagina")
        view_container.gradient = None
    return view_container

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

    view_container = Container(content=conteudo_treino, alignment=alignment.center, expand=True, padding=PADDING_VIEW)
    if tema_ativo_nome == "escuro_moderno":
        view_container.gradient = obter_cor_do_tema_ativo("gradient_page_bg")
        view_container.bgcolor = None
    else:
        view_container.bgcolor = obter_cor_do_tema_ativo("fundo_pagina")
        view_container.gradient = None
    return view_container

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
            Container(
                Text("Proficiência por Tabuada:", size=22, weight=FontWeight.BOLD, color=obter_cor_do_tema_ativo("texto_titulos")),
                margin=ft.margin.only(top=20, bottom=10)
            ),
            col_prof,
            Container(height=10),
            Container(
                Text("Maiores Dificuldades Atuais:", size=22, weight=FontWeight.BOLD, color=obter_cor_do_tema_ativo("texto_titulos")),
                margin=ft.margin.only(top=20, bottom=10)
            ),
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
    view_container = Container(content=conteudo_stats, alignment=alignment.center, expand=True, padding=PADDING_VIEW)
    if tema_ativo_nome == "escuro_moderno":
        view_container.gradient = obter_cor_do_tema_ativo("gradient_page_bg")
        view_container.bgcolor = None
    else:
        view_container.bgcolor = obter_cor_do_tema_ativo("fundo_pagina")
        view_container.gradient = None
    return view_container

# --- Tela de Quiz com Fórmula Personalizada ---
def build_tela_custom_quiz(page: Page):
    global current_custom_formula_for_quiz

    if current_custom_formula_for_quiz is None:
        error_content = Column([
            Text("Erro: Nenhuma fórmula personalizada selecionada.", color=obter_cor_do_tema_ativo("feedback_erro_texto"), size=20),
            ElevatedButton("Voltar para Seleção", on_click=lambda _: page.go("/custom_formula_setup"), bgcolor=obter_cor_do_tema_ativo("botao_principal_bg"), color=obter_cor_do_tema_ativo("botao_principal_texto"))
        ], alignment=MainAxisAlignment.CENTER, horizontal_alignment=CrossAxisAlignment.CENTER, spacing=20)
        return Container(content=error_content, alignment=alignment.center, expand=True, padding=PADDING_VIEW)

    formula_obj = current_custom_formula_for_quiz
    texto_pergunta = Text(size=24, weight=FontWeight.BOLD, text_align=TextAlign.CENTER, color=obter_cor_do_tema_ativo("texto_titulos"), opacity=0, animate_opacity=ANIMACAO_APARICAO_TEXTO_BOTAO)
    botoes_opcoes = [ElevatedButton(width=BOTAO_LARGURA_OPCAO_QUIZ, height=BOTAO_ALTURA_OPCAO_QUIZ, opacity=0, animate_opacity=ANIMACAO_APARICAO_TEXTO_BOTAO) for _ in range(4)]
    texto_feedback = Text(size=18, weight=FontWeight.BOLD, text_align=TextAlign.CENTER, opacity=0, scale=0.8, animate_opacity=ANIMACAO_FEEDBACK_OPACIDADE, animate_scale=ANIMACAO_FEEDBACK_ESCALA)

    # Renomeada de generate_custom_question_data
    # A variável safe_globals_for_eval não é mais necessária aqui, pois não usamos eval() com strings de usuário.
    def generate_notable_formula_question_data(quiz_config):
        formula_id = quiz_config.get('formula_id')
        user_ranges = quiz_config.get('ranges', {})

        formula_definition = get_formula_definition(formula_id)
        if not formula_definition:
            print(f"Erro: Definição da fórmula não encontrada para ID: {formula_id}")
            return None

        variables_defs = formula_definition.get('variables', [])
        calculation_func = formula_definition.get('calculation_function')
        question_template = formula_definition.get('question_template')
        reminder_template = formula_definition.get('reminder_template')
        range_constraints = formula_definition.get('range_constraints', {})

        if not all([variables_defs, calculation_func, question_template, reminder_template]):
            print(f"Erro: Definição da fórmula incompleta para ID: {formula_id}")
            return None

        local_vars_values = {}
        # Sortear valores para as variáveis base
        # Exemplo para 'a' e 'b', adaptável se houver mais ou menos variáveis no futuro

        val_a, val_b = None, None

        if 'a' in variables_defs:
            range_a_config = user_ranges.get('a', {'min': 1, 'max': 10}) # Pega range do usuário ou default
            min_a_constr = range_constraints.get('a', {}).get('min', 1)

            actual_min_a = max(range_a_config['min'], min_a_constr)
            actual_max_a = range_a_config['max']
            if actual_min_a > actual_max_a : actual_min_a = actual_max_a # Evitar erro no randint

            val_a = random.randint(actual_min_a, actual_max_a)
            local_vars_values['a'] = val_a

        if 'b' in variables_defs:
            range_b_config = user_ranges.get('b', {'min': 1, 'max': 10})
            min_b_constr = range_constraints.get('b', {}).get('min', 1)

            actual_min_b = max(range_b_config['min'], min_b_constr)
            actual_max_b = range_b_config['max']

            # Aplicar restrições relacionais
            if range_constraints.get('b', {}).get('less_than_a') and val_a is not None:
                actual_max_b = min(actual_max_b, val_a - 1)
            elif range_constraints.get('b', {}).get('less_than_equal_a') and val_a is not None:
                actual_max_b = min(actual_max_b, val_a)

            if actual_min_b > actual_max_b: # Se restrições tornarem impossível
                # Tentar um fallback simples: se b precisa ser < a, e a é 1, não é possível.
                # Esta lógica de fallback pode precisar de mais refinamento para casos complexos.
                # Por agora, se o range ficar inválido, pode dar erro no randint ou gerar valor não ideal.
                # Uma solução seria tentar sortear 'a' novamente ou sinalizar erro.
                # Para as fórmulas atuais, os ranges 1-10 e as restrições devem ser gerenciáveis.
                # Se min_b se tornou > max_b, forçar min_b = max_b (ou o contrário, dependendo da causa)
                # Ex: se a=1 e b<a, max_b fica 0. min_b é 1. randint(1,0) falha.
                # Ajuste:
                if actual_min_b > actual_max_b:
                     if range_constraints.get('b', {}).get('less_than_a') and val_a == 1: # Caso específico: a=1, b<a
                         print(f"Aviso: Não é possível sortear b < a quando a=1 para fórmula {formula_id}. Tentando a=2.")
                         val_a = 2 # Tenta forçar 'a' para um valor que permita 'b'
                         local_vars_values['a'] = val_a
                         actual_max_b = min(range_b_config['max'], val_a -1) # Recalcula max_b
                         if actual_min_b > actual_max_b: # Ainda problemático
                             print(f"Erro Crítico: Range inválido para 'b' mesmo após ajuste de 'a' para fórmula {formula_id}")
                             return None
                     else: # Outro caso de min > max
                         actual_min_b = actual_max_b # Ou alguma outra lógica de ajuste

            val_b = random.randint(actual_min_b, actual_max_b)
            local_vars_values['b'] = val_b

        try:
            # As funções de cálculo esperam argumentos nomeados
            correct_answer = calculation_func(**local_vars_values)
        except Exception as e:
            print(f"Erro ao calcular fórmula '{formula_id}' com valores {local_vars_values}. Erro: {e}")
            return None

        # Formatar a pergunta
        full_question_text = question_template.format(**local_vars_values)

        # Gerar opções incorretas (lógica similar à anterior)
        options_set = {correct_answer}
        attempts = 0
        # Garantir que as opções sejam inteiras se a resposta for inteira
        is_correct_answer_int = isinstance(correct_answer, int)

        while len(options_set) < 4 and attempts < 50: # Aumentado tentativas para mais robustez
            offset_val = random.choice([-3, -2, -1, 1, 2, 3, 5, -5]) # Offsets inteiros
            if abs(correct_answer) > 20: # Maior variação para números maiores
                 # Tenta gerar offsets proporcionais, mas garante que sejam inteiros
                prop_offset_candidate = round(correct_answer * random.choice([0.1, -0.1, 0.2, -0.2]))
                if prop_offset_candidate == 0: prop_offset_candidate = random.choice([-1,1])
                offset_val = random.choice([offset_val, int(prop_offset_candidate)]) # Usa o offset proporcional ou um fixo

            new_opt = correct_answer + offset_val
            if is_correct_answer_int: # Se a resposta é int, as opções devem ser int
                new_opt = int(round(new_opt))

            if new_opt not in options_set:
                options_set.add(new_opt)
            attempts += 1

        idx = 1
        while len(options_set) < 4: # Fallback mais simples
            alt_opt = correct_answer + (idx * random.choice([-1,1]))
            if is_correct_answer_int: alt_opt = int(round(alt_opt))

            if alt_opt not in options_set : options_set.add(alt_opt)
            idx +=1
            if idx > 20 : break

        final_options = list(options_set)
        # Se por algum motivo ainda não tem 4, preenche com sequenciais simples
        idx = 1
        base_fill_val = correct_answer if isinstance(correct_answer, (int, float)) else 1
        while len(final_options) < 4:
            fill_opt = base_fill_val + idx * 10 + random.randint(0,5) # Gera números mais distintos
            if is_correct_answer_int: fill_opt = int(round(fill_opt))
            if fill_opt not in final_options: final_options.append(fill_opt)
            else: final_options.append(base_fill_val - idx * 10 - random.randint(0,5)) # Tenta outro lado
            idx +=1
            if idx > 10: break # Evita loop infinito no fallback do fallback

        random.shuffle(final_options)

        return {
            'full_question': full_question_text,
            'options': final_options[:4], # Garante que só tem 4 opções
            'correct_answer': correct_answer,
            'reminder_template': reminder_template
            # 'formula_details' não é mais a string da fórmula, mas a config do quiz já está em current_custom_formula_for_quiz
        }

    def handle_custom_answer(e, botao_clicado_ref, todos_botoes_opcoes_ref, txt_feedback_ctrl_ref, btn_proxima_ctrl_ref, question_data_ref):
        selected_option = botao_clicado_ref.data['option']
        correct_answer = question_data_ref['correct_answer']

        is_correct = (selected_option == correct_answer) # Cuidado com float precision, mas aqui deve ser ok

        if is_correct:
            txt_feedback_ctrl_ref.value = "Correto!"
            txt_feedback_ctrl_ref.color = obter_cor_do_tema_ativo("feedback_acerto_texto")
            botao_clicado_ref.bgcolor = obter_cor_do_tema_ativo("feedback_acerto_botao_bg")
        else:
            txt_feedback_ctrl_ref.value = f"Errado! A resposta era {correct_answer}"
            txt_feedback_ctrl_ref.color = obter_cor_do_tema_ativo("feedback_erro_texto")
            botao_clicado_ref.bgcolor = obter_cor_do_tema_ativo("feedback_erro_botao_bg")
            # Destacar a opção correta
            for btn_op in todos_botoes_opcoes_ref:
                if btn_op.data['option'] == correct_answer:
                    btn_op.bgcolor = obter_cor_do_tema_ativo("feedback_acerto_botao_bg")
                    break

        for btn in todos_botoes_opcoes_ref: btn.disabled = True
        txt_feedback_ctrl_ref.opacity = 1; txt_feedback_ctrl_ref.scale = 1
        btn_proxima_ctrl_ref.visible = True; page.update()

    botao_proxima = ElevatedButton("Próxima Pergunta", on_click=None, visible=False, width=BOTAO_LARGURA_PRINCIPAL, height=BOTAO_ALTURA_PRINCIPAL, bgcolor=obter_cor_do_tema_ativo("botao_principal_bg"), color=obter_cor_do_tema_ativo("botao_principal_texto"))

    # Store current question data to be accessible by handlers
    current_question_data_ref = {} # Armazena dados da pergunta atual, incluindo o gabarito do lembrete

    # Novo controle para exibir o lembrete da fórmula
    texto_lembrete_formula = Text(
        "",
        size=16,
        color=obter_cor_do_tema_ativo("texto_padrao"),
        text_align=TextAlign.CENTER,
        opacity=0,
        animate_opacity=ANIMACAO_APARICAO_TEXTO_BOTAO
    )

    def carregar_nova_pergunta_custom(page_ref, formula_config_ref, txt_pergunta_ctrl, btn_opcoes_ctrls, txt_feedback_ctrl, txt_lembrete_ctrl, btn_proxima_ctrl, question_data_storage):
        txt_feedback_ctrl.opacity = 0; txt_feedback_ctrl.scale = 0.8
        txt_lembrete_ctrl.opacity = 0 # Esconde lembrete ao carregar nova pergunta
        txt_pergunta_ctrl.opacity = 0
        for btn_opcao in btn_opcoes_ctrls: btn_opcao.opacity = 0

        # A função foi renomeada e sua lógica interna alterada na Etapa 5
        question_data = generate_notable_formula_question_data(formula_config_ref)

        if not question_data:
            txt_pergunta_ctrl.value = "Erro ao gerar pergunta para esta configuração."; txt_pergunta_ctrl.opacity = 1
            for btn in btn_opcoes_ctrls: btn.visible = False
            txt_feedback_ctrl.value = ""; btn_proxima_ctrl.visible = False
            btn_proxima_ctrl.text = "Voltar para Configuração"
            # A rota /custom_formula_setup foi renomeada para /formula_quiz_setup
            btn_proxima_ctrl.on_click = lambda _: page.go("/formula_quiz_setup")
            btn_proxima_ctrl.visible = True
            page_ref.update(); return

        question_data_storage.clear()
        question_data_storage.update(question_data) # Salva dados da pergunta, incluindo reminder_template

        txt_pergunta_ctrl.value = question_data['full_question']

        for i in range(4):
            if i < len(question_data['options']):
                op_val = question_data['options'][i]
                btn_opcoes_ctrls[i].text = str(op_val)
                btn_opcoes_ctrls[i].data = {'option': op_val}
                # Passar txt_lembrete_ctrl para handle_custom_answer
                btn_opcoes_ctrls[i].on_click = lambda e, btn=btn_opcoes_ctrls[i]: handle_custom_answer(page_ref, btn, btn_opcoes_ctrls, txt_feedback_ctrl, txt_lembrete_ctrl, btn_proxima_ctrl, question_data_storage)
                btn_opcoes_ctrls[i].bgcolor = obter_cor_do_tema_ativo("botao_opcao_quiz_bg")
                btn_opcoes_ctrls[i].color = obter_cor_do_tema_ativo("botao_opcao_quiz_texto")
                btn_opcoes_ctrls[i].disabled = False; btn_opcoes_ctrls[i].visible = True
            else:
                btn_opcoes_ctrls[i].visible = False

        txt_feedback_ctrl.value = ""; btn_proxima_ctrl.visible = False
        btn_proxima_ctrl.text = "Próxima Pergunta"
        # Passar txt_lembrete_ctrl para o on_click do botão Próxima Pergunta
        btn_proxima_ctrl.on_click = lambda _: carregar_nova_pergunta_custom(page_ref, formula_config_ref, txt_pergunta_ctrl, btn_opcoes_ctrls, txt_feedback_ctrl, txt_lembrete_ctrl, btn_proxima_ctrl, question_data_storage)

        txt_pergunta_ctrl.opacity = 1
        for btn_opcao in btn_opcoes_ctrls:
            if btn_opcao.visible: btn_opcao.opacity = 1
        page_ref.update()

    # Modificar handle_custom_answer para aceitar e usar txt_lembrete_ctrl
    def handle_custom_answer(e, botao_clicado_ref, todos_botoes_opcoes_ref, txt_feedback_ctrl_ref, txt_lembrete_ctrl_ref, btn_proxima_ctrl_ref, question_data_ref):
        selected_option = botao_clicado_ref.data['option']
        correct_answer = question_data_ref['correct_answer']
        reminder_text = question_data_ref.get('reminder_template', "") # Obter o lembrete

        is_correct = (selected_option == correct_answer)

        if is_correct:
            txt_feedback_ctrl_ref.value = "Correto!"
            txt_feedback_ctrl_ref.color = obter_cor_do_tema_ativo("feedback_acerto_texto")
            botao_clicado_ref.bgcolor = obter_cor_do_tema_ativo("feedback_acerto_botao_bg")
        else:
            txt_feedback_ctrl_ref.value = f"Errado! A resposta era {correct_answer}"
            txt_feedback_ctrl_ref.color = obter_cor_do_tema_ativo("feedback_erro_texto")
            botao_clicado_ref.bgcolor = obter_cor_do_tema_ativo("feedback_erro_botao_bg")
            for btn_op in todos_botoes_opcoes_ref:
                if btn_op.data['option'] == correct_answer:
                    btn_op.bgcolor = obter_cor_do_tema_ativo("feedback_acerto_botao_bg")
                    break

        for btn in todos_botoes_opcoes_ref: btn.disabled = True
        txt_feedback_ctrl_ref.opacity = 1; txt_feedback_ctrl_ref.scale = 1

        # Exibir o lembrete da fórmula
        if reminder_text:
            txt_lembrete_ctrl_ref.value = f"Lembrete: {reminder_text}"
            txt_lembrete_ctrl_ref.opacity = 1

        btn_proxima_ctrl_ref.visible = True; page.update()


    # Configurar o clique do botão "Próxima Pergunta"
    # formula_obj é current_custom_formula_for_quiz, que agora é a quiz_config
    botao_proxima.on_click = lambda _: carregar_nova_pergunta_custom(page, formula_obj, texto_pergunta, botoes_opcoes, texto_feedback, texto_lembrete_formula, botao_proxima, current_question_data_ref)

    # Carregar a primeira pergunta
    carregar_nova_pergunta_custom(page, formula_obj, texto_pergunta, botoes_opcoes, texto_feedback, texto_lembrete_formula, botao_proxima, current_question_data_ref)

    # O botão voltar deve ir para a nova tela de setup /formula_quiz_setup
    botao_voltar_setup = ElevatedButton("Mudar Config. / Menu", on_click=lambda _: page.go("/formula_quiz_setup"), width=BOTAO_LARGURA_PRINCIPAL, height=BOTAO_ALTURA_PRINCIPAL, bgcolor=obter_cor_do_tema_ativo("botao_principal_bg"), color=obter_cor_do_tema_ativo("botao_principal_texto"))

    layout_botoes = Column([Row(botoes_opcoes[0:2], alignment=MainAxisAlignment.CENTER, spacing=15), Container(height=10), Row(botoes_opcoes[2:4], alignment=MainAxisAlignment.CENTER, spacing=15)], horizontal_alignment=CrossAxisAlignment.CENTER, spacing=10)

    # Adicionar texto_lembrete_formula ao layout
    conteudo_quiz = Column(
        [
            Text(f"Quiz Fórmula: {formula_obj['name']}", size=20, weight=FontWeight.BOLD, color=obter_cor_do_tema_ativo("texto_titulos"), text_align=TextAlign.CENTER), # Nome da config salva
            Container(height=5),
            texto_pergunta,
            Container(height=15),
            layout_botoes,
            Container(height=15),
            texto_feedback,
            Container(height=10), # Espaço antes do lembrete
            texto_lembrete_formula, # Novo controle adicionado
            Container(height=20),
            botao_proxima,
            Container(height=10),
            botao_voltar_setup
        ],
        alignment=MainAxisAlignment.CENTER,
        horizontal_alignment=CrossAxisAlignment.CENTER,
        spacing=ESPACAMENTO_COLUNA_GERAL,
        scroll=ScrollMode.AUTO
    )

    view_container = Container(content=conteudo_quiz, alignment=alignment.center, expand=True, padding=PADDING_VIEW)
    if tema_ativo_nome == "escuro_moderno":
        view_container.gradient = obter_cor_do_tema_ativo("gradient_page_bg")
        view_container.bgcolor = None
    else:
        view_container.bgcolor = obter_cor_do_tema_ativo("fundo_pagina")
        view_container.gradient = None
    return view_container


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

    # --- Elementos Globais da UI para Atualização ---
    update_status_icon = ft.Icon(name=ft.icons.SYNC_PROBLEM, color=obter_cor_do_tema_ativo("update_icon_color_error"), tooltip=update_check_status_message, size=20)
    update_status_text = ft.Text(f"v{APP_CURRENT_VERSION} ({local_git_commit})", size=10, color=obter_cor_do_tema_ativo("texto_padrao"), opacity=0.7)
    update_action_button = ft.ElevatedButton(
        text="Atualizar Agora",
        icon=ft.icons.UPDATE,
        visible=False,
        on_click=lambda _: show_update_dialog(page), # Definiremos show_update_dialog depois
        bgcolor=obter_cor_do_tema_ativo("botao_destaque_bg"),
        color=obter_cor_do_tema_ativo("botao_destaque_texto")
    )

    def update_ui_elements_for_update_status():
        """Atualiza os elementos da UI com base no status da verificação de atualização."""
        global update_available, latest_version_tag, update_check_status_message, APP_CURRENT_VERSION, local_git_commit

        update_status_text.value = f"v{APP_CURRENT_VERSION} ({local_git_commit.splitlines()[0] if local_git_commit else 'N/A'}) - {update_check_status_message}"
        update_status_text.color = obter_cor_do_tema_ativo("texto_padrao") # Resetar cor
        update_action_button.visible = False # Esconder por padrão

        if "Erro ao verificar" in update_check_status_message or "Erro inesperado" in update_check_status_message:
            update_status_icon.name = ft.icons.ERROR_OUTLINE
            update_status_icon.color = obter_cor_do_tema_ativo("update_icon_color_error")
            update_status_icon.tooltip = update_check_status_message
        elif update_available:
            update_status_icon.name = ft.icons.NEW_RELEASES
            update_status_icon.color = obter_cor_do_tema_ativo("update_icon_color_available")
            update_status_icon.tooltip = f"Nova versão {latest_version_tag} disponível!"
            update_status_text.value = f"Atualização: v{APP_CURRENT_VERSION} -> {latest_version_tag}"
            update_action_button.visible = True
            update_action_button.bgcolor = obter_cor_do_tema_ativo("botao_destaque_bg")
            update_action_button.color = obter_cor_do_tema_ativo("botao_destaque_texto")

        else: # Nenhuma atualização ou já atualizado
            update_status_icon.name = ft.icons.CHECK_CIRCLE_OUTLINE
            update_status_icon.color = obter_cor_do_tema_ativo("update_icon_color_uptodate")
            update_status_icon.tooltip = "Você está na versão mais recente."

        # Atualiza o botão de atualização se estiver na tela de apresentação
        # (ou em qualquer outra tela que o contenha - precisa ser adicionado lá também)
        # Esta é uma forma simples, idealmente o botão seria parte de um layout persistente ou AppBar
        if page.route == "/":
             # A lógica de reconstrução da tela de apresentação precisará adicionar este botão
             # ou teremos que encontrar o botão no `page.views` e atualizá-lo.
             # Por agora, vamos assumir que o botão é atualizado ao reconstruir a view.
             pass


        if page.controls: # Se houver AppBar, atualiza lá
            app_bar = page.appbar
            if app_bar and hasattr(app_bar, 'actions'):
                # Encontrar e atualizar os elementos na AppBar
                for action_item in app_bar.actions:
                    if isinstance(action_item, ft.Row) and len(action_item.controls) > 1:
                        icon_ctrl = action_item.controls[0]
                        text_ctrl = action_item.controls[1]
                        if isinstance(icon_ctrl, ft.Icon) and isinstance(text_ctrl, ft.Text):
                            icon_ctrl.name = update_status_icon.name
                            icon_ctrl.color = update_status_icon.color
                            icon_ctrl.tooltip = update_status_icon.tooltip
                            text_ctrl.value = update_status_text.value
                            text_ctrl.color = update_status_text.color
                            break
        page.update()

    def run_update_check_and_ui_refresh(page_ref: Page):
        """Executa a verificação de atualização e atualiza a UI."""
        check_for_updates()
        update_ui_elements_for_update_status()
        page_ref.update()


    # --- Diálogo de Confirmação e Lógica de Atualização ---
    update_progress_indicator = ft.ProgressRing(width=16, height=16, stroke_width=2, visible=False)
    update_dialog_content_text = Text("Uma nova versão do aplicativo está disponível. Deseja atualizar agora? O aplicativo precisará ser reiniciado.")

    def perform_update_action(e, page_ref: Page, dialog_ref: ft.AlertDialog):
        global update_check_status_message

        dialog_ref.content = Column([
            update_dialog_content_text,
            Container(height=10),
            Row([update_progress_indicator, Text("Atualizando...")], alignment=MainAxisAlignment.CENTER)
        ])
        update_progress_indicator.visible = True
        dialog_ref.actions = [] # Remover botões durante o processo
        page_ref.update()

        try:
            # 1. Verificar se é um repositório git
            if not os.path.exists(".git"):
                update_dialog_content_text.value = "Erro: Não é um repositório git. A atualização automática não pode prosseguir."
                update_progress_indicator.visible = False
                dialog_ref.actions = [ft.TextButton("OK", on_click=lambda ev: close_dialog(ev, page_ref, dialog_ref))]
                page_ref.update()
                return

            # 2. Salvar quaisquer alterações locais não commitadas (stash)
            subprocess.run(['git', 'stash', 'push', '-u', '-m', 'autostash_before_update'], check=True, capture_output=True)
            print("Git stash push executado.")

            # 3. Puxar as últimas alterações do repositório (branch padrão)
            pull_result = subprocess.run(['git', 'pull', '--ff-only'], check=True, capture_output=True, text=True) # --ff-only para evitar merges
            print(f"Git pull executado: {pull_result.stdout}")

            # 4. Tentar aplicar o stash de volta (opcional, mas bom para manter alterações locais)
            #    Se houver conflitos, o usuário precisará resolver manualmente após reiniciar.
            subprocess.run(['git', 'stash', 'pop'], capture_output=True) # Não checa 'check=True' aqui, pois pode falhar com conflitos
            print("Git stash pop tentado.")

            update_dialog_content_text.value = "Atualização concluída com sucesso! Por favor, reinicie o aplicativo para aplicar as alterações."
            update_check_status_message = "Atualizado! Reinicie." # Atualiza a mensagem global também

        except subprocess.CalledProcessError as err:
            error_message = f"Erro durante a atualização: {err.stderr or err.stdout or str(err)}"
            print(error_message)
            update_dialog_content_text.value = error_message
            # Tentar reverter o stash se o pull falhou
            subprocess.run(['git', 'stash', 'pop'], capture_output=True)

        except FileNotFoundError:
            update_dialog_content_text.value = "Erro: Git não encontrado. A atualização não pode prosseguir."
        except Exception as ex:
            update_dialog_content_text.value = f"Erro inesperado: {str(ex)}"

        update_progress_indicator.visible = False
        dialog_ref.actions = [ft.TextButton("OK, Reiniciar Manualmente", on_click=lambda ev: close_dialog(ev, page_ref, dialog_ref))]
        page_ref.update()


    update_dialog = ft.AlertDialog(
        modal=True,
        title=Text("Confirmar Atualização"),
        content=update_dialog_content_text, # Usar o controle de texto
        actions=[
            ft.TextButton("Sim, Atualizar", on_click=lambda e: perform_update_action(e, page, update_dialog)),
            ft.TextButton("Agora Não", on_click=lambda e: close_dialog(e, page, update_dialog)),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    def close_dialog(e, page_ref: Page, dialog_ref: ft.AlertDialog):
        dialog_ref.open = False
        page_ref.update()

    def show_update_dialog(page_ref: Page):
        page_ref.dialog = update_dialog
        update_dialog.open = True
        page_ref.update()

    # --- Fim dos Elementos de Atualização ---


    def route_change(route_obj):
        page.bgcolor = obter_cor_do_tema_ativo("fundo_pagina")
        page.views.clear()

        page.views.append(
            View(
                route="/",
                controls=[build_tela_apresentacao(page)], # build_tela_apresentacao precisará ser modificado
                vertical_alignment=MainAxisAlignment.CENTER,
                horizontal_alignment=CrossAxisAlignment.CENTER,
                # Adicionando AppBar simples para mostrar status da atualização
                appbar=ft.AppBar(
                    title=Text("Quiz Mestre da Tabuada", color=obter_cor_do_tema_ativo("texto_titulos")),
                    center_title=True,
                    bgcolor=obter_cor_do_tema_ativo("fundo_pagina"),
                    actions=[
                        Row([
                            update_status_icon,
                            Container(width=5),
                            update_status_text,
                            Container(width=10)
                        ], alignment=MainAxisAlignment.CENTER, vertical_alignment=CrossAxisAlignment.CENTER),
                        # update_action_button # Poderia ser adicionado aqui também, se desejado
                    ]
                )
            )
        )
        if page.route == "/quiz":
            page.views.append(View("/quiz", [build_tela_quiz(page)], vertical_alignment=MainAxisAlignment.CENTER, horizontal_alignment=CrossAxisAlignment.CENTER, appbar=page.views[0].appbar)) # Reutiliza AppBar
        elif page.route == "/quiz_invertido":
            page.views.append(View("/quiz_invertido", [build_tela_quiz_invertido(page)], vertical_alignment=MainAxisAlignment.CENTER, horizontal_alignment=CrossAxisAlignment.CENTER, appbar=page.views[0].appbar))
        elif page.route == "/treino":
            page.views.append(View("/treino", [build_tela_treino(page)], vertical_alignment=MainAxisAlignment.CENTER, horizontal_alignment=CrossAxisAlignment.CENTER, appbar=page.views[0].appbar))
        elif page.route == "/estatisticas":
            page.views.append(View("/estatisticas", [build_tela_estatisticas(page)], vertical_alignment=MainAxisAlignment.CENTER, horizontal_alignment=CrossAxisAlignment.CENTER, appbar=page.views[0].appbar))
        elif page.route == "/formula_quiz_setup":
            page.views.append(View("/formula_quiz_setup", [build_tela_formula_quiz_setup(page)], vertical_alignment=MainAxisAlignment.CENTER, horizontal_alignment=CrossAxisAlignment.CENTER, appbar=page.views[0].appbar))
        elif page.route == "/custom_quiz":
            page.views.append(View("/custom_quiz", [build_tela_custom_quiz(page)], vertical_alignment=MainAxisAlignment.CENTER, horizontal_alignment=CrossAxisAlignment.CENTER, appbar=page.views[0].appbar))

        # Garantir que a UI de atualização seja atualizada na mudança de rota
        # Isso é importante porque a AppBar é reconstruída.
        update_ui_elements_for_update_status()
        page.update()

    def view_pop(view_instance):
        if page.views:
            top_view = page.views[-1]
            page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop

    # Iniciar a verificação de atualização em uma thread separada para não bloquear a UI
    update_thread = threading.Thread(target=run_update_check_and_ui_refresh, args=(page,), daemon=True)
    update_thread.start()

    page.go("/")

ft.app(target=main)
