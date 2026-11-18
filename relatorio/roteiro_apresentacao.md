# Roteiro de apresentação ao vivo — Fábrica de Corpus CitizenTech

Duração alvo: **5 minutos**. A coluna **Mostrar** diz o que estar na tela. A coluna **Falar** é um texto-base: fale com as suas palavras, mas mantenha os números (estão conferidos com a execução atual).

## Antes de começar (5 min de preparação)

1. Abra um terminal na pasta do projeto e rode uma vez, para tudo estar quente:
   ```bash
   python run_pipeline.py
   ```
2. Deixe a interface aberta no navegador:
   ```bash
   streamlit run app.py
   ```
   Na barra lateral: **Incluir acervo base** marcado e **Incluir exemplos de upload** desmarcado (você vai fazer o upload na frente de todos).
3. Deixe abertos, em abas ou janelas:
   - a pasta `dados/exemplos_upload/` no Explorador de Arquivos (os 4 arquivos: `.pdf`, `.docx`, `.html`, `.md`)
   - o `relatorio/relatorio.pdf` na página 3 (tabelas de avaliação e LoRA)
   - o terminal, com a saída do `run_pipeline.py` visível
4. Plano B: se algo travar, o vídeo `relatorio/video/video_fabrica_de_corpus.mp4` mostra tudo.

## Roteiro

| Tempo | Mostrar | Falar |
|---|---|---|
| **0:00–0:20** | Tela inicial da interface | "Somos Davi Gravina, Henry Andrade Browne e Luiz Felipe dos Santos Tragi. Este é o nosso projeto de PLN da Global Solution: a Fábrica de Corpus CitizenTech." |
| **0:20–0:50** | Mesma tela (ou o enunciado no relatório, seção 1) | "O desafio pede uma ferramenta que receba vários tipos de documento, limpe e normalize, e gere três corpus — conversacional, perguntas e respostas e texto puro — para fazer fine-tuning de uma LLM pequena. Nosso tema é o cidadão: leis como o Código de Defesa do Consumidor, a LAI e a LGPD, e orientações de uma prefeitura. A regra que guiou tudo foi: **forma se treina, fato se consulta**. O modelo aprende o comportamento — citar a fonte, recusar, encaminhar urgência — e o fato vem sempre de um trecho do documento." |
| **0:50–1:30** | **Upload ao vivo:** arraste os 4 arquivos de `dados/exemplos_upload/` (PDF, DOCX, HTML, MD) para o campo *Documentos* e clique em **Gerar corpus** | "Vou enviar quatro documentos fictícios, um de cada formato: um decreto em PDF, uma cartilha em Word, uma página HTML e um FAQ em Markdown. Junto vai o acervo base com quatro leis federais. Tudo roda nesta máquina, sem chave de API." Enquanto processa: "O log mostra as etapas: ingestão, limpeza, anonimização, chunking, geração, auditoria e avaliação." |
| **1:30–1:50** | Cartões do topo: **Texto puro 14 · Conversacional 103 · Perguntas e respostas 336 · Auditoria OK** | "Pronto: catorze registros de texto puro, cento e três conversas e trezentos e trinta e seis pares de pergunta e resposta. E a auditoria passou." |
| **1:50–2:30** | Aba **Antes × depois** → escolha `guia_vila_esperanca` (role até a linha do WhatsApp) e depois `cartilha_coleta_seletiva` | "Nenhum dado pessoal real entra no corpus. Os documentos de teste têm dados inventados — CPF com dígito inválido, e-mail example.com. A anonimização troca CPF, telefone, e-mail, endereço e nomes por etiquetas, inclusive nome escrito em minúsculas, como no WhatsApp: *'aqui é o josé roberto almeida'* vira *'aqui é o [NOME]'*. Foram trinta substituições em cinco documentos." |
| **2:30–3:10** | Aba **Perguntas e respostas** → Origem: **automatico** → avance o *Exemplo* até um do `decreto_hortas_comunitarias` (ou qualquer um); abra *CONTEXTO recuperado* | "Para qualquer documento enviado, as perguntas e respostas são geradas automaticamente, por regras sobre a estrutura do texto: artigos, listas, definições, prazos e seções. A resposta copia o trecho literal, então é fiel por construção, e sempre termina com a fonte entre colchetes. No contexto vai a fonte certa e um trecho parecido, mas errado — o distrator —, para o modelo aprender a escolher. Um gabarito escrito à mão completa com respostas em linguagem simples, recusas e urgências." |
| **3:10–3:40** | Aba **Conversacional** → Tipo de diálogo: **urgencia** → mostre o diálogo | "O corpus conversacional tem diálogos de várias trocas. Aqui o cidadão faz uma pergunta comum e, no meio da conversa, relata uma emergência. O assistente não continua no assunto anterior: manda ligar para o serviço certo — Defesa Civil, 199; SAMU, 192; CVV, 188." |
| **3:40–3:55** | Aba **Texto puro** → abra `cartilha_coleta_seletiva#parte1` | "O texto puro é o documento limpo e anonimizado, em partes de até 600 palavras, no formato `text` usado para pré-treino continuado. Repare que a frase revogada do Word sumiu e o contato virou etiqueta." |
| **3:55–4:20** | Expander **Auditoria** (10 itens verdes) | "No fim roda uma auditoria com dez testes: zero dado pessoal, fidelidade dos trechos, recusas e urgências, formato, diálogos de várias trocas e nenhum vazamento entre treino e teste. Se um teste falha, os downloads ficam bloqueados. Ela pegou dois problemas reais durante o projeto: um nome que escapava da anonimização, e respostas que citavam uma fonte que o modelo nunca tinha recebido — o que ensinaria o modelo a inventar citação." |
| **4:20–4:45** | `relatorio.pdf`, página 3: tabela **Avaliação sem LLM** e tabela **LoRA** | "Antes de treinar, medimos uma régua sem LLM: regras e busca. A busca híbrida põe o trecho certo entre os três primeiros em 86% das perguntas de teste e encaminha as sete urgências. No bônus, um LoRA no Qwen de meio bilhão de parâmetros, mesmo num treino reduzido, passou a citar a fonte em 86% das respostas, contra 59% do prompt longo, com um prompt de 8 tokens. Mas nenhuma configuração acertou as urgências — por isso urgência é tratada por regra **antes** do modelo." |
| **4:45–5:00** | Botões **Baixar** (ou o GitHub: `github.com/Tragl56/fabrica-corpus-citizentech`) | "Os três corpus saem prontos para download. O código, os corpus, os notebooks e o relatório estão no GitHub. Obrigado!" |

## Se faltar tempo (versão de 3 minutos)

Mantenha: abertura → enunciado (curto) → upload ao vivo → cartões 14/103/336 → Antes × depois → Conversacional com urgência → Auditoria → encerramento. Pule texto puro e as tabelas.

## Divisão entre os três (se apresentarem juntos)

| Quem | Trechos |
|---|---|
| Davi | 0:00–1:30 (abertura, enunciado, upload ao vivo) |
| Henry | 1:30–3:40 (resultado, anonimização, perguntas e respostas, conversacional) |
| Luiz Felipe | 3:40–5:00 (texto puro, auditoria, avaliação, LoRA, encerramento) |

## Perguntas prováveis — respostas curtas

- **"Por que não usar um LLM para gerar as perguntas?"** — Funciona sem API e sem custo, e a resposta extrativa é fiel por construção: não tem como inventar fato. O ponto fraco é o registro formal do texto; o gabarito curado ensina a linguagem simples. Usar um LLM local para reescrever, mantendo a checagem literal do trecho, é o próximo passo.
- **"Como vocês garantem que não sobrou dado pessoal?"** — Duas camadas: os detectores rodam de novo sobre todas as strings dos arquivos de saída, e um gabarito com os 41 valores fictícios plantados nos documentos é procurado em tudo. Se aparecer um, a fábrica não libera o corpus.
- **"E nomes que não estão no dicionário?"** — Pegamos por gatilho de contexto ("falar com", "Sr.", "aqui é o"…). Ainda pode escapar um nome sem gatilho; um NER seria a próxima camada. A regra erra para o lado da cautela.
- **"O que é vazamento entre treino e teste?"** — Perguntas de teste parecidas demais com as de treino inflariam o resultado. Medimos a maior semelhança entre qualquer par: 0,50, abaixo do limite de 0,70. E toda escolha (busca, limiar, sinônimos) foi feita só no treino.
- **"Por que o LoRA recusou demais?"** — Treino reduzido (200 exemplos, 1 época, na CPU, porque a GPU de 4 GB não tinha memória). O treino completo, com 403 exemplos e 3 épocas, está pronto no notebook para a T4 do Colab. Depois desse teste, acrescentamos 36 exemplos sem contexto ao corpus.
- **"Para que serve o texto puro se o treino é de chat?"** — Para uma etapa anterior, de pré-treino continuado: o modelo se acostuma com o vocabulário do domínio antes do ajuste de comportamento.
- **"Aceita PDF escaneado?"** — Ainda não: PDF de imagem precisa de OCR. Está nas limitações do relatório.
