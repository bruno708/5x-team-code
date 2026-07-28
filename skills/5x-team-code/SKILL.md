---
name: 5x-team-code
description: Protocolo de desenvolvimento baseado em evidência — diagnóstico por hipóteses falseáveis testadas em paralelo, implementação com worktrees isoladas, escada de testes até ambiente real, e memória de projeto em vault Obsidian. Use SEMPRE que o usuário relatar um bug ou comportamento estranho ("está dando erro", "não funciona", "por que isso acontece", "descobre o que está causando"), pedir para investigar causa raiz, pedir para implementar correção ou feature depois de um diagnóstico, pedir para instalar/iniciar o protocolo num projeto ("roda o protocolo aqui", "instala o protocolo", "analisa esse projeto e monta a memória"), ou mencionar hipóteses, evidência, experimento numerado, memória do projeto, worktree, crivo. Use mesmo que o usuário não cite o protocolo pelo nome — se há bug para investigar ou ciclo de implementação para conduzir, este protocolo se aplica.
---

# Protocolo de Desenvolvimento

Sistema de trabalho baseado em evidência. Divide o trabalho por **camada cognitiva e custo**: quem pensa gera hipóteses e interpreta; subagents executam em paralelo, isolados, e devolvem evidência estruturada.

A regra que governa tudo: **narração não é prova.**

---

## Primeiro: em que estado está o projeto?

Antes de qualquer coisa, verifique se o protocolo já está instalado:

```bash
ls CLAUDE.md memory/ design/ 2>/dev/null
```

| Situação | Ação |
|---|---|
| Falta `memory/` ou `CLAUDE.md` | **Bootstrap primeiro** → `/5x-init`, ou leia `references/bootstrap.md` |
| Estrutura existe | Leia `memory/INDEX.md` e siga para o modo certo |

**Nunca carregue o vault inteiro no contexto.** O `INDEX.md` é o mapa; o conteúdo vem por relevância, sob demanda. Carregar tudo toda sessão contradiz a disciplina de token do próprio protocolo.

---

## Modos

Escolha pelo tipo de pergunta que está aberta:

| Pergunta do usuário | Modo | Referência |
|---|---|---|
| "por que isso está acontecendo?" | **Diagnóstico** (`/5x-diag`) | `references/diagnostico.md` |
| "implementa isso" (causa já conhecida) | **Implementação** (`/5x-build`) | `references/implementacao.md` |
| "instala o protocolo aqui" | **Bootstrap** (`/5x-init`) | `references/bootstrap.md` |

Diagnóstico e implementação são o mesmo motor. Muda **uma coisa: permissão de escrita no código-alvo.**

| | Diagnóstico | Implementação |
|---|---|---|
| Unidade | hipótese | tarefa |
| Pergunta | isso é verdade? | isso funciona? |
| Escrita no alvo | não | sim |
| Escrita de instrumento | sim | sim |
| Convergência | causa encontrada | tudo verde |

Não pule do diagnóstico para a correção sem passar pelo usuário. Achou a causa → apresente a evidência → pergunte se implementa.

---

## Princípios

Heurísticas com faixa de aplicação, não dogmas. Duas são absolutas e estão marcadas.

**1. Delegue por volume, não por hierarquia.**
Varredura ampla ou edição mecânica em massa → delega para subagent. Leitura cirúrgica de arquivo-chave → faz direto. Ler o arquivo certo *é* o trabalho de diagnóstico; proibir isso deixa o processo mais lento e mais burro.

**2. Delegue por ação, não por estoque.**
O gatilho é o próximo passo, não uma estimativa de contexto: vai varrer mais de ~5 arquivos ou editar em massa? Delega. Vai abrir o arquivo-chave e ler? Faz direto. Não tente medir a própria janela — o modelo não a enxerga com precisão.

**3. Nada volta como texto livre.**
Todo retorno de subagent segue o JSON Schema em `schemas/`. Sem estrutura, não há interpretação consistente entre rodadas.

**4. Determinístico é script, nunca LLM. [ABSOLUTO]**
Se a resposta sai de `grep`, `ffprobe`, um teste, um diff ou vinte linhas de Python — escreva o script. Modelo não é para o que código resolve.

**5. Diagnóstico não muda o objeto observado.**
Instrumento de observação é escrita permitida (harness, fixture, telemetria). Consertar o código-alvo durante o fan-out é proibido: contamina a evidência das outras hipóteses rodando em paralelo.

**6. Tarefa paralela possui seus arquivos, exclusivamente. [ABSOLUTO]**
Duas tarefas que tocam o mesmo arquivo nunca vão na mesma onda. Viram sequência.

**7. Todo loop para em 3 rodadas.**
Três rodadas sem convergir significa que **falta dado, não falta hipótese**. A saída não é uma quarta rodada de chute mais elaborado — é instrumentar.

**8. Crivo é sobre evidência de máquina.**
Exit code, diff, saída bruta, screenshot. Nunca a narração do agente sobre o próprio trabalho.

**9. Número sem medição própria não entra.**
Vale para benchmark de ferramenta igual vale para relatório de agente.

---

## Contrato de retorno

Todo subagent devolve JSON validado contra o schema do modo:

- `schemas/diagnostico.schema.json` — hipótese testada (subagent `5x-investigador`)
- `schemas/implementacao.schema.json` — tarefa executada (subagent `5x-executor`)

**Schema sem validador é honra.** Rode o validador em todo retorno:

```bash
5x-validate retorno.json --schema diagnostico
```

Exit 1 aponta o campo que falta. Retorno que não passa não entra na interpretação.

O campo `fatos_novos` no schema de diagnóstico é o motor de convergência. É dele que sai a rodada seguinte — e é ele que separa investigação que anda de investigação que gira em círculo.

Relatório útil fica tipicamente entre 500 e 1.500 tokens. **Não comprima abaixo disso** — comprimir demais destrói o valor do fan-out.

---

## Memória

```
memory/
├── INDEX.md
├── hipoteses/       status no frontmatter: viva | confirmada | refutada
├── experimentos/    E1, E2… com números medidos
└── decisoes/
```

**Hipótese viva vira morta mudando o status no frontmatter — nunca movendo o arquivo.** Mover quebra os wikilinks, e o grafo é o ativo.

**Hipótese morta é o item mais barato do sistema.** Custa uma linha e economiza rodadas inteiras: antes de gerar hipóteses novas, leia o que já foi refutado neste projeto.

Templates em `assets/hipotese.template.md` e `assets/experimento.template.md`.

---

## Estado entre sessões

`memory/ESTADO.md` é arquivo **único e sobrescrito** — não é log. Histórico já
vive nas hipóteses e experimentos.

O estado é **derivado, não narrado**: hipótese com `status: viva` no frontmatter
*é* pendência. O script lê o vault e monta o bloco; não pede pro modelo lembrar,
e não inventa — se o vault não diz, o campo fica vazio.

```bash
5x-state --write   # deriva e sobrescreve
5x-state --read    # imprime para injeção
```

Os hooks do plugin fazem isso sozinhos: injetam na abertura da sessão, salvam
antes da compactação, reinjetam depois, e salvam no fim. Todos com timeout de 3s
e **fail-silent** — hook nunca bloqueia sessão.

Estado de runtime vive em `.5x/` (`ciclo.json`, `plano.json`, `tarefas.jsonl`,
`custo.jsonl`). A pasta é nossa e não polui a árvore do usuário.

---

## Onde o ciclo para e pergunta

Nos limites em que a próxima ação **gasta dinheiro ou muda estado**:

| Parou em | Pergunta |
|---|---|
| hipóteses levantadas | disparo o fan-out? |
| fan-out interpretado | rodada 2 ou converge? |
| 3 rodadas esgotadas | escrevo o instrumento? |
| causa encontrada | implemento? |
| plano montado | disparo as ondas? |
| ciclo verde | crivo |
| crivo aprovado | aprovação nomeada para produção |

---

## Scripts

Determinístico é script, nunca LLM. Invocáveis como comando bare (o `bin/` do plugin entra no PATH do Bash),
Python 3 stdlib, com `--help`, saída JSON e exit code significativo.

| Script | Função |
|---|---|
| `5x-waves` | grafo → ondas, com a regra de ownership |
| `5x-validate` | valida retorno contra o JSON Schema |
| `5x-cost` | registra e soma custo real por tarefa/ciclo |
| `5x-state` | deriva e lê o estado do ciclo |
| `5x-gate` | grep-gate de instrumentos |
| `5x-worktree` | cria e remove worktrees por tarefa |
| `5x-bootstrap` | cria a estrutura do protocolo no projeto |
| `5x-deps-install` | instala e configura ponytail e caveman |

---

## Instrumentação

Todo instrumento nasce marcado com `// DIAG:` (ou o equivalente da linguagem).

Gate na integração:

```bash
5x-gate   # exit 1 se sobrou instrumento
```

Os comandos acima só existem quando o plugin está ativo. Se um deles voltar
`command not found`, o plugin não está carregado — reporte, não improvise a mão.

Tem que voltar vazio, ou com justificativa explícita no crivo. **Marcador sem gate não segura nada** — merge ressuscita lixo removido.

No fim do ciclo o instrumento sai, ou é promovido a permanente pelo humano no crivo. Promoção exige os três: provou valor recorrente, custo marginal ~zero, sem superfície de risco.

---

## Escada de testes

Ordem obrigatória, do barato ao caro:

| # | Degrau | Quando |
|---|---|---|
| 1 | Determinístico — lint, tipo, unitário, build | sempre |
| 2 | Smoke de runtime + `git grep DIAG:` | toda integração |
| 3 | Funcional — suíte, mocks, fixtures | se 1 e 2 passaram |
| 4 | **Ambiente real** — navegador real, API real, arquivo real | antes do crivo, obrigatório |
| 5 | Visual | se tocou interface |

**Unit verde não quer dizer que funciona.** O degrau 4 é o maior gerador de verdade do sistema — e o mais caro e instável, por isso é gate de ciclo (roda uma vez sobre o conjunto integrado), nunca de tarefa.

Conserto feito no degrau 4 ou 5 é código escrito depois dos testes passarem. **Rejoga do degrau 1.**

Detalhes e matriz de ambiente real em `references/implementacao.md`.

---

## Crivo

Fim de ciclo, sempre. Formato completo em `references/crivo.md`.

O relatório entrega evidência, não resumo. E **ação de produção — deploy, migration, credencial — exige aprovação nomeada e separada.** O agente nunca decide sozinho.

---

## Erros que este protocolo existe para evitar

- Hipótese sobre bug que ninguém reproduziu — chute ao quadrado
- Agente que "aproveita e conserta" no meio do fan-out — evidência contaminada
- Dois agentes escrevendo na mesma árvore — o último sobrescreve, e ninguém sabe qual quebrou
- Memória gravada por inferência sem status — erro herdado como fato por todas as sessões futuras
- Crivo sobre narração — aprovação teatral
- Reorganizar pastas de um projeto que você acabou de conhecer
