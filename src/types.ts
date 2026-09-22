export type OracleType = "Baralho Cigano (Lenormand)" | "Tarô Tradicional";

export type SpreadMethod =
  | "Linha de 3 Cartas"
  | "Linha de 5 Cartas"
  | "Bloco de 9 Cartas (3x3)"
  | "Cruz Simples (5 cartas)"
  | "Pirâmide Invertida (7 cartas)"
  | "Livre / Outro";

export interface SpreadInfo {
  name: SpreadMethod;
  description: string;
  positions: string[];
  placeholderLenormand: string;
  placeholderTarot: string;
}

export interface ReadingRequest {
  apiKey?: string;
  oracle: OracleType;
  spread: SpreadMethod;
  question: string;
  cards: string;
  imageBase64?: string;
  mimeType?: string;
}

export interface AnalysisResponse {
  text?: string;
  error?: string;
}
