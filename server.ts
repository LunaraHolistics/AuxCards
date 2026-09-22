import express from "express";
import path from "path";
import fs from "fs";
import { fileURLToPath } from "url";
import { GoogleGenAI } from "@google/genai";
import dotenv from "dotenv";

dotenv.config();

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const PORT = 3000;

// System instruction especializado em Cartomancia & Oráculos
const SYSTEM_INSTRUCTION = `
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
`;

async function startServer() {
  const app = express();
  app.use(express.json({ limit: "25mb" }));

  // API Status / Health
  app.get("/api/health", (_req, res) => {
    res.json({
      status: "ok",
      hasEnvKey: Boolean(process.env.GEMINI_API_KEY && process.env.GEMINI_API_KEY !== "MY_GEMINI_API_KEY"),
    });
  });

  // API para fornecer os arquivos Python (app.py e requirements.txt)
  app.get("/api/python-files", (_req, res) => {
    try {
      const appPyPath = path.join(process.cwd(), "app.py");
      const reqTxtPath = path.join(process.cwd(), "requirements.txt");

      const appPy = fs.existsSync(appPyPath) ? fs.readFileSync(appPyPath, "utf-8") : "";
      const requirements = fs.existsSync(reqTxtPath) ? fs.readFileSync(reqTxtPath, "utf-8") : "";

      res.json({ appPy, requirements });
    } catch (err: any) {
      res.status(500).json({ error: err.message });
    }
  });

  // Endpoint de interpretação com Google Gemini
  app.post("/api/analyze-tarot", async (req, res) => {
    try {
      const { apiKey, oracle, spread, question, cards, imageBase64, mimeType } = req.body;

      const activeApiKey = (apiKey && typeof apiKey === "string" && apiKey.trim().length > 0)
        ? apiKey.trim()
        : process.env.GEMINI_API_KEY;

      if (!activeApiKey || activeApiKey === "MY_GEMINI_API_KEY") {
        return res.status(400).json({
          error: "Chave da API do Google Gemini não fornecida. Insira sua chave na barra lateral ou configure a variável GEMINI_API_KEY.",
        });
      }

      if (!question || !question.trim()) {
        return res.status(400).json({
          error: "Por favor, informe a Pergunta ou Contexto da Tiragem.",
        });
      }

      if ((!cards || !cards.trim()) && !imageBase64) {
        return res.status(400).json({
          error: "Por favor, informe as Cartas Sorteadas ou envie uma foto da mesa.",
        });
      }

      // Inicialização oficial do @google/genai
      const ai = new GoogleGenAI({
        apiKey: activeApiKey,
        httpOptions: {
          headers: {
            "User-Agent": "aistudio-build",
          },
        },
      });

      const userPromptText = `
Por favor, realize a interpretação aprofundada da seguinte tiragem oracular:

- **Oráculo Escolhido**: ${oracle || "Baralho Cigano (Lenormand)"}
- **Método de Tiragem**: ${spread || "Linha de 3 Cartas"}
- **Pergunta / Contexto do Consulente**:
${question.trim()}

- **Cartas Sorteadas e Posições Informadas**:
${cards && cards.trim() ? cards.trim() : "(Consulte a foto em anexo para identificar as cartas dispostas na mesa)"}

Lembre-se de aplicar rigorosamente todas as regras oraculares da system instruction, especialmente a sintaxe de leitura, o tom ético e a regra estrita das 2 a 3 cartas de sombra para qualquer menção a questões espirituais densas.
`;

      const parts: any[] = [];

      if (imageBase64) {
        // Remove prefix se houver (data:image/...;base64,)
        const base64Data = imageBase64.includes(",")
          ? imageBase64.split(",")[1]
          : imageBase64;

        parts.push({
          inlineData: {
            mimeType: mimeType || "image/jpeg",
            data: base64Data,
          },
        });
      }

      parts.push({ text: userPromptText });

      // Tenta gemini-2.5-flash (solicitado) com fallback transparente para gemini-3.6-flash e gemini-3.8-flash
      const candidateModels = ["gemini-2.5-flash", "gemini-3.6-flash", "gemini-3.8-flash", "gemini-flash-latest"];
      let response: any = null;
      let lastError: any = null;

      for (const modelName of candidateModels) {
        try {
          response = await ai.models.generateContent({
            model: modelName,
            contents: { parts },
            config: {
              systemInstruction: SYSTEM_INSTRUCTION,
              temperature: 0.7,
            },
          });
          if (response && response.text) {
            break;
          }
        } catch (err: any) {
          console.warn(`Tentativa com modelo ${modelName} falhou:`, err.message);
          lastError = err;
        }
      }

      if (!response || !response.text) {
        throw lastError || new Error("Não foi possível obter resposta dos modelos oraculares.");
      }

      const interpretationText = response.text || "Nenhuma interpretação gerada pelo oráculo.";
      res.json({ text: interpretationText });
    } catch (error: any) {
      console.error("Erro na rota /api/analyze-tarot:", error);
      res.status(500).json({
        error: error.message || "Falha ao consultar a API do Gemini. Verifique a chave e tente novamente.",
      });
    }
  });

  // Vite middleware no desenvolvimento / Arquivos estáticos em produção
  if (process.env.NODE_ENV !== "production") {
    const { createServer: createViteServer } = await import("vite");
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa",
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), "dist");
    app.use(express.static(distPath));
    app.get("*", (_req, res) => {
      res.sendFile(path.join(distPath, "index.html"));
    });
  }

  app.listen(PORT, "0.0.0.0", () => {
    console.log(`Servidor rodando em http://localhost:${PORT}`);
  });
}

startServer();
