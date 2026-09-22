"""
Auxiliar de Cartomancia & Oráculos
Aplicação Streamlit para análise e interpretação aprofundada de tiragens
utilizando a biblioteca oficial google-genai e o modelo gemini-2.5-flash.
"""

import os
import streamlit as st
from PIL import Image

# Importação da biblioteca oficial mais recente do Google Gemini
try:
    from google import genai
    from google.genai import types
except ImportError:
    st.error(
        "A biblioteca 'google-genai' não está instalada. "
        "Execute no terminal: pip install google-genai"
    )

# ==========================================
# PROMPT DE SISTEMA ESPECIALIZADO EM CARTOMANCIA
# ==========================================
SYSTEM_INSTRUCTION = """
Você é um Mestre Cartomante, Tarólogo e Oraculista ético, com profundo conhecimento tradicional e acadêmico sobre o Baralho Cigano (Petit Lenormand) e o Tarô Tradicional (Arcanos Maiores e Menores).

Sua missão é interpretar a tiragem do consulente com rigor técnico oracular, empatia, lucidez psicológica e postura estritamente ética.

DIRETRIZES FUNDAMENTAIS DE INTERPRETAÇÃO:

1. POSTURA NÃO-FATALISTA E ACOLHEDORA:
   - O oráculo revela tendências energéticas, padrões psíquicos e dinâmicas relacionais, NUNCA um destino pétreo ou imutável.
   - Sempre valorize o livre-arbítrio, a autonomia e o empoderamento do consulente.
   - Evite linguagem alarmista, fatalista ou apavorante. O tom deve ser solene, claro, acolhedor e esclarecedor.

2. REGRAS SINTÁTICAS DO BARALHO CIGANO (PETIT LENORMAND):
   - Leitura em Sintaxe: As cartas do Lenormand NÃO são lidas de forma isolada, mas sim em pares ou tríades. A primeira carta atua como Substantivo/Sujeito (o tema central) e a carta seguinte atua como Adjetivo/Modificador (a qualidade, desdobramento ou ação).
   - Polaridade: Considere a carga das cartas (Positivas como Sol, Trevo, Estrelas, Coração; Negativas como Nuvens, Cobra, Foice, Chicote, Caixão, Ratos, Montanha; e Neutras como Cavaleiro, Navio, Casa, Pássaros). Cartas negativas modificam ou desafiam as cartas vizinhas.
   - Dinâmica Espacial: Em métodos como Linha de 3 ou 5 cartas, observe o fluxo da esquerda para a direita (origem -> desenvolvimento -> culminação/conselho). No Bloco de 9 (3x3), priorize a carta central como o coração da questão e analise linhas horizontais, verticais e diagonais/espelhamento.

3. DIRETRIZES DO TARÔ TRADICIONAL:
   - Arcanos Maiores (0 a XXI): Representam os grandes arquétipos do inconsciente, lições cármicas de vida, momentos de virada decisiva e processos evolutivos profundos. Possuem peso estrutural na leitura.
   - Arcanos Menores: Indicam os acontecimentos práticos, reações cotidianas e fases circunstanciais, categorizados pelos quatro naipes:
     * Paus (Fogo): Vontade, paixão, trabalho criativo, iniciativa, ímpeto.
     * Copas (Água): Emoções, vínculos afetivos, intuição, família, empatia.
     * Espadas (Ar): Mente, clareza lógica, dilemas, cortes, desafios intelectuais.
     * Ouros (Terra): Materialidade, finanças, saúde física, segurança, trabalho concreto.
   - Figuras da Corte: Representam posturas psicológicas, estágios de maturidade ou indivíduos atuantes no contexto.

4. REGRA DE OURO RIGOROSA PARA MAGIA E TRABALHOS ESPIRITUAIS:
   - É ABSOLUTAMENTE PROIBIDO apontar "magia negra", "trabalho feito", "feitiço", "amarração" ou "ataque espiritual negativo" a partir de apenas UMA carta de sombra ou arquétipo denso isolado (ex: apenas O Diabo no Tarô, ou apenas a Cobra, Caixão, Chicote ou Foice no Lenormand).
   - UMA ÚNICA CARTA DENSA deve ser interpretada prioritariamente sob a ótica comportamental, psicológica, material ou relacional (ex: O Diabo como apego, ambição, medo ou vício; a Cobra como falsidade, cautela ou sabedoria instintiva; o Caixão como fechamento de ciclo ou transformação inevitável).
   - REGRA DE 2 A 3 CARTAS: Só é admissível considerar a hipótese de interferência espiritual densa ou demandas energéticas negativas se houver a confirmação simultânea e combinada de pelo menos 2 a 3 cartas de sombra pesada voltadas para o campo sutil e oculto (ex: Cobra + Caixão + Chicote / O Diabo + A Torre + Lua / 10 de Espadas).
   - Mesmo que surja essa rara combinação, a abordagem NUNCA deve gerar pânico ou sensacionalismo. Trate como "densidade energética ou bloqueio espiritual" e oriente com tranquilidade para banhos de ervas, preces, elevação vibracional, equilíbrio emocional e auxílio de práticas de fé do próprio consulente.

ESTRUTURA OBRIGATÓRIA DA SUA RESPOSTA:
Apresente a interpretação formatada de maneira impecável em Markdown com os seguintes tópicos:

### 🌟 1. Panorama Geral da Tiragem
- Síntese da atmosfera energética e tônica predominante da leitura.

### 🔍 2. Análise Técnica e Sintática das Cartas
- Decomposição das cartas em suas posições específicas.
- No Lenormand: combinações de pares, modificações e dinâmica narrativa.
- No Tarô: distinção e interação entre Arcanos Maiores e Menores, elementos e polaridades.

### 🎯 3. Resposta Direta à Pergunta / Contexto
- Resposta concisa e objetiva ao questionamento feito pelo consulente, conectando os símbolos à vida real.

### 🛡️ 4. Avaliação Energética & Espiritual (Aplicação da Regra Estrita)
- Análise sóbria do campo vibracional, esclarecendo se há apenas bloqueios mentais/emocionais naturais ou indícios de sobrecarga, aplicando estritamente o critério das 2 a 3 cartas de sombra.

### 🕊️ 5. Conselho do Oráculo & Direcionamento Prático
- Recomendações práticas, atitudes recomendadas e postura interior para o consulente assumir as rédeas da situação.
"""

# ==========================================
# CONFIGURAÇÃO DA PÁGINA STREAMLIT
# ==========================================
st.set_page_config(
    page_title="Auxiliar de Cartomancia & Oráculos",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==========================================
# BARRA LATERAL (SIDEBAR)
# ==========================================
with st.sidebar:
    st.markdown("## 🔮 Configurações do Oráculo")
    st.markdown("---")

    # 1. Chave de API Gemini
    api_key_default = os.environ.get("GEMINI_API_KEY", "")
    user_api_key = st.text_input(
        "🔑 Chave de API do Gemini (google-genai)",
        value=api_key_default,
        type="password",
        help="Insira sua chave da API do Google Gemini. Se definida na variável de ambiente GEMINI_API_KEY, será carregada automaticamente.",
    )

    st.caption(
        "Não tem uma chave? Obtenha gratuitamente no "
        "[Google AI Studio](https://aistudio.google.com/app/apikey)."
    )

    st.markdown("---")

    # 2. Seleção do Oráculo
    oracle_choice = st.selectbox(
        "🃏 Oráculo Utilizado",
        options=[
            "Baralho Cigano (Lenormand)",
            "Tarô Tradicional",
        ],
        index=0,
        help="Selecione o sistema simbólico utilizado na sua tiragem.",
    )

    # 3. Seleção do Método de Tiragem
    spread_choice = st.selectbox(
        "📐 Método de Tiragem",
        options=[
            "Linha de 3 Cartas",
            "Linha de 5 Cartas",
            "Bloco de 9 Cartas (3x3)",
            "Cruz Simples (5 cartas)",
            "Pirâmide Invertida (7 cartas)",
            "Livre / Outro",
        ],
        index=0,
        help="Selecione a disposição geométrica das cartas sorteadas.",
    )

    # Dicas contextuais sobre o método
    with st.expander("ℹ️ Guia rápido do método selecionado"):
        if spread_choice == "Linha de 3 Cartas":
            st.markdown(
                "**Linha de 3:**\n"
                "- Carta 1: Passado / Causa / Sujeito\n"
                "- Carta 2: Presente / Situação Atual / Ação\n"
                "- Carta 3: Futuro Imediato / Desfecho / Modificador"
            )
        elif spread_choice == "Linha de 5 Cartas":
            st.markdown(
                "**Linha de 5:**\n"
                "- Posições 1 e 2: Passado e raízes\n"
                "- Posição 3: O coração da questão (presente central)\n"
                "- Posições 4 e 5: Desdobramentos e conselho final"
            )
        elif spread_choice == "Bloco de 9 Cartas (3x3)":
            st.markdown(
                "**Bloco de 9:**\n"
                "- Carta 5 (Centro): Foco principal\n"
                "- Linha superior (1, 2, 3): Pensamentos / Passado\n"
                "- Linha do meio (4, 5, 6): Presente e ambiente\n"
                "- Linha inferior (7, 8, 9): Consequências e desfecho\n"
                "- Diagonais e espelhamentos cruzados"
            )
        elif spread_choice == "Cruz Simples (5 cartas)":
            st.markdown(
                "**Cruz Simples:**\n"
                "- 1: A favor / Base\n"
                "- 2: Contra / Obstáculo\n"
                "- 3: Conselho / Ponto de apoio mental\n"
                "- 4: Resolução / Caminho de ação\n"
                "- 5: Síntese e desfecho"
            )
        elif spread_choice == "Pirâmide Invertida (7 cartas)":
            st.markdown(
                "**Pirâmide Invertida:**\n"
                "- Base (1, 2, 3, 4): Raízes e fatores externos\n"
                "- Nível médio (5, 6): Forças em conflito ou transição\n"
                "- Vértice inferior (7): Síntese e ápice da resposta"
            )
        else:
            st.markdown(
                "**Livre / Outro:** Descreva no campo de cartas a função de cada posição tirada."
            )

    st.markdown("---")
    st.markdown(
        "<small style='color: #888;'>Versão com biblioteca oficial <code>google-genai</code> & modelo <code>gemini-2.5-flash</code>.</small>",
        unsafe_allow_html=True,
    )

# ==========================================
# ÁREA PRINCIPAL
# ==========================================
st.title("🔮 Auxiliar de Cartomancia & Oráculos")
st.markdown(
    "##### *Interpretação oracular sintática, ética e profunda para Baralho Cigano e Tarô com Google Gemini*"
)

# Card informativo com regras oraculares
with st.expander("📜 Princípios Éticos & Regras de Interpretação Deste Auxiliar", expanded=False):
    st.markdown(
        """
        - **Sintaxe do Lenormand:** Cartas são lidas em duplas ou tríades (Substantivo + Adjetivo / Tema + Qualificador).
        - **Tarô Estruturado:** Clara distinção entre as lições arquetípicas dos Arcanos Maiores e as dinâmicas cotidianas dos 4 naipes dos Arcanos Menores.
        - **Regra Estrita das 3 Cartas para Magia:** NUNCA afirma demandas ou feitiços por uma carta isolada (ex: O Diabo, Caixão ou Cobra sozinhos). É obrigatória a conjunção de **2 a 3 cartas de sombra pesada** direcionadas para o campo sutil.
        - **Livre-Arbítrio Soberano:** O oráculo orienta e aconselha tendências, preservando a autonomia do consulente.
        """
    )

st.markdown("### 📝 Dados da Tiragem")

col1, col2 = st.columns([1, 1], gap="medium")

with col1:
    question_context = st.text_area(
        "1. Pergunta / Contexto da Tiragem *",
        height=140,
        placeholder="Exemplo: 'Consulente pergunta sobre a transição de carreira para um novo projeto independente. Sente insegurança sobre a estabilidade financeira nos próximos 6 meses.'",
        help="Forneça a dúvida do consulente ou o contexto em que a leitura foi solicitada.",
    )

with col2:
    drawn_cards = st.text_area(
        "2. Cartas Sorteadas e suas Posições *",
        height=140,
        placeholder="Exemplo no Baralho Cigano:\nPosição 1 (Passado): 24. Coração\nPosição 2 (Presente): 34. Peixes\nPosição 3 (Futuro): 35. Âncora\n\nOu no Tarô:\n1. O Mago, 2. 8 de Ouros, 3. 2 de Espadas",
        help="Liste as cartas sorteadas, indicando a posição ou número da carta se desejar.",
    )

# Upload de Imagem da Mesa
uploaded_image_file = st.file_uploader(
    "📷 Foto da Mesa / Tiragem (Opcional - Formatos: JPG, JPEG, PNG)",
    type=["jpg", "jpeg", "png"],
    help="Envie uma foto das cartas sobre a mesa para que a visão computacional do Gemini complemente a análise simbólica.",
)

# Exibição da prévia da imagem se carregada
image_for_gemini = None
if uploaded_image_file is not None:
    try:
        image_for_gemini = Image.open(uploaded_image_file)
        st.image(
            image_for_gemini,
            caption="📷 Imagem da tiragem carregada com sucesso",
            use_container_width=False,
            width=360,
        )
    except Exception as img_err:
        st.warning(f"Não foi possível abrir a imagem enviada: {img_err}")

st.markdown("<br>", unsafe_allow_html=True)

# Botão de Envio Principal
analyze_button = st.button(
    "🔮 Analisar Tiragem",
    type="primary",
    use_container_width=True,
)

# ==========================================
# PROCESSAMENTO E CHAMADA DA API GEMINI
# ==========================================
if analyze_button:
    # 1. Validações de Pré-requisitos
    active_api_key = user_api_key.strip() or os.environ.get("GEMINI_API_KEY", "").strip()

    if not active_api_key:
        st.error(
            "⚠️ **Chave de API ausente!** Por favor, insira sua chave da API do Gemini "
            "na barra lateral esquerda para continuar, ou configure a variável GEMINI_API_KEY."
        )
    elif not question_context.strip():
        st.warning("⚠️ Por favor, informe a **Pergunta / Contexto da Tiragem** antes de prosseguir.")
    elif not drawn_cards.strip() and image_for_gemini is None:
        st.warning(
            "⚠️ Por favor, preencha as **Cartas Sorteadas** ou faça o upload de uma **Foto da Tiragem**."
        )
    else:
        # 2. Execução da Chamada à API Oficial
        with st.spinner("✨ Consultando o oráculo e desvendando os arcanos com Gemini 2.5 Flash..."):
            try:
                # Inicialização do cliente oficial google-genai
                client = genai.Client(api_key=active_api_key)

                # Montagem do prompt do usuário
                user_prompt_text = f"""
Por favor, realize a interpretação aprofundada da seguinte tiragem oracular:

- **Oráculo Escolhido**: {oracle_choice}
- **Método de Tiragem**: {spread_choice}
- **Pergunta / Contexto do Consulente**:
{question_context.strip()}

- **Cartas Sorteadas e Posições Informadas**:
{drawn_cards.strip() if drawn_cards.strip() else "(Consulte a foto em anexo para identificar as cartas dispostas na mesa)"}

Lembre-se de aplicar rigorosamente todas as regras oraculares da system instruction, especialmente a sintaxe de leitura, o tom ético e a regra estrita das 2 a 3 cartas de sombra para qualquer menção a questões espirituais densas.
"""

                # Montagem dos conteúdos (texto + imagem se houver)
                contents_payload = []
                if image_for_gemini is not None:
                    contents_payload.append(image_for_gemini)
                contents_payload.append(user_prompt_text)

                # Chamada com o modelo oficial gemini-2.5-flash e contingência automática
                candidate_models = ["gemini-2.5-flash", "gemini-3.6-flash", "gemini-3.8-flash", "gemini-flash-latest"]
                response = None
                last_err = None

                for model_name in candidate_models:
                    try:
                        response = client.models.generate_content(
                            model=model_name,
                            contents=contents_payload,
                            config=types.GenerateContentConfig(
                                system_instruction=SYSTEM_INSTRUCTION,
                                temperature=0.7,
                            ),
                        )
                        if response and response.text:
                            break
                    except Exception as err:
                        last_err = err

                if response is None or not response.text:
                    raise last_err or Exception("Não foi possível obter resposta dos modelos oraculares.")

                # 3. Exibição do Resultado
                st.success("✨ Tiragem interpretada com sucesso!")
                st.markdown("---")
                
                interpretation_text = response.text or "Nenhum texto retornado pelo oráculo."

                # Renderização rica do Markdown
                st.markdown(interpretation_text)

                st.markdown("---")

                # Área para copiar o resultado facilmente
                st.markdown("#### 📋 Copiar ou Salvar Interpretação")
                st.download_button(
                    label="💾 Baixar Interpretação (.txt)",
                    data=interpretation_text,
                    file_name="interpretacao_oraculo.txt",
                    mime="text/plain",
                    use_container_width=False,
                )

                with st.expander("📄 Ver texto bruto para cópia rápida"):
                    st.code(interpretation_text, language="markdown")

            except Exception as e:
                st.error(
                    f"❌ **Erro durante a consulta oracular:**\n\n`{str(e)}`\n\n"
                    "Dica: Verifique se sua chave da API do Gemini é válida e possui permissão para o modelo `gemini-2.5-flash`."
                )

# ==========================================
# RODAPÉ
# ==========================================
st.markdown("<br><hr>", unsafe_allow_html=True)
st.markdown(
    "<center><small style='color: #777;'>Auxiliar de Cartomancia & Oráculos • Desenvolvido com Python, Streamlit e Google Gemini API (<code>google-genai</code>)</small></center>",
    unsafe_allow_html=True,
)
