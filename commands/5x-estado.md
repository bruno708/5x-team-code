---
description: Onde estamos e onde vamos — derivado do vault, nao narrado
---

Imprima o estado do ciclo. Ele é **derivado** do vault, não lembrado:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/5x-state.py" --write
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/5x-state.py" --read
```

Mostre a saída ao usuário como veio. Se um campo está vazio, o vault não diz —
**não preencha por inferência**. Memória gravada por inferência sem status é
erro herdado como fato por todas as sessões futuras.

Faltando `memory/`? O protocolo não está instalado aqui: ofereça `/5x-init`.
