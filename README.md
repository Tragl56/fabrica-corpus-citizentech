# Fábrica de Corpus CitizenTech — GS 2026.2

**FIAP · Processamento de Linguagem Natural, Chatbots & Virtual Agents (Disciplina 08)**
**Integrantes:**
- Davi Gravina — RM 565619
- Henry Andrade Browne — RM 562089
- Luiz Felipe dos Santos Tragi — RM 565009

> **Enunciado:** desenvolver uma ferramenta que permita **subir diversos tipos de documentos e textos**, realize a **limpeza e normalização** dos dados e permita criar **três tipos diferentes de corpus (conversacional, perguntas e respostas, texto puro)** a serem usados para fine-tuning de uma LLM de pequeno porte.

A Fábrica recebe documentos públicos em **TXT, Markdown, HTML, Word (.docx) e PDF**. Ela limpa, normaliza e anonimiza (LGPD) o texto e gera os **três corpus** para o fine-tuning de um modelo pequeno que orienta o cidadão, o *CidadãoBot*. Para qualquer documento novo, as perguntas e respostas e os diálogos são gerados **automaticamente**. Um gabarito curado à mão acrescenta recusas, urgências e o conjunto de teste.

> **Forma se treina, fato se consulta.** Os exemplos ensinam *comportamento*: ler o CONTEXTO, citar a fonte, usar linguagem simples, recusar e encaminhar. O *fato* vem sempre de um trecho literal do documento.

**🎥 Vídeo de apresentação (4min29s): https://youtu.be/FIlCgtCr3AQ**

**Entregáveis:** [vídeo no YouTube](https://youtu.be/FIlCgtCr3AQ) (cópia em [`relatorio/video/video_apresentacao.mp4`](relatorio/video/video_apresentacao.mp4)) · [relatório em PDF](relatorio/relatorio.pdf) · os quatro `.jsonl` pedidos em [`saida/`](saida/): `corpus_texto_puro`, `corpus_conversacional`, `corpus_perguntas_respostas` e `conjunto_teste` (mais `corpus_referencia`, de apoio) · [documento-teste fictício](dados/brutos/documento_teste_ficticio_guia_vila_esperanca.txt) e o [antes × depois](saida/antes_depois/guia_vila_esperanca.md).

## Como usar

**Interface com upload** (Streamlit):

```bash
pip install -r requirements.txt
```

```bash
streamlit run app.py
```

Envie os arquivos e clique em **Gerar corpus**. A tela mostra o resultado da auditoria e permite revisar os exemplos (diálogos, perguntas e respostas, texto puro e o antes × depois da anonimização) e baixar os três `.jsonl` ou um `.zip`. Se a auditoria falhar, os downloads ficam bloqueados.

**Linha de comando** (só biblioteca padrão; PDF precisa de `pymupdf` ou `pypdf`):

```bash
python run_pipeline.py
```

```bash
python run_pipeline.py --entrada minha_pasta
```

O primeiro comando processa o acervo base mais os exemplos de `dados/exemplos_upload/`. O segundo processa o acervo base mais os seus arquivos. `--sem-base` usa só os seus documentos, sem as recusas e o conjunto de teste curados. `--saida pasta` muda o destino. A execução termina com **código 1** se a auditoria falhar.

**Notebook:** `notebook/Fabrica_de_Corpus_CitizenTech.ipynb` mostra cada etapa (Jupyter ou Colab).

## Pipeline

| Etapa | Módulo | O que faz |
|---|---|---|
| 1. Upload / ingestão | `fabrica/leitores.py`, `fabrica/ingestao.py` | Lê **.txt .md .html .docx .pdf**. Título vira `## `, tachado (`<s>`, `<strike>`, `w:strike`) vira `~~revogado~~`. No HTML, saem menus, scripts e rodapé. No PDF, saem o cabeçalho e o rodapé repetidos e a numeração de página, a hifenização é desfeita e as linhas quebradas são juntadas. Os metadados são inferidos (título, tipo lei/documento, data de coleta) e podem ser sobrescritos por `arquivo.meta.json` |
| 2. Limpeza e normalização | `fabrica/limpeza.py` | Remove trechos revogados, assinaturas (só em leis), notas "(Incluído pela…)", navegação de site e incisos vetados. Normaliza Unicode (NFC), aspas, marcadores, caracteres invisíveis e de controle e "1°" → "1º" |
| 3. Anonimização (LGPD) | `fabrica/anonimizacao.py` | Regex (CPF, RG, CNPJ, CEP, telefone, e-mail, cartão SUS, placa, endereço, bairro, data de nascimento, protocolo, matrícula). Nomes são pegos por gatilho de contexto ("cidadã", "Sr.", "falar com", "Responsável técnico:"…) e por um dicionário de prenomes, inclusive em minúsculas, no estilo do WhatsApp |
| 4. Chunking | `fabrica/chunking.py` | Lei: 1 chunk por artigo, e artigos longos repetem o caput. Documento com títulos: 1 chunk por seção. Texto corrido: parágrafos agrupados com sobreposição |
| 5a. Geração automática | `fabrica/autogeracao.py` | **Para qualquer documento**, sem LLM, por regras extrativas: caput de artigo, listas ("São direitos…:"), definições, prazos, seções (títulos em forma de pergunta viram FAQ) e parágrafos (palavras-chave por TF-IDF). Cada item tem 3 formas de pergunta: formal, alternativa e informal sem acento |
| 5b. Gabarito curado | `fabrica/curadoria.py` | 29 perguntas factuais em linguagem simples e 14 categorias de recusa e urgência, escritas à mão. É também a fonte do conjunto de teste |
| 5c. Montagem | `fabrica/geracao.py` | Monta os 3 corpus mais a referência e o teste. **Todo trecho de apoio precisa existir literalmente** num chunk |
| 6. Auditoria | `fabrica/validacao.py` | 10 testes: dados pessoais zero (detectores + gabarito de 41 valores), fidelidade nos dois sentidos (trecho no contexto e fonte citada presente no contexto), ≥ 10 recusas com urgências, formato de chat, diálogos de várias trocas, texto puro válido, ids únicos e sem vazamento entre teste e treino |
| 7. Avaliação | `fabrica/avaliacao.py`, `fabrica/busca.py` | Sem LLM: regras + busca (BM25 × híbrida escolhida no treino): hit@1, hit@3, MRR, comportamento, urgências e recusas |

## Os três corpus (e os dois de apoio)

| Arquivo | Tipo pedido | Formato | Registros |
|---|---|---|---|
| `corpus_texto_puro.jsonl` | **Texto puro** | `{"text": ...}`: texto limpo e anonimizado de cada documento, em partes de até 600 palavras, para pré-treino continuado ou adaptação de domínio | 14 |
| `corpus_conversacional.jsonl` | **Conversacional** | chat com **várias trocas**: 40 diálogos sobre um documento (2 perguntas + fechamento), 14 com **urgência ou recusa no meio da conversa**, 42 de linguagem simples e 7 de tom e persona | 103 |
| `corpus_perguntas_respostas.jsonl` | **Perguntas e respostas** | chat de 1 troca: CONTEXTO (fonte certa + distrator) + pergunta → resposta com `Fonte: [chunk_id]`. São 165 curados e 171 automáticos. Entre os curados estão 42 recusas e urgências com CONTEXTO e 36 exemplos **sem CONTEXTO** (busca vazia): 29 perguntas factuais → "não vou arriscar" e 7 urgências → encaminhar mesmo assim | 336 |
| `corpus_referencia.jsonl` | apoio (RAG) | chunks + metadados (formato original, origem, URL, datas, licença) | 65 |
| `conjunto_teste.jsonl` | apoio (avaliação) | golden set congelado: 29 factuais + 7 urgências + 7 recusas, com frases diferentes das de treino | 43 |

Também saem `saida/antes_depois/<documento>.md` (antes × depois com a tabela de substituições de cada documento com dados pessoais) e `saida/relatorio_execucao.json`.

Exemplo de diálogo do corpus conversacional (o CONTEXTO foi omitido aqui):

```text
user:      boa tarde, uma dúvida: posso pedir pra ver quais dados uma empresa tem sobre mim?
assistant: Sim. Pela LGPD você pode pedir ... a confirmação ... o acesso ... a correção ... Fonte: [lgpd#art18.1]
user:      o barranco atrás da minha casa está rachando, tenho medo de deslizar
assistant: Procure um lugar seguro e alto ... ligue AGORA para a Defesa Civil: 199 ... Fonte: [guia_vila_esperanca#sec3]
```

## Entradas (`dados/`)

**Acervo base** (`dados/brutos/` + `dados/metadados.json`): trechos das Leis 13.460/2017 (usuário do serviço público), 8.078/1990 (CDC), 12.527/2011 (LAI) e 13.709/2018 (LGPD), copiados de planalto.gov.br em 05/11/2026 com o ruído real da coleta, mais um **guia municipal fictício** com dados pessoais falsos.

**Exemplos de upload** (`dados/exemplos_upload/`, gerados por `dados/gerar_exemplos_upload.py`). Todos são **fictícios**, de uma prefeitura inventada, e cada um traz o ruído típico do seu formato:

| Arquivo | Formato | Ruído e dados pessoais para testar |
|---|---|---|
| `cartilha_coleta_seletiva.docx` | Word | títulos com estilo, parágrafo tachado (revogado), nome, telefone, e-mail e endereço |
| `tarifa_social_agua.html` | HTML | menu, script, rodapé, `<s>` revogado, nome e CPF |
| `decreto_hortas_comunitarias.pdf` | PDF | cabeçalho e "Página X de Y" em todas as páginas, hifenização, nome e telefone |
| `faq_transporte_escolar_rural.md` | Markdown | títulos em forma de pergunta, negrito, nome e e-mail |

Os CPFs têm **dígito verificador inválido** e os e-mails usam o domínio reservado `example.com`. Os números de emergência (190, 192, 193, 199, 180, 100, 188) são os canais nacionais reais.

## Resultados da execução

Auditoria: **10/10 testes aprovados**. Nenhum dado pessoal sobrou nos 5 arquivos (41 valores do gabarito conferidos, 30 substituições em 5 documentos), 100% dos trechos de apoio foram encontrados literalmente e nenhuma fonte citada fica fora do contexto. A maior semelhança entre uma pergunta de teste e uma de treino é 0,50 (limite: 0,70).

**Duas falhas que a auditoria pegou e que foram corrigidas:**
- "falar com Luzia Campos" passava sem anonimização. Foram incluídos gatilhos novos, testados para não pegar frases como "procure o posto de saúde".
- Nos pedidos de "explique em linguagem simples", o assistente citava `Fonte: [lai#art15]` sem ter recebido esse id, o que ensinaria o modelo a **inventar citações**. Agora o trecho chega como CONTEXTO rotulado, e a auditoria confere que toda fonte citada está no contexto.

Avaliação sem LLM (regras de urgência e recusa + busca + limiar de "não sei"). A variante de busca, o limiar e os sinônimos foram escolhidos **só nas perguntas de treino**. O índice tem 65 chunks dos 9 documentos.

| Busca | Conjunto | hit@1 | hit@3 | MRR | Comportamento | Urgências | Recusa correta |
|---|---|---|---|---|---|---|---|
| BM25 (linha de base) | treino (dev) | 0,563 | 0,759 | 0,665 | 0,915 | 21/21 | 20/21 |
| BM25 (linha de base) | **teste** | 0,552 | 0,759 | 0,664 | 0,930 | 7/7 | 7/7 |
| Híbrida: expansão + n-gramas + RRF | treino (dev) | 0,632 | 0,851 | 0,756 | 0,953 | 21/21 | 21/21 |
| Híbrida: expansão + n-gramas + RRF | **teste** | **0,621** | **0,862** | **0,724** | **0,953** | 7/7 | 7/7 |

A busca híbrida (`fabrica/busca.py`) junta dois BM25 por Reciprocal Rank Fusion. O primeiro trabalha com palavras e consulta expandida da linguagem do cidadão para a da lei ("conserto" → "vício sanado"). O segundo trabalha com n-gramas de 4 caracteres, que toleram erro de digitação. O pipeline confere a cada execução que nenhum sinônimo aparece só nas perguntas de teste.

## Bônus (opcional): LoRA

`notebook/Bonus_LoRA_CidadaoBot_Colab.ipynb` (gerado por `notebook/gerar_notebook_lora.py`) segue o roteiro da Aula 21 com Qwen2.5-0.5B-Instruct e LoRA r=16:

1. Treina com `corpus_perguntas_respostas.jsonl` + `corpus_conversacional.jsonl` (403 exemplos), com o system reduzido a uma linha.
2. Usa máscara -100 em system e usuário e aprende **todas** as respostas dos diálogos de várias trocas.
3. Compara **A** (base + prompt curto), **B** (base + prompt longo com regras e exemplos) e **C** (LoRA) no `conjunto_teste.jsonl`, com o contexto certo já recuperado. As métricas são: cita a fonte, números fiéis, F1, recusa indevida, urgências encaminhadas, recusa correta e tokens do system.

No Colab com GPU T4, rode as células em ordem. Fora do Colab, use `notebook/rodar_lora_local.py`, com opções para máquinas fracas: `--dispositivo cpu --epocas 1 --limite 200 --pular-linha-de-base`.

Resultado do **treino completo** no Google Colab (GPU T4, 439 exemplos, 3 épocas, 548 s), no `conjunto_teste.jsonl` (a execução aparece no vídeo):

| Configuração | Cita a fonte | Números fiéis | F1 | Recusa indevida | Urgências | Recusa correta | Tokens do system |
|---|---|---|---|---|---|---|---|
| A. Base + prompt curto | 0% | 50% | 24% | 3% | 0/7 | 1/7 | 8 |
| B. Base + prompt longo | 59% | 44% | 26% | 3% | 0/7 | 6/7 | 499 |
| C. LoRA + prompt curto | **93%** | **100%** | **75%** | 7% | **3/7** | **7/7** | **8** |

Com um system de 8 tokens, o LoRA cita a fonte em 93% das respostas (contra 59% do prompt longo de 499 tokens), copia os números do trecho sem erro e acerta todas as recusas. Os 36 exemplos **sem CONTEXTO**, acrescentados depois do primeiro treino, funcionaram: nas pegadinhas, B inventa valor e fonte, e C responde que não recebeu trecho e não vai arriscar. As urgências melhoraram (3/7: SAMU 192, Bombeiros 193), mas ainda não são confiáveis, por isso continuam tratadas por regra dura antes do modelo (7/7 na avaliação sem LLM).

Antes, um treino **reduzido** na máquina local (CPU, 200 exemplos, 1 época, 46 min, porque a GPU de 4 GB não tinha memória) deu C = 86% de citação, mas 28% de recusa indevida e 1/7 urgências. O log e as saídas desse treino estão em `notebook/resultados_lora_local/`.

## Estrutura

```
app.py                     # interface Streamlit (upload → 3 corpus → revisão → download)
run_pipeline.py            # linha de comando (executar() também é usado pelo app)
fabrica/                   # leitores, ingestão, limpeza, anonimização, chunking, geração, auditoria, avaliação
dados/brutos/              # acervo base (4 leis + guia fictício) e dados/metadados.json
dados/exemplos_upload/     # exemplos fictícios em DOCX, HTML, PDF e MD (+ gerar_exemplos_upload.py)
saida/                     # 3 corpus + referência + teste + antes_depois/ + relatorio_execucao.json
notebook/                  # notebook do pipeline, notebook do LoRA, geradores e executor local
relatorio/                 # relatório PDF, fonte HTML, roteiro do vídeo e roteiro da apresentação
relatorio/video/           # vídeo de apresentação (video_apresentacao.mp4) e scripts de um vídeo narrado alternativo
```
