<!-- 5x-team protocolo v1.0.1 -->
<!-- ══════════════════════════════════════════════════════════════
     BLOCO DE PROTOCOLO — importado, igual em todo projeto.
     Não edite aqui. Edite na skill e reimporte.
     ══════════════════════════════════════════════════════════════ -->

# Protocolo de trabalho

Este projeto opera sob o protocolo de desenvolvimento baseado em evidência.
A skill `5x-team-code` carrega o detalhe. Este bloco é o mínimo que vale em toda sessão.

## Abertura de sessão

Leia `memory/INDEX.md` e `memory/ESTADO.md`. **Não carregue o vault inteiro** —
puxe por relevância. O `ESTADO.md` é derivado do vault por script, sobrescrito a
cada ciclo: não edite a mão.

## Comandos

`/5x-init` `/5x-diag` `/5x-build` `/5x-estado` `/5x-custo` `/5x-crivo` `/5x-deps`

## Regra que governa tudo

**Narração não é prova.** Nada é dado como feito sem exit code, saída bruta, diff ou imagem.

## Princípios

1. **Delegue por volume, não por hierarquia** — varredura e edição em massa vão para subagent; leitura cirúrgica se faz direto
2. **Delegue por ação, não por estoque** — mais de ~5 arquivos ou edição em massa → delega
3. **Nada volta como texto livre** — subagent devolve JSON contra schema
4. **Determinístico é script, nunca LLM** [absoluto]
5. **Diagnóstico não muda o objeto observado** — instrumento é escrita permitida; conserto não
6. **Tarefa paralela possui seus arquivos, exclusivamente** [absoluto]
7. **Todo loop para em 3 rodadas** — depois disso, instrumenta
8. **Crivo é sobre evidência de máquina**
9. **Número sem medição própria não entra**

## Antes de investigar

Consulte `memory/hipoteses/` por status `refutada`. Hipótese já morta neste projeto não volta para a mesa.

## Antes de hipotetizar

Reproduza. Hipótese sobre bug não reproduzido é chute ao quadrado.

## Instrumentação

Todo instrumento temporário leva `// DIAG:`. Na integração:

```bash
git grep "DIAG:"
```

Vazio, ou justificado no crivo.

## Paralelismo

Uma branch por worktree — o git recusa a mesma branch em dois lugares:

```bash
git worktree add ../wt-t1 -b task/t1-nome
```

## Escada de testes

1. determinístico → 2. smoke + grep-gate → 3. funcional → 4. **ambiente real** → 5. visual

Conserto feito no degrau 4 ou 5 rejoga do degrau 1.

## Produção

Deploy, migration e credencial exigem **aprovação nomeada**, separada do crivo de código.

<!-- ══════════════════════════════════════════════════════════════
     FIM DO BLOCO DE PROTOCOLO
     Abaixo desta linha: diretrizes específicas deste projeto.
     ══════════════════════════════════════════════════════════════ -->

# Este projeto

## Stack

<preencher>

## Como rodar

```bash
# instalar
# dev
# build
# testes
```

## Ambiente real disponível

<quais alvos, como rodar>

## Convenções

<padrões que este projeto segue>

## O que quebra fácil

<armadilhas conhecidas — alimentado pelos ciclos>
