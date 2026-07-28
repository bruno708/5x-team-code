# 5x-team

Plugin do Claude Code que instala um protocolo de desenvolvimento **baseado em
evidência** em qualquer projeto, com uma linha de comando.

A regra que governa tudo: **narração não é prova.**

## Instalar

```bash
claude plugin marketplace add <user>/5x-team
claude plugin install 5x-team@5x-team
```

Depois, no projeto:

```
/5x-init
```

## Os dois modos

Diagnóstico e implementação são o mesmo motor. Muda **uma coisa: permissão de
escrita no código-alvo.**

| | Diagnóstico (`/5x-diag`) | Implementação (`/5x-build`) |
|---|---|---|
| Unidade | hipótese | tarefa |
| Pergunta | isso é verdade? | isso funciona? |
| Escrita no alvo | não | sim |
| Escrita de instrumento | sim | sim |
| Isolamento | contexto | contexto + worktree |
| Convergência | causa encontrada | tudo verde |

Diagnóstico levanta hipóteses **falseáveis**, testa em paralelo com subagents
somente leitura, e para em 3 rodadas — três rodadas sem convergir significa que
falta dado, não falta hipótese. Aí instrumenta.

Implementação resolve o plano em ondas, isola cada tarefa numa worktree própria,
e sobe a escada de testes até **ambiente real** antes do crivo.

## Comandos

| Comando | Função |
|---|---|
| `/5x-init` | bootstrap do protocolo no projeto |
| `/5x-diag` | inicia modo diagnóstico |
| `/5x-build` | inicia modo implementação |
| `/5x-estado` | imprime onde estamos / onde vamos |
| `/5x-custo` | custo medido do ciclo atual |
| `/5x-crivo` | monta o relatório de crivo |
| `/5x-deps` | instala e configura as dependências externas |

## Por que plugin e não skill

Skill é uma pasta de markdown e **não registra hooks**. Duas funcionalidades
centrais do protocolo — persistência de estado entre sessões e encadeamento
automático de ondas — dependem de hooks. Como skill puro, elas não existem.

Os hooks do plugin injetam `INDEX.md` + `ESTADO.md` na abertura da sessão, salvam
o estado antes da compactação, reinjetam depois, e sinalizam quando uma onda
fecha. Todos com timeout de 3s e **fail-silent** — hook nunca bloqueia sessão.

O estado é **derivado**, não narrado: hipótese com `status: viva` no frontmatter
*é* pendência. O script lê o vault e monta o bloco. Não pede pro modelo lembrar,
e não inventa — se o vault não diz, o campo fica vazio.

## Scripts

Determinístico é script, nunca LLM. Python 3 stdlib apenas, com `--help`, saída
JSON e exit code significativo.

| Script | Função |
|---|---|
| `5x-waves.py` | grafo de dependências → ondas de paralelismo |
| `5x-validate.py` | valida retorno de subagent contra o JSON Schema |
| `5x-cost.py` | registra e soma custo real por tarefa/ciclo |
| `5x-state.py` | escreve e lê o estado do ciclo |
| `5x-gate.py` | grep-gate de instrumentos (`DIAG:`) |
| `5x-worktree.sh` | cria e remove worktrees por tarefa |

`5x-waves.py` tem uma regra que o grafo declarado não tem: **duas tarefas com
arquivo em comum em `owns` nunca vão na mesma onda**, mesmo sem dependência
declarada. Sem isso o grafo mente e dois agentes escrevem na mesma árvore.

`5x-validate.py` é o que torna o contrato real — schema sem validador é honra.

## Dependências externas

Nenhuma é obrigatória. Ausente, o `/5x-deps` avisa e o ciclo roda até o fim — só
mais caro.

| Dependência | O que fazemos com ela | Padrão |
|---|---|---|
| [ponytail](https://github.com/DietrichGebert/ponytail) | `/ponytail-review` antes do crivo, `/ponytail-audit` no bootstrap de projeto existente, `/ponytail-debt` alimenta a dívida declarada | ligado, modo `full` |
| [caveman](https://github.com/JuliusBrussee/caveman) | `/caveman-compress` no `CLAUDE.md` uma vez, `/caveman-stats` para medir | compressão sim; sempre-ligado **não** |
| [claude-mem](https://github.com/thedotmack/claude-mem) | captura automática por hooks; complementa o vault curado, não substitui | opcional, desligado |

**O caveman sempre-ligado fica desligado por padrão.** O README dele avisa que
adiciona ~1–1,5k tokens de entrada por turno, e o benchmark agêntico do ponytail
mediu caveman em +7% tokens contra baseline. A carga deste protocolo já é enxuta
por construção — contratos JSON de 500–1.500 tokens. Ligar por padrão violaria o
nosso próprio Princípio 9. O `/caveman-compress` é mecanismo diferente:
reescrita única de arquivo, sem overhead por turno. Esse entra.

**O `PONYTAIL_SUBAGENT_MATCHER` é restrito a `^5x-team:5x-executor$`.** Por padrão
o ponytail injeta o ruleset dele em todo subagent. Os investigadores do protocolo
são somente leitura — não escrevem código, então não há nada a enxugar.

## Créditos

- [caveman](https://github.com/JuliusBrussee/caveman) (MIT) — dependência.
  Instalamos e configuramos; o nome é deles e continua deles.
- [ponytail](https://github.com/DietrichGebert/ponytail) (MIT) — dependência,
  mesmo tratamento.
- [aiox-squads](https://github.com/SynkraAI/aiox-squads) — **referência
  arquitetural apenas**. O repositório não tem arquivo de licença, então nenhum
  arquivo foi copiado. A arquitetura de hooks e o formato `record`/`summary`/
  `estimate` do rastreio de custo foram estudados lá e **reimplementados do
  zero** contra o nosso contrato. Ordenação topológica de Kahn é matemática de
  domínio público; tabela de preço é informação pública.

O que é nosso: a camada cognitiva, o contrato de evidência, o loop de
convergência com corte em 3 rodadas, a regra de ownership nas ondas, e a escada
de testes até ambiente real.

## Permissões

Os scripts viram comandos bare (`5x-bootstrap`, `5x-waves`, `5x-gate`…) porque o
`bin/` do plugin entra no PATH do Bash. Na primeira vez que um deles roda, o
Claude Code pede aprovação — escolha "sempre permitir" e não pergunta mais.

Path absoluto para dentro do plugin **não funciona**: o harness bloqueia acesso a
arquivo fora do diretório do projeto, e o comando trava sem criar nada. Por isso
tudo passa pelo `bin/`.

Para liberar de uma vez em `.claude/settings.json` do projeto:

```json
{ "permissions": { "allow": ["Bash(5x-bootstrap:*)", "Bash(5x-waves:*)", "Bash(5x-validate:*)", "Bash(5x-state:*)", "Bash(5x-cost:*)", "Bash(5x-gate:*)", "Bash(5x-worktree:*)"] } }
```

## Desenvolver o plugin

`version` no `plugin.json` **pina o cache**: com `1.0.0` fixo, editar o repositório
não propaga para a instalação — `claude plugin update` responde *already at the
latest version*. Para ver uma edição valer:

```bash
claude plugin uninstall 5x-team@5x-team && claude plugin install 5x-team@5x-team
```

Ou bumpe a versão no `plugin.json`. Em release, bumpe sempre — é o que faz o
usuário receber a atualização.

## Divergências entre o briefing e a documentação oficial

A documentação vence, e aqui está o que mudou:

1. **Hooks não passam por `.claude/settings.json`.** O briefing previa backup e
   merge do `settings.json` para registrar hooks. A documentação oficial define
   `hooks/hooks.json` na raiz do plugin como local nativo: o Claude Code carrega
   os hooks quando o plugin está ativo e os descarrega quando é desativado.
   Resultado: **não tocamos no `settings.json` do usuário para registrar hook
   nenhum**, e instalar duas vezes não pode duplicar registro. O único write em
   `settings.json` é o `install-deps.sh`, que grava as duas variáveis de ambiente
   do ponytail — e esse faz backup com timestamp, faz merge e é idempotente.

2. **`SessionStart(compact)` não é o evento certo para restaurar.** A
   documentação lista `PostCompact` como evento próprio. Registramos os dois:
   `SessionStart` com matcher `compact` e o comportamento de `--restore`.

3. **`timeout` de hook é em segundos, com padrão 600.** Fixado em 3 em todos,
   como o briefing pede.

4. **Agentes não estavam no briefing.** Foram adicionados dois — `5x-investigador`
   (somente leitura) e `5x-executor` (escreve na worktree). Sem eles o
   `PONYTAIL_SUBAGENT_MATCHER` "que casa só executores" não teria o que casar: o
   matcher precisa de um nome de tipo de agente que exista de fato.

## Licença

MIT. Ver [LICENSE](LICENSE).
