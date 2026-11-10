# Roteiro do vídeo (até 5 min)

| Tempo | Tela | Fala (resumo) |
|---|---|---|
| 0:00–0:25 | Enunciado da Disciplina 08 | O pedido: subir vários tipos de documento, limpar e normalizar, e gerar 3 corpus (conversacional, perguntas e respostas, texto puro) para fine-tuning de uma LLM pequena. Regra: forma se treina, fato se consulta. |
| 0:25–1:10 | `streamlit run app.py` | Upload de um PDF, um DOCX, um HTML e um MD (os exemplos fictícios), com "Incluir acervo base" marcado, e clique em **Gerar corpus**. Mostrar o log das etapas e a auditoria 10/10. |
| 1:10–1:50 | Notebook, seções 1–2 | Leitores por formato: no PDF, saem o cabeçalho repetido e a "Página X de Y" e a hifenização é desfeita ("ali-mentos"); no HTML, saem menu e rodapé. Limpeza do Art. 10-A: revogado e "(Incluído pela…)" removidos. |
| 1:50–2:30 | Aba **Antes × depois** | CPF, nomes (inclusive "josé roberto" em minúsculas e "falar com Luzia Campos") viram etiquetas. Contar a falha que a auditoria pegou e a correção. |
| 2:30–3:20 | Abas **Perguntas e respostas** e **Conversacional** | Uma pergunta automática do decreto em PDF ("Quais são os pontos do Art. 2º?"), com CONTEXTO + distrator e `Fonte: [decreto_hortas#art2]`. Um diálogo de 3 trocas com a urgência no meio (LGPD → barranco rachando → Defesa Civil 199). |
| 3:20–3:45 | Aba **Texto puro** | O registro `{"text": ...}` limpo e anonimizado, para pré-treino continuado. |
| 3:45–4:30 | Terminal: `python run_pipeline.py` | Auditoria 10/10, incluindo a checagem nova que pegou "citação inventada". Avaliação sem LLM: urgências 7/7; a busca híbrida põe o trecho certo entre os 3 primeiros em 86% das perguntas. |
| 4:30–5:00 | Tabela do LoRA (relatório, seção 9) | Base × prompt longo × LoRA no conjunto de teste. Lição: a urgência é garantida por regra dura antes do modelo. Próximo passo: treino completo na T4 do Colab. |
