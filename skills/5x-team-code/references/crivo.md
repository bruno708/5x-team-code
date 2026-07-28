# Crivo

Fim de ciclo. O momento em que o humano aprova.

**Se o relatório for narração do agente, o crivo é teatro** — você está confiando na redação de quem fez a prova e se autocorrigiu.

## Formato

```markdown
## Ciclo: <o que foi feito>

### Critérios
| Critério | Prova | Comando | Exit | 
|---|---|---|---|
| <condição> | <teste> | <comando> | 0 |

Saída bruta:
<colada, não resumida>

### Escada
- [ ] 1 determinístico
- [ ] 2 smoke + grep-gate
- [ ] 3 funcional
- [ ] 4 ambiente real — qual alvo, qual evidência
- [ ] 5 visual — screenshots anexados

### Mudanças
- arquivos tocados: <lista>
- diff: <completo>

### Instrumentos
- criados: <lista com marcador DIAG>
- removidos / promovidos: <quais e por quê>
- `git grep DIAG:` → vazio ou justificado

### Dívida declarada
- <atalhos conscientes e caminho de upgrade>

### Fora de escopo
- <o que foi visto e não corrigido, e por quê>
```

## Regras

**Saída bruta, não resumo.** Exit code e output colados. "Os testes passaram" não é evidência; é afirmação.

**Evidência visual é imagem.** Se houve degrau 5, anexe screenshot. Descrição de tela não substitui a tela.

**Fora de escopo é registrado, não corrigido.** Viu outro problema durante o ciclo? Reporta. Não conserta — isso é outro ciclo, com outro crivo.

## Promoção de instrumento

Quem decide: **humano, aqui no crivo.** Três critérios, todos obrigatórios:

1. provou valor diagnóstico **recorrente**
2. custo marginal ~zero
3. sem superfície de risco

Falhou em um, remove.

## Aprovação nomeada

Crivo de código não cobre ação de produção.

**Deploy, migration e credencial exigem aprovação separada e nomeada** — quem aprovou, o quê, quando. Registre em `memory/decisoes/`.

O agente nunca decide sozinho, e o registro é auditável depois.
