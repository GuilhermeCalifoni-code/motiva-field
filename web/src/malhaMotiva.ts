export interface ConcessaoMotiva { nome: string; ufs: string; rodovias: string; centro: [number, number]; zoom: number; status?: "confirmada" | "detalhar"; }
// Fonte: portal público Motiva Rodovias. A lista detalhada publicada enumera
// as 11 operações abaixo; o portal informa 13 concessionárias no total.
export const malhaMotiva: ConcessaoMotiva[] = [
  { nome:"Motiva RioSP", ufs:"SP · RJ", rodovias:"BR-116, BR-101", centro:[-22.93,-45.46], zoom:8 },
  { nome:"Motiva ViaLagos", ufs:"RJ", rodovias:"RJ-124", centro:[-22.73,-42.44], zoom:9 },
  { nome:"Motiva AutoBAn", ufs:"SP", rodovias:"SP-330, SP-348, SP-300, SPI-102/330", centro:[-22.91,-47.06], zoom:9 },
  { nome:"Motiva ViaOeste", ufs:"SP", rodovias:"SP-270, SP-280, SP-075, SPI-091/270", centro:[-23.49,-47.45], zoom:9 },
  { nome:"Motiva RodoAnel", ufs:"SP", rodovias:"SP-021", centro:[-23.54,-46.82], zoom:10 },
  { nome:"Motiva SPVias", ufs:"SP", rodovias:"SP-280, SP-270, SP-255, SP-258, SP-127", centro:[-23.74,-48.02], zoom:8 },
  { nome:"Renovias", ufs:"SP", rodovias:"SP-340, SP-215, SP-342, SP-344, SP-350", centro:[-22.42,-46.95], zoom:9 },
  { nome:"ViaRio", ufs:"RJ", rodovias:"Corredor Transolímpica", centro:[-22.92,-43.46], zoom:11 },
  { nome:"Motiva ViaSul", ufs:"RS", rodovias:"BR-101, BR-290, BR-386, BR-448", centro:[-29.93,-51.16], zoom:8 },
  { nome:"Motiva ViaCosteira", ufs:"SC", rodovias:"BR-101/SC", centro:[-28.42,-48.93], zoom:9 },
  { nome:"Motiva MSVia", ufs:"MS", rodovias:"BR-163/MS", centro:[-20.47,-54.62], zoom:7 },
  { nome:"Motiva Paraná", ufs:"PR", rodovias:"Malha concessionada", centro:[-24.80,-51.57], zoom:7, status:"detalhar" },
  { nome:"Motiva Sorocabana", ufs:"SP", rodovias:"Malha concessionada", centro:[-23.50,-47.46], zoom:9, status:"detalhar" },
];
