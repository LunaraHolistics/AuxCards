import React, { useState } from "react";
import {
  KeyRound,
  Eye,
  EyeOff,
  ExternalLink,
  Sparkles,
  Layers,
  FileCode2,
  CheckCircle2,
  HelpCircle,
  BookOpen,
} from "lucide-react";
import { OracleType, SpreadMethod } from "../types";
import { SPREADS_DATA } from "../data/spreads";

interface SidebarProps {
  apiKey: string;
  setApiKey: (key: string) => void;
  hasEnvKey: boolean;
  oracle: OracleType;
  setOracle: (oracle: OracleType) => void;
  spread: SpreadMethod;
  setSpread: (spread: SpreadMethod) => void;
  onOpenPythonModal: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  apiKey,
  setApiKey,
  hasEnvKey,
  oracle,
  setOracle,
  spread,
  setSpread,
  onOpenPythonModal,
}) => {
  const [showKey, setShowKey] = useState(false);
  const [showGuide, setShowGuide] = useState(true);

  const currentSpreadInfo = SPREADS_DATA[spread];

  return (
    <aside
      id="app-sidebar"
      className="w-full lg:w-80 shrink-0 bg-slate-900 border-r border-slate-800 p-5 flex flex-col gap-6 text-slate-200"
    >
      {/* Cabeçalho da Sidebar */}
      <div className="flex items-center gap-3 pb-4 border-b border-slate-800">
        <div className="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400">
          <Sparkles className="w-5 h-5" />
        </div>
        <div>
          <h2 className="text-base font-semibold text-amber-300 font-serif tracking-wide">
            Configurações
          </h2>
          <p className="text-xs text-slate-400">Parâmetros da consulta</p>
        </div>
      </div>

      {/* 1. Campo Chave de API Gemini */}
      <div className="flex flex-col gap-2">
        <div className="flex items-center justify-between">
          <label
            htmlFor="api-key-input"
            className="text-xs font-semibold text-slate-300 flex items-center gap-1.5"
          >
            <KeyRound className="w-3.5 h-3.5 text-amber-400" />
            Gemini API Key
          </label>
          {hasEnvKey && (
            <span
              id="env-key-badge"
              className="text-[10px] bg-emerald-950/80 text-emerald-400 border border-emerald-700/50 px-2 py-0.5 rounded-full flex items-center gap-1"
            >
              <CheckCircle2 className="w-2.5 h-2.5" />
              Ambiente Ativo
            </span>
          )}
        </div>

        <div className="relative">
          <input
            id="api-key-input"
            type={showKey ? "text" : "password"}
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            placeholder={
              hasEnvKey
                ? "Chave do servidor configurada (opcional sobrepor)"
                : "Cole sua chave AI Studio aqui..."
            }
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-amber-500 pr-9 transition-colors"
          />
          <button
            type="button"
            onClick={() => setShowKey(!showKey)}
            className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-200 transition-colors"
            title={showKey ? "Ocultar chave" : "Mostrar chave"}
          >
            {showKey ? (
              <EyeOff className="w-3.5 h-3.5" />
            ) : (
              <Eye className="w-3.5 h-3.5" />
            )}
          </button>
        </div>

        <p className="text-[11px] text-slate-400 leading-relaxed">
          Sem chave? Obtenha gratuitamente no{" "}
          <a
            href="https://aistudio.google.com/app/apikey"
            target="_blank"
            rel="noopener noreferrer"
            className="text-amber-400 hover:text-amber-300 underline inline-flex items-center gap-0.5"
          >
            Google AI Studio <ExternalLink className="w-2.5 h-2.5 inline" />
          </a>
        </p>
      </div>

      <hr className="border-slate-800 my-0" />

      {/* 2. Seleção do Oráculo */}
      <div className="flex flex-col gap-2">
        <label
          htmlFor="oracle-select"
          className="text-xs font-semibold text-slate-300 flex items-center gap-1.5"
        >
          <BookOpen className="w-3.5 h-3.5 text-amber-400" />
          Oráculo Utilizado
        </label>
        <select
          id="oracle-select"
          value={oracle}
          onChange={(e) => setOracle(e.target.value as OracleType)}
          className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-amber-500 transition-colors cursor-pointer"
        >
          <option value="Baralho Cigano (Lenormand)">
            Baralho Cigano (Lenormand)
          </option>
          <option value="Tarô Tradicional">Tarô Tradicional</option>
        </select>
        <p className="text-[11px] text-slate-400">
          {oracle === "Baralho Cigano (Lenormand)"
            ? "36 lâminas tradicionais focadas em sintaxe de duplas e tríades práticas."
            : "78 arcanos divididos em 22 Arcanos Maiores e 56 Arcanos Menores."}
        </p>
      </div>

      {/* 3. Seleção do Método de Tiragem */}
      <div className="flex flex-col gap-2">
        <label
          htmlFor="spread-select"
          className="text-xs font-semibold text-slate-300 flex items-center gap-1.5"
        >
          <Layers className="w-3.5 h-3.5 text-amber-400" />
          Método de Tiragem
        </label>
        <select
          id="spread-select"
          value={spread}
          onChange={(e) => setSpread(e.target.value as SpreadMethod)}
          className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-amber-500 transition-colors cursor-pointer"
        >
          <option value="Linha de 3 Cartas">Linha de 3 Cartas</option>
          <option value="Linha de 5 Cartas">Linha de 5 Cartas</option>
          <option value="Bloco de 9 Cartas (3x3)">
            Bloco de 9 Cartas (3x3)
          </option>
          <option value="Cruz Simples (5 cartas)">Cruz Simples (5 cartas)</option>
          <option value="Pirâmide Invertida (7 cartas)">
            Pirâmide Invertida (7 cartas)
          </option>
          <option value="Livre / Outro">Livre / Outro</option>
        </select>
      </div>

      {/* Guia Rápido do Método */}
      <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-3 flex flex-col gap-2">
        <button
          type="button"
          onClick={() => setShowGuide(!showGuide)}
          className="flex items-center justify-between text-xs font-medium text-amber-300 hover:text-amber-200 transition-colors text-left"
        >
          <span className="flex items-center gap-1.5">
            <HelpCircle className="w-3.5 h-3.5 text-amber-400" />
            Guia: {spread}
          </span>
          <span className="text-[10px] text-slate-500">
            {showGuide ? "Recolher" : "Expandir"}
          </span>
        </button>

        {showGuide && (
          <div className="text-[11px] text-slate-300 flex flex-col gap-1.5 pt-1 border-t border-slate-800/80">
            <p className="text-slate-400 italic">
              {currentSpreadInfo.description}
            </p>
            <ul className="space-y-1 list-disc pl-3 text-slate-300">
              {currentSpreadInfo.positions.map((pos, idx) => (
                <li key={idx} className="leading-snug">
                  {pos}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Botão para visualizar código Python Streamlit */}
      <div className="mt-auto pt-4 border-t border-slate-800">
        <button
          id="btn-view-python-code"
          type="button"
          onClick={onOpenPythonModal}
          className="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-amber-500/10 to-amber-600/10 hover:from-amber-500/20 hover:to-amber-600/20 border border-amber-500/30 text-amber-300 hover:text-amber-200 text-xs font-medium py-2.5 px-3 rounded-xl transition-all shadow-sm"
        >
          <FileCode2 className="w-4 h-4 text-amber-400" />
          Código Streamlit (app.py)
        </button>
        <p className="text-[10px] text-center text-slate-500 mt-2">
          Executável local com <code>streamlit run app.py</code>
        </p>
      </div>
    </aside>
  );
};
