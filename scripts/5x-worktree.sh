#!/usr/bin/env bash
# Worktree por tarefa. Isolamento real: mesmo repositorio, diretorios separados.
#
#   5x-worktree.sh add T1 task/t1-decoder
#   5x-worktree.sh remove T1
#   5x-worktree.sh list
#   5x-worktree.sh clean
#
# UMA BRANCH POR WORKTREE. O git recusa a mesma branch em check-out em dois
# lugares — por isso o `-b` e sempre usado e a branch e derivada do id da tarefa
# quando nao informada.
set -euo pipefail

uso() {
  sed -n '2,12p' "$0" | sed 's/^# \{0,1\}//'
  exit "${1:-0}"
}

[ $# -ge 1 ] || uso 2
comando=$1
shift

git rev-parse --show-toplevel >/dev/null 2>&1 || { echo "erro: nao e um repositorio git" >&2; exit 2; }
raiz=$(git rev-parse --show-toplevel)
base=$(dirname "$raiz")
prefixo=$(basename "$raiz")

case "$comando" in
  add)
    [ $# -ge 1 ] || { echo "erro: uso: 5x-worktree.sh add <id-tarefa> [branch]" >&2; exit 2; }
    tarefa=$1
    branch=${2:-task/$(echo "$tarefa" | tr '[:upper:]' '[:lower:]')}
    destino="$base/${prefixo}-wt-${tarefa}"

    if git show-ref --verify --quiet "refs/heads/$branch"; then
      echo "erro: branch '$branch' ja existe. Uma branch por worktree — escolha outro nome." >&2
      exit 1
    fi
    git worktree add "$destino" -b "$branch"
    printf '{"tarefa":"%s","worktree":"%s","branch":"%s"}\n' "$tarefa" "$destino" "$branch"
    ;;

  remove)
    [ $# -ge 1 ] || { echo "erro: uso: 5x-worktree.sh remove <id-tarefa>" >&2; exit 2; }
    destino="$base/${prefixo}-wt-${1}"
    git worktree remove "$destino" "${2:-}"
    echo "removido: $destino"
    ;;

  list)
    git worktree list
    ;;

  clean)
    git worktree prune -v
    for d in "$base/${prefixo}-wt-"*; do
      [ -d "$d" ] || continue
      git worktree remove "$d" 2>/dev/null && echo "removido: $d" || echo "mantido (sujo): $d"
    done
    ;;

  -h|--help|help) uso 0 ;;
  *) echo "erro: comando desconhecido '$comando'" >&2; uso 2 ;;
esac
