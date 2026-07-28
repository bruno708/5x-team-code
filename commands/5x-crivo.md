---
description: Monta o relatorio de crivo — evidencia de maquina, nao narracao
---

Monte o relatório de crivo do ciclo. Formato completo em
a referência `crivo` (leia com `5x-ref crivo`).

**Se o relatório for narração do agente, o crivo é teatro.** Você está pedindo
para o usuário confiar na redação de quem fez a prova e se autocorrigiu.

## Colete a evidência antes de escrever

```bash
5x-gate --justify
5x-cost summary --ciclo <c>
git diff <base>...HEAD --stat && git diff <base>...HEAD
```

Se o ponytail estiver instalado, alimente as duas seções que ele cobre:

- `/ponytail-review` — antes do crivo, sobre o diff do ciclo
- `/ponytail-debt` — alimenta o campo **dívida declarada**

Não instalado? Escreva a dívida declarada à mão, dos campos `divida_declarada`
dos retornos das tarefas. O ciclo não para por dependência ausente.

## Regras

- **Saída bruta, não resumo.** Exit code e output colados. "Os testes passaram"
  não é evidência; é afirmação.
- **Evidência visual é imagem.** Houve degrau 5? Anexe screenshot.
- **Fora de escopo é registrado, não corrigido.**
- `git grep DIAG:` vazio, ou justificado item a item.

## Promoção de instrumento

Quem decide é o **humano, aqui**. Três critérios, todos obrigatórios: valor
diagnóstico recorrente, custo marginal ~zero, sem superfície de risco. Falhou em
um, remove.

## Aprovação nomeada

Crivo de código **não** cobre ação de produção. Deploy, migration e credencial
exigem aprovação separada e nomeada — quem aprovou, o quê, quando. Registre em
`memory/decisoes/`. O agente nunca decide sozinho.
