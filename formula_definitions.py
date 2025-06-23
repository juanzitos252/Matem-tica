# Este arquivo conterá as definições das fórmulas notáveis.

# Este arquivo conterá as definições das fórmulas notáveis.

# --- Funções de Cálculo para Fórmulas Notáveis ---

def calc_quadrado_soma(a: int, b: int) -> int:
    """Calcula (a+b)^2."""
    return (a + b) ** 2

def calc_quadrado_diferenca(a: int, b: int) -> int:
    """Calcula (a-b)^2."""
    return (a - b) ** 2

def calc_produto_soma_diferenca(a: int, b: int) -> int:
    """Calcula a^2 - b^2."""
    # A restrição de range b <= a é para garantir resultado >= 0 se desejado na UI.
    # A função em si calcula corretamente para quaisquer a, b.
    return a**2 - b**2

def calc_raiz_soma_diferenca(val_a: int, val_b: int) -> int:
    """Calcula a - b, onde val_a e val_b são os números DENTRO das raízes na pergunta.
    A pergunta será (sqrt(val_a) + sqrt(val_b)) * (sqrt(val_a) - sqrt(val_b)).
    O resultado da expressão é val_a - val_b.
    """
    # A restrição de range val_b < val_a é para garantir resultado > 0.
    return val_a - val_b

# --- Definições das Fórmulas Notáveis ---
# Cada entrada define uma fórmula que o usuário pode selecionar para o quiz.

FORMULAS_NOTAVEIS = [
    {
        'id': "quadrado_soma",
        'display_name': "Quadrado da Soma: (a+b)^2",
        'variables': ['a', 'b'],
        'calculation_function': calc_quadrado_soma,
        'question_template': "Se a={a} e b={b}, qual o valor de (a+b)^2?",
        'reminder_template': "(x+y)^2 = x^2 + 2xy + y^2",
        'range_constraints': {}, # Nenhuma restrição especial além dos ranges 1-10
        'variable_labels': {'a': "Valor de 'a'", 'b': "Valor de 'b'"}
    },
    {
        'id': "quadrado_diferenca",
        'display_name': "Quadrado da Diferença: (a-b)^2",
        'variables': ['a', 'b'],
        'calculation_function': calc_quadrado_diferenca,
        'question_template': "Se a={a} e b={b}, qual o valor de (a-b)^2?",
        'reminder_template': "(x-y)^2 = x^2 - 2xy + y^2",
        'range_constraints': {}, # Poderíamos adicionar 'a_greater_equal_b' se quisermos sempre resultado >= 0 para (a-b)
        'variable_labels': {'a': "Valor de 'a'", 'b': "Valor de 'b'"}
    },
    {
        'id': "produto_soma_diferenca",
        'display_name': "Produto da Soma pela Diferença: (a+b)(a-b)",
        'variables': ['a', 'b'],
        'calculation_function': calc_produto_soma_diferenca,
        'question_template': "Se a={a} e b={b}, qual o valor de (a+b)(a-b)?",
        'reminder_template': "(x+y)(x-y) = x^2 - y^2",
        'range_constraints': {'b': 'less_than_equal_a'}, # Para garantir a^2 - b^2 >= 0
        'variable_labels': {'a': "Valor de 'a'", 'b': "Valor de 'b' (b <= a)"}
    },
    {
        'id': "raiz_soma_diferenca",
        'display_name': "Diferença de Quadrados (Raízes): (sqrt(a)+sqrt(b))(sqrt(a)-sqrt(b))",
        'variables': ['a', 'b'], # Estes 'a' e 'b' são os números DENTRO das raízes
        'calculation_function': calc_raiz_soma_diferenca,
        'question_template': "Qual o valor de (sqrt({a}) + sqrt({b})) * (sqrt({a}) - sqrt({b}))?",
        'reminder_template': "(sqrt(x) + sqrt(y))(sqrt(x) - sqrt(y)) = x - y",
        'range_constraints': { # a e b são os números que aparecem dentro da raiz na pergunta
            'a': {'min': 2}, # 'a' DEVE ser pelo menos 2 para que b possa ser 1 se b < a
            'b': {'less_than_a': True, 'min': 1} # 'b' deve ser menor que 'a' e pelo menos 1
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
