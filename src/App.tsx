/**
 * Auxiliar de Cartomancia & Oráculos
 * Frontend React interativo integrado ao Gemini 2.5 Flash via Express
 */

import React, { useState, useEffect } from "react";
import { Sparkles, Moon, Compass, BookOpen, Code2 } from "lucide-react";
import { OracleType, SpreadMethod } from "./types";
import { Sidebar } from "./components/Sidebar";
import { EthicsBanner } from "./components/EthicsBanner";
import { ReadingForm } from "./components/ReadingForm";
import { InterpretationView } from "./components/InterpretationView";
import { PythonCodeModal } from "./components/PythonCodeModal";

export default function App() {
  const [apiKey, setApiKey] = useState<string>("");
  const [hasEnvKey, setHasEnvKey] = useState<boolean>(false);
  const [oracle, setOracle] = useState<OracleType>("Baralho Cigano (Lenormand)");
  const [spread, setSpread] = useState<SpreadMethod>("Linha de 3 Cartas");
  const [question, setQuestion] = useState<string>("");
  const [cards, setCards] = useState<string>("");
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imagePreviewUrl, setImagePreviewUrl] = useState<string | null>(null);

  const [loading, setLoading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [interpretation, setInterpretation] = useState<string | null>(null);
  const [isPythonModalOpen, setIsPythonModalOpen] = useState<boolean>(false);

  // Checar disponibilidade da chave de ambiente no backend
  useEffect(() => {
    fetch("/api/health")
      .then((res) => res.json())
      .then((data) => {
        if (data.hasEnvKey) {
          setHasEnvKey(true);
        }
      })
      .catch((err) => console.log("Servidor iniciando...", err));
  }, []);

  const handleAnalyze = async () => {
    setErrorMessage(null);

    // Validações locais
    const effectiveKey = apiKey.trim();
    if (!effectiveKey && !hasEnvKey) {
      setErrorMessage(
        "Chave de API do Gemini não informada. Por favor, insira sua chave na barra lateral ou configure a variável de ambiente GEMINI_API_KEY."
      );
      return;
    }

    if (!question.trim()) {
      setErrorMessage("Por favor, informe a Pergunta / Contexto da Tiragem.");
      return;
    }

    if (!cards.trim() && !imageFile) {
      setErrorMessage(
        "Por favor, informe as Cartas Sorteadas ou envie uma Foto da Mesa."
      );
      return;
    }

    setLoading(true);

    try {
      let imageBase64: string | undefined = undefined;
      let mimeType: string | undefined = undefined;

      if (imageFile) {
        imageBase64 = await new Promise<string>((resolve, reject) => {
          const reader = new FileReader();
          reader.onload = () => resolve(reader.result as string);
          reader.onerror = reject;
          reader.readAsDataURL(imageFile);
        });
        mimeType = imageFile.type || "image/jpeg";
      }

      const response = await fetch("/api/analyze-tarot", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          apiKey: effectiveKey || undefined,
          oracle,
          spread,
          question,
          cards,
          imageBase64,
          mimeType,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Falha ao processar a leitura.");
      }

      setInterpretation(data.text);
      // Rola a página suavemente para o resultado
      setTimeout(() => {
        const resultEl = document.getElementById("interpretation-result-container");
        if (resultEl) {
          resultEl.scrollIntoView({ behavior: "smooth" });
        }
      }, 100);
    } catch (err: any) {
      setErrorMessage(err.message || "Erro desconhecido ao consultar a API.");
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setInterpretation(null);
    setErrorMessage(null);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Barra de Topo */}
      <header className="border-b border-slate-800/80 bg-slate-900/60 backdrop-blur-md sticky top-0 z-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-amber-500/20 to-amber-400/30 border border-amber-500/30 flex items-center justify-center text-amber-300 shadow-sm">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-base sm:text-lg font-serif font-bold text-amber-300 tracking-wide">
                Auxiliar de Cartomancia & Oráculos
              </h1>
              <p className="text-[11px] text-slate-400 hidden sm:block">
                Interpretação ética de Baralho Cigano & Tarô com Google Gemini
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => setIsPythonModalOpen(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-800/80 hover:bg-slate-700/80 text-amber-300 border border-amber-500/30 rounded-xl text-xs font-medium transition-all"
            >
              <Code2 className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Ver Código</span> Python Streamlit
            </button>
          </div>
        </div>
      </header>

      {/* Conteúdo Principal: Sidebar + Painel de Leitura */}
      <div className="max-w-7xl mx-auto w-full flex-1 flex flex-col lg:flex-row">
        {/* Sidebar */}
        <Sidebar
          apiKey={apiKey}
          setApiKey={setApiKey}
          hasEnvKey={hasEnvKey}
          oracle={oracle}
          setOracle={setOracle}
          spread={spread}
          setSpread={setSpread}
          onOpenPythonModal={() => setIsPythonModalOpen(true)}
        />

        {/* Área Central */}
        <main className="flex-1 p-4 sm:p-6 lg:p-8 flex flex-col gap-6 overflow-y-auto">
          {/* Banner de Princípios Éticos */}
          <EthicsBanner />

          {/* Se houver interpretação, exibe o resultado */}
          {interpretation ? (
            <InterpretationView
              interpretation={interpretation}
              oracle={oracle}
              spread={spread}
              onReset={handleReset}
            />
          ) : null}

          {/* Formulário de Tiragem */}
          <ReadingForm
            oracle={oracle}
            spread={spread}
            question={question}
            setQuestion={setQuestion}
            cards={cards}
            setCards={setCards}
            imageFile={imageFile}
            setImageFile={setImageFile}
            imagePreviewUrl={imagePreviewUrl}
            setImagePreviewUrl={setImagePreviewUrl}
            onSubmit={handleAnalyze}
            loading={loading}
            errorMessage={errorMessage}
          />
        </main>
      </div>

      {/* Rodapé */}
      <footer className="border-t border-slate-800/80 bg-slate-950 py-4 px-6 text-center text-xs text-slate-500">
        <p>
          Auxiliar de Cartomancia & Oráculos • Desenvolvido com Python/Streamlit e integrado à biblioteca oficial{" "}
          <code className="text-amber-400">google-genai</code> (modelo{" "}
          <code className="text-amber-400">gemini-2.5-flash</code>).
        </p>
      </footer>

      {/* Modal de Código Python Streamlit */}
      <PythonCodeModal
        isOpen={isPythonModalOpen}
        onClose={() => setIsPythonModalOpen(false)}
      />
    </div>
  );
}
