"""
Auxiliar de Cartomancia & Oráculos v5.2
Aplicação Streamlit profissional para análise e interpretação aprofundada de tiragens
utilizando a biblioteca oficial google-genai.

Oráculos suportados:
- Baralho Cigano (Lenormand, 36 cartas)
- Tarô Tradicional (78 cartas)
- Sibilla Italiana (54 cartas, fichas via sibilla.json)
- Búzios (Merindilogun, tradição Ifá, 23 cartas aberto/fechado via buzios.json)

Recursos: Histórico SQLite com Comparativa Temporal, Exportação PDF (mesa automática,
paginação) e TXT, Modo Profissional, Múltiplos Tons, Anti-duplicata, Sorteio Digital,
Mesa Visual com arte real e medalhões, Retry com backoff (503/429), Painel de
Estatísticas, Manuais do Terapeuta e ponte para a Sala de Estudo Lumina.

v5.1: Aba 🐚 Búzios (registro da jogada, mesa visual, Mentor Ifá, histórico, PDF/TXT).
v5.2: Registro da jogada de búzios SIMPLIFICADO — tabela por número de carta
      (estado + casa em selects), apoios em mini-tabela, validação automática.
"""

import os
import re
import json
import time
import math
import random
import sqlite3
import unicodedata
from collections import Counter
from datetime import datetime
from io import BytesIO
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from PIL import Image, ImageDraw, ImageFont

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
MODELO_GEMINI = "gemini-3.6-flash"
MODELO_RESERVA = ""
MAX_TENTATIVAS = 4
ESPERA_BASE_SEGUNDOS = 4
PLACEHOLDER_CARTA = "-- Selecione uma carta --"
PASTA_CARTAS = Path(__file__).parent / "assets" / "cartas"
PASTA_MEDALHOES = Path(__file__).parent / "assets" / "medalhoes"
ARQ_SIBILLA = Path(__file__).parent / "sibilla.json"
ARQ_BUZIOS = Path(__file__).parent / "buzios.json"

# PONTE COM O LUMINA (Sala de Estudo interativa em React)
LUMINA_URL = "https://luminacards.netlify.app/"

MANUAIS = {
    "Sibilla Italiana (54 cartas)": "manual-sibilla-completo.html",
    "Tarô Tradicional (78 cartas)": "manual-taro-completo.html",
    "Baralho Cigano (36 cartas)": "manual-cigano-completo.html",
}

TEMAS_BUZIOS = [
    "Geral do mês",
    "Amor & Relacionamentos",
    "Saúde & Vitalidade",
    "Trabalho & Prosperidade",
    "Espiritual & Proteção",
    "Outro (descrever)",
]

# ==========================================
# SEGURANÇA - LEITURA DA CHAVE DE API
# ==========================================
def obter_chave_api():
    """Obtém a chave de API dos secrets do Streamlit ou de variável de ambiente."""
    chave = ""
    try:
        chave = st.secrets.get("GEMINI_API_KEY", "") or ""
    except Exception:
        chave = ""
    if not chave:
        chave = os.environ.get("GEMINI_API_KEY", "") or ""
    return chave.strip()

# ==========================================
# UTILITÁRIOS DE TEXTO
# ==========================================
def _slug(texto):
    txt = unicodedata.normalize("NFD", str(texto or ""))
    txt = "".join(ch for ch in txt if unicodedata.category(ch) != "Mn")
    txt = re.sub(r"[^A-Za-z0-9]+", "_", txt).strip("_").lower()
    return txt or "pessoal"

def _carimbo(data_hora):
    return re.sub(r"[^0-9]", "", str(data_hora))[:12]

# ==========================================
# RESILIÊNCIA - RETRY COM BACKOFF
# ==========================================
def eh_erroro_transitorio(exc):
    txt = str(exc).upper()
    marcadores = (
        "503", "429", "500", "502", "504",
        "UNAVAILABLE", "RESOURCE_EXHAUSTED", "DEADLINE_EXCEEDED",
        "OVERLOADED", "HIGH DEMAND", "TRY AGAIN LATER",
    )
    return any(m in txt for m in marcadores)

def chamar_gemini(client, contents, config, ao_tentar=None):
    ultima_exc = None
    for tentativa in range(1, MAX_TENTATIVAS + 1):
        if ao_tentar:
            ao_tentar(tentativa, MAX_TENTATIVAS)
        try:
            return client.models.generate_content(
                model=MODELO_GEMINI,
                contents=contents,
                config=config,
            )
        except Exception as exc:
            ultima_exc = exc
            if not eh_erroro_transitorio(exc) or tentativa == MAX_TENTATIVAS:
                break
            time.sleep(ESPERA_BASE_SEGUNDOS * tentativa)

    if MODELO_RESERVA:
        try:
            return client.models.generate_content(
                model=MODELO_RESERVA,
                contents=contents,
                config=config,
            )
        except Exception:
            pass

    raise ultima_exc

# ==========================================
# BANCO DE DADOS - HISTÓRICO DE LEITURAS
# ==========================================
def init_db():
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
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM leituras WHERE id = ?", (reading_id,))
    conn.commit()
    conn.close()

init_db()

# ==========================================
# ORÁCULO SIBILLA - CARGA DO sibilla.json
# ==========================================
def _carregar_sibilla():
    try:
        with open(ARQ_SIBILLA, "r", encoding="utf-8") as f:
            dados = json.load(f)
        return {int(item["id"]): item for item in dados}
    except Exception:
        return {}

def _rotulo_sibilla(d):
    base = f"{int(d['id']):02d}. {d.get('titulo', '')}"
    carta = str(d.get("carta", ""))
    if carta and not carta.isdigit():
        base += f" — {carta}"
    return base

SIBILLA_DADOS = _carregar_sibilla()
CARTAS_SIBILLA = [PLACEHOLDER_CARTA] + [
    _rotulo_sibilla(d) for _, d in sorted(SIBILLA_DADOS.items())
]

def _ficha_sibilla(rotulo_carta):
    try:
        cid = int(str(rotulo_carta).split(".")[0])
    except Exception:
        return None
    return SIBILLA_DADOS.get(cid)

# ==========================================
# ORÁCULO BÚZIOS - CARGA DO buzios.json
# ==========================================
def _carregar_buzios():
    """Carrega as 46 fichas (23 cartas × aberto/fechado) do buzios.json."""
    try:
        with open(ARQ_BUZIOS, "r", encoding="utf-8") as f:
            dados = json.load(f)
    except Exception:
        return {}
    mapa = {}
    for item in dados:
        try:
            cid = int(item["id"])
        except Exception:
            continue
        entrada = mapa.setdefault(cid, {
            "entidade": item.get("entidade", ""),
            "tipo": item.get("tipo", "orixa"),
        })
        estado = item.get("estado", "aberto")
        entrada[estado] = {
            "palavra": item.get("palavra_chave", ""),
            "mensagem": item.get("mensagem", ""),
        }
    return mapa

BUZIOS_DADOS = _carregar_buzios()
BUZIOS_CARTAS_MESA = [
    cid for cid, d in sorted(BUZIOS_DADOS.items())
    if d.get("tipo") in ("orixa", "consulente")
]
BUZIOS_CARTAS_APOIO = [
    cid for cid, d in sorted(BUZIOS_DADOS.items()) if d.get("tipo") == "apoio"
]

BUZIOS_CASAS = [
    "Casa 1 · Xangô",
    "Casa 2 · Exu",
    "Casa 3 · Ogun",
    "Casa 4 · Oxóssi",
    "Casa 5 · Oxalá",
    "Casa 6 · Iemanjá",
    "Casa 7 · Ossain",
    "Moeda (centro)",
]

# Posições (x, y) das casas na mesa visual 1500x1500 (círculo horário + centro)
_BUZIOS_POSICOES = [
    (750, 300),    # Casa 1 Xangô (topo)
    (1120, 470),   # Casa 2 Exu
    (1230, 830),   # Casa 3 Ogun
    (1000, 1160),  # Casa 4 Oxóssi
    (500, 1160),   # Casa 5 Oxalá
    (270, 830),    # Casa 6 Iemanjá
    (380, 470),    # Casa 7 Ossain
    (750, 760),    # Moeda (centro)
]

def _rotulo_buzios(cid):
    d = BUZIOS_DADOS.get(cid)
    if not d:
        return f"{cid:02d}"
    return f"{cid:02d} · {d['entidade']}"

def _id_do_rotulo_buzios(rotulo):
    try:
        return int(str(rotulo).split(" ")[0])
    except Exception:
        return None

def _ficha_buzios(cid, estado):
    d = BUZIOS_DADOS.get(cid)
    if not d:
        return None
    chave = "aberto" if str(estado).lower().startswith("ab") else "fechado"
    return d.get(chave)

SYSTEM_INSTRUCTION_BUZIOS = """
Você é um **Mentor de Búzios (Merindilogun, tradição inspirada em Ifá)**, auxiliando um terapeuta humano em sessão.

A MESA (padrão Lunara Terapias):
- 7 casas em círculo (sentido horário, do topo): 1 Xangô (justiça, trabalho, verdade), 2 Exu (caminhos, escolhas, movimento), 3 Ogun (abertura prática, conquista), 4 Oxóssi (fartura, prosperidade), 5 Oxalá (fé, paz, destino), 6 Iemanjá (família, lar, emoções), 7 Ossain (cura, ervas, segredos).
- MOEDA (centro): o presente, o coração do ciclo.
- 16 búzios-cartas caem nas casas, cada um ABERTO ou FECHADO.

LEITURA DOS ESTADOS:
- ABERTO: a força fala a favor; caminho iluminado; use a palavra-chave e a mensagem ABERTA da ficha.
- FECHADO: a força recolhe, alerta ou pede preparo; use a palavra-chave e a mensagem FECHADA da ficha.
- Casa com vários búzios: o orixá da casa "recebe visitas" — cruze o domínio da casa com as entidades caídas nela.
- Casa vazia: domínio adormecido no ciclo (não é negativo; é o que não está em jogo).
- CLIMA: maioria aberta = ciclo expansivo; maioria fechada = ciclo de recolhimento e preparo.

PONTO DO CONSULENTE:
- A casa (ou a Moeda) onde caiu a carta 20 (Consulente) mostra onde a pessoa está energeticamente; aberto = visível/ativo; fechado = introspectivo/travado/protegido.
- Cartas caídas na MESMA casa do consulente falam diretamente com ele.

CARTAS DE APOIO (Zé Pilintra):
- Não entram na contagem dos 16; são conselhos laterais do mestre malandro: use a ficha para fechar a orientação com alerta, jeito ou bênção.

LIMITES ÉTICOS INEGOCIÁVEIS:
- Ferramenta de estudo e apoio: nunca substitui sacerdote iniciado (babalorixá/ialorixá/babalawo).
- NÃO profetize morte, diagnóstico médico, sentença judicial ou catástrofe; descreva processos e encaminhe ao profissional.
- Respeite o livre-arbítrio; linguagem de tendência, nunca de sentença.
- Use EXATAMENTE as fichas fornecidas (palavra-chave e mensagem) como alicerce; não invente quantidades nem casas.

ESTRUTURA OBRIGATÓRIA DA RESPOSTA (Markdown):
### 🐚 1. Clima da Jogada (abertos × fechados)
### 🏛️ 2. As Casas que Falam (orixás ativados e o que dizem)
### 🌑 3. O que o Silêncio Guarda (casas vazias e fechamentos)
### 🧭 4. O Ponto do Consulente
### 🎯 5. Resposta ao Tema Perguntado
### 🕊️ 6. Orientações e Cuidados (com o recado dos apoios, se houver)
"""

# ==========================================
# BANCO DE DADOS DE CARTAS E POSIÇÕES
# ==========================================
CARTAS_CIGANO = [
    PLACEHOLDER_CARTA,
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
    PLACEHOLDER_CARTA,
    "0. O Louco", "I. O Mago", "II. A Sacerdotisa", "III. A Imperatriz",
    "IV. O Imperador", "V. O Papa / O Hierofante", "VI. Os Enamorados",
    "VII. O Carro", "VIII. A Força", "IX. O Eremita", "X. A Roda da Fortuna",
    "XI. A Justiça", "XII. O Enforcado", "XIII. A Morte", "XIV. A Temperança",
    "XV. O Diabo", "XVI. A Torre", "XVII. A Estrela", "XVIII. A Lua",
    "XIX. O Sol", "XX. O Julgamento", "XXI. O Mundo",
    "Ás de Paus", "2 de Paus", "3 de Paus", "4 de Paus", "5 de Paus",
    "6 de Paus", "7 de Paus", "8 de Paus", "9 de Paus", "10 de Paus",
    "Valete de Paus", "Cavaleiro de Paus", "Rainha de Paus", "Rei de Paus",
    "Ás de Copas", "2 de Copas", "3 de Copas", "4 de Copas", "5 de Copas",
    "6 de Copas", "7 de Copas", "8 de Copas", "9 de Copas", "10 de Copas",
    "Valete de Copas", "Cavaleiro de Copas", "Rainha de Copas", "Rei de Copas",
    "Ás de Espadas", "2 de Espadas", "3 de Espadas", "4 de Espadas", "5 de Espadas",
    "6 de Espadas", "7 de Espadas", "8 de Espadas", "9 de Espadas", "10 de Espadas",
    "Valete de Espadas", "Cavaleiro de Espadas", "Rainha de Espadas", "Rei de Espadas",
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
    ],
    "Ferradura (7 cartas)": [
        "Posição 1 (Passado Recente)",
        "Posição 2 (Presente / Situação Atual)",
        "Posição 3 (Futuro Próximo)",
        "Posição 4 (Conselho / Orientação)",
        "Posição 5 (Influências Externas)",
        "Posição 6 (Esperanças e Medos)",
        "Posição 7 (Desfecho / Resultado Final)"
    ],
    "Grande Jogo (12 cartas)": [
        "Posição 1 (Passado Distante)",
        "Posição 2 (Passado Recente)",
        "Posição 3 (Presente Imediato)",
        "Posição 4 (Desafio Atual)",
        "Posição 5 (Oculto / Subconsciente)",
        "Posição 6 (Futuro Próximo)",
        "Posição 7 (Sua Atitude)",
        "Posição 8 (Atitude dos Outros)",
        "Posição 9 (Esperanças e Medos)",
        "Posição 10 (Influências Externas)",
        "Posição 11 (Conselho do Oráculo)",
        "Posição 12 (Desfecho Final)"
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
4. SIBILLA ITALIANA (54 cartas): Cada carta narra uma cena cotidiana e possui POLARIDADE (Positiva/Negativa/Neutra) e correspondência com o baralho comum (ex.: A♠). Use as FICHAS TÉCNICAS fornecidas (essência, significados favorável/desafiador e combinações clássicas) como alicerce da interpretação, cruzando-as com as posições da tiragem. As cartas 53 (Nemico) e 54 (Nemica) são cartas-extra de hostilidade declarada.
5. REGRA DE OURO (MAGIA/DEMANDAS): PROIBIDO apontar magia/trabalho feito com apenas 1 carta de sombra. Exige 2-3 cartas de sombra alinhadas voltadas ao campo sutil.
6. LIVRE-ARBÍTRIO: Sempre preserve a autonomia do consulente.

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

SYSTEM_INSTRUCTION_COMPARATIVA = """
Você é um Oraculista especializado em ACOMPANHAMENTO TEMPORAL de tiragens.
Você receberá: (A) uma LEITURA ORIGINAL com data, pergunta, cartas e interpretação; e (B) um RELATO ATUAL do consulente descrevendo o momento presente.

SUA MISSÃO:
1. Comparar as tendências apontadas na leitura original com o que de fato se desdobrou.
2. Identificar: o que SE CONFIRMOU, o que SE TRANSFORMOU, o que permanece LATENTE.
3. Reinterpretar as cartas originais à luz do relato atual (a carta X, que dizia Y, agora se revela como Z).
4. Apontar o próximo movimento energético e uma ação prática para o ciclo que se abre.

REGRAS:
- Postura não-fatalista: tendências, nunca sentenças.
- Valorize o livre-arbítrio e as escolhas feitas pelo consulente no período.
- Linguagem clara, acolhedora e organizada.

ESTRUTURA DA RESPOSTA:
### ⏳ 1. O Que Se Confirmou
### 🔄 2. O Que Se Transformou
### 🌱 3. O Que Permanece Latente
### 🧭 4. Releitura das Cartas Originais
### 🕊️ 5. Próximo Movimento & Ação Prática
"""

# ==========================================
# FUNÇÕES AUXILIARES - PDF
# ==========================================
def sanitizar_texto_pdf(texto):
    """Converte qualquer texto para o conjunto latin-1 suportado pela Helvetica."""
    if not texto:
        return ""

    replacements = {
        '🌟': '[1.]', '🔍': '[2.]', '🎯': '[3.]', '🛡️': '[4.]', '🕊️': '[5.]',
        '✨': '*', '⭐': '*', '💫': '*', '🌙': '*', '☀️': '*',
        '—': '-', '–': '-', '―': '-', '−': '-',
        '‐': '-', '‑': '-', '‒': '-', '⁃': '-',
        '♠': ' (Espadas)', '♥': ' (Copas)',
        '♣': ' (Paus)', '♦': ' (Ouros)',
        '→': '->', '←': '<-', '↔': '<->', '⇒': '=>',
        '⇐': '<=', '⇔': '<=>', '➔': '->', '➜': '->',
        '•': '*', '✦': '*', '❖': '*', '◦': '*',
        '▪': '*', '▫': '*', '○': '*', '●': '*',
        '⚠️': '[!]', '❌': '[X]', '✅': '[OK]',
        '❓': '[?]', '❗': '[!]', '⭕': '[O]', '✖': '[X]',
        '🔮': '[ORACULO]', '📜': '[DOC]', '📝': '[NOTA]',
        '💾': '[SALVAR]', '📄': '[PG]', '📷': '[CAM]',
        '🎴': '[CARTA]', '🃏': '[BARALHO]', '🎲': '[DADO]',
        '⏳': '[TEMPO]', '🔄': '[CICLO]', '🌱': '[GERME]',
        '🧭': '[BUSSOLA]', '📊': '[GRAFICO]', '📈': '[GRAFICO]',
        '📚': '[LIVROS]', '📖': '[LIVRO]', '📕': '[LIVRO]',
        '🖼️': '[IMG]', '🔒': '[TRAVA]', '⚖️': '[BALANCA]',
        '👤': '[PESSOA]', '🧑': '[PESSOA]', '🕐': '[RELOGIO]',
        '🔗': '[LINK]', '💡': '[IDEIA]', '📂': '[PASTA]',
        '🗑️': '[LIXO]', '🧹': '[LIMPEZA]', '🎓': '[ESTUDO]',
        '📐': '[GEOMETRIA]', '🧠': '[MENTE]', '🪞': '[ESPELHO]',
        '🐴': '[CAVALO]', '🧵': '[TRAMA]', '🏛️': '[CASAS]',
        '🐚': '[BUZIOS]', '🌑': '[SILENCIO]', '🎪': '[SALA]',
        '“': '"', '”': '"', '‘': "'", '’': "'",
        '‹': '<', '›': '>', '«': '<<', '»': '>>',
        '…': '...', '·': '.', '‧': '.', '⋅': '.',
        '⁄': '/', '∕': '/', '⁎': '*',
        '\u00a0': ' ', '\u2002': ' ', '\u2003': ' ',
        '\u2009': ' ', '\u200b': '',
    }

    for k, v in replacements.items():
        texto = texto.replace(k, v)

    texto_limpo = []
    for char in texto:
        try:
            char.encode('latin-1')
            texto_limpo.append(char)
        except UnicodeEncodeError:
            texto_limpo.append('?')

    return ''.join(texto_limpo)


class _PDFOraculo(FPDF):
    """FPDF com rodapé de paginação automática."""

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 5, f"Pagina {self.page_no()}/{{nb}}", align="C")


def gerar_pdf_leitura(dados_leitura, modo_profissional=False, dados_oraculista=None, imagem_mesa=None):
    """Gera um PDF formatado da leitura oracular, com mesa visual opcional."""
    pdf = _PDFOraculo()
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=20)

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

    if dados_leitura.get("pergunta"):
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "Pergunta / Contexto", ln=True)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(3)
        pdf.set_font("Helvetica", "I", 11)
        pdf.multi_cell(0, 6, sanitizar_texto_pdf(dados_leitura["pergunta"]))
        pdf.ln(5)

    if dados_leitura.get("cartas"):
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "Cartas Sorteadas", ln=True)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(3)
        pdf.set_font("Helvetica", "", 11)
        for pos, carta in dados_leitura["cartas"].items():
            pdf.cell(0, 6, sanitizar_texto_pdf(f"  - {pos}: {carta}"), ln=True)
        pdf.ln(2)

        if str(dados_leitura.get("oraculo", "")).startswith("Sibilla"):
            pol = {"Positiva": 0, "Neutra": 0, "Negativa": 0}
            for carta in dados_leitura["cartas"].values():
                ficha = _ficha_sibilla(carta)
                if ficha:
                    chave_pol = str(ficha.get("polaridade", ""))
                    if chave_pol in pol:
                        pol[chave_pol] += 1
            pdf.set_font("Helvetica", "I", 10)
            pdf.cell(
                0, 6,
                sanitizar_texto_pdf(
                    f"Clima da tiragem: {pol['Positiva']} positivas, "
                    f"{pol['Neutra']} neutras, {pol['Negativa']} negativas."
                ),
                ln=True,
            )
        pdf.ln(5)

    if imagem_mesa is not None:
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 8, "Representacao Visual da Tiragem (Mesa)", ln=True, align="C")
        pdf.ln(4)
        buf = BytesIO()
        imagem_mesa.save(buf, format="PNG")
        buf.seek(0)
        w_mm = 180.0
        h_mm = w_mm * imagem_mesa.height / imagem_mesa.width
        pdf.image(buf, x=15, y=pdf.get_y() + 2, w=w_mm, h=h_mm)
        pdf.ln(h_mm + 10)
        pdf.set_font("Helvetica", "I", 9)
        pdf.cell(0, 5, "Mesa gerada automaticamente pelo sistema.", ln=True, align="C")

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Interpretacao Oracular", ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)
    pdf.set_font("Helvetica", "", 11)
    interpretacao = sanitizar_texto_pdf(dados_leitura.get("interpretacao", ""))
    pdf.multi_cell(0, 6, interpretacao)

    pdf.ln(10)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)
    pdf.set_font("Helvetica", "I", 9)
    pdf.cell(0, 5, "Documento gerado pelo sistema 'Auxiliar de Cartomancia & Oraculos'", ln=True, align="C")
    pdf.cell(0, 5, "Leitura baseada em tendencias energeticas - Respeite seu livre-arbitrio.", ln=True, align="C")

    try:
        saida = pdf.output(dest="S")
    except TypeError:
        saida = pdf.output()
    return bytes(saida)

# ==========================================
# IMAGENS REAIS DAS CARTAS (assets/cartas/)
# ==========================================
_ARTIGOS = {"o", "a", "os", "as", "de", "do", "da", "dos", "das", "e", "la", "il", "le", "lo"}
_NUM_ROMANO = re.compile(r"^(?:\d+\.|[ivxlc]+\.?)$", re.IGNORECASE)
_CHAVE_NUMERO = re.compile(r"^(\d+)\.$")

_SINONIMOS_CARTAS = {
    "cavaleiro": ["mensageiro"],
    "cao": ["cachorro"],
    "carta": ["cartas"],
    "enamorados": ["amantes"],
    "eremita": ["heremita"],
    "julgamento": ["jugamento"],
}

_SINONIMOS_NAIPE = {"ouros": "ouro"}

_RANK = {
    "as": "01", "1": "01", "2": "02", "3": "03", "4": "04", "5": "05",
    "6": "06", "7": "07", "8": "08", "9": "09", "10": "10",
    "valete": "valete", "cavaleiro": "cavaleiro",
    "rainha": "rainha", "rei": "rei",
}

_PALAVRAS_BARALHO = ("cigano", "lenormand", "taro", "tarot", "sibilla", "sibila")

def _normalizar_texto(texto):
    txt = unicodedata.normalize("NFD", str(texto))
    txt = "".join(ch for ch in txt if unicodedata.category(ch) != "Mn")
    txt = txt.lower()
    return re.sub(r"[^a-z0-9]+", "", txt)

def _tokens(stem):
    partes = re.split(r"[^0-9A-Za-zÀ-ÖØ-öø-ÿ]+", str(stem))
    return [ _normalizar_texto(p) for p in partes if _normalizar_texto(p) ]

def _chaves_para_arquivo(stem):
    toks = _tokens(stem)
    if not toks:
        return []
    chaves = ["".join(toks)]
    sem_num_art = [t for t in toks if not t.isdigit() and t not in _ARTIGOS]
    if sem_num_art and sem_num_art != toks:
        chaves.append("".join(sem_num_art))
    return chaves

def _chaves_para_carta(nome):
    chaves = []
    for segmento in str(nome).split("/"):
        tokens = [t for t in segmento.split() if t]
        if not tokens:
            continue

        m = _CHAVE_NUMERO.match(tokens[0])
        if m:
            dig = m.group(1)
            chaves.append(dig.zfill(2))
            chaves.append(str(int(dig)))
            tokens = tokens[1:]
        elif _NUM_ROMANO.match(tokens[0]):
            tokens = tokens[1:]

        if "(" in segmento and ")" in segmento:
            dentro = segmento.split("(", 1)[1].rsplit(")", 1)[0]
            chave_dentro = _normalizar_texto(dentro)
            if chave_dentro:
                chaves.append(chave_dentro)
            segmento = segmento.split("(", 1)[0]
            tokens = [t for t in segmento.split() if t]

        if len(tokens) == 3 and tokens[1].lower() == "de":
            rank = _normalizar_texto(tokens[0])
            naipe = _normalizar_texto(tokens[2])
            naipe = _SINONIMOS_NAIPE.get(naipe, naipe)
            chaves.append(f"{naipe}{_RANK.get(rank, rank)}")

        nucleos = [
            _normalizar_texto(t) for t in tokens
            if _normalizar_texto(t) and _normalizar_texto(t) not in _ARTIGOS
        ]
        core = "".join(nucleos)
        if core:
            chaves.append(core)
            chaves.extend(_SINONIMOS_CARTAS.get(core, []))
        for nuc in nucleos:
            chaves.append(nuc)
            chaves.extend(_SINONIMOS_CARTAS.get(nuc, []))

    vistas = set()
    finais = []
    for c in chaves:
        if c and c not in vistas:
            vistas.add(c)
            finais.append(c)
    return finais

@st.cache_data(show_spinner=False)
def _mapa_imagens_cartas():
    indice = {}
    if not PASTA_CARTAS.exists():
        return indice
    for arquivo in sorted(PASTA_CARTAS.rglob("*")):
        if arquivo.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp"):
            pasta = _normalizar_texto(arquivo.parent.name)
            for chave in _chaves_para_arquivo(arquivo.stem):
                indice.setdefault(chave, []).append((str(arquivo), pasta))
    return indice

def _pasta_neutra(nome_pasta):
    return not any(palavra in nome_pasta for palavra in _PALAVRAS_BARALHO)

def obter_imagem_carta(nome_carta, oraculo):
    if not nome_carta or nome_carta == PLACEHOLDER_CARTA:
        return None
    indice = _mapa_imagens_cartas()
    if not indice:
        return None
    for chave in _chaves_para_carta(nome_carta):
        candidatos = indice.get(chave)
        if not candidatos:
            continue
        if oraculo.startswith("Baralho"):
            meus = [c for c in candidatos if ("cigano" in c[1] or "lenormand" in c[1])]
        elif oraculo.startswith("Sibilla"):
            meus = [c for c in candidatos if ("sibilla" in c[1] or "sibila" in c[1])]
        else:
            meus = [c for c in candidatos if ("taro" in c[1] or "tarot" in c[1])]
        neutros = [c for c in candidatos if _pasta_neutra(c[1])]
        escolha = meus or neutros
        if not escolha:
            continue
        try:
            return Image.open(escolha[0][0]).convert("RGB")
        except Exception:
            continue
    return None

# ==========================================
# IMAGENS DO BARALHO DE BÚZIOS
# ==========================================
def _abrir_imagem_buzios(nome_base):
    """Tenta abrir assets/cartas/buzios/{nome_base} em várias extensões."""
    pasta = PASTA_CARTAS / "buzios"
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        caminho = pasta / f"{nome_base}{ext}"
        if caminho.exists():
            try:
                return Image.open(caminho)
            except Exception:
                continue
    return None

def _imagem_carta_buzios(cid, estado):
    sufixo = "aberto" if str(estado).lower().startswith("ab") else "fechado"
    arte = _abrir_imagem_buzios(f"{cid:02d}_{sufixo}")
    if arte is not None:
        return arte.convert("RGB")
    return None

# ==========================================
# MEDALHÕES DECORATIVOS (assets/medalhoes/)
# ==========================================
@st.cache_data(show_spinner=False)
def _lista_medalhoes():
    if not PASTA_MEDALHOES.exists():
        return []
    return [
        str(p) for p in sorted(PASTA_MEDALHOES.glob("*"))
        if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")
    ]

def _medalhao_imagem(indice):
    lista = _lista_medalhoes()
    if not lista:
        return None
    try:
        return Image.open(lista[indice % len(lista)]).convert("RGBA")
    except Exception:
        return None

# ==========================================
# FUNÇÕES AUXILIARES - MESA VISUAL (PIL)
# ==========================================
def _fonte(tamanho):
    try:
        return ImageFont.load_default(size=tamanho)
    except Exception:
        return ImageFont.load_default()

def _layout_mesa(metodo, n_posicoes):
    if metodo == "Linha de 3 Cartas" and n_posicoes == 3:
        return [(500, 540), (800, 540), (1100, 540)], (240, 380)
    if metodo == "Linha de 5 Cartas" and n_posicoes == 5:
        return [(240, 540), (520, 540), (800, 540), (1080, 540), (1360, 540)], (220, 340)
    if metodo.startswith("Bloco de 9") and n_posicoes == 9:
        centros = []
        for y in (300, 540, 780):
            for x in (480, 800, 1120):
                centros.append((x, y))
        return centros, (190, 210)
    if metodo.startswith("Cruz") and n_posicoes == 5:
        return [(800, 540), (520, 540), (1080, 540), (800, 280), (800, 800)], (200, 300)
    if metodo.startswith("Pirâmide") and n_posicoes == 7:
        return [
            (800, 220),
            (520, 450), (800, 450), (1080, 450),
            (660, 680), (940, 680),
            (800, 890),
        ], (170, 200)
    if metodo.startswith("Ferradura") and n_posicoes == 7:
        return [
            (400, 700), (300, 500), (400, 300), (600, 200),
            (800, 300), (900, 500), (800, 700)
        ], (160, 240)
    if metodo.startswith("Grande Jogo") and n_posicoes == 12:
        centros = []
        for y in (300, 500, 700):
            for x in (400, 600, 800, 1000):
                centros.append((x, y))
        return centros, (140, 180)

    cols = 5 if n_posicoes <= 10 else 6
    rows = math.ceil(n_posicoes / cols)
    cell_h = 860 // rows
    card_h = max(120, min(300, cell_h - 40))
    card_w = int(card_h * 0.68)
    centros = []
    for i in range(n_posicoes):
        r, c = divmod(i, cols)
        x = 1600 // (cols + 1) * (c + 1)
        y = 140 + cell_h * r + cell_h // 2
        centros.append((x, y))
    return centros, (card_w, card_h)

def gerar_imagem_mesa(cartas_ordem, metodo, oraculo):
    largura, altura = 1600, 1000
    img = Image.new("RGB", (largura, altura), (28, 58, 48))
    draw = ImageDraw.Draw(img)

    draw.rectangle([18, 18, largura - 18, altura - 18], outline=(196, 168, 90), width=4)
    draw.rectangle([30, 30, largura - 30, altura - 30], outline=(196, 168, 90), width=2)

    fonte_titulo = _fonte(34)
    fonte_carta = _fonte(24)
    fonte_pos = _fonte(20)
    fonte_num = _fonte(34)

    titulo = f"{metodo}  -  {oraculo}"
    draw.text((largura // 2, 62), sanitizar_titulo_mesa(titulo), font=fonte_titulo, fill=(240, 230, 200), anchor="mm")

    centros, (cw, ch) = _layout_mesa(metodo, len(cartas_ordem))

    for idx, (carta, (cx, cy)) in enumerate(zip(cartas_ordem, centros), start=1):
        x0, y0 = cx - cw // 2, cy - ch // 2
        x1, y1 = cx + cw // 2, cy + ch // 2

        med = _medalhao_imagem(idx - 1)
        if med is not None:
            size = 72
            med_rs = med.resize((size, size))
            mx = cx - size // 2
            my = max(y0 - size - 12, 12)
            img.paste(med_rs, (mx, my), med_rs)
            draw.text((cx, my + size // 2), str(idx), font=fonte_num, fill=(252, 248, 235), anchor="mm")
        else:
            draw.text((cx, max(y0 - 14, 46)), f"Posicao {idx}", font=fonte_pos, fill=(220, 200, 140), anchor="mm")

        arte = obter_imagem_carta(carta, oraculo) if carta else None

        if arte is not None:
            draw.rounded_rectangle([x0 + 6, y0 + 8, x1 + 6, y1 + 8], radius=16, fill=(15, 30, 25))
            ratio = min(cw / arte.width, ch / arte.height)
            nw = max(1, int(arte.width * ratio))
            nh = max(1, int(arte.height * ratio))
            arte_rs = arte.resize((nw, nh))
            px, py = x0 + (cw - nw) // 2, y0 + (ch - nh) // 2
            img.paste(arte_rs, (px, py))
            draw.rounded_rectangle([x0, y0, x1, y1], radius=16, outline=(196, 168, 90), width=3)
        else:
            draw.rounded_rectangle([x0 + 6, y0 + 8, x1 + 6, y1 + 8], radius=16, fill=(15, 30, 25))
            draw.rounded_rectangle([x0, y0, x1, y1], radius=16, fill=(246, 240, 224), outline=(120, 90, 40), width=3)
            draw.rounded_rectangle([x0 + 8, y0 + 8, x1 - 8, y1 - 8], radius=10, outline=(196, 168, 90), width=2)
            nome = carta if carta else "(vazio)"
            linhas = []
            for parte in str(nome).split():
                if linhas and len(linhas[-1]) + len(parte) + 1 <= 14:
                    linhas[-1] += " " + parte
                else:
                    linhas.append(parte)
            lh = 30
            y_txt = cy - (len(linhas) - 1) * lh // 2
            for linha in linhas:
                draw.text((cx, y_txt), linha, font=fonte_carta, fill=(40, 30, 20), anchor="mm")
                y_txt += lh

    rodape = "Mesa gerada pelo Auxiliar de Cartomancia & Oraculos"
    draw.text((largura // 2, altura - 52), rodape, font=fonte_pos, fill=(200, 190, 160), anchor="mm")
    return img

def sanitizar_titulo_mesa(texto):
    return texto.replace("⏳", "*").replace("—", "-").replace("♠", "").replace("♥", "").replace("♣", "").replace("♦", "")

# ==========================================
# MESA VISUAL DOS BÚZIOS (PIL)
# ==========================================
def gerar_imagem_mesa_buzios(jogada, apoio=None, tema=""):
    """Desenha a mesa circular de búzios com as cartas caídas em cada casa."""
    L = 1500
    fundo = _abrir_imagem_buzios("mesa_fundo")
    if fundo is not None:
        img = fundo.convert("RGB").resize((L, L))
    else:
        img = Image.new("RGB", (L, L), (26, 46, 38))
        draw_s = ImageDraw.Draw(img)
        draw_s.ellipse([90, 90, L - 90, L - 90], outline=(196, 168, 90), width=6)
        draw_s.ellipse([L // 2 - 150, L // 2 - 150, L // 2 + 150, L // 2 + 150],
                       outline=(196, 168, 90), width=4)
        for i, nome_casa in enumerate(BUZIOS_CASAS):
            x, y = _BUZIOS_POSICOES[i]
            draw_s.text((x, y - 120), sanitizar_titulo_mesa(nome_casa.split("·")[-1].strip()),
                        font=_fonte(26), fill=(230, 215, 180), anchor="mm")

    draw = ImageDraw.Draw(img)
    fonte_ent = _fonte(20)
    fonte_leg = _fonte(17)

    por_casa = {}
    for item in jogada:
        por_casa.setdefault(item["casa"], []).append(item)

    for casa_idx, itens in por_casa.items():
        cx, cy = _BUZIOS_POSICOES[casa_idx]
        for k, item in enumerate(itens):
            dx = ((k % 3) - 1) * 160
            dy = (k // 3) * 250 - 40
            px, py = cx + dx, cy + dy
            cw, chh = 140, 235
            x0, y0 = px - cw // 2, py - chh // 2
            x1, y1 = px + cw // 2, py + chh // 2

            arte = _imagem_carta_buzios(item["carta"], item["estado"])
            draw.rounded_rectangle([x0 + 5, y0 + 7, x1 + 5, y1 + 7], radius=14, fill=(12, 24, 20))
            if arte is not None:
                ratio = min(cw / arte.width, chh / arte.height)
                nw = max(1, int(arte.width * ratio))
                nh = max(1, int(arte.height * ratio))
                rs = arte.resize((nw, nh))
                img.paste(rs, (px - nw // 2, py - nh // 2))
            else:
                draw.rounded_rectangle([x0, y0, x1, y1], radius=14,
                                       fill=(246, 240, 224), outline=(120, 90, 40), width=3)
                d = BUZIOS_DADOS.get(item["carta"])
                nome = d["entidade"] if d else f"Carta {item['carta']}"
                draw.text((px, py), nome, font=fonte_leg, fill=(40, 30, 20), anchor="mm")

            cor_estado = (46, 204, 113) if item["estado"] == "Aberto" else (231, 76, 60)
            draw.rounded_rectangle([x0, y0, x1, y1], radius=14, outline=cor_estado, width=5)
            if item["carta"] == 20:
                draw.rounded_rectangle([x0 - 6, y0 - 6, x1 + 6, y1 + 6], radius=16,
                                       outline=(255, 215, 90), width=6)

            d = BUZIOS_DADOS.get(item["carta"])
            nome_curto = d["entidade"].split(" ")[0] if d else "?"
            draw.text((px, y1 + 16), nome_curto, font=fonte_ent, fill=(250, 244, 226), anchor="mm")
            draw.ellipse([x1 - 16, y0 + 4, x1 - 2, y0 + 18], fill=cor_estado)

    if apoio:
        draw.text((60, L - 150), "APOIO:", font=fonte_ent, fill=(250, 244, 226), anchor="lm")
        for k, item in enumerate(apoio):
            px = 220 + k * 150
            py = L - 150
            cw, chh = 100, 168
            x0, y0 = px - cw // 2, py - chh // 2
            x1, y1 = px + cw // 2, py + chh // 2
            arte = _imagem_carta_buzios(item["carta"], item["estado"])
            if arte is not None:
                ratio = min(cw / arte.width, chh / arte.height)
                nw = max(1, int(arte.width * ratio))
                nh = max(1, int(arte.height * ratio))
                img.paste(arte.resize((nw, nh)), (px - nw // 2, py - nh // 2))
            cor_estado = (46, 204, 113) if item["estado"] == "Aberto" else (231, 76, 60)
            draw.rounded_rectangle([x0, y0, x1, y1], radius=10, outline=cor_estado, width=4)

    borda = _abrir_imagem_buzios("mesa_borda")
    if borda is not None and borda.mode in ("RGBA", "LA"):
        borda_rs = borda.convert("RGBA").resize((L, L))
        img.paste(borda_rs, (0, 0), borda_rs)

    draw = ImageDraw.Draw(img)
    draw.text((L - 40, L - 30), "Mesa de Buzios - Lunara Terapias",
              font=_fonte(18), fill=(210, 195, 160), anchor="rm")
    return img

# ==========================================
# v5.2: TABELAS BASE DO REGISTRO DE BÚZIOS
# ==========================================
def _df_jogada_vazio():
    return pd.DataFrame({
        "Carta": [_rotulo_buzios(c) for c in BUZIOS_CARTAS_MESA],
        "Estado": ["Não caiu"] * len(BUZIOS_CARTAS_MESA),
        "Casa": ["—"] * len(BUZIOS_CARTAS_MESA),
    })

def _df_apoio_vazio():
    return pd.DataFrame({
        "Apoio": ["—", "—", "—"],
        "Estado": ["Aberto", "Aberto", "Aberto"],
    })

# ==========================================
# CONFIGURAÇÃO DA PÁGINA
# ==========================================
st.set_page_config(
    page_title="Auxiliar de Cartomancia & Oráculos",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded",
)

if "interpretacao_atual" not in st.session_state:
    st.session_state.interpretacao_atual = None
if "dados_leitura_atual" not in st.session_state:
    st.session_state.dados_leitura_atual = None
if "mesa_img" not in st.session_state:
    st.session_state.mesa_img = None
if "comparativa_id" not in st.session_state:
    st.session_state.comparativa_id = None
if "comparativa_resultado" not in st.session_state:
    st.session_state.comparativa_resultado = None
if "buz_mesa" not in st.session_state:
    st.session_state.buz_mesa = None
if "buz_resultado" not in st.session_state:
    st.session_state.buz_resultado = None
if "buz_dados" not in st.session_state:
    st.session_state.buz_dados = None
if "buz_df" not in st.session_state:
    st.session_state.buz_df = _df_jogada_vazio()
if "buz_df_apoio" not in st.session_state:
    st.session_state.buz_df_apoio = _df_apoio_vazio()

# ==========================================
# BARRA LATERAL (SIDEBAR)
# ==========================================
with st.sidebar:
    st.markdown("# 🔮 Oráculo")
    st.markdown("---")

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

    with st.expander("🃏 Oráculo e Método", expanded=True):
        oracle_choice = st.selectbox(
            "Sistema Simbólico",
            options=[
                "Baralho Cigano (Lenormand)",
                "Tarô Tradicional",
                "Sibilla Italiana (54 cartas)",
            ],
            index=0,
        )

        spread_choice = st.selectbox(
            "Disposição da Tiragem",
            options=list(ESTRUTURA_POSICOES.keys()) + ["Livre / Outro"],
            index=0,
        )
        if spread_choice == "Livre / Outro":
            num_free_cards = st.number_input(
                "Quantidade de Cartas:", min_value=1, max_value=54, value=3, step=1
            )
        else:
            num_free_cards = 0

    with st.expander("🎨 Tom da Leitura", expanded=True):
        tom_leitura = st.selectbox(
            "Estilo de Interpretação",
            options=list(SYSTEM_INSTRUCTIONS.keys()),
            index=0,
        )

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

    if LUMINA_URL:
        st.link_button(
            "🎪 Abrir Sala de Estudo Lumina",
            LUMINA_URL,
            use_container_width=True,
        )
        st.caption(
            "O Lumina é o app companheiro de estudo interativo "
            "(tabuleiro, geometria e Mentor do Cigano)."
        )
    else:
        st.caption(
            "🎪 Sala de Estudo: defina LUMINA_URL no topo do app.py "
            "para ativar o atalho do Lumina."
        )

    st.markdown(
        f"<small style='color: #888;'>Serviço via Google Gemini API (<code>{MODELO_GEMINI}</code>).</small>",
        unsafe_allow_html=True,
    )

# ==========================================
# ÁREA PRINCIPAL - COM TABS
# ==========================================
st.title("🔮 Auxiliar de Cartomancia & Oráculos")
st.markdown(
    "##### *Interpretação oracular sintática, ética e profunda com Google Gemini*"
)

tab_nova, tab_buzios, tab_historico, tab_stats, tab_manuais = st.tabs(
    ["🆕 Nova Leitura", "🐚 Búzios", "📚 Histórico", "📊 Estatísticas", "📖 Manuais"]
)

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
            - **Sibilla Italiana:** 54 cartas com polaridade e fichas técnicas; cenas cotidianas lidas como narrativa.
            - **Búzios (Ifá):** 16 búzios-cartas em 7 casas + Moeda; aberto fala, fechado recolhe (aba 🐚).
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
            "📷 Foto da Mesa / Tiragem (Opcional - Formatos: JPG, JPEG, PNG)",
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
        st.markdown("**2. Cartas de Cada Posição (manual ou sorteio) ***")

        if oracle_choice.startswith("Sibilla") and not SIBILLA_DADOS:
            st.warning(
                "Arquivo `sibilla.json` não encontrado na pasta do projeto. "
                "Salve o JSON das 54 fichas como `sibilla.json` ao lado do `app.py`."
            )

        if oracle_choice.startswith("Baralho"):
            opcoes_cartas = CARTAS_CIGANO
        elif oracle_choice.startswith("Sibilla"):
            opcoes_cartas = CARTAS_SIBILLA
        else:
            opcoes_cartas = CARTAS_TARO

        if spread_choice in ESTRUTURA_POSICOES:
            rotulos_posicoes = ESTRUTURA_POSICOES[spread_choice]
        else:
            rotulos_posicoes = [f"Carta {i+1}" for i in range(int(num_free_cards))]

        if st.session_state.get("sortear_agora"):
            st.session_state["sortear_agora"] = False
            pool = [c for c in opcoes_cartas if c != PLACEHOLDER_CARTA]
            amostra = random.sample(pool, k=len(rotulos_posicoes))
            for rotulo, carta in zip(rotulos_posicoes, amostra):
                st.session_state[f"card_{rotulo}"] = carta
            st.session_state["mesa_img"] = None

        if st.session_state.get("limpar_cartas_agora"):
            st.session_state["limpar_cartas_agora"] = False
            for rotulo in rotulos_posicoes:
                st.session_state[f"card_{rotulo}"] = PLACEHOLDER_CARTA
            st.session_state["mesa_img"] = None

        cartas_selecionadas = {}
        with st.container(height=380, border=True):
            for rotulo in rotulos_posicoes:
                key = f"card_{rotulo}"
                valor_atual = st.session_state.get(key, PLACEHOLDER_CARTA)
                usadas_antes = list(cartas_selecionadas.values())

                if valor_atual in usadas_antes:
                    valor_atual = PLACEHOLDER_CARTA
                    st.session_state[key] = valor_atual

                pool = [c for c in opcoes_cartas if c != PLACEHOLDER_CARTA and c not in usadas_antes]
                opcoes = [PLACEHOLDER_CARTA] + pool

                if valor_atual not in opcoes:
                    valor_atual = PLACEHOLDER_CARTA
                    st.session_state[key] = valor_atual

                escolha = st.selectbox(
                    rotulo,
                    options=opcoes,
                    index=opcoes.index(valor_atual),
                    key=key,
                    help="Cartas já usadas em outras posições não aparecem aqui.",
                )
                if escolha != PLACEHOLDER_CARTA:
                    cartas_selecionadas[rotulo] = escolha

        st.caption("🔒 Anti-duplicata ativo: cada carta só pode aparecer uma vez na tiragem.")

        col_b1, col_b2, col_b3 = st.columns(3)
        with col_b1:
            if st.button(
                "🎲 Sortear Cartas",
                use_container_width=True,
                help="Embaralha o baralho e preenche todas as posições aleatoriamente",
            ):
                st.session_state["sortear_agora"] = True
                st.rerun()
        with col_b2:
            if st.button("🧹 Limpar Seleção", use_container_width=True):
                st.session_state["limpar_cartas_agora"] = True
                st.rerun()
        with col_b3:
            if st.button(
                "🖼️ Gerar Mesa Visual",
                use_container_width=True,
                help="Desenha a mesa com as cartas (e medalhões) para o relatório",
            ):
                if not cartas_selecionadas:
                    st.warning("Selecione ou sorteie ao menos uma carta antes de gerar a mesa.")
                else:
                    ordem = [cartas_selecionadas.get(r) for r in rotulos_posicoes]
                    st.session_state["mesa_img"] = gerar_imagem_mesa(
                        ordem, spread_choice, oracle_choice
                    )

        if st.session_state.get("mesa_img") is not None:
            st.image(
                st.session_state["mesa_img"],
                caption="🖼️ Mesa virtual da tiragem",
                use_container_width=True,
            )

    analyze_button = st.button(
        "🔮 Analisar Tiragem",
        type="primary",
        use_container_width=True
    )

    if analyze_button:
        active_api_key = obter_chave_api()

        erros = []
        if not active_api_key:
            erros.append(
                "Chave de API não configurada. Crie o arquivo `.streamlit/secrets.toml` "
                "com `GEMINI_API_KEY = \"sua_chave\"` (local) ou cadastre em "
                "Settings → Secrets no Streamlit Cloud."
            )
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
            try:
                client = genai.Client(api_key=active_api_key)

                texto_cartas_formatado = "\n".join(
                    [f"- {pos}: {carta}" for pos, carta in cartas_selecionadas.items()]
                )

                bloco_sibilla = ""
                if oracle_choice.startswith("Sibilla") and SIBILLA_DADOS:
                    linhas_ficha = []
                    for pos, carta in cartas_selecionadas.items():
                        d = _ficha_sibilla(carta)
                        if not d:
                            continue
                        linhas_ficha.append(
                            f"- {pos}: {d.get('titulo','')} ({d.get('carta','')}) | "
                            f"Polaridade: {d.get('polaridade','')}\n"
                            f"  Essência: {d.get('legenda_curta','')}\n"
                            f"  Significado geral: {d.get('significado_geral','')}\n"
                            f"  Leitura favorável: {d.get('posicao_correta','')}\n"
                            f"  Leitura desafiadora: {d.get('posicao_invertida','')}\n"
                            f"  Combinações clássicas: {d.get('combinacoes','')}"
                        )
                    if linhas_ficha:
                        bloco_sibilla = (
                            "\n\nFICHAS TÉCNICAS DAS CARTAS SIBILLA SORTEADAS "
                            "(use-as como alicerce da interpretação):\n"
                            + "\n".join(linhas_ficha)
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
{bloco_sibilla}

Aplique rigorosamente todas as regras oraculares da system instruction.
"""

                contents_payload = []
                if image_for_gemini is not None:
                    contents_payload.append(image_for_gemini)
                contents_payload.append(user_prompt_text)

                config_gemini = types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTIONS[tom_leitura],
                    temperature=0.7,
                )

                with st.status("✨ Consultando os arcanos com o Google Gemini...", expanded=False) as status:
                    def _atualizar_progresso(tentativa, total):
                        if total > 1:
                            status.update(
                                label=f"✨ Tentativa {tentativa} de {total} — "
                                      f"picos de demanda podem exigir paciência..."
                            )

                    response = chamar_gemini(
                        client,
                        contents_payload,
                        config_gemini,
                        ao_tentar=_atualizar_progresso,
                    )
                    status.update(label="✨ Interpretação concluída", state="complete")

                if response and response.text:
                    interpretation_text = response.text
                    data_hora = datetime.now().strftime("%d/%m/%Y %H:%M")

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

                    save_reading(dados_leitura)

                    st.success(f"✨ Tiragem interpretada e salva no histórico ({data_hora})!")
                else:
                    st.error("❌ Não foi possível gerar a resposta. Tente novamente.")

            except Exception as e:
                if eh_erroro_transitorio(e):
                    st.error(
                        "❌ **O oráculo está sob alta demanda (erro 503/429).** "
                        "O app já tentou várias vezes automaticamente. "
                        "Aguarde 1–2 minutos e clique em **Analisar Tiragem** novamente — "
                        "picos de demanda do Google Gemini costumam passar rápido."
                    )
                else:
                    st.error(f"❌ **Erro durante a consulta:** `{str(e)}`")

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
            st.download_button(
                label="📄 Baixar Interpretação (.txt)",
                data=st.session_state.interpretacao_atual.encode("utf-8-sig"),
                file_name=f"leitura_{_slug(dados['nome_consulente'])}_{_carimbo(dados['data_hora'])}.txt",
                mime="text/plain; charset=utf-8",
                use_container_width=True,
            )

        with col_exp2:
            try:
                mesa_para_pdf = st.session_state.get("mesa_img")
                if mesa_para_pdf is None and dados.get("cartas"):
                    mesa_para_pdf = gerar_imagem_mesa(
                        list(dados["cartas"].values()),
                        dados.get("metodo", ""),
                        dados.get("oraculo", ""),
                    )

                dados_orac_pdf = {
                    "nome": nome_oraculista,
                    "contato": contato_oraculista,
                } if modo_profissional else None

                pdf_bytes = gerar_pdf_leitura(
                    dados_leitura=dados,
                    modo_profissional=modo_profissional,
                    dados_oraculista=dados_orac_pdf,
                    imagem_mesa=mesa_para_pdf,
                )

                st.download_button(
                    label="📕 Baixar Relatório (.pdf)",
                    data=pdf_bytes,
                    file_name=f"relatorio_{_slug(dados['nome_consulente'])}_{_carimbo(dados['data_hora'])}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            except Exception as e:
                st.error(f"Erro ao gerar PDF: {e}")

        with st.expander("📋 Ver texto formatado para cópia rápida"):
            st.code(st.session_state.interpretacao_atual, language="markdown")

# ========================
# TAB 2 - BÚZIOS (v5.2: tabela por número)
# ========================
with tab_buzios:
    st.markdown("### 🐚 Mesa de Búzios (Merindilogun · tradição Ifá)")
    st.caption(
        "Ferramenta de estudo e apoio à interpretação. Não substitui o jogo de um sacerdote "
        "iniciado, nem orientações médicas, jurídicas ou psicológicas profissionais."
    )

    if not BUZIOS_DADOS:
        st.warning(
            "Arquivo `buzios.json` não encontrado na raiz do projeto. "
            "Salve o JSON das 46 fichas (23 cartas × aberto/fechado) ao lado do `app.py`."
        )
    else:
        # ---------- Tema ----------
        col_t1, col_t2 = st.columns([2, 3])
        with col_t1:
            tema_buzios = st.selectbox("Tema da leitura", options=TEMAS_BUZIOS, key="buz_tema")
        with col_t2:
            tema_livre_buzios = st.text_input(
                "Descreva o tema (quando 'Outro')",
                key="buz_tema_livre",
                disabled=(tema_buzios != TEMAS_BUZIOS[-1]),
            )

        # ---------- Registro da jogada: tabela por número ----------
        st.markdown("#### 🎲 Registro da jogada — carta por carta, em ordem de número")
        st.caption(
            "Para cada carta que **caiu na mesa**, marque **Aberto** ou **Fechado** e a **casa** onde caiu. "
            "Deixe **Não caiu** nas demais. Exatamente **16** devem cair, e a **20 · Consulente** "
            "precisa estar entre elas (ela marca o ponto do consulente). "
            "Ex.: *01 · Exu — Aberto — Casa 6 · Iemanjá*."
        )

        df_jogada = st.data_editor(
            st.session_state.buz_df,
            num_rows="fixed",
            hide_index=True,
            use_container_width=True,
            key="buz_editor",
            column_config={
                "Carta": st.column_config.TextColumn("Carta", disabled=True, width="medium"),
                "Estado": st.column_config.SelectboxColumn(
                    "Estado",
                    options=["Não caiu", "Aberto", "Fechado"],
                    required=True,
                ),
                "Casa": st.column_config.SelectboxColumn(
                    "Casa onde caiu",
                    options=["—"] + BUZIOS_CASAS,
                    required=True,
                ),
            },
        )

        st.markdown("#### 🃏 Cartas de apoio (Zé Pilintra — fora dos 16)")
        df_apoio = st.data_editor(
            st.session_state.buz_df_apoio,
            num_rows="fixed",
            hide_index=True,
            use_container_width=True,
            key="buz_editor_apoio",
            column_config={
                "Apoio": st.column_config.SelectboxColumn(
                    "Carta de apoio",
                    options=["—"] + [_rotulo_buzios(c) for c in BUZIOS_CARTAS_APOIO],
                    required=True,
                ),
                "Estado": st.column_config.SelectboxColumn(
                    "Estado",
                    options=["Aberto", "Fechado"],
                    required=True,
                ),
            },
        )

        col_x1, col_x2 = st.columns(2)
        with col_x1:
            btn_exemplo_buz = st.button(
                "🎲 Preencher jogada-exemplo", use_container_width=True,
                help="Gera uma jogada válida aleatória para teste/estudo",
            )
        with col_x2:
            btn_limpar_buz = st.button("🧹 Limpar jogada", use_container_width=True)

        if btn_exemplo_buz:
            ids_ex = random.sample([c for c in BUZIOS_CARTAS_MESA if c != 20], 15) + [20]
            novo_df = _df_jogada_vazio()
            for cid in ids_ex:
                linha = BUZIOS_CARTAS_MESA.index(cid)
                novo_df.loc[linha, "Estado"] = random.choice(["Aberto", "Fechado"])
                novo_df.loc[linha, "Casa"] = random.choice(BUZIOS_CASAS)
            st.session_state.buz_df = novo_df
            apoio_ex = random.choice(BUZIOS_CARTAS_APOIO)
            novo_apoio = _df_apoio_vazio()
            novo_apoio.loc[0, "Apoio"] = _rotulo_buzios(apoio_ex)
            novo_apoio.loc[0, "Estado"] = random.choice(["Aberto", "Fechado"])
            st.session_state.buz_df_apoio = novo_apoio
            st.session_state.pop("buz_editor", None)
            st.session_state.pop("buz_editor_apoio", None)
            st.session_state["buz_resultado"] = None
            st.session_state["buz_mesa"] = None
            st.rerun()

        if btn_limpar_buz:
            st.session_state.buz_df = _df_jogada_vazio()
            st.session_state.buz_df_apoio = _df_apoio_vazio()
            st.session_state.pop("buz_editor", None)
            st.session_state.pop("buz_editor_apoio", None)
            st.session_state["buz_resultado"] = None
            st.session_state["buz_mesa"] = None
            st.rerun()

        st.markdown("---")

        col_a1, col_a2 = st.columns(2)
        with col_a1:
            btn_mesa_buz = st.button("🖼️ Gerar Mesa Visual", type="secondary", use_container_width=True)
        with col_a2:
            btn_interp_buz = st.button("🐚 Interpretar Jogada", type="primary", use_container_width=True)

        # ---------- montagem da jogada a partir da tabela ----------
        jogada_buz = []
        casas_faltando = []
        for idx_linha, row in df_jogada.iterrows():
            if row["Estado"] in ("Aberto", "Fechado"):
                cid = BUZIOS_CARTAS_MESA[idx_linha]
                if row["Casa"] == "—":
                    casas_faltando.append(_rotulo_buzios(cid))
                    continue
                jogada_buz.append({
                    "carta": cid,
                    "estado": row["Estado"],
                    "casa": BUZIOS_CASAS.index(row["Casa"]),
                })

        apoio_buz = []
        vistos_apoio = set()
        for _, row in df_apoio.iterrows():
            if row["Apoio"] != "—":
                cid = _id_do_rotulo_buzios(row["Apoio"])
                if cid and cid not in vistos_apoio:
                    vistos_apoio.add(cid)
                    apoio_buz.append({"carta": cid, "estado": row["Estado"]})

        if btn_mesa_buz:
            if len(jogada_buz) == 0:
                st.warning("Registre ao menos um búzio caído antes de gerar a mesa.")
            else:
                st.session_state["buz_mesa"] = gerar_imagem_mesa_buzios(
                    jogada_buz, apoio_buz, tema_buzios
                )

        if st.session_state.get("buz_mesa") is not None:
            st.image(st.session_state["buz_mesa"], caption="🐚 Mesa da jogada", use_container_width=True)

        if btn_interp_buz:
            erros_buz = []
            if casas_faltando:
                erros_buz.append(
                    "Defina a casa de: " + ", ".join(casas_faltando) + "."
                )
            if len(jogada_buz) != 16:
                erros_buz.append(
                    f"A jogada precisa de exatamente 16 búzios caídos (atualmente: {len(jogada_buz)})."
                )
            ids_jogados = [j["carta"] for j in jogada_buz]
            if 20 not in ids_jogados:
                erros_buz.append(
                    "A carta 20 (Consulente) precisa estar entre as 16 caídas — ela marca o ponto do consulente."
                )
            chave_buz = obter_chave_api()
            if not chave_buz:
                erros_buz.append("Chave de API não configurada (secrets.toml / Secrets do Cloud).")

            if erros_buz:
                for eb in erros_buz:
                    st.error(f"⚠️ {eb}")
            else:
                tot_ab = sum(1 for j in jogada_buz if j["estado"] == "Aberto")
                tot_fe = 16 - tot_ab
                cont_casa = Counter(j["casa"] for j in jogada_buz)
                vazias = [idx for idx in range(8) if idx not in cont_casa]
                consul = next(j for j in jogada_buz if j["carta"] == 20)

                linhas_casa = []
                for idx in range(8):
                    itens = [j for j in jogada_buz if j["casa"] == idx]
                    if not itens:
                        continue
                    linhas_casa.append(f"{BUZIOS_CASAS[idx]}:")
                    for j in itens:
                        d = BUZIOS_DADOS.get(j["carta"], {})
                        ficha = _ficha_buzios(j["carta"], j["estado"]) or {}
                        linhas_casa.append(
                            f"  - {d.get('entidade', '?')} — {j['estado'].upper()} "
                            f"({ficha.get('palavra', '')}): \"{ficha.get('mensagem', '')}\""
                        )

                linhas_apoio = []
                for j in apoio_buz:
                    d = BUZIOS_DADOS.get(j["carta"], {})
                    ficha = _ficha_buzios(j["carta"], j["estado"]) or {}
                    linhas_apoio.append(
                        f"- {d.get('entidade', '?')} — {j['estado'].upper()} "
                        f"({ficha.get('palavra', '')}): \"{ficha.get('mensagem', '')}\""
                    )

                f_cons = _ficha_buzios(20, consul["estado"]) or {}
                tema_final = tema_livre_buzios.strip() if tema_buzios == TEMAS_BUZIOS[-1] else tema_buzios

                prompt_buz = f"""
TEMA DA LEITURA: {tema_final}

DISTRIBUIÇÃO DOS 16 BÚZIOS NA MESA:
{chr(10).join(linhas_casa)}

CASAS SEM BÚZIOS (domínios adormecidos): {', '.join(BUZIOS_CASAS[i] for i in vazias) if vazias else 'nenhuma'}

CLIMA: {tot_ab} abertos / {tot_fe} fechados.

PONTO DO CONSULENTE: a carta Consulente caiu em {BUZIOS_CASAS[consul['casa']]}, {consul['estado'].upper()}
— ficha: {f_cons.get('palavra', '')}: "{f_cons.get('mensagem', '')}"

CARTAS DE APOIO (Zé Pilintra, fora dos 16):
{chr(10).join(linhas_apoio) if linhas_apoio else '(nenhuma carta de apoio tirada)'}

Interprete a jogada conforme as regras da system instruction, cruzando clima, casas,
ponto do consulente e apoios com o tema perguntado.
"""

                try:
                    client_buz = genai.Client(api_key=chave_buz)
                    with st.spinner("🐚 Os búzios estão falando..."):
                        resp_buz = chamar_gemini(
                            client_buz,
                            prompt_buz,
                            types.GenerateContentConfig(
                                system_instruction=SYSTEM_INSTRUCTION_BUZIOS,
                                temperature=0.7,
                            ),
                        )
                    if resp_buz and resp_buz.text:
                        st.session_state["buz_resultado"] = resp_buz.text
                        if st.session_state.get("buz_mesa") is None:
                            st.session_state["buz_mesa"] = gerar_imagem_mesa_buzios(
                                jogada_buz, apoio_buz, tema_buzios
                            )
                        cartas_hist = {}
                        for n, j in enumerate(jogada_buz, start=1):
                            d = BUZIOS_DADOS.get(j["carta"], {})
                            cartas_hist[f"Búzio {n:02d} · {BUZIOS_CASAS[j['casa']]}"] = \
                                f"{d.get('entidade', '?')} ({j['estado']})"
                        for n, j in enumerate(apoio_buz, start=1):
                            d = BUZIOS_DADOS.get(j["carta"], {})
                            cartas_hist[f"Apoio {n}"] = f"{d.get('entidade', '?')} ({j['estado']})"

                        st.session_state["buz_dados"] = {
                            "data_hora": datetime.now().strftime("%d/%m/%Y %H:%M"),
                            "nome_consulente": nome_consulente,
                            "signo_consulente": signo_consulente,
                            "modo_atendimento": modo_atendimento,
                            "oraculo": "Búzios (Ifá)",
                            "metodo": f"Mesa de Búzios · {tema_final}",
                            "tom_leitura": "Mentor de Búzios",
                            "pergunta": tema_final,
                            "cartas": cartas_hist,
                            "interpretacao": resp_buz.text,
                        }
                        save_reading(st.session_state["buz_dados"])
                        st.rerun()
                    else:
                        st.error("❌ Não foi possível gerar a interpretação.")
                except Exception as e:
                    if eh_erroro_transitorio(e):
                        st.error(
                            "❌ **Alta demanda no Gemini (503/429).** "
                            "Aguarde 1–2 minutos e tente novamente."
                        )
                    else:
                        st.error(f"❌ **Erro na consulta:** `{str(e)}`")

        # ---------- resultado ----------
        if st.session_state.get("buz_resultado") and st.session_state.get("buz_dados"):
            st.markdown("---")
            st.markdown("## 🐚 Leitura da Jogada")
            with st.container(border=True):
                st.markdown(st.session_state["buz_resultado"])

            st.markdown("### 💾 Exportar")
            col_e1, col_e2 = st.columns(2)
            with col_e1:
                st.download_button(
                    "📄 Baixar leitura (.txt)",
                    data=st.session_state["buz_resultado"].encode("utf-8-sig"),
                    file_name=f"buzios_{_slug(st.session_state['buz_dados']['nome_consulente'])}_{_carimbo(st.session_state['buz_dados']['data_hora'])}.txt",
                    mime="text/plain; charset=utf-8",
                    use_container_width=True,
                )
            with col_e2:
                try:
                    pdf_buz = gerar_pdf_leitura(
                        dados_leitura=st.session_state["buz_dados"],
                        modo_profissional=modo_profissional,
                        dados_oraculista={"nome": nome_oraculista, "contato": contato_oraculista} if modo_profissional else None,
                        imagem_mesa=st.session_state.get("buz_mesa"),
                    )
                    st.download_button(
                        "📕 Baixar relatório (.pdf)",
                        data=pdf_buz,
                        file_name=f"buzios_{_slug(st.session_state['buz_dados']['nome_consulente'])}_{_carimbo(st.session_state['buz_dados']['data_hora'])}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                    )
                except Exception as e:
                    st.error(f"Erro ao gerar PDF: {e}")

# ========================
# TAB 3 - HISTÓRICO + COMPARATIVA TEMPORAL
# ========================
with tab_historico:
    st.markdown("### 📚 Leituras Salvas")
    st.markdown(
        "Reabra leituras anteriores, exclua registros ou use o botão **⏳ Reavaliar** "
        "para uma Análise Comparativa Temporal (como a situação se desdobrou)."
    )

    if st.session_state.get("comparativa_id"):
        base = load_reading(st.session_state["comparativa_id"])
        if not base:
            st.session_state["comparativa_id"] = None
        else:
            with st.container(border=True):
                st.markdown(f"### ⏳ Reavaliando a leitura de {base['data_hora']}")
                st.caption(f"**Consulente:** {base['nome_consulente'] or 'Não informado'}")
                st.caption(f"**Pergunta original:** {base['pergunta']}")
                st.caption(
                    "**Cartas:** " + " | ".join(f"{k}: {v}" for k, v in base["cartas"].items())
                )
                with st.expander("📜 Interpretação original"):
                    st.markdown(base["interpretacao"])

                relato_atual = st.text_area(
                    "Como está a situação hoje? O que mudou desde a leitura original?",
                    height=140,
                    key="comp_relato",
                    placeholder="Ex.: 'O contrato que estava travado foi assinado, mas surgiu uma nova tensão com o sócio...'",
                )

                c_ok, c_cancel = st.columns([3, 1])
                with c_ok:
                    btn_comp = st.button(
                        "🔮 Analisar Desdobramento", type="primary", use_container_width=True
                    )
                with c_cancel:
                    if st.button("✖ Cancelar", use_container_width=True):
                        st.session_state["comparativa_id"] = None
                        st.session_state["comparativa_resultado"] = None
                        st.rerun()

                if btn_comp:
                    if not relato_atual.strip():
                        st.warning("Descreva brevemente o momento atual antes de analisar.")
                    else:
                        chave = obter_chave_api()
                        if not chave:
                            st.error("Chave de API não configurada.")
                        else:
                            try:
                                client = genai.Client(api_key=chave)
                                cartas_base = "\n".join(
                                    f"- {k}: {v}" for k, v in base["cartas"].items()
                                )
                                prompt_comp = f"""
LEITURA ORIGINAL:
- Data: {base['data_hora']}
- Oráculo: {base['oraculo']} | Método: {base['metodo']}
- Pergunta: {base['pergunta']}
- Cartas:
{cartas_base}
- Interpretação da época:
{base['interpretacao']}

RELATO ATUAL DO CONSULENTE:
{relato_atual.strip()}

Realize a Análise Comparativa Temporal completa.
"""
                                with st.spinner("⏳ Comparando passado e presente..."):
                                    resp = chamar_gemini(
                                        client,
                                        prompt_comp,
                                        types.GenerateContentConfig(
                                            system_instruction=SYSTEM_INSTRUCTION_COMPARATIVA,
                                            temperature=0.6,
                                        ),
                                    )
                                if resp and resp.text:
                                    st.session_state["comparativa_resultado"] = resp.text
                                    dados_comp = {
                                        "data_hora": datetime.now().strftime("%d/%m/%Y %H:%M"),
                                        "nome_consulente": base["nome_consulente"],
                                        "signo_consulente": base["signo_consulente"],
                                        "modo_atendimento": base["modo_atendimento"],
                                        "oraculo": base["oraculo"],
                                        "metodo": f"⏳ Desdobramento Temporal (leitura #{base['id']})",
                                        "tom_leitura": "Comparativa Temporal",
                                        "pergunta": f"[Desdobramento] {base['pergunta']}",
                                        "cartas": base["cartas"],
                                        "interpretacao": resp.text,
                                    }
                                    save_reading(dados_comp)
                                    st.rerun()
                                else:
                                    st.error("❌ Não foi possível gerar a comparação.")
                            except Exception as e:
                                if eh_erroro_transitorio(e):
                                    st.error(
                                        "❌ **Alta demanda no Gemini (503/429).** "
                                        "Aguarde 1–2 minutos e tente novamente."
                                    )
                                else:
                                    st.error(f"❌ **Erro na comparação:** `{str(e)}`")

                if st.session_state.get("comparativa_resultado"):
                    st.markdown("#### 📖 Análise do Desdobramento")
                    st.markdown(st.session_state["comparativa_resultado"])
                    st.caption(
                        "💾 Esta análise foi salva automaticamente no Histórico "
                        "como 'Desdobramento Temporal'."
                    )
                    st.download_button(
                        "📄 Baixar análise (.txt)",
                        data=st.session_state["comparativa_resultado"].encode("utf-8-sig"),
                        file_name=f"desdobramento_{_carimbo(datetime.now().strftime('%d/%m/%Y %H:%M'))}.txt",
                        mime="text/plain; charset=utf-8",
                    )
                    if st.button("🔄 Concluir e fechar análise"):
                        st.session_state["comparativa_id"] = None
                        st.session_state["comparativa_resultado"] = None
                        st.rerun()

    leituras = list_readings()

    if not leituras:
        st.info("📭 Nenhuma leitura salva ainda. Realize sua primeira análise na aba **Nova Leitura**.")
    else:
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
                    if st.button("⏳ Reavaliar", key=f"comp_{reading_id}", use_container_width=True):
                        st.session_state["comparativa_id"] = reading_id
                        st.session_state["comparativa_resultado"] = None
                        st.rerun()
                    if st.button("🗑️ Excluir", key=f"del_{reading_id}", use_container_width=True):
                        delete_reading(reading_id)
                        st.rerun()

# ========================
# TAB 4 - ESTATÍSTICAS
# ========================
with tab_stats:
    st.markdown("### 📊 Painel de Estatísticas do Oraculista")

    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM leituras", conn)
    conn.close()

    if df.empty:
        st.info("📭 Ainda não há leituras para analisar. O painel ganha vida após a primeira leitura.")
    else:
        df["data_dt"] = pd.to_datetime(df["data_hora"], format="%d/%m/%Y %H:%M", errors="coerce")
        df["periodo"] = df["data_dt"].dt.to_period("M").astype(str)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Leituras totais", len(df))
        ultimos_30 = df[df["data_dt"] >= (pd.Timestamp.now() - pd.Timedelta(days=30))]
        m2.metric("Últimos 30 dias", len(ultimos_30))
        m3.metric("Oráculo favorito", df["oraculo"].value_counts().idxmax().split(" (")[0])
        m4.metric("Tom favorito", df["tom_leitura"].value_counts().idxmax().split(" (")[0])

        st.markdown("#### 📈 Leituras por mês")
        serie_mes = df["periodo"].value_counts().sort_index()
        st.line_chart(serie_mes)

        ca, cb = st.columns(2)
        with ca:
            st.markdown("#### 🃏 Por oráculo")
            st.bar_chart(df["oraculo"].value_counts())
        with cb:
            st.markdown("#### 📐 Por método")
            st.bar_chart(df["metodo"].value_counts())

        cc, cd = st.columns(2)
        with cc:
            st.markdown("#### 🎨 Por tom de leitura")
            st.bar_chart(df["tom_leitura"].value_counts())
        with cd:
            st.markdown("#### 🎴 Cartas mais sorteadas (Top 10)")
            cnt = Counter()
            for j in df["cartas"]:
                try:
                    cnt.update(json.loads(j).values())
                except Exception:
                    continue
            if cnt:
                top = pd.Series(dict(cnt.most_common(10)))
                st.bar_chart(top)
            else:
                st.caption("Sem dados de cartas.")

        pol = Counter()
        for _, r in df.iterrows():
            if str(r["oraculo"]).startswith("Sibilla"):
                try:
                    vals = json.loads(r["cartas"]).values()
                except Exception:
                    continue
                for v in vals:
                    d = _ficha_sibilla(v)
                    if d:
                        pol[str(d.get("polaridade", "Neutra"))] += 1
        if pol:
            st.markdown("#### ⚖️ Clima das tiragens Sibilla (polaridades)")
            p1, p2, p3 = st.columns(3)
            p1.metric("Positivas [+]", pol.get("Positiva", 0))
            p2.metric("Neutras [±]", pol.get("Neutra", 0))
            p3.metric("Negativas [−]", pol.get("Negativa", 0))

# ========================
# TAB 5 - MANUAIS
# ========================
with tab_manuais:
    st.markdown("### 📖 Manuais do Terapeuta")
    st.markdown(
        "Estude a linhagem, a arquitetura e as combinações de cada oráculo. "
        "Os manuais são arquivos HTML na raiz do projeto — leia aqui ou baixe para estudar offline. "
        "Para prática interativa do Cigano (tabuleiro, geometria e Mentor), use a **Sala Lumina** na sidebar."
    )

    manual_escolha = st.selectbox("Escolha o manual", options=list(MANUAIS.keys()), index=0)
    arquivo_manual = Path(__file__).parent / MANUAIS[manual_escolha]

    if arquivo_manual.exists():
        try:
            conteudo = arquivo_manual.read_text(encoding="utf-8")
            col_leitura, col_acoes = st.columns([4, 1])
            with col_leitura:
                components.html(conteudo, height=780, scrolling=True)
            with col_acoes:
                st.download_button(
                    "💾 Baixar manual (.html)",
                    data=conteudo.encode("utf-8"),
                    file_name=MANUAIS[manual_escolha],
                    mime="text/html; charset=utf-8",
                    use_container_width=True,
                )
                st.markdown("---")
                st.markdown(
                    f"[🔗 Abrir no GitHub](https://github.com/LunaraHolistics/AuxCards/blob/main/{MANUAIS[manual_escolha]})"
                )
                st.caption(
                    "Dica: o arquivo baixado abre em qualquer navegador, "
                    "com imagens carregadas direto do repositório."
                )
        except Exception as e:
            st.error(f"Erro ao carregar o manual: {e}")
    else:
        st.warning(
            f"Arquivo `{MANUAIS[manual_escolha]}` não encontrado na raiz do projeto. "
            "Salve o HTML correspondente ao lado do `app.py` e faça o commit."
        )

# ==========================================
# RODAPÉ
# ==========================================
st.markdown("<br><hr>", unsafe_allow_html=True)
st.markdown(
    f"<center><small style='color: #777;'>"
    f"Auxiliar de Cartomancia & Oráculos v5.2 • Google Gemini API ({MODELO_GEMINI}) • "
    f"Cigano · Tarô · Sibilla · Búzios • Sala de Estudo: Lumina • "
    f"Leituras baseadas em tendências energéticas. Respeite seu livre-arbítrio."
    f"</small></center>",
    unsafe_allow_html=True,
)