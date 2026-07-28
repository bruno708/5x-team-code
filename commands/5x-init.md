---
description: Bootstrap do protocolo 5x neste projeto — CLAUDE.md, memory/, design/
---

Instale o protocolo 5x-team neste projeto. Siga
`${CLAUDE_PLUGIN_ROOT}/skills/5x-team-code/references/bootstrap.md` inteiro.

## Regra que não se negocia

**Bootstrap é diagnóstico, e diagnóstico não muda o objeto observado.**
Não mova, renomeie nem reorganize nenhum arquivo do usuário. O bootstrap escreve
**só** os artefatos do protocolo: `CLAUDE.md`, `memory/`, `design/`.

## Passos

1. Detecte o modo:

```bash
ls CLAUDE.md memory/ design/ 2>/dev/null; ls package.json pyproject.toml src/ app/ 2>/dev/null | head; git log --oneline -1 2>/dev/null
```

Projeto vazio → **Modo A**. Projeto com código → **Modo B** (fan-out de análise
somente leitura, com status de confiança em toda entrada de memória).

2. Crie a estrutura, sem tocar no que já existe:

```
CLAUDE.md          bloco de protocolo + bloco do projeto
memory/            INDEX.md, hipoteses/, experimentos/, decisoes/
design/
```

3. O bloco de protocolo do `CLAUDE.md` é copiado de
   `${CLAUDE_PLUGIN_ROOT}/skills/5x-team-code/assets/CLAUDE-protocolo.md`, com o
   marcador de versão no topo:

```markdown
<!-- 5x-team protocolo v1.0.0 -->
```

Sem ele não dá para saber qual projeto está com bloco velho. Se o arquivo já tem
um marcador de versão diferente, avise antes de substituir.

4. `memory/INDEX.md` sai de `assets/INDEX.template.md`. Templates de hipótese e
   experimento ficam em `assets/`.

5. No **Modo B**, feche declarando a linha de base (builda? sobe? tem suíte?
   ambiente real? lint?) e grave `memory/experimentos/E0-bootstrap.md`. Buraco na
   linha de base vira o primeiro ciclo de implementação do projeto.

6. Registre o ciclo para os hooks derivarem estado:

```bash
mkdir -p .5x && printf '{"fase":"bootstrap","ciclo":"bootstrap","proximo_passo":"<o que vem agora>"}' > .5x/ciclo.json
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/5x-state.py" --write
```

7. Ofereça `/5x-deps` para instalar ponytail e caveman. O protocolo roda sem
   eles — só mais caro.

Ao final, mostre o que foi criado e **pergunte antes** de qualquer passo que
gaste dinheiro (fan-out) ou mude estado.
