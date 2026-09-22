import React, { useState } from "react";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Copy, Check, Download, Sparkles, RefreshCw, ScrollText } from "lucide-react";

interface InterpretationViewProps {
  interpretation: string;
  oracle: string;
  spread: string;
  onReset: () => void;
}

export const InterpretationView: React.FC<InterpretationViewProps> = ({
  interpretation,
  oracle,
  spread,
  onReset,
}) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(interpretation);
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    } catch {
      // Fallback
      const textArea = document.createElement("textarea");
      textArea.value = interpretation;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand("copy");
      document.body.removeChild(textArea);
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    }
  };

  const handleDownload = () => {
    const element = document.createElement("a");
    const file = new Blob([interpretation], { type: "text/plain;charset=utf-8" });
    element.href = URL.createObjectURL(file);
    element.download = `interpretacao_${oracle.toLowerCase().replace(/\s+/g, "_")}.txt`;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  return (
    <div
      id="interpretation-result-container"
      className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col gap-6"
    >
      {/* Topo do Card de Resultado */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400">
            <ScrollText className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-semibold text-amber-300 font-serif flex items-center gap-2">
              Interpretação do Oráculo
              <span className="text-[11px] font-sans font-normal bg-amber-500/10 text-amber-300 border border-amber-500/30 px-2 py-0.5 rounded-full">
                Gemini 2.5 Flash
              </span>
            </h3>
            <p className="text-xs text-slate-400">
              {oracle} • {spread}
            </p>
          </div>
        </div>

        {/* Botões de Ação */}
        <div className="flex items-center gap-2 flex-wrap">
          <button
            id="btn-copy-result"
            type="button"
            onClick={handleCopy}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white rounded-lg text-xs font-medium border border-slate-700 transition-colors"
          >
            {copied ? (
              <>
                <Check className="w-3.5 h-3.5 text-emerald-400" />
                <span className="text-emerald-400 font-semibold">Copiado!</span>
              </>
            ) : (
              <>
                <Copy className="w-3.5 h-3.5 text-slate-400" />
                Copiar Resultado
              </>
            )}
          </button>

          <button
            id="btn-download-result"
            type="button"
            onClick={handleDownload}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white rounded-lg text-xs font-medium border border-slate-700 transition-colors"
          >
            <Download className="w-3.5 h-3.5 text-slate-400" />
            Baixar (.txt)
          </button>

          <button
            id="btn-new-reading"
            type="button"
            onClick={onReset}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 hover:text-amber-200 rounded-lg text-xs font-medium border border-amber-500/30 transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5 text-amber-400" />
            Nova Análise
          </button>
        </div>
      </div>

      {/* Renderização do Markdown */}
      <div className="prose prose-invert prose-amber max-w-none text-slate-300 leading-relaxed text-sm space-y-4">
        <Markdown
          remarkPlugins={[remarkGfm]}
          components={{
            h1: ({ children }) => (
              <h1 className="text-xl font-bold font-serif text-amber-300 mt-6 mb-3 pb-2 border-b border-slate-800 flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-amber-400 inline" />
                {children}
              </h1>
            ),
            h2: ({ children }) => (
              <h2 className="text-lg font-semibold font-serif text-amber-200 mt-5 mb-2.5 pb-1.5 border-b border-slate-800/80">
                {children}
              </h2>
            ),
            h3: ({ children }) => (
              <h3 className="text-base font-semibold font-serif text-amber-100 mt-4 mb-2">
                {children}
              </h3>
            ),
            p: ({ children }) => <p className="mb-3 leading-relaxed text-slate-300">{children}</p>,
            ul: ({ children }) => <ul className="list-disc pl-5 mb-3 space-y-1.5 text-slate-300">{children}</ul>,
            ol: ({ children }) => <ol className="list-decimal pl-5 mb-3 space-y-1.5 text-slate-300">{children}</ol>,
            li: ({ children }) => <li className="leading-relaxed">{children}</li>,
            strong: ({ children }) => <strong className="font-semibold text-amber-200">{children}</strong>,
            blockquote: ({ children }) => (
              <blockquote className="border-l-4 border-amber-500/50 pl-4 py-1.5 my-3 italic text-amber-100/90 bg-amber-500/5 rounded-r-lg">
                {children}
              </blockquote>
            ),
            code: ({ children }) => (
              <code className="bg-slate-950 border border-slate-800 text-amber-300 px-1.5 py-0.5 rounded text-xs font-mono">
                {children}
              </code>
            ),
          }}
        >
          {interpretation}
        </Markdown>
      </div>

      {/* Rodapé do container */}
      <div className="pt-4 border-t border-slate-800/80 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-500 gap-2">
        <span>✨ Interpretação gerada sob princípios éticos e diretrizes sintáticas oraculares.</span>
        <span className="text-[11px] text-amber-400/80">Livre-arbítrio & Consciência</span>
      </div>
    </div>
  );
};
