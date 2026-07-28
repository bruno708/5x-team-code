---
description: Inicia o modo implementacao — plano, ondas, worktrees, escada de testes
argument-hint: [o que implementar, com a causa ja conhecida]
---

Modo implementação. Pergunta aberta: **"isso funciona?"** — causa conhecida.

Siga `${CLAUDE_PLUGIN_ROOT}/skills/5x-team-code/references/implementacao.md`.

Alvo: $ARGUMENTS

## Pré-condição

O usuário autorizou implementar. Se a causa ainda não está estabelecida com
evidência, volte para `/5x-diag`.

## Plano → grafo → ondas

Cada tarefa declara **critério de aceite**, **arquivos que possui** (exclusivo) e
**como se prova**. Grave o plano e resolva as ondas com script — não a olho:

```bash
mkdir -p .5x
# .5x/plano.json: {"tasks":[{"id":"T1","criterio":"...","depends_on":[],"owns":["src/a.py"]}]}
5x-waves .5x/plano.json
```

**Duas tarefas com arquivo em comum nunca vão na mesma onda**, mesmo sem
dependência declarada. O script força a sequência; sem isso o grafo mente.
Ciclo detectado → exit 1 com o ciclo apontado, e o plano está errado.

## Worktrees

Uma branch por worktree — o git recusa a mesma branch em check-out em dois lugares:

```bash
5x-worktree add T1 task/t1-decoder
```

## Fan-out

Um subagent `5x-executor` por tarefa da onda. Cada retorno é validado e
registrado — é daí que o hook de `SubagentStop` sabe que a onda fechou:

```bash
5x-validate retorno.json --schema implementacao
cat retorno.json | python3 -c 'import sys,json;print(json.dumps(json.load(sys.stdin)))' >> .5x/tarefas.jsonl
5x-cost record --ciclo <c> --tarefa T1 --modelo sonnet --tokens-in <n> --tokens-out <n>
```

## Integração — toda vez, sem exceção

```bash
# sobe o runtime e carrega a rota afetada, depois:
5x-gate
```

Build passa com JSX órfão. Compilação verde não garante que a aplicação sobe.

## Escada de testes

1 determinístico → 2 smoke + grep-gate → 3 funcional → **4 ambiente real** → 5 visual.

Degrau 4 é gate de **ciclo**, não de tarefa. Conserto feito no degrau 4 ou 5 é
código escrito depois dos testes passarem: **rejoga do degrau 1**.

## Limpeza e crivo

```bash
5x-worktree clean
```

Tudo verde → `/5x-crivo`. Pare e pergunte antes de disparar as ondas e antes do
crivo. Ação de produção exige aprovação nomeada, separada.
