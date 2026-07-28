---
description: Bootstrap do protocolo 5x neste projeto — CLAUDE.md, memory/, design/
---

Instale o protocolo 5x-team neste projeto.

## 1. Rode o script. Não copie arquivo a mão.

Criar a estrutura é determinístico, então é script (Princípio 4). O script lê os
assets do próprio plugin — você não consegue lê-los, o harness gateia acesso a
arquivo fora do diretório do projeto.

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/5x-bootstrap.py"
```

Ele cria `CLAUDE.md` (bloco de protocolo, com marcador de versão), `memory/` com
`INDEX.md` e os templates, e `design/`. **Nunca sobrescreve o que já existe** e é
idempotente. Leia o JSON de saída: `criados`, `ja_existiam`, `avisos`.

Se o script não estiver acessível, pare e reporte — **não improvise o conteúdo do
bloco de protocolo**. Bloco inventado é pior que bloco ausente.

## 2. Regra que não se negocia

**Bootstrap é diagnóstico, e diagnóstico não muda o objeto observado.**
Não mova, renomeie nem reorganize nenhum arquivo do usuário. Reorganização vira
ciclo de implementação depois — com plano, worktrees, escada de testes e crivo.

## 3. Detecte o modo

```bash
ls package.json pyproject.toml Cargo.toml go.mod src/ app/ 2>/dev/null | head; git log --oneline -1 2>/dev/null
```

**Projeto vazio → Modo A.** Preencha o bloco "Este projeto" do `CLAUDE.md` com o
que o usuário informar (stack, objetivo, como rodar). Pergunte o que faltar.
Acabou.

**Projeto com código → Modo B.** É o modo diagnóstico rodando sobre o projeto
inteiro em vez de sobre um bug. Siga
`${CLAUDE_PLUGIN_ROOT}/skills/5x-team-code/references/bootstrap.md`:

```
1. REPRO          builda? sobe? o que roda hoje?
2. FAN-OUT        subagents 5x-investigador, SOMENTE LEITURA, um por eixo
3. SÍNTESE        consolida os retornos
4. MEMÓRIA        grava com status: verificado | inferido
5. LINHA DE BASE  o que é verificável hoje
6. CRIVO          o usuário confere antes de virar canônico
```

**Pare e pergunte antes do fan-out** — ele gasta dinheiro. Estime:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/5x-cost.py" estimate --tarefas 7 --modelo sonnet --avg-in 3000 --avg-out 800
```

Toda entrada de memória nasce com `status: verificado` (executou e observou) ou
`inferido` (leu e acredita). **Memória sem status é memória que envelhece
mentindo** — e toda sessão futura herda o erro como fato.

Feche o Modo B com `memory/experimentos/E0-bootstrap.md` e a linha de base:
builda? sobe? tem suíte? ambiente real? lint? Buraco aqui vira o primeiro ciclo
de implementação do projeto.

## 4. Registre o ciclo

Os hooks derivam o estado daqui:

```bash
mkdir -p .5x
printf '{"fase":"bootstrap","ciclo":"bootstrap","proximo_passo":"<acao concreta>"}' > .5x/ciclo.json
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/5x-state.py" --write
```

## 5. Feche

Mostre o que foi criado, o que já existia e os avisos. Ofereça `/5x-deps` —
o protocolo roda sem ponytail e caveman, só mais caro.
