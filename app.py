"""
Auxiliar de Cartomancia & Oráculos v2.0
Aplicação Streamlit profissional para análise e interpretação aprofundada de tiragens
utilizando a biblioteca oficial google-genai e o modelo gemini-2.5-flash.

Recursos: Histórico SQLite, Exportação PDF, Modo Profissional, Múltiplos Tons de Leitura.
"""

import os
import re
import json
import sqlite3
from datetime import datetime
from io import BytesIO

import streamlit as st
from PIL import Image

try:
    from google import genai
    from google.genai import types
except ImportError:
    st.error(
        "A biblioteca 'google-genai' não está instalada. "
        "Execute no terminal: pip install google-genai"
    )
    st.stop()

try:
    from fpdf import FPDF
except ImportError:
    st.error(
        "A biblioteca 'fpdf2' não está instalada. "
        "Execute no terminal: pip install fpdf2"
    )
    st.stop()

# ==========================================
# CONFIGURAÇÕES GLOBAIS
# ==========================================
DB_PATH = "leituras.db"

# ==========================================
# BANCO DE DADOS - HISTÓRICO DE LEITURAS
# ==========================================
def init_db():
    """Inicializa o banco SQLite e cria a tabela de leituras."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS leituras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_hora TEXT,
            nome_consulente TEXT,
            signo_consulente TEXT,
            modo_atendimento TEXT,
            oraculo TEXT,
            metodo TEXT,
            tom_leitura TEXT,
            pergunta TEXT,
            cartas TEXT,
            interpretacao TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_reading(data):
    """Salva uma nova leitura no histórico."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO leituras
        (data_hora, nome_consulente, signo_consulente, modo_atendimento,
         oraculo, metodo, tom_leitura, pergunta, cartas, interpretacao)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["data_hora"], data["nome_consulente"], data["signo_consulente"],
        data["modo_atendimento"], data["oraculo"], data["metodo"],
        data["tom_leitura"], data["pergunta"], json.dumps(data["cartas"], ensure_ascii=False),
        data["interpretacao"]
    ))
    conn.commit()
    conn.close()

def list_readings():
    """Lista todas as leituras salvas."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT id, data_hora, nome_consulente, oraculo, metodo, tom_leitura
        FROM leituras ORDER BY id DESC
    """)
    rows = c.fetchall()
    conn.close()
    return rows

def load_reading(reading_id):
    """Carrega uma leitura específica pelo ID."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM leituras WHERE id = ?", (reading_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return {
            "id": row[0], "data_hora": row[1], "nome_consulente": row[2],
            "signo_consulente": row[3], "modo_atendimento": row[4],
            "oraculo": row[5], "metodo": row[6], "tom_leitura": row[7],
            "pergunta": row[8], "cartas": json.loads(row[9]),
            "interpretacao": row[10]
        }
    return None

def delete_reading(reading_id):
    """Remove uma leitura do histórico."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM leituras WHERE id = ?", (reading_id,))
    conn.commit()
    conn.close()

# Inicializa o banco ao iniciar
init_db()

# ==========================================
# BANCO DE DADOS DE CARTAS E POSIÇÕES
# ==========================================
CARTAS_CIGANO = [
    "-- Selecione uma carta --",
    "01. O Cavaleiro", "02. O Trevo", "03. O Navio", "04. A Casa",
    "05. A Árvore", "06. As Nuvens", "07. A Cobra", "08. O Caixão",
    "09. O Buquê", "10. A Foice", "11. O Chicote", "12. Os Pássaros",
    "13. A Criança", "14. A Raposa", "15. O Urso", "16. A Estrela",
    "17. A Cegonha", "18. O Cão", "19. A Torre", "20. O Jardim",
    "21. A Montanha", "22. Os Caminhos", "23. Os Ratos", "24. O Coração",
    "25. O Anel", "26. O Livro", "27. A Carta", "28. O Cigano",
    "29. A Cigana", "30. Os Lírios", "31. O Sol", "32. A Lua",
    "33. A Chave", "34. Os Peixes", "35. A Âncora", "36. A Cruz"
]

CARTAS_TARO = [
    "-- Selecione uma carta --",
    # Arcanos Maiores
    "0. O Louco", "I. O Mago", "II. A Sacerdotisa", "III. A Imperatriz",
    "IV. O Imperador", "V. O Papa / O Hierofante", "VI. Os Enamorados",
    "VII. O Carro", "VIII. A Força", "IX. O Eremita", "X. A Roda da Fortuna",
    "XI. A Justiça", "XII. O Enforcado", "XIII. A Morte", "XIV. A Temperança",
    "XV. O Diabo", "XVI. A Torre", "XVII. A Estrela", "XVIII. A Lua",
    "XIX. O Sol", "XX. O Julgamento", "XXI. O Mundo",
    # Paus
    "Ás de Paus", "2 de Paus", "3 de Paus", "4 de Paus", "5 de Paus",
    "6 de Paus", "7 de Paus", "8 de Paus", "9 de Paus", "10 de Paus",
    "Valete de Paus", "Cavaleiro de Paus", "Rainha de Paus", "Rei de Paus",
    # Copas
    "Ás de Copas", "2 de Copas", "3 de Copas", "4 de Copas", "5 de Copas",
    "6 de Copas", "7 de Copas", "8 de Copas", "9 de Copas", "10 de Copas",
    "Valete de Copas", "Cavaleiro de Copas", "Rainha de Copas", "Rei de Copas",
    # Espadas
    "Ás de Espadas", "2 de Espadas", "3 de Espadas", "4 de Espadas", "5 de Espadas",
    "6 de Espadas", "7 de Espadas", "8 de Espadas", "9 de Espadas", "10 de Espadas",
    "Valete de Espadas", "Cavaleiro de Espadas", "Rainha de Espadas", "Rei de Espadas",
    # Ouros
    "Ás de Ouros", "2 de Ouros", "3 de Ouros", "4 de Ouros", "5 de Ouros",
    "6 de Ouros", "7 de Ouros", "8 de Ouros", "9 de Ouros", "10 de Ouros",
    "Valete de Ouros", "Cavaleiro de Ouros", "Rainha de Ouros", "Rei de Ouros"
]

ESTRUTURA_POSICOES = {
    "Linha de 3 Cartas": [
        "Posição 1 (Passado / Causa / Sujeito)",
        "Posição 2 (Presente / Situação / Ação)",
        "Posição 3 (Futuro / Desfecho / Modificador)"
    ],
    "Linha de 5 Cartas": [
        "Posição 1 (Passado / Raízes)",
        "Posição 2 (Influências Atuais)",
        "Posição 3 (O Coração da Questão - Centro)",
        "Posição 4 (Desdobramentos Próximos)",
        "Posição 5 (Desfecho / Conselho)"
    ],
    "Bloco de 9 Cartas (3x3)": [
        "Posição 1 (Pensamentos / Passado Superior)",
        "Posição 2 (Ambiente / Passado Central)",
        "Posição 3 (Ações / Passado Inferior)",
        "Posição 4 (Presente / Influência Esquerda)",
        "Posição 5 (O Foco Principal - CENTRO)",
        "Posição 6 (Presente / Influência Direita)",
        "Posição 7 (Tendência / Futuro Superior)",
        "Posição 8 (Ambiente / Futuro Central)",
        "Posição 9 (Consequência / Futuro Inferior)"
    ],
    "Cruz Simples (5 cartas)": [
        "Posição 1 (A favor / A Situação)",
        "Posição 2 (Contra / O Obstáculo)",
        "Posição 3 (O Mental / Conselho)",
        "Posição 4 (Caminho / Resolução)",
        "Posição 5 (Síntese e Desfecho)"
    ],
    "Pirâmide Invertida (7 cartas)": [
        "Posição 1 (Topo - O Tema Principal)",
        "Posição 2 (Linha 2 - Fator Influenciador 1)",
        "Posição 3 (Linha 2 - Fator Influenciador 2)",
        "Posição 4 (Linha 2 - Fator Influenciador 3)",
        "Posição 5 (Linha 3 - Desafio / Bloqueio 1)",
        "Posição 6 (Linha 3 - Desafio / Bloqueio 2)",
        "Posição 7 (Base - Síntese e Ápice)"
    ]
}

# ==========================================
# SYSTEM INSTRUCTIONS - MÚLTIPLOS TONS
# ==========================================
_BASE_RULES = """
DIRETRIZES ÉTICAS FUNDAMENTAIS (VÁLIDAS PARA TODOS OS TONS):
1. POSTURA NÃO-FATALISTA: O oráculo revela tendências energéticas, NUNCA destino imutável.
2. SINTAXE LENORMAND: Leitura em pares/tríades (Substantivo + Adjetivo / Tema + Qualificador).
3. TARÔ ESTRUTURADO: Arcanos Maiores = lições arquetípicas; Menores = cotidiano/prático.
4. REGRA DE OURO (MAGIA/DEMANDAS): PROIBIDO apontar magia/trabalho feito com apenas 1 carta de sombra. Exige 2-3 cartas de sombra alinhadas voltadas ao campo sutil.
5. LIVRE-ARBÍTRIO: Sempre preserve a autonomia do consulente.

ESTRUTURA OBRIGATÓRIA DA RESPOSTA:
### 🌟 1. Panorama Geral da Tiragem
### 🔍 2. Análise Técnica e Sintática das Cartas
### 🎯 3. Resposta Direta à Pergunta / Contexto
### 🛡️ 4. Avaliação Energética & Espiritual (Aplicação da Regra Estrita)
### 🕊️ 5. Conselho do Oráculo & Direcionamento Prático
"""

SYSTEM_INSTRUCTIONS = {
    "Terapêutica (Acolhedora e Emocional)": f"""Você é um Cartomante Terapêutico, especialista em autoconhecimento, cura emocional e padrões psíquicos.

FOCO PRINCIPAL:
- Identificar padrões emocionais repetitivos e crenças limitantes.
- Acolher as vulnerabilidades do consulente com empatia profunda.
- Apontar caminhos de cura interior, reconciliação e autocompaixão.
- Usar linguagem suave, nutritiva e encorajadora.
- Explorar as origens psíquicas das situações (infância, traumas, ciclos familiares).

{_BASE_RULES}
""",
    "Objetiva (Direta e Prática)": f"""Você é um Oraculista Estratégico, focado em respostas claras, timing e ações práticas.

FOCO PRINCIPAL:
- Entregar respostas objetivas, sem rodeios, com clareza cirúrgica.
- Indicar TIMING (quando agir, quando esperar).
- Listar ações concretas e decisões práticas a serem tomadas.
- Sinalizar riscos objetivos e oportunidades tangíveis.
- Usar linguagem assertiva, profissional e focada em resultados.

{_BASE_RULES}
""",
    "Profunda (Arquetípica e Espiritual)": f"""Você é um Mestre Oraculista com visão arquetípica, astrológica e espiritual.

FOCO PRINCIPAL:
- Interpretar a tiragem sob a ótica dos arquétipos junguianos e da jornada da alma.
- Conectar as cartas a ciclos cármicos, lições de vida e propósito maior.
- Apontar aprendizados espirituais e transformações profundas em curso.
- Usar linguagem simbólica, poética e inspiradora.
- Relacionar os Arcanos Maiores a grandes processos alquímicos internos.

{_BASE_RULES}
""",
}

# ==========================================
# FUNÇÕES AUXILIARES - PDF
# ==========================================
def sanitizar_texto_pdf(texto):
    """Remove emojis e caracteres não suportados pelo PDF (latin-1)."""
    # Substitui emojis e símbolos comuns por marcadores de texto
    replacements = {
        '🌟': '[1.]', '🔍': '[2.]', '🎯': '[3.]', '🛡️': '[4.]', '🕊️': '[5.]',
        '✨': '*', '⭐': '*', '💫': '*',
        '—': '-', '→': '->', '←': '<-', '↔': '<->',
        '•': '*', '✦': '*', '❖': '*',
        '⚠️': '[!]', '❌': '[X]', '✅': '[OK]',
        '🔮': '[ORACULO]', '📜': '[DOC]', '📝': '[NOTA]',
        '💾': '[SALVAR]', '📄': '[PG]', '📷': '[CAM]',
    }
    for k, v in replacements.items():
        texto = texto.replace(k, v)
    # Remove qualquer caractere fora do latin-1
    texto = re.sub(r'[^\x00-\xFF]', '', texto)
    return texto

def gerar_pdf_leitura(dados_leitura, modo_profissional=False, dados_oraculista=None):
    """Gera um PDF formatado da leitura oracular."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=20)

    # Cabeçalho
    if modo_profissional and dados_oraculista:
        pdf.set_font("Helvetica", "B", 18)
        pdf.cell(0, 10, sanitizar_texto_pdf(dados_oraculista.get("nome", "Oraculista")), ln=True, align="C")
        pdf.set_font("Helvetica", "", 10)
        contato = dados_oraculista.get("contato", "")
        if contato:
            pdf.cell(0, 5, sanitizar_texto_pdf(contato), ln=True, align="C")
        pdf.ln(5)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)

    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Relatorio de Leitura Oracular", ln=True, align="C")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"Gerado em: {dados_leitura['data_hora']}", ln=True, align="C")
    pdf.ln(8)

    # Dados do Consulente
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Dados da Consulta", ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(50, 6, "Consulente:", ln=False)
    pdf.cell(0, 6, sanitizar_texto_pdf(dados_leitura.get("nome_consulente") or "Nao informado"), ln=True)
    if dados_leitura.get("signo_consulente"):
        pdf.cell(50, 6, "Signo/Ref:", ln=False)
        pdf.cell(0, 6, sanitizar_texto_pdf(dados_leitura["signo_consulente"]), ln=True)
    pdf.cell(50, 6, "Oraculo:", ln=False)
    pdf.cell(0, 6, sanitizar_texto_pdf(dados_leitura["oraculo"]), ln=True)
    pdf.cell(50, 6, "Metodo:", ln=False)
    pdf.cell(0, 6, sanitizar_texto_pdf(dados_leitura["metodo"]), ln=True)
    pdf.cell(50, 6, "Tom da Leitura:", ln=False)
    pdf.cell(0, 6, sanitizar_texto_pdf(dados_leitura["tom_leitura"]), ln=True)
    pdf.ln(5)

    # Pergunta
    if dados_leitura.get("pergunta"):
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "Pergunta / Contexto", ln=True)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(3)
        pdf.set_font("Helvetica", "I", 11)
        pdf.multi_cell(0, 6, sanitizar_texto_pdf(dados_leitura["pergunta"]))
        pdf.ln(5)

    # Cartas Sorteadas
    if dados_leitura.get("cartas"):
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "Cartas Sorteadas", ln=True)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(3)
        pdf.set_font("Helvetica", "", 11)
        for pos, carta in dados_leitura["cartas"].items():
            pdf.cell(0, 6, f"  - {pos}: {carta}", ln=True)
        pdf.ln(5)

    # Interpretação
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Interpretacao Oracular", ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)
    pdf.set_font("Helvetica", "", 11)
    interpretacao = sanitizar_texto_pdf(dados_leitura.get("interpretacao", ""))
    pdf.multi_cell(0, 6, interpretacao)

    # Rodapé
    pdf.ln(10)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)
    pdf.set_font("Helvetica", "I", 9)
    pdf.cell(0, 5, "Documento gerado pelo sistema 'Auxiliar de Cartomancia & Oraculos'", ln=True, align="C")
    pdf.cell(0, 5, "Leitura baseada em tendencias energeticas - Respeite seu livre-arbitrio.", ln=True, align="C")

    return pdf.output(dest="S")

# ==========================================
# CONFIGURAÇÃO DA PÁGINA
# ==========================================
st.set_page_config(
    page_title="Auxiliar de Cartomancia & Oráculos",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inicializa session_state
if "interpretacao_atual" not in st.session_state:
    st.session_state.interpretacao_atual = None
if "dados_leitura_atual" not in st.session_state:
    st.session_state.dados_leitura_atual = None

# ==========================================
# BARRA LATERAL (SIDEBAR) - REORGANIZADA
# ==========================================
with st.sidebar:
    st.markdown("# 🔮 Oráculo")
    st.markdown("---")

    # 1. Modo de Atendimento
    with st.expander("🎯 Tipo de Atendimento", expanded=True):
        modo_atendimento = st.radio(
            "Modalidade da Leitura",
            options=["Pessoal (Uso próprio)", "Profissional (Para cliente)"],
            index=0,
            label_visibility="collapsed"
        )
        modo_profissional = (modo_atendimento == "Profissional (Para cliente)")

        if modo_profissional:
            st.markdown("#### 👤 Seus Dados (Oraculista)")
            nome_oraculista = st.text_input("Seu Nome / Marca", value="")
            contato_oraculista = st.text_input(
                "Contato (Instagram, email, etc.)",
                value="",
                placeholder="@seuinstagram"
            )
        else:
            nome_oraculista = ""
            contato_oraculista = ""

    # 2. Oráculo e Método
    with st.expander("🃏 Oráculo e Método", expanded=True):
        oracle_choice = st.selectbox(
            "Sistema Simbólico",
            options=["Baralho Cigano (Lenormand)", "Tarô Tradicional"],
            index=0,
        )
        spread_choice = st.selectbox(
            "Disposição da Tiragem",
            options=[
                "Linha de 3 Cartas",
                "Linha de 5 Cartas",
                "Bloco de 9 Cartas (3x3)",
                "Cruz Simples (5 cartas)",
                "Pirâmide Invertida (7 cartas)",
                "Livre / Outro",
            ],
            index=0,
        )
        if spread_choice == "Livre / Outro":
            num_free_cards = st.number_input(
                "Quantidade de Cartas:", min_value=1, max_value=36, value=3, step=1
            )
        else:
            num_free_cards = 0

    # 3. Tom da Leitura
    with st.expander("🎨 Tom da Leitura", expanded=True):
        tom_leitura = st.selectbox(
            "Estilo de Interpretação",
            options=list(SYSTEM_INSTRUCTIONS.keys()),
            index=0,
        )

    # 4. Dados do Consulente
    with st.expander("🧑‍🦰 Dados do Consulente", expanded=True):
        nome_consulente = st.text_input(
            "Nome do Consulente *" if modo_profissional else "Nome do Consulente",
            value="",
        )
        signo_consulente = st.text_input(
            "Signo / Data de Nascimento (Opcional)",
            value="",
            placeholder="Ex: Áries, 15/03/1990"
        )

    st.markdown("---")
    st.markdown(
        "<small style='color: #888;'>Serviço via Google Gemini API (<code>gemini-2.5-flash</code>).</small>",
        unsafe_allow_html=True,
    )

# ==========================================
# ÁREA PRINCIPAL - COM TABS
# ==========================================
st.title("🔮 Auxiliar de Cartomancia & Oráculos")
st.markdown(
    "##### *Interpretação oracular sintática, ética e profunda com Google Gemini*"
)

tab_nova, tab_historico = st.tabs(["🆕 Nova Leitura", "📚 Histórico de Leituras"])

# ========================
# TAB 1 - NOVA LEITURA
# ========================
with tab_nova:
    with st.expander("📜 Princípios Éticos & Regras de Interpretação", expanded=False):
        st.markdown(
            f"""
            **Tom Ativo:** {tom_leitura}

            - **Sintaxe do Lenormand:** Cartas lidas em duplas/tríades (Substantivo + Adjetivo).
            - **Tarô Estruturado:** Distinção entre Arcanos Maiores e Menores.
            - **Regra Estrita para Magia:** NUNCA afirma demandas por uma carta isolada. Exige 2-3 cartas de sombra pesada alinhadas.
            - **Livre-Arbítrio Soberano:** O oráculo orienta, preservando a autonomia do consulente.
            """
        )

    st.markdown("### 📝 Dados da Tiragem")
    col1, col2 = st.columns([1, 1], gap="medium")

    with col1:
        question_context = st.text_area(
            "1. Pergunta / Contexto da Tiragem *",
            height=180,
            placeholder="Exemplo: 'Consulente pergunta sobre a relação profissional ou vida amorosa...'",
        )

        uploaded_image_file = st.file_uploader(
            "📷 Foto da Mesa / Tiragem (Opcional)",
            type=["jpg", "jpeg", "png"],
        )

        image_for_gemini = None
        if uploaded_image_file is not None:
            try:
                image_for_gemini = Image.open(uploaded_image_file)
                if image_for_gemini.mode != "RGB":
                    image_for_gemini = image_for_gemini.convert("RGB")
                image_for_gemini.thumbnail((1600, 1600))
                st.image(
                    image_for_gemini,
                    caption="📷 Imagem processada e otimizada",
                    width=300,
                )
            except Exception as img_err:
                st.warning(f"Não foi possível processar a imagem: {img_err}")

    with col2:
        st.markdown("**2. Selecione as Cartas de Cada Posição ***")
        opcoes_cartas = CARTAS_CIGANO if oracle_choice == "Baralho Cigano (Lenormand)" else CARTAS_TARO

        if spread_choice in ESTRUTURA_POSICOES:
            rotulos_posicoes = ESTRUTURA_POSICOES[spread_choice]
        else:
            rotulos_posicoes = [f"Carta {i+1}" for i in range(int(num_free_cards))]

        cartas_selecionadas = {}
        with st.container(height=380, border=True):
            for rotulo in rotulos_posicoes:
                escolha = st.selectbox(
                    rotulo,
                    options=opcoes_cartas,
                    key=f"card_{rotulo}"
                )
                if escolha != "-- Selecione uma carta --":
                    cartas_selecionadas[rotulo] = escolha

    analyze_button = st.button(
        "🔮 Analisar Tiragem",
        type="primary",
        use_container_width=True
    )

    # ==========================================
    # PROCESSAMENTO E CHAMADA DA API GEMINI
    # ==========================================
    if analyze_button:
        active_api_key = (
            st.secrets.get("GEMINI_API_KEY", "")
            or os.environ.get("GEMINI_API_KEY", "")
        ).strip()

        # Validações
        erros = []
        if not active_api_key:
            erros.append("Chave de API não configurada. Configure no `.streamlit/secrets.toml` ou como variável de ambiente.")
        if not question_context.strip():
            erros.append("Informe a Pergunta / Contexto da Tiragem.")
        if modo_profissional and not nome_consulente.strip():
            erros.append("No Modo Profissional, o nome do consulente é obrigatório.")
        if not cartas_selecionadas and image_for_gemini is None:
            erros.append("Selecione as cartas nos menus suspensos ou envie uma foto da tiragem.")

        if erros:
            for erro in erros:
                st.error(f"⚠️ {erro}")
        else:
            with st.spinner("✨ Consultando os arcanos com o Google Gemini..."):
                try:
                    client = genai.Client(api_key=active_api_key)

                    texto_cartas_formatado = "\n".join(
                        [f"- {pos}: {carta}" for pos, carta in cartas_selecionadas.items()]
                    )

                    user_prompt_text = f"""
Por favor, realize a interpretação aprofundada da seguinte tiragem oracular:

- **Oráculo Escolhido**: {oracle_choice}
- **Método de Tiragem**: {spread_choice}
- **Tom da Leitura Solicitado**: {tom_leitura}
- **Nome do Consulente**: {nome_consulente or 'Não informado'}
- **Signo/Referência**: {signo_consulente or 'Não informado'}
- **Pergunta / Contexto**: {question_context.strip()}

- **Cartas Sorteadas e Posições**:
{texto_cartas_formatado if texto_cartas_formatado else "(Analise as cartas a partir da foto da mesa enviada em anexo)"}

Aplique rigorosamente todas as regras oraculares da system instruction.
"""

                    contents_payload = []
                    if image_for_gemini is not None:
                        contents_payload.append(image_for_gemini)
                    contents_payload.append(user_prompt_text)

                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=contents_payload,
                        config=types.GenerateContentConfig(
                            system_instruction=SYSTEM_INSTRUCTIONS[tom_leitura],
                            temperature=0.7,
                        ),
                    )

                    if response and response.text:
                        interpretation_text = response.text
                        data_hora = datetime.now().strftime("%d/%m/%Y %H:%M")

                        # Salva no session_state
                        dados_leitura = {
                            "data_hora": data_hora,
                            "nome_consulente": nome_consulente,
                            "signo_consulente": signo_consulente,
                            "modo_atendimento": modo_atendimento,
                            "oraculo": oracle_choice,
                            "metodo": spread_choice,
                            "tom_leitura": tom_leitura,
                            "pergunta": question_context.strip(),
                            "cartas": cartas_selecionadas,
                            "interpretacao": interpretation_text,
                        }
                        st.session_state.dados_leitura_atual = dados_leitura
                        st.session_state.interpretacao_atual = interpretation_text

                        # Salva no banco de histórico
                        save_reading(dados_leitura)

                        st.success(f"✨ Tiragem interpretada e salva no histórico ({data_hora})!")
                    else:
                        st.error("❌ Não foi possível gerar a resposta. Tente novamente.")

                except Exception as e:
                    st.error(f"❌ **Erro durante a consulta:** `{str(e)}`")

    # ==========================================
    # EXIBIÇÃO DA INTERPRETAÇÃO + EXPORTAÇÕES
    # ==========================================
    if st.session_state.interpretacao_atual and st.session_state.dados_leitura_atual:
        dados = st.session_state.dados_leitura_atual
        st.markdown("---")
        st.markdown("## 📖 Resultado da Leitura")

        with st.container(border=True):
            st.markdown(st.session_state.interpretacao_atual)

        st.markdown("---")
        st.markdown("### 💾 Exportar Relatório")

        col_exp1, col_exp2 = st.columns(2)

        with col_exp1:
            # Exportação TXT
            st.download_button(
                label="📄 Baixar Interpretação (.txt)",
                data=st.session_state.interpretacao_atual.encode("utf-8-sig"),
                file_name=f"leitura_{dados['nome_consulente'] or 'pessoal'}_{dados['data_hora'].replace('/','').replace(' ','_').replace(':','')}.txt",
                mime="text/plain; charset=utf-8",
                use_container_width=True,
            )

        with col_exp2:
            # Exportação PDF
            try:
                dados_orac_pdf = {
                    "nome": nome_oraculista,
                    "contato": contato_oraculista,
                } if modo_profissional else None

                pdf_bytes = gerar_pdf_leitura(
                    dados_leitura=dados,
                    modo_profissional=modo_profissional,
                    dados_oraculista=dados_orac_pdf
                )

                st.download_button(
                    label="📕 Baixar Relatório (.pdf)",
                    data=pdf_bytes,
                    file_name=f"relatorio_{dados['nome_consulente'] or 'pessoal'}_{dados['data_hora'].replace('/','').replace(' ','_').replace(':','')}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            except Exception as e:
                st.error(f"Erro ao gerar PDF: {e}")

        with st.expander("📋 Ver texto formatado para cópia rápida"):
            st.code(st.session_state.interpretacao_atual, language="markdown")

# ========================
# TAB 2 - HISTÓRICO
# ========================
with tab_historico:
    st.markdown("### 📚 Leituras Salvas")
    st.markdown("Acompanhe abaixo todas as suas leituras anteriores. Você pode recarregar ou excluir qualquer registro.")

    leituras = list_readings()

    if not leituras:
        st.info("📭 Nenhuma leitura salva ainda. Realize sua primeira análise na aba **Nova Leitura**.")
    else:
        # Tabela do histórico
        for leitura in leituras:
            reading_id, data_hora, nome_cons, oraculo, metodo, tom = leitura

            with st.container(border=True):
                col_info, col_acoes = st.columns([3, 1])

                with col_info:
                    st.markdown(f"**🕐 {data_hora}**")
                    st.markdown(f"👤 **Consulente:** {nome_cons or 'Não informado'}")
                    st.markdown(f"🃏 **Oráculo:** {oraculo} | **Método:** {metodo}")
                    st.caption(f"Tom: {tom}")

                with col_acoes:
                    if st.button("📂 Abrir", key=f"open_{reading_id}", use_container_width=True):
                        loaded = load_reading(reading_id)
                        if loaded:
                            st.session_state.dados_leitura_atual = loaded
                            st.session_state.interpretacao_atual = loaded["interpretacao"]
                            st.rerun()

                if st.button("🗑️ Excluir", key=f"del_{reading_id}", use_container_width=True):
                    delete_reading(reading_id)
                    st.rerun()

# ==========================================
# RODAPÉ
# ==========================================
st.markdown("<br><hr>", unsafe_allow_html=True)
st.markdown(
    "<center><small style='color: #777;'>"
    "Auxiliar de Cartomancia & Oráculos v2.0 • Google Gemini API • "
    "Leituras baseadas em tendências energéticas. Respeite seu livre-arbítrio."
    "</small></center>",
    unsafe_allow_html=True,
)