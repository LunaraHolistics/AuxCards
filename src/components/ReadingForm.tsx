import React, { useRef, useState } from "react";
import {
  UploadCloud,
  X,
  Sparkles,
  HelpCircle,
  FileQuestion,
  Layers,
  Wand2,
  AlertCircle,
  Image as ImageIcon,
} from "lucide-react";
import { OracleType, SpreadMethod } from "../types";
import { SPREADS_DATA } from "../data/spreads";

interface ReadingFormProps {
  oracle: OracleType;
  spread: SpreadMethod;
  question: string;
  setQuestion: (q: string) => void;
  cards: string;
  setCards: (c: string) => void;
  imageFile: File | null;
  setImageFile: (f: File | null) => void;
  imagePreviewUrl: string | null;
  setImagePreviewUrl: (url: string | null) => void;
  onSubmit: () => void;
  loading: boolean;
  errorMessage: string | null;
}

export const ReadingForm: React.FC<ReadingFormProps> = ({
  oracle,
  spread,
  question,
  setQuestion,
  cards,
  setCards,
  imageFile,
  setImageFile,
  imagePreviewUrl,
  setImagePreviewUrl,
  onSubmit,
  loading,
  errorMessage,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [dragActive, setDragActive] = useState(false);

  const currentSpread = SPREADS_DATA[spread];

  const handleImageChange = (file: File | null) => {
    if (!file) {
      setImageFile(null);
      setImagePreviewUrl(null);
      return;
    }
    setImageFile(file);
    const reader = new FileReader();
    reader.onload = (e) => {
      setImagePreviewUrl(e.target?.result as string);
    };
    reader.readAsDataURL(file);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleImageChange(e.dataTransfer.files[0]);
    }
  };

  const handleFillExample = () => {
    if (oracle === "Baralho Cigano (Lenormand)") {
      setCards(currentSpread.placeholderLenormand);
    } else {
      setCards(currentSpread.placeholderTarot);
    }
    if (!question) {
      setQuestion(
        "Consulente busca orientação sobre um momento de transição importante na vida profissional, querendo clareza sobre desafios imediatos e o melhor caminho de ação nos próximos meses."
      );
    }
  };

  return (
    <form
      id="reading-form"
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit();
      }}
      className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col gap-6"
    >
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-4 border-b border-slate-800">
        <div>
          <h2 className="text-lg font-serif font-semibold text-amber-300 flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-amber-400" />
            Dados da Consulta
          </h2>
          <p className="text-xs text-slate-400">
            Informe a dúvida e as lâminas retiradas na mesa
          </p>
        </div>

        {/* Botão de Preenchimento Rápido / Exemplo */}
        <button
          type="button"
          onClick={handleFillExample}
          className="self-start sm:self-auto flex items-center gap-1.5 px-3 py-1.5 bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 hover:text-amber-200 border border-amber-500/30 rounded-lg text-xs font-medium transition-colors"
          title="Preenche o formulário com um exemplo coerente do oráculo e tiragem atuais"
        >
          <Wand2 className="w-3.5 h-3.5" />
          Preencher com Exemplo
        </button>
      </div>

      {errorMessage && (
        <div
          id="form-error-alert"
          className="bg-rose-950/70 border border-rose-800/80 text-rose-200 p-3.5 rounded-xl text-xs flex items-start gap-2.5"
        >
          <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
          <div className="flex-1 leading-relaxed">{errorMessage}</div>
        </div>
      )}

      {/* Grid: Pergunta e Cartas */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* Campo 1: Pergunta / Contexto */}
        <div className="flex flex-col gap-2">
          <div className="flex items-center justify-between">
            <label
              htmlFor="question-input"
              className="text-xs font-semibold text-slate-200 flex items-center gap-1.5"
            >
              <FileQuestion className="w-3.5 h-3.5 text-amber-400" />
              1. Pergunta / Contexto da Tiragem *
            </label>
            <span className="text-[11px] text-slate-500">Obrigatório</span>
          </div>

          <textarea
            id="question-input"
            rows={6}
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Exemplo: 'Consulente pergunta se deve aceitar uma proposta de sociedade em um novo negócio ou focar em consolidar a carreira atual. Sente receio de instabilidade...'"
            className="w-full bg-slate-950 border border-slate-700 rounded-xl p-3 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-amber-500 transition-colors resize-none leading-relaxed"
          />

          <div className="flex items-center gap-1.5 flex-wrap">
            <span className="text-[10px] text-slate-400">Sugestões de temas:</span>
            <button
              type="button"
              onClick={() =>
                setQuestion(
                  "Orientação profissional: Como equilibrar estabilidade e novos projetos para os próximos meses?"
                )
              }
              className="text-[10px] bg-slate-800 hover:bg-slate-700 text-slate-300 px-2 py-0.5 rounded-md transition-colors"
            >
              💼 Trabalho
            </button>
            <button
              type="button"
              onClick={() =>
                setQuestion(
                  "Relação afetiva: Quais as tendências e o que precisa ser harmonizado entre o casal?"
                )
              }
              className="text-[10px] bg-slate-800 hover:bg-slate-700 text-slate-300 px-2 py-0.5 rounded-md transition-colors"
            >
              ❤️ Relacionamento
            </button>
            <button
              type="button"
              onClick={() =>
                setQuestion(
                  "Desenvolvimento pessoal: Qual a principal lição que o momento atual me pede?"
                )
              }
              className="text-[10px] bg-slate-800 hover:bg-slate-700 text-slate-300 px-2 py-0.5 rounded-md transition-colors"
            >
              🌱 Evolução
            </button>
          </div>
        </div>

        {/* Campo 2: Cartas Sorteadas */}
        <div className="flex flex-col gap-2">
          <div className="flex items-center justify-between">
            <label
              htmlFor="cards-input"
              className="text-xs font-semibold text-slate-200 flex items-center gap-1.5"
            >
              <Layers className="w-3.5 h-3.5 text-amber-400" />
              2. Cartas Sorteadas e Posições *
            </label>
            <span className="text-[11px] text-slate-500">
              {oracle === "Baralho Cigano (Lenormand)" ? "Lenormand (36)" : "Tarô (78)"}
            </span>
          </div>

          <textarea
            id="cards-input"
            rows={6}
            value={cards}
            onChange={(e) => setCards(e.target.value)}
            placeholder={
              oracle === "Baralho Cigano (Lenormand)"
                ? currentSpread.placeholderLenormand
                : currentSpread.placeholderTarot
            }
            className="w-full bg-slate-950 border border-slate-700 rounded-xl p-3 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-amber-500 transition-colors resize-none font-mono leading-relaxed"
          />

          <p className="text-[10px] text-slate-400 leading-snug">
            💡 Dica: Você pode indicar os números das lâminas (ex: <em>24. Coração</em>) ou o nome do arcano.
          </p>
        </div>
      </div>

      {/* Campo 3: Upload de Imagem da Mesa */}
      <div className="flex flex-col gap-2">
        <label className="text-xs font-semibold text-slate-200 flex items-center gap-1.5">
          <ImageIcon className="w-3.5 h-3.5 text-amber-400" />
          3. Foto da Mesa / Tiragem (Opcional)
        </label>

        {imagePreviewUrl ? (
          <div
            id="image-preview-container"
            className="relative bg-slate-950 border border-amber-500/30 rounded-xl p-3 flex items-center gap-4"
          >
            <img
              src={imagePreviewUrl}
              alt="Mesa de cartas"
              className="w-24 h-24 object-cover rounded-lg border border-slate-800"
            />
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-amber-300 truncate">
                {imageFile?.name || "imagem_tiragem.jpg"}
              </p>
              <p className="text-[11px] text-slate-400 mt-0.5">
                {(imageFile?.size ? (imageFile.size / 1024).toFixed(1) : 0)} KB • Foto pronta para envio ao Gemini
              </p>
              <button
                type="button"
                onClick={() => handleImageChange(null)}
                className="mt-2 text-xs text-rose-400 hover:text-rose-300 flex items-center gap-1 transition-colors"
              >
                <X className="w-3 h-3" />
                Remover imagem
              </button>
            </div>
          </div>
        ) : (
          <div
            id="dropzone-image"
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-xl p-5 text-center cursor-pointer transition-all ${
              dragActive
                ? "border-amber-400 bg-amber-500/10"
                : "border-slate-700 hover:border-slate-600 bg-slate-950/60 hover:bg-slate-950"
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept="image/png, image/jpeg, image/jpg"
              onChange={(e) => {
                if (e.target.files && e.target.files[0]) {
                  handleImageChange(e.target.files[0]);
                }
              }}
              className="hidden"
            />
            <div className="flex flex-col items-center gap-2">
              <div className="w-9 h-9 rounded-full bg-slate-800 flex items-center justify-center text-slate-400">
                <UploadCloud className="w-4 h-4" />
              </div>
              <div>
                <p className="text-xs text-slate-300 font-medium">
                  Clique para carregar ou arraste uma foto da mesa
                </p>
                <p className="text-[10px] text-slate-500 mt-0.5">
                  Formatos aceitos: JPG, JPEG, PNG (Visão Computacional do Gemini)
                </p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Botão de Envio Principal */}
      <button
        id="btn-analyze-spread"
        type="submit"
        disabled={loading}
        className="w-full bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 font-semibold py-3 px-6 rounded-xl transition-all shadow-lg hover:shadow-amber-500/20 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 text-sm"
      >
        {loading ? (
          <>
            <div className="w-4 h-4 border-2 border-slate-950 border-t-transparent rounded-full animate-spin" />
            <span>Consultando o Oráculo com Gemini 2.5 Flash...</span>
          </>
        ) : (
          <>
            <Sparkles className="w-4 h-4 fill-current" />
            <span>🔮 Analisar Tiragem</span>
          </>
        )}
      </button>
    </form>
  );
};
