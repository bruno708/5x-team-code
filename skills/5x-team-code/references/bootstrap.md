# Bootstrap — instalar o protocolo num projeto

Roda **uma vez por projeto**. Monta o terreno para os ciclos de trabalho.

```
projeto/
├── CLAUDE.md          diretrizes — lidas em toda sessão
├── memory/            vault Obsidian
│   ├── INDEX.md
│   ├── hipoteses/
│   ├── experimentos/
│   └── decisoes/
└── design/            design system e diretrizes visuais
```

Detecte o modo:

```bash
ls package.json src/ app/ 2>/dev/null | head
git log --oneline -1 2>/dev/null
```

Projeto vazio → **Modo A**. Projeto com código → **Modo B**.

---

## CLAUDE.md — dois blocos

| Bloco | Conteúdo | Muda por projeto? |
|---|---|---|
| **Protocolo** | gravado pelo `5x-bootstrap` | não |
| **Projeto** | stack, como rodar, convenções, o que quebra | sim |

Misturar os dois faz o protocolo ser reeditado em cada projeto e derivar da origem. Mantenha separados por cabeçalho explícito.

---

## Modo A — projeto do zero

1. Rode `5x-bootstrap` — cria a estrutura, o `CLAUDE.md` com o bloco de
   protocolo versionado, `memory/INDEX.md` e os templates. **Não copie asset a
   mão**: você não consegue ler os arquivos do plugin, e criar estrutura é
   determinístico — é script (Princípio 4).
2. Escreva o bloco "Este projeto" do `CLAUDE.md` com o que o usuário informar
   (stack, objetivo, como rodar)
3. Preencha `design/` com o design system, se já houver diretriz

Direto. Sem cerimônia.

---

## Modo B — projeto que já existe

**Bootstrap em projeto existente é o modo diagnóstico rodando sobre o projeto inteiro em vez de sobre um bug.** Mesmo motor, mesmas regras.

```
0. BRANCH           branch nova, sempre
1. REPRO            builda? sobe? o que roda hoje?
2. FAN-OUT          análise em paralelo, SOMENTE LEITURA
3. SÍNTESE          consolida os retornos
4. MEMÓRIA          grava com status de confiança
5. LINHA DE BASE    o que é verificável hoje
6. CRIVO            o usuário confere antes de virar canônico
```

### 1. REPRO

Antes de analisar, estabeleça o que funciona hoje:

```bash
# adapte ao ecossistema do projeto
cat package.json 2>/dev/null | head -40
# instala, builda, sobe, testa — nessa ordem, registrando o que falha
```

Isso não é formalidade: é a base de comparação de tudo que vier depois.

### 2. FAN-OUT de análise

Um subagent por eixo, todos **somente leitura**:

| Eixo | Investiga |
|---|---|
| Estrutura | árvore de pastas, convenção de organização, pontos de entrada |
| Stack | linguagens, frameworks, versões, dependências pesadas ou desatualizadas |
| Rotas / superfície | endpoints, telas, comandos — o que o produto expõe |
| Dados | schema, migrations, onde o estado vive |
| Build e deploy | como builda, como sobe, onde roda |
| Testes | o que existe, o que cobre, o que passa |
| Design | tokens **em uso**, paleta real, inconsistências |

Cada um devolve JSON contra `schemas/diagnostico.schema.json`, com `veredito` refletindo confiança.

### 4. MEMÓRIA com status de confiança

**Este é o risco central do Modo B.**

A análise produz *afirmações sobre como o projeto funciona*. Se entram na memória sem verificação, você envenenou o ativo de maior alavancagem do sistema com alucinação — e **toda sessão futura herda o erro como fato estabelecido**.

O protocolo recusa narração no lugar de prova. A instalação dele não pode ser a exceção.

Toda entrada nasce com status no frontmatter:

```yaml
---
status: verificado    # executou e observou
# ou
status: inferido      # leu o código e acredita
---
```

Verificar o que importa é barato: builda? a suíte roda? o entrypoint faz o que o nome diz quando executado? O que não deu para verificar fica `inferido` — e na primeira vez que alguém tropeçar nele, vira `verificado` ou vira correção.

**Memória sem status é memória que envelhece mentindo.**

### 5. LINHA DE BASE

A escada de testes pressupõe que exista o que rodar. Em projeto alheio, frequentemente não existe.

Feche declarando:

- [ ] builda?
- [ ] sobe? (smoke é possível?)
- [ ] tem suíte? passa?
- [ ] dá para rodar em ambiente real? qual?
- [ ] tem lint / checagem de tipo?

**Buraco aqui vira o primeiro ciclo de implementação do projeto** — construir a verificação mínima que o protocolo exige. Sem isso a escada é teatro naquele repositório, e todo crivo posterior é crivo sobre nada.

### 6. O bootstrap é o E0

O Modo B produz números medidos sobre o projeto. Isso é experimento: tem pergunta, método e conclusão.

Grave como `memory/experimentos/E0-bootstrap.md`. É a fundação com a qual todo experimento seguinte se compara.

---

## O que o bootstrap NÃO faz

**Não reorganiza pasta nenhuma.**

Princípio 5: diagnóstico não muda o objeto observado — e bootstrap é diagnóstico. Mover arquivo num projeto que você acabou de conhecer é a ação de maior risco e menor valor do ciclo inteiro, e destrói a base de comparação antes de você ter base de comparação.

O bootstrap escreve **só os artefatos do próprio protocolo**: `CLAUDE.md`, `memory/`, `design/`. Não encosta no layout do projeto.

Reorganização vira ciclo de implementação depois — com plano, worktrees, escada de testes e crivo. Aí sim, e aí com rede.

---

## Design em projeto existente

O design system é **extraído do que existe**, não do que deveria existir: tokens realmente em uso, paleta real, violações reais.

Mesmo status de confiança. Aspiração vai para `decisoes/`, não para `design/`.
