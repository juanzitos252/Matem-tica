# Quiz Mestre da Tabuada

O "Quiz Mestre da Tabuada" é um aplicativo desktop interativo desenvolvido em Python com a biblioteca Flet. Seu objetivo é ajudar usuários de todas as idades a aprender, praticar e memorizar a tabuada de multiplicação (de 1x1 a 10x10) de uma forma divertida, adaptativa e eficaz. O aplicativo foca em identificar as dificuldades do usuário e reforçar o aprendizado nas áreas que mais precisam de atenção.

## Funcionalidades Principais

*   **Quiz Interativo:** Um modo de quiz dinâmico com perguntas de multiplicação variando de 1x1 até 10x10.
*   **Algoritmo Adaptativo:** Um sistema inteligente personaliza a seleção de perguntas. Ele considera um 'peso' associado a cada multiplicação, o histórico de erros recentes do usuário e a frequência com que uma pergunta já foi apresentada.
*   **Geração Inteligente de Opções:** Para cada pergunta no quiz, são geradas automaticamente 3 opções de resposta incorretas, mas plausíveis, tornando o desafio mais interessante.
*   **Feedback Imediato:** O usuário recebe feedback visual instantâneo (cores e mensagens) indicando se a resposta selecionada no quiz está correta ou incorreta.
*   **Modo de Treino Dedicado:** Permite ao usuário praticar uma tabuada completa (ex: toda a tabuada do 7). O aplicativo sugere qual tabuada treinar com base no desempenho histórico do usuário, focando nas suas maiores dificuldades.
*   **Integração do Treino com o Algoritmo:** As respostas fornecidas no Modo de Treino também são registradas e influenciam o algoritmo adaptativo, ajustando os pesos das multiplicações.
*   **Interface Gráfica Moderna:** Desenvolvido com a biblioteca Flet, proporcionando uma interface de usuário limpa, responsiva e agradável.
*   **Navegação Intuitiva:** O aplicativo possui uma navegação clara entre as diferentes seções: Tela de Apresentação, Tela de Quiz e Tela de Treino.
*   **Foco na Usabilidade:** O design foi pensado para ser simples e direto, permitindo que o usuário se concentre no aprendizado.

## Tecnologias Utilizadas

*   **Python 3.x:** Linguagem de programação principal.
*   **Flet:** Biblioteca Python para a criação da interface gráfica do usuário (GUI) como uma aplicação web, desktop ou mobile.

## Como Executar o Aplicativo

Siga os passos abaixo para executar o "Quiz Mestre da Tabuada" em seu ambiente local:

1.  **Clone o Repositório / Baixe o Arquivo:**
    *   Se estiver usando Git: `git clone <URL_DO_REPOSITORIO>`
    *   Ou, baixe o arquivo `main.py` diretamente.

2.  **Python 3:**
    *   Certifique-se de que você tem o Python 3 instalado em seu sistema. Você pode baixá-lo em [python.org](https://www.python.org/).

3.  **Instale a Biblioteca Flet:**
    *   Abra o terminal ou prompt de comando e execute:
        ```bash
        pip install flet
        ```

4.  **Navegue até o Diretório:**
    *   Pelo terminal, navegue até o diretório (pasta) onde você salvou o arquivo `main.py`.

5.  **Execute o Aplicativo:**
    *   No mesmo diretório, execute o seguinte comando:
        ```bash
        python main.py
        ```
    *   Isso deverá iniciar a interface gráfica do aplicativo.

## Estrutura do Código

Para manter a simplicidade e facilitar a execução, todo o código da aplicação (lógica do quiz, interface do usuário e gerenciamento de estado) está contido em um único arquivo: `main.py`.

## Algoritmo Adaptativo

O coração do "Quiz Mestre da Tabuada" é seu algoritmo de seleção de perguntas. Ele funciona da seguinte maneira:

*   Cada uma das 100 multiplicações possíveis (de 1x1 a 10x10) possui um 'peso' inicial.
*   Quando o usuário responde a uma pergunta incorretamente, o peso daquela multiplicação específica aumenta.
*   Quando o usuário acerta, o peso diminui.
*   Ao selecionar a próxima pergunta para o quiz, o algoritmo prioriza:
    1.  **Perguntas com maior peso:** Indicando maior dificuldade para o usuário.
    2.  **Perguntas com erros recentes:** Reforçando o aprendizado de itens que foram errados há pouco tempo.
    3.  **Perguntas menos apresentadas:** Garantindo que todas as multiplicações sejam cobertas ao longo do tempo.
*   Este método visa criar uma experiência de aprendizado personalizada, focada nas necessidades individuais do usuário, e ao mesmo tempo abrangente.

## Observações

Este aplicativo foi desenvolvido em um ambiente assistido por IA. Devido a limitações nesse ambiente (especificamente, timeouts recorrentes durante a tentativa de execução de aplicações Flet), testes interativos e visuais exaustivos da interface do usuário não puderam ser realizados pelo assistente em todas as etapas de desenvolvimento.

Recomenda-se fortemente que o usuário execute e teste o aplicativo em seu próprio ambiente local para verificar completamente todas as funcionalidades, o comportamento da interface gráfica e a experiência de usuário. Qualquer feedback ou sugestão de melhoria é bem-vindo!
