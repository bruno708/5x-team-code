# Modo Implementação

Rode quando a pergunta aberta é **"isso funciona?"** — causa conhecida, correção a construir.

```
0. APROVAÇÃO          o usuário autorizou implementar
1. BRANCH BASE
2. PLANO              tarefas com critério de aceite
3. GRAFO              dependências → ondas
4. WORKTREES          uma branch por worktree
5. FAN-OUT            subagents escrevem e testam
6. INTEGRAÇÃO         merge na ordem do plano
7. SMOKE + GREP-GATE  toda integração
8. ESCADA DE TESTES
9. CRIVO HUMANO
10. DEV → PRODUÇÃO    aprovação nomeada
```

---

## 2. PLANO

Cada tarefa declara:

- **critério de aceite** — a condição verificável que define "pronto"
- **arquivos que possui** — exclusivo, ninguém mais toca
- **como se prova** — qual teste ou comando demonstra o critério

Critério de aceite sem teste que o prove é critério que ninguém vai conferir. Se não dá para provar, reescreva o critério.

---

## 3. GRAFO

Monte o grafo de dependências e resolva em ondas: tudo que não depende de nada roda junto; o resto espera.

**Duas tarefas com arquivo em comum nunca vão na mesma onda.** Viram sequência, mesmo que logicamente independentes. Sem essa regra o grafo mente.

---

## 4. WORKTREES

`git worktree` dá isolamento real: mesmo repositório, diretórios separados, `.git` compartilhado.

**Uma branch por worktree.** O git recusa a mesma branch em check-out em dois lugares:

```bash
git worktree add ../wt-t1 -b task/t1-decoder
git worktree add ../wt-t2 -b task/t2-upload
git worktree add ../wt-t3 -b task/t3-ui
```

Cada subagent trabalha na sua árvore, roda o teste dele num sistema de arquivos que só ele mexe. O conflito aparece na integração — visível, não silencioso.

Limpeza:

```bash
git worktree remove ../wt-t1
```

Sem isso, cinco agentes escrevendo na mesma árvore significa: o último sobrescreve o primeiro, testes falham por estado que nem existe, e ninguém descobre qual tarefa quebrou o build.

### Prompt do subagent executor

```
Você vai executar UMA tarefa e provar que ela funciona.

TAREFA: <descrição>
CRITÉRIO DE ACEITE: <condição verificável>
WORKTREE: <caminho>  (trabalhe SOMENTE aqui)
ARQUIVOS QUE VOCÊ POSSUI: <lista>  (não toque em nenhum outro)

REGRAS
- Não modifique arquivo fora da sua lista. Se precisar, pare e reporte.
- Menor mudança que satisfaz o critério. Não refatore o que está em volta.
- Rode o teste e cole a saída bruta, com exit code.
- Instrumento temporário leva marcador // DIAG:.

ENTREGA
JSON válido contra schemas/implementacao.schema.json.
Se o critério não foi atendido, reporte honestamente — não maquie.
```

---

## 6-7. INTEGRAÇÃO, SMOKE E GATE

Merge de cada `task/*` na branch base, na ordem do plano.

Depois de **toda** integração, sem exceção:

```bash
# sobe o runtime e carrega a rota afetada
# e:
git grep "DIAG:"
```

**Build passa com JSX órfão.** Compilação verde não garante que a aplicação sobe. O smoke custa ~10 segundos e pega a falha mais cara do sistema.

Não condicione a "houve conflito" — rebase silencioso também quebra runtime, e a economia é irrelevante.

O `git grep DIAG:` tem que voltar vazio ou justificado. Merge ressuscita instrumento removido: sem gate, o lixo volta.

---

## 8. ESCADA DE TESTES

| # | Degrau | O que é | Quando |
|---|---|---|---|
| 1 | Determinístico | lint, tipo, unitário, build | sempre |
| 2 | Smoke + grep-gate | sobe, carrega rota, `git grep DIAG:` | toda integração |
| 3 | Funcional | suíte, mocks, fixtures | se 1 e 2 passaram |
| 4 | **Ambiente real** | navegador real, API real, arquivo real | antes do crivo |
| 5 | Visual | interface | se tocou UI |

### Degrau 4 — ambiente real

**Unit verde não quer dizer que funciona.** Navegador headless empacotado não reproduz o navegador de verdade; fixture sintética não reproduz arquivo de verdade.

Matriz mínima — ajuste ao projeto, mas defina por cicatriz, não por preferência:

| Alvo | Como |
|---|---|
| Chrome real | Playwright com `channel: 'chrome'` — não o Chromium empacotado |
| Safari real | `safaridriver` — o WebKit do Playwright não pega o que o Safari pega |
| Mobile | aparelho físico assistido por telemetria, quando não há automação viável |
| Corpus de arquivos | versionado, com os formatos reais que o produto recebe |

**Gate de ciclo, não de tarefa.** Roda uma vez sobre o conjunto integrado. Rodar por tarefa multiplica o custo por N e importa a instabilidade N vezes.

### Regra do conserto tardio

Conserto feito no degrau 4 ou 5 é código escrito **depois** dos testes passarem. Rejoga do degrau 1 — senão você entrega verde que já não é verde.

---

## Disciplina de código

Menor mudança que satisfaz o critério. Procure código existente antes de escrever novo, prefira recurso nativo da plataforma, evite dependência nova.

Atalho consciente leva comentário nomeando o caminho de upgrade — e entra no crivo como dívida declarada, não como surpresa.
