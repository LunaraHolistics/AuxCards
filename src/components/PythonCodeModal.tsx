import React, { useState, useEffect } from "react";
import { X, Copy, Check, Download, FileCode, Terminal, Sparkles } from "lucide-react";

interface PythonCodeModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const PythonCodeModal: React.FC<PythonCodeModalProps> = ({ isOpen, onClose }) => {
  const [activeTab, setActiveTab] = useState<"app.py" | "requirements.txt">("app.py");
  const [appPyCode, setAppPyCode] = useState<string>("");
  const [requirementsCode, setRequirementsCode] = useState<string>("");
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (isOpen) {
      fetch("/api/python-files")
        .then((res) => res.json())
        .then((data) => {
          if (data.appPy) setAppPyCode(data.appPy);
          if (data.requirements) setRequirementsCode(data.requirements);
        })
        .catch((err) => {
          console.error("Falha ao carregar arquivos Python:", err);
        });
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const currentCode = activeTab === "app.py" ? appPyCode : requirementsCode;
  const currentFilename = activeTab;

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(currentCode);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      const textArea = document.createElement("textarea");
      textArea.value = currentCode;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand("copy");
      document.body.removeChild(textArea);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleDownload = () => {
    const element = document.createElement("a");
    const file = new Blob([currentCode], { type: "text/plain;charset=utf-8" });
    element.href = URL.createObjectURL(file);
    element.download = currentFilename;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  return (
    <div
      id="python-code-modal-overlay"
      className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4"
    >
      <div
        id="python-code-modal-card"
        className="bg-slate-900 border border-slate-800 w-full max-w-4xl rounded-2xl shadow-2xl flex flex-col max-h-[90vh] overflow-hidden"
      >
        {/* Topo do Modal */}
        <div className="p-4 sm:p-5 border-b border-slate-800 flex items-center justify-between bg-slate-900/90">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400">
              <FileCode className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-slate-100 font-serif flex items-center gap-2">
                Código Fonte Python (Streamlit)
                <span className="text-[10px] font-sans font-normal bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 px-2 py-0.5 rounded-full">
                  google-genai oficial
                </span>
              </h3>
              <p className="text-xs text-slate-400">
                Arquivos gerados para execução local ou na nuvem
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="text-slate-400 hover:text-slate-200 p-1.5 rounded-lg hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Abas e Ações */}
        <div className="px-5 py-3 border-b border-slate-800 bg-slate-950/60 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setActiveTab("app.py")}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                activeTab === "app.py"
                  ? "bg-amber-500/20 text-amber-300 border border-amber-500/40"
                  : "bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800"
              }`}
            >
              app.py
            </button>
            <button
              type="button"
              onClick={() => setActiveTab("requirements.txt")}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                activeTab === "requirements.txt"
                  ? "bg-amber-500/20 text-amber-300 border border-amber-500/40"
                  : "bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800"
              }`}
            >
              requirements.txt
            </button>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={handleCopy}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-medium border border-slate-700 transition-colors"
            >
              {copied ? (
                <>
                  <Check className="w-3.5 h-3.5 text-emerald-400" />
                  <span className="text-emerald-400 font-medium">Copiado!</span>
                </>
              ) : (
                <>
                  <Copy className="w-3.5 h-3.5 text-slate-400" />
                  Copiar {activeTab}
                </>
              )}
            </button>

            <button
              type="button"
              onClick={handleDownload}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 rounded-lg text-xs font-medium border border-amber-500/40 transition-colors"
            >
              <Download className="w-3.5 h-3.5" />
              Baixar {activeTab}
            </button>
          </div>
        </div>

        {/* Bloco de Código com Scroll */}
        <div className="flex-1 overflow-auto p-4 bg-slate-950 font-mono text-xs text-slate-200 leading-relaxed">
          <pre className="whitespace-pre">{currentCode || "# Carregando código..."}</pre>
        </div>

        {/* Instruções de Execução */}
        <div className="p-4 bg-slate-900/90 border-t border-slate-800 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs text-slate-400">
          <div className="flex items-center gap-2">
            <Terminal className="w-4 h-4 text-amber-400 shrink-0" />
            <span>
              Para rodar no seu computador:{" "}
              <code className="text-amber-300 bg-slate-950 px-2 py-0.5 rounded border border-slate-800">
                pip install -r requirements.txt && streamlit run app.py
              </code>
            </span>
          </div>
          <span className="text-[11px] text-slate-500">Python 3.10+</span>
        </div>
      </div>
    </div>
  );
};
