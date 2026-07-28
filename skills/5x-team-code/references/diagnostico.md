# Modo Diagnóstico

Rode quando a pergunta aberta é **"por que isso está acontecendo?"** — causa desconhecida.

```
0. REPRO            reproduza — ou instrumente até reproduzir
1. ANÁLISE          modelo do problema (leitura cirúrgica permitida)
2. HIPÓTESES        N causas candidatas, falseáveis
3. INDEPENDÊNCIA    dá para testar em paralelo?
4. FAN-OUT          N subagents — somente leitura no alvo
5. INTERPRETAÇÃO    lê evidências, atualiza o modelo
6. rodada 2, rodada 3
7. ESGOTOU 3 RODADAS → PARA DE HIPOTETIZAR E INSTRUMENTA
```

---

## 0. REPRO — pré-condição, não formalidade

**Hipótese sobre bug não reproduzido é chute ao quadrado.** Sem repro você não tem sinal de referência: não consegue distinguir hipótese refutada de teste que simplesmente não exercitou o caminho.

Antes de gerar qualquer hipótese, estabeleça:

- em que condição o problema aparece
- em que condição não aparece
- qual o sinal observável (erro, número, comportamento)

Não reproduziu? **Instrumente até reproduzir.** Instrumentação é a saída nas duas pontas do loop — aqui para conseguir enxergar, e no degrau 7 quando as hipóteses esgotam. Mesma ferramenta, mesmo problema: falta de dado.

Se o bug só existe no aparelho do usuário, telemetria remota é ferramenta de primeira classe, não último recurso.

---

## 1. ANÁLISE

Leia o que for cirúrgico — o arquivo-chave, o stack trace, o commit suspeito. Isso *é* o trabalho.

Delegue se o próximo passo for varredura ampla (mais de ~5 arquivos) — use um subagent de exploração para isso.

**Antes de gerar hipóteses, consulte `memory/hipoteses/` por status `refutada` relacionado.** Hipótese já morta neste projeto não volta para a mesa. É a economia mais barata do sistema.

---

## 2. HIPÓTESES — falseáveis

Cada hipótese precisa de um teste que possa dizer **não**.

| Ruim | Boa |
|---|---|
| "deve ser problema de performance" | "o decode roda 2× por frame — se instrumentar a contagem, aparece o dobro" |
| "algo no upload está errado" | "arquivos acima de 1 GB estouram o limite do multipart — falha em >1 GB, passa em 900 MB" |

Se não dá para escrever a condição que refutaria, não é hipótese — é palpite. Reescreva.

Grave cada uma em `memory/hipoteses/` com status `viva` antes do fan-out.

---

## 3. INDEPENDÊNCIA

Só vão em paralelo se:

- **não competem** — a resposta de uma não torna a outra irrelevante
- **não colidem** — não dependem do mesmo estado mutável

Dependentes → sequencie por **probabilidade ÷ custo de testar**. Testa primeiro o que é barato e provável, igual bisseção.

Duas hipóteses testando o mesmo arquivo em paralelo pagam duas vezes pela mesma informação.

---

## 4. FAN-OUT

Um subagent por hipótese, contexto isolado.

**Regra de escrita:**

- **Permitido:** harness de medição, fixture, instrumentação, telemetria — marcados com `// DIAG:`
- **Proibido:** consertar o código-alvo

Se o agente da H3 conserta, ele contamina a evidência de H1, H2, H4 e H5 rodando ao mesmo tempo — você recebe cinco relatórios sobre cinco versões diferentes do código. Escrever um contador não contamina: ele mede.

### Prompt do subagent investigador

Adapte este esqueleto:

```
Você vai testar UMA hipótese e reportar evidência. Você NÃO conserta nada.

HIPÓTESE: <enunciado falseável>
CONTEXTO: <repro — como o problema aparece>
ARQUIVOS RELEVANTES: <caminhos>

REGRAS
- Você NÃO pode modificar o código-alvo. Nenhuma correção, nenhuma melhoria.
- Você PODE escrever instrumento de observação (log, contador, harness, fixture).
  Todo instrumento leva o marcador // DIAG: na linha.
- Prefira script determinístico a inspeção por leitura sempre que der.
- Se descobrir algo fora da hipótese, registre em fatos_novos. Não investigue por conta própria.

ENTREGA
Retorne JSON válido contra schemas/diagnostico.schema.json.
Cole a saída bruta dos comandos — não resuma.
Se não conseguiu concluir, veredito = "inconclusiva" e explique o que faltou.
Inconclusiva honesta vale mais que confirmada inventada.
```

---

## 5. INTERPRETAÇÃO

Leia os retornos e atualize o modelo do problema.

**`fatos_novos` é o campo que importa mais.** Confirmações fecham; fatos novos abrem. É deles que sai a rodada seguinte.

Atualize `memory/hipoteses/` — status `viva` → `confirmada` ou `refutada`, **mudando o frontmatter, nunca movendo o arquivo.**

---

## 6-7. CONVERGÊNCIA E CORTE

### Convergiu

Causa identificada com evidência. Apresente ao usuário:

- a causa
- a evidência que a sustenta
- as hipóteses refutadas no caminho
- pergunte se implementa a correção

**Não emende direto na implementação.**

### Não convergiu em 3 rodadas → instrumente

Três rodadas sem convergir significa que **falta dado, não falta hipótese**. Quarta rodada de chute mais elaborado não resolve.

Pare de hipotetizar. Escreva medição:

- telemetria no ponto cego
- log estruturado no caminho suspeito
- contador, timing, dump de estado

Depois rode o ciclo de novo com o dado novo em mãos. O fato que resolve normalmente **não estava em nenhuma das hipóteses** — por isso instrumentar funciona onde hipotetizar mais não funcionaria.

### Detector de repetição

Se as hipóteses da rodada N são as da rodada N−1 reformuladas, o loop travou. Vá direto para instrumentação, sem gastar a rodada.

---

## Fechamento

Todo diagnóstico que produziu número vira experimento numerado em `memory/experimentos/` — com pergunta, método, números medidos, conclusão e **a tabela de falsas pistas descartadas**.

Essa tabela é consultada pelos diagnósticos futuros. É o ativo se acumulando.
