---
description: Custo medido do ciclo atual — numero, nao opiniao
argument-hint: [nome do ciclo]
---

Custo real do ciclo. Serve o Princípio 9: **número sem medição própria não entra.**

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/5x-cost.py" summary --ciclo $ARGUMENTS
```

Sem argumento, some tudo que está registrado. Antes de disparar um fan-out novo:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/5x-cost.py" estimate --tarefas <N> --modelo sonnet --avg-in 3000 --avg-out 800
```

Estimativa não é medição — rotule como estimativa no relatório.

A tabela de preço tem a data da consulta no cabeçalho. Confira se envelheceu:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/5x-cost.py" precos
```

Preço muda e número velho vira mentira. Se a data está velha, avise o usuário
antes de apresentar qualquer total.

Este é também o comando que responde **"o caveman compensa neste projeto?"** —
com número, comparando ciclos com e sem ele. Não com opinião.
