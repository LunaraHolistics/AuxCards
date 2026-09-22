import React, { useState } from "react";
import { ShieldAlert, ChevronDown, ChevronUp, Sparkles, BookOpen, Scale } from "lucide-react";

export const EthicsBanner: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div
      id="ethics-principles-accordion"
      className="bg-slate-900/90 border border-amber-500/20 rounded-2xl overflow-hidden shadow-sm"
    >
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-5 py-3.5 flex items-center justify-between text-left hover:bg-slate-800/40 transition-colors"
      >
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-amber-500/10 flex items-center justify-center text-amber-400">
            <Scale className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-xs font-semibold text-amber-300 font-serif">
              Princípios Éticos & Regras de Interpretação
            </h3>
            <p className="text-[11px] text-slate-400">
              Sintaxe oracular, livre-arbítrio e a regra de ouro das 3 cartas para magia
            </p>
          </div>
        </div>

        <div className="flex items-center gap-1 text-slate-400 text-xs">
          <span>{isOpen ? "Ocultar" : "Ver diretrizes"}</span>
          {isOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </div>
      </button>

      {isOpen && (
        <div className="px-5 pb-5 pt-2 border-t border-slate-800 grid grid-cols-1 md:grid-cols-2 gap-4 text-xs text-slate-300">
          <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-3.5 flex flex-col gap-1.5">
            <h4 className="font-semibold text-amber-200 flex items-center gap-1.5">
              <BookOpen className="w-3.5 h-3.5 text-amber-400" />
              Sintaxe do Baralho Cigano (Lenormand)
            </h4>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              Cartas nunca são lidas soltas: atuam em pares (Substantivo + Adjetivo). A primeira define o assunto e a segunda qualifica. Polaridades (positivas, negativas e neutras) alteram a dinâmica narrativa.
            </p>
          </div>

          <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-3.5 flex flex-col gap-1.5">
            <h4 className="font-semibold text-amber-200 flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-amber-400" />
              Arcanos do Tarô Tradicional
            </h4>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              Distinção nítida: Arcanos Maiores trazem lições cármicas e viradas arquetípicas profundas; Arcanos Menores detalham o dia a dia nos quatro elementos (Fogo, Água, Ar e Terra).
            </p>
          </div>

          <div className="md:col-span-2 bg-amber-950/20 border border-amber-500/30 rounded-xl p-3.5 flex flex-col gap-1.5">
            <h4 className="font-semibold text-amber-300 flex items-center gap-1.5">
              <ShieldAlert className="w-3.5 h-3.5 text-amber-400" />
              Regra de Ouro: Proibição de Diagnóstico Fatalista de Magia
            </h4>
            <p className="text-[11px] text-amber-100/90 leading-relaxed">
              <strong>NUNCA</strong> diagnosticar feitiço ou demanda espiritual com base em apenas uma carta isolada (ex: O Diabo no Tarô ou Cobra/Caixão no Lenormand). Cartas isoladas sempre expressam questões comportamentais, emocionais ou materiais. Apenas a combinação explícita de <strong>2 a 3 cartas de sombra severa</strong> juntas pode sugerir bloqueios energéticos, e sempre com tom consultivo de autocuidado e sem gerar medo.
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
