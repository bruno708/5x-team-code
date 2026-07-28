---
description: Inicia o modo diagnostico — hipoteses falseaveis testadas em paralelo
argument-hint: [descricao do bug ou comportamento estranho]
---

Modo diagnóstico. Pergunta aberta: **"por que isso está acontecendo?"**

Siga `${CLAUDE_PLUGIN_ROOT}/skills/5x-team-code/references/diagnostico.md`.

Alvo: $ARGUMENTS

## O loop

```
0. REPRO            reproduza — ou instrumente até reproduzir
1. ANÁLISE          leitura cirúrgica permitida; varredura ampla vai para subagent
2. HIPÓTESES        N causas falseáveis, gravadas em memory/hipoteses/ com status: viva
3. INDEPENDÊNCIA    dá para testar em paralelo?
4. FAN-OUT          um subagent 5x-investigador por hipótese
5. INTERPRETAÇÃO    fatos_novos é o motor da rodada seguinte
6. rodada 2, rodada 3
7. ESGOTOU 3 RODADAS → PARA DE HIPOTETIZAR E INSTRUMENTA
```

## Antes de gerar hipótese

Consulte `memory/hipoteses/` por `status: refutada`. Hipótese já morta neste
projeto não volta para a mesa — é a economia mais barata do sistema.

## Nos limites, pare e pergunte

| Parou em | Pergunta |
|---|---|
| hipóteses levantadas | disparo o fan-out? (estime o custo primeiro) |
| fan-out interpretado | rodada 2 ou converge? |
| 3 rodadas esgotadas | escrevo o instrumento? |
| causa encontrada | implemento? |

Estime antes de disparar:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/5x-cost.py" estimate --tarefas <N> --modelo sonnet --avg-in 3000 --avg-out 800
```

## Contrato

Cada subagent devolve JSON validado. Rejeite retorno que não passa:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/5x-validate.py" retorno.json --schema diagnostico
```

Atualize o status no frontmatter da hipótese — `viva` → `confirmada` | `refutada`.
**Nunca movendo o arquivo**: mover quebra os wikilinks, e o grafo é o ativo.

Registre o ciclo para os hooks derivarem estado:

```bash
mkdir -p .5x && printf '{"fase":"diagnostico rodada 1","ciclo":"%s","proximo_passo":"<acao concreta>"}' "<nome>" > .5x/ciclo.json
```

Convergiu? Apresente causa, evidência e as hipóteses refutadas no caminho.
**Não emende direto na implementação** — pergunte.
