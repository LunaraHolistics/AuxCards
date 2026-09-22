import { SpreadInfo, SpreadMethod } from "../types";

export const SPREADS_DATA: Record<SpreadMethod, SpreadInfo> = {
  "Linha de 3 Cartas": {
    name: "Linha de 3 Cartas",
    description: "Visão linear e direta da questão. Excelente para perguntas pontuais, conselhos imediatos e síntese.",
    positions: [
      "Posição 1: Passado / Causa raiz / Tema central",
      "Posição 2: Presente / Situação atual / Ação em curso",
      "Posição 3: Futuro imediato / Desfecho / Conselho final",
    ],
    placeholderLenormand: `1. 24. Coração (sentimentos em jogo)
2. 34. Peixes (fluidez e abundância)
3. 35. Âncora (estabilidade e solidez)`,
    placeholderTarot: `1. O Mago (potencial de ação e iniciativa)
2. 8 de Ouros (dedicação e aprimoramento contínuo)
3. 10 de Copas (harmonia emocional e realização)`,
  },
  "Linha de 5 Cartas": {
    name: "Linha de 5 Cartas",
    description: "Narrativa aprofundada com coração da questão destacado no centro e evolução temporal bem definida.",
    positions: [
      "Posições 1 e 2: Raízes da questão, passado recente e fatores influenciadores",
      "Posição 3 (Centro): O cerne da situação atual (foco de atenção)",
      "Posições 4 e 5: Desdobramentos imediatos, resolução e orientação final",
    ],
    placeholderLenormand: `1. 01. Cavaleiro
2. 12. Pássaros
3. 25. Anel (centro)
4. 31. Sol
5. 33. A Chave`,
    placeholderTarot: `1. 3 de Paus
2. 2 de Espadas
3. A Imperatriz (centro)
4. 6 de Ouros
5. O Sol`,
  },
  "Bloco de 9 Cartas (3x3)": {
    name: "Bloco de 9 Cartas (3x3)",
    description: "Tiragem multidimensional com leitura em cruz, diagonais, linhas horizontais (tempo) e espelhamentos.",
    positions: [
      "Carta 5 (Centro absoluto): Coração do tema analisado",
      "Linha Superior (1, 2, 3): Pensamentos, energias superiores e passado recente",
      "Linha Central (4, 5, 6): Realidade presente e ambiente próximo",
      "Linha Inferior (7, 8, 9): Consequências materiais, base e futuro",
      "Diagonais e espelhamentos (1 com 9, 3 com 7, 2 com 8, etc.)",
    ],
    placeholderLenormand: `1. Casa | 2. Livro | 3. Árvore
4. Flores | 5. Coração (Centro) | 6. Trevo
7. Navio | 8. Peixes | 9. Sol`,
    placeholderTarot: `1. A Sacerdotisa | 2. 4 de Copas | 3. O Hierofante
4. Cavaleiro de Espadas | 5. A Estrela (Centro) | 6. Ás de Paus
7. 2 de Ouros | 8. Rei de Ouros | 9. O Mundo`,
  },
  "Cruz Simples (5 cartas)": {
    name: "Cruz Simples (5 cartas)",
    description: "Método clássico para tomada de decisões, pesando forças favoráveis, obstáculos e desfecho.",
    positions: [
      "1. A Favor (À esquerda): O que apoia o consulente, talentos ou aliados",
      "2. Contra / Obstáculo (À direita): Desafios, forças de oposição ou ilusões",
      "3. Conselho Superior (Acima): A postura mental recomendada",
      "4. Caminho de Resolução (Abaixo): A ação prática concreta necessária",
      "5. Síntese e Desfecho (Centro): A conclusão e resultado provável",
    ],
    placeholderLenormand: `1. Sol (favor)
2. Nuvens (contra)
3. Torre (conselho)
4. Cavaleiro (ação)
5. Aliança (síntese)`,
    placeholderTarot: `1. A Força (a favor)
2. 5 de Espadas (obstáculo)
3. O Eremita (conselho mental)
4. 8 de Paus (ação prática)
5. A Roda da Fortuna (síntese)`,
  },
  "Pirâmide Invertida (7 cartas)": {
    name: "Pirâmide Invertida (7 cartas)",
    description: "Método que afunila as influências do plano material e ambiental até o ponto de resolução e clímax.",
    positions: [
      "Base (1, 2, 3, 4): Causas terrenas, fatores externos e pessoas envolvidas",
      "Nível Médio (5, 6): As duas forças polares em negociação interna ou conflito",
      "Vértice Inferior (7): A síntese final, veredito e resposta nuclear",
    ],
    placeholderLenormand: `Base: 1. Jardim | 2. Chicote | 3. Livro | 4. Cão
Médio: 5. Caminhos | 6. Coração
Vértice: 7. A Chave`,
    placeholderTarot: `Base: 1. 7 de Paus | 2. A Torre | 3. Pajem de Espadas | 4. 4 de Ouros
Médio: 5. Os Enamorados | 6. A Temperança
Vértice: 7. O Julgamento`,
  },
  "Livre / Outro": {
    name: "Livre / Outro",
    description: "Disposição personalizada definida pelo oraculista (Peladan, Mandala Astrológica, Conselho do Dia, etc.).",
    positions: [
      "Especifique livremente o nome da posição e a carta correspondente sorteada.",
    ],
    placeholderLenormand: `Posição A (Conselho para a semana): 24. Coração
Posição B (Alerta): 14. Raposa
Posição C (Oportunidade oculta): 33. A Chave`,
    placeholderTarot: `Carta do Momento: O Louco
O que deixar para trás: 8 de Copas
O que abraçar com coragem: O Mago`,
  },
};
