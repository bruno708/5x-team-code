#!/usr/bin/env bash
# Instala e configura as dependencias externas do protocolo.
#
#   install-deps.sh              # ponytail + caveman + configuracao
#   install-deps.sh --check      # so diagnostica o que falta
#   install-deps.sh --with-mem   # inclui claude-mem (opcional, nao instalado por padrao)
#
# DEGRADACAO LIMPA: nenhuma dependencia ausente quebra o ciclo. O protocolo roda
# sem elas — so mais caro. Este script avisa o que faltou e sai com 0.
set -uo pipefail

CHECK=0
WITH_MEM=0
for a in "$@"; do
  case "$a" in
    --check) CHECK=1 ;;
    --with-mem) WITH_MEM=1 ;;
    -h|--help) sed -n '2,9p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "erro: argumento desconhecido '$a'" >&2; exit 2 ;;
  esac
done

ok()   { printf '  ok    %s\n' "$1"; }
falta(){ printf '  FALTA %s\n' "$1"; }

tem() { command -v "$1" >/dev/null 2>&1; }

echo "== dependencias =="
tem claude && ok "claude CLI" || { falta "claude CLI — sem ele nada abaixo instala"; exit 0; }
tem node   && ok "node (exigido pelo ponytail)" || falta "node — ponytail nao roda sem ele"
tem python3 && ok "python3 (exigido pelos scripts 5x-*)" || falta "python3 — os scripts 5x-* nao rodam"
tem git    && ok "git (worktrees e grep-gate)" || falta "git — worktrees e grep-gate indisponiveis"

instalados=$(claude plugin list 2>/dev/null || true)
for p in ponytail caveman; do
  echo "$instalados" | grep -q "$p" && ok "plugin $p" || falta "plugin $p"
done

[ "$CHECK" = 1 ] && exit 0

echo
echo "== instalando =="
# Nomes de terceiros ficam como sao. Instalamos e configuramos; nao rebatizamos.
if ! echo "$instalados" | grep -q ponytail; then
  claude plugin marketplace add DietrichGebert/ponytail && claude plugin install ponytail@ponytail \
    || echo "  aviso: ponytail nao instalou. Ciclo segue sem ele."
fi
if ! echo "$instalados" | grep -q caveman; then
  claude plugin marketplace add JuliusBrussee/caveman && claude plugin install caveman@caveman \
    || echo "  aviso: caveman nao instalou. Ciclo segue sem ele."
fi
if [ "$WITH_MEM" = 1 ]; then
  npx claude-mem install || echo "  aviso: claude-mem nao instalou. E opcional."
fi

echo
echo "== configurando ponytail =="
# PONYTAIL_SUBAGENT_MATCHER casa SO o executor. Subagent de diagnostico e
# somente leitura: nao escreve codigo, entao nao ha nada a enxugar — ponytail
# nele e overhead puro.
python3 - "$PWD" <<'PY'
import json, shutil, sys, time
from pathlib import Path

raiz = Path(sys.argv[1])
alvo = raiz / ".claude" / "settings.json"
alvo.parent.mkdir(parents=True, exist_ok=True)

dados = {}
if alvo.exists():
    backup = alvo.with_suffix(f".json.bak-{time.strftime('%Y%m%d-%H%M%S')}")
    shutil.copy2(alvo, backup)          # backup antes de tocar, sempre
    print(f"  backup: {backup.name}")
    try:
        dados = json.loads(alvo.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        print("  aviso: settings.json ilegivel. Nada foi alterado.")
        sys.exit(0)

env = dados.setdefault("env", {})       # merge, nunca sobrescreve o arquivo todo
antes = dict(env)
env.setdefault("PONYTAIL_DEFAULT_MODE", "full")
env.setdefault("PONYTAIL_SUBAGENT_MATCHER", "^5x-team:5x-executor$")

if env == antes:
    print("  ja configurado (idempotente, nada mudou)")
else:
    alvo.write_text(json.dumps(dados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"  escrito: {alvo}")
PY

echo
echo "== caveman =="
echo "  sempre-ligado fica DESLIGADO por padrao: o benchmark agentico do ponytail"
echo "  mediu caveman em +7% tokens contra baseline, e a carga deste protocolo ja"
echo "  e enxuta por construcao. Ligar por padrao violaria o Principio 9."
if [ -f CLAUDE.md ]; then
  echo "  rode dentro do Claude Code, uma vez:  /caveman-compress CLAUDE.md"
  echo "  e meça o resultado com:               /caveman-stats"
else
  echo "  CLAUDE.md ainda nao existe. Rode /5x-init antes, depois /caveman-compress CLAUDE.md"
fi

echo
echo "pronto. O que faltou acima nao impede o ciclo — so o deixa mais caro."
