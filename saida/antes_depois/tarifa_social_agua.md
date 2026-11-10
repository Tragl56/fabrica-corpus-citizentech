# Antes × depois: Tarifa social da água

Arquivo `tarifa_social_agua.html` (formato html, fictício=True).

## Substituições feitas pela anonimização

| # | Tipo | Valor original | Vira |
|---|---|---|---|
| 1 | CPF | `321.654.987-00` | `[CPF]` |
| 2 | NOME | `Roberto Alves Nunes` | `[NOME]` |

Total: **2** dados pessoais substituídos (CPF: 1, NOME: 1).

## ANTES (texto extraído do arquivo, sem limpeza)

```text
Tarifa social da água
## Tarifa Social da Água — Vila Esperança
A Tarifa Social garante desconto de 50% na conta de água para famílias de baixa renda.
## Quem tem direito
Têm direito as famílias inscritas no Cadastro Único com renda mensal de até meio salário mínimo por pessoa, e os moradores que recebem o Benefício de Prestação Continuada (BPC).
~~O desconto era de 30% até dezembro de 2025.~~
## Como pedir
O pedido é feito no Posto de Atendimento ao Cidadão ou pelo telefone 156. Leve a conta de água mais recente, um documento com foto e o número de inscrição no Cadastro Único.
O desconto começa a valer na conta do mês seguinte à aprovação do pedido. A análise leva até 15 dias úteis.
## Renovação
O benefício deve ser renovado a cada 2 anos. A família recebe um aviso na conta de água 60 dias antes do vencimento.
Exemplo de atendimento registrado: o morador Roberto Alves Nunes, CPF 321.654.987-00, teve o pedido aprovado em 5 dias.
```

## DEPOIS (limpo + anonimizado, como entra no corpus)

```text
Tarifa social da água
## Tarifa Social da Água — Vila Esperança
A Tarifa Social garante desconto de 50% na conta de água para famílias de baixa renda.
## Quem tem direito
Têm direito as famílias inscritas no Cadastro Único com renda mensal de até meio salário mínimo por pessoa, e os moradores que recebem o Benefício de Prestação Continuada (BPC).
## Como pedir
O pedido é feito no Posto de Atendimento ao Cidadão ou pelo telefone 156. Leve a conta de água mais recente, um documento com foto e o número de inscrição no Cadastro Único.
O desconto começa a valer na conta do mês seguinte à aprovação do pedido. A análise leva até 15 dias úteis.
## Renovação
O benefício deve ser renovado a cada 2 anos. A família recebe um aviso na conta de água 60 dias antes do vencimento.
Exemplo de atendimento registrado: o morador [NOME], CPF [CPF], teve o pedido aprovado em 5 dias.
```
