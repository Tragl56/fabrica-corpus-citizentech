# Antes × depois: Guia de Atendimento ao Cidadão — Prefeitura de Vila Esperança (DOCUMENTO-TESTE FICTÍCIO)

Arquivo `brutos/documento_teste_ficticio_guia_vila_esperanca.txt` (formato txt, fictício=True).

## Substituições feitas pela anonimização

| # | Tipo | Valor original | Vira |
|---|---|---|---|
| 1 | DATA_NASCIMENTO | `14/03/1978` | `[DATA_NASCIMENTO]` |
| 2 | PROTOCOLO | `2026.000123-4` | `[PROTOCOLO]` |
| 3 | MATRICULA | `45.678` | `[MATRICULA]` |
| 4 | BAIRRO | `Jardim Esperança` | `[BAIRRO]` |
| 5 | ENDERECO | `Rua das Palmeiras, nº 245` | `[ENDERECO]` |
| 6 | ENDERECO | `av. brasil 1500 apto 32` | `[ENDERECO]` |
| 7 | EMAIL | `maria.lima78@example.com` | `[EMAIL]` |
| 8 | CARTAO_SUS | `898 0012 3456 7890` | `[CARTAO_SUS]` |
| 9 | CPF | `123.456.789-00` | `[CPF]` |
| 10 | CPF | `98765432111` | `[CPF]` |
| 11 | RG | `12.345.678-X` | `[RG]` |
| 12 | CEP | `01234-567` | `[CEP]` |
| 13 | TELEFONE | `(11) 98888-7777` | `[TELEFONE]` |
| 14 | TELEFONE | `11 97777-6666` | `[TELEFONE]` |
| 15 | PLACA | `BRA2E19` | `[PLACA]` |
| 16 | NOME | `Maria Aparecida dos Santos Lima` | `[NOME]` |
| 17 | NOME | `João Carlos Pereira` | `[NOME]` |
| 18 | NOME | `josé roberto almeida` | `[NOME]` |
| 19 | NOME | `José Roberto` | `[NOME]` |
| 20 | NOME | `Carlos Eduardo Souza` | `[NOME]` |

Total: **20** dados pessoais substituídos (DATA_NASCIMENTO: 1, PROTOCOLO: 1, MATRICULA: 1, BAIRRO: 1, ENDERECO: 2, EMAIL: 1, CARTAO_SUS: 1, CPF: 2, RG: 1, CEP: 1, TELEFONE: 2, PLACA: 1, NOME: 5).

## ANTES (texto extraído do arquivo, sem limpeza)

```text
DOCUMENTO FICTÍCIO — CRIADO APENAS PARA TESTE DA FÁBRICA DE CORPUS
Prefeitura Municipal de Vila Esperança (município fictício)
Ouvidoria-Geral do Município
GUIA DE ATENDIMENTO AO CIDADÃO — versão 1.0 (2026)
Página 1 de 3

## Como registrar uma manifestação na Ouvidoria
A Ouvidoria-Geral de Vila Esperança recebe reclamações, denúncias, sugestões, elogios e pedidos de providência sobre os serviços municipais. A manifestação pode ser feita pelo portal da Prefeitura, por carta ou presencialmente no Balcão do Cidadão, de segunda a sexta, das 8h às 17h. Toda manifestação recebe um número de protocolo, que serve para acompanhar o andamento.
A Ouvidoria responde em até 30 dias, prazo que pode ser prorrogado uma única vez por igual período, com justificativa, conforme a Lei nº 13.460/2017.

## Iluminação pública e buracos na via
Lâmpada queimada, poste danificado ou buraco na rua devem ser informados à Ouvidoria com o endereço aproximado e um ponto de referência. Fotos ajudam, mas não são obrigatórias. O prazo de atendimento informado na Carta de Serviços do município é de até 15 dias úteis para reparos de iluminação.
Página 2 de 3

## Situações de urgência e emergência
A Ouvidoria e o assistente virtual NÃO atendem emergências. Em situação de risco, ligue imediatamente:
- SAMU (emergência médica): 192
- Corpo de Bombeiros (incêndio, resgate, afogamento): 193
- Polícia Militar (crime em andamento, violência): 190
- Defesa Civil (enchente, deslizamento, risco de desabamento): 199
- Central de Atendimento à Mulher (violência contra a mulher): 180
- Disque Direitos Humanos (violação de direitos de crianças, idosos e pessoas com deficiência): 100
- CVV — Centro de Valorização da Vida (apoio emocional e prevenção do suicídio): 188
Ligações para esses números são gratuitas.

## Exemplo de registro de atendimento (dados fictícios)
Protocolo 2026.000123-4. A cidadã Maria Aparecida dos Santos Lima, CPF 123.456.789-00, RG 12.345.678-X, nascida em 14/03/1978, residente na Rua das Palmeiras, nº 245, Bairro Jardim Esperança, CEP 01234-567, telefone (11) 98888-7777, e-mail maria.lima78@example.com, cartão SUS 898 0012 3456 7890, procurou o Balcão do Cidadão para reclamar de um buraco em frente à sua casa. Foi atendida pelo servidor João Carlos Pereira, matrícula 45.678. A reclamação foi encaminhada à Secretaria de Obras.

## Exemplo de conversa recebida pelo WhatsApp (dados fictícios)
[10:02] cidadão: oi bom dia, aqui é o josé roberto almeida, meu cpf é 98765432111
[10:03] cidadão: moro na av. brasil 1500 apto 32, meu zap é 11 97777-6666
[10:03] cidadão: a lampada do poste da minha rua ta queimada faz 1 semana
[10:05] atendente: Bom dia, Sr. José Roberto! Vou registrar a sua solicitação. Placa do carro que bateu no poste, se souber?
[10:06] cidadão: era um carro prata placa BRA2E19, o dono é o vizinho Carlos Eduardo Souza
Página 3 de 3
Prefeitura Municipal de Vila Esperança — Rua Fictícia, s/n — documento sem valor legal
```

## DEPOIS (limpo + anonimizado, como entra no corpus)

```text
DOCUMENTO FICTÍCIO — CRIADO APENAS PARA TESTE DA FÁBRICA DE CORPUS
Prefeitura Municipal de Vila Esperança (município fictício)
Ouvidoria-Geral do Município
GUIA DE ATENDIMENTO AO CIDADÃO — versão 1.0 (2026)
## Como registrar uma manifestação na Ouvidoria
A Ouvidoria-Geral de Vila Esperança recebe reclamações, denúncias, sugestões, elogios e pedidos de providência sobre os serviços municipais. A manifestação pode ser feita pelo portal da Prefeitura, por carta ou presencialmente no Balcão do Cidadão, de segunda a sexta, das 8h às 17h. Toda manifestação recebe um número de protocolo, que serve para acompanhar o andamento.
A Ouvidoria responde em até 30 dias, prazo que pode ser prorrogado uma única vez por igual período, com justificativa, conforme a Lei nº 13.460/2017.
## Iluminação pública e buracos na via
Lâmpada queimada, poste danificado ou buraco na rua devem ser informados à Ouvidoria com o endereço aproximado e um ponto de referência. Fotos ajudam, mas não são obrigatórias. O prazo de atendimento informado na Carta de Serviços do município é de até 15 dias úteis para reparos de iluminação.
## Situações de urgência e emergência
A Ouvidoria e o assistente virtual NÃO atendem emergências. Em situação de risco, ligue imediatamente:
- SAMU (emergência médica): 192
- Corpo de Bombeiros (incêndio, resgate, afogamento): 193
- Polícia Militar (crime em andamento, violência): 190
- Defesa Civil (enchente, deslizamento, risco de desabamento): 199
- Central de Atendimento à Mulher (violência contra a mulher): 180
- Disque Direitos Humanos (violação de direitos de crianças, idosos e pessoas com deficiência): 100
- CVV — Centro de Valorização da Vida (apoio emocional e prevenção do suicídio): 188
Ligações para esses números são gratuitas.
## Exemplo de registro de atendimento (dados fictícios)
Protocolo [PROTOCOLO]. A cidadã [NOME], CPF [CPF], RG [RG], nascida em [DATA_NASCIMENTO], residente na [ENDERECO], Bairro [BAIRRO], CEP [CEP], telefone [TELEFONE], e-mail [EMAIL], cartão SUS [CARTAO_SUS], procurou o Balcão do Cidadão para reclamar de um buraco em frente à sua casa. Foi atendida pelo servidor [NOME], matrícula [MATRICULA]. A reclamação foi encaminhada à Secretaria de Obras.
## Exemplo de conversa recebida pelo WhatsApp (dados fictícios)
[10:02] cidadão: oi bom dia, aqui é o [NOME], meu cpf é [CPF]
[10:03] cidadão: moro na [ENDERECO], meu zap é [TELEFONE]
[10:03] cidadão: a lampada do poste da minha rua ta queimada faz 1 semana
[10:05] atendente: Bom dia, Sr. [NOME]! Vou registrar a sua solicitação. Placa do carro que bateu no poste, se souber?
[10:06] cidadão: era um carro prata placa [PLACA], o dono é o vizinho [NOME]
```
