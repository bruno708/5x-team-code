---
description: Instala e configura as dependencias externas (ponytail, caveman)
argument-hint: [--check | --with-mem]
---

Instale e configure as dependências externas do protocolo:

```bash
5x-deps-install $ARGUMENTS
```

`--check` só diagnostica. `--with-mem` inclui `claude-mem` (opcional; complementa
o vault curado, não substitui).

## O que entra e por quê

| Dependência | Uso | Padrão |
|---|---|---|
| `ponytail` | `/ponytail-review` antes do crivo, `/ponytail-audit` no bootstrap modo B, `/ponytail-debt` na dívida declarada | ligado, `full` |
| `caveman` | `/caveman-compress CLAUDE.md` uma vez, `/caveman-stats` para medir | compressão sim; sempre-ligado **não** |
| `claude-mem` | captura automática por hooks | opcional, desligado |

**Por que o caveman sempre-ligado fica desligado:** ele adiciona ~1–1,5k tokens
de entrada por turno, e o benchmark agêntico do ponytail mediu +7% tokens contra
baseline. Nossa carga já é enxuta por construção — contratos JSON de 500–1.500
tokens. Ligar por padrão violaria o Princípio 9. O `/caveman-compress` é
mecanismo diferente: reescrita única de arquivo, sem overhead por turno. Esse entra.

**Por que o `PONYTAIL_SUBAGENT_MATCHER` é restrito:** por padrão o ponytail injeta
o ruleset dele em todo subagent. Os investigadores do protocolo são somente
leitura — não escrevem código, então não há nada a enxugar. O matcher casa só
`^5x-team:5x-executor$`.

Depois de instalar, rode uma vez e meça:

```
/caveman-compress CLAUDE.md
/caveman-stats
```

Nada aqui é obrigatório. Ausente, o script avisa e o ciclo segue — só mais caro.
