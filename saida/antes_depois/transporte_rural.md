# Antes × depois: Transporte escolar rural — perguntas frequentes

Arquivo `faq_transporte_escolar_rural.md` (formato md, fictício=True).

## Substituições feitas pela anonimização

| # | Tipo | Valor original | Vira |
|---|---|---|---|
| 1 | EMAIL | `luzia.campos@example.com` | `[EMAIL]` |
| 2 | NOME | `Luzia Campos` | `[NOME]` |

Total: **2** dados pessoais substituídos (EMAIL: 1, NOME: 1).

## ANTES (texto extraído do arquivo, sem limpeza)

```text
## Transporte escolar rural — perguntas frequentes

Documento fictício da Secretaria de Educação de Vila Esperança.

## Quem pode usar o transporte escolar rural?

Alunos da rede pública que moram na zona rural a mais de 2 km da escola ou do ponto de ônibus urbano mais próximo têm direito ao transporte escolar gratuito.

## Como fazer a inscrição?

A inscrição é feita na secretaria da própria escola no ato da matrícula. É preciso apresentar um comprovante de endereço rural ou uma declaração da associação de produtores.

## O que fazer se o ônibus não passar?

Registre a falta na escola no mesmo dia ou na Ouvidoria pelo telefone 156. Se a rota ficar mais de 3 dias sem atendimento, a Secretaria deve oferecer transporte alternativo.

## Contato

Dúvidas sobre rotas: falar com Luzia Campos, e-mail luzia.campos@example.com.
```

## DEPOIS (limpo + anonimizado, como entra no corpus)

```text
## Transporte escolar rural — perguntas frequentes
Documento fictício da Secretaria de Educação de Vila Esperança.
## Quem pode usar o transporte escolar rural?
Alunos da rede pública que moram na zona rural a mais de 2 km da escola ou do ponto de ônibus urbano mais próximo têm direito ao transporte escolar gratuito.
## Como fazer a inscrição?
A inscrição é feita na secretaria da própria escola no ato da matrícula. É preciso apresentar um comprovante de endereço rural ou uma declaração da associação de produtores.
## O que fazer se o ônibus não passar?
Registre a falta na escola no mesmo dia ou na Ouvidoria pelo telefone 156. Se a rota ficar mais de 3 dias sem atendimento, a Secretaria deve oferecer transporte alternativo.
## Contato
Dúvidas sobre rotas: falar com [NOME], e-mail [EMAIL].
```
