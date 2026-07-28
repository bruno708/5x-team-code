#!/usr/bin/env python3
"""Grafo de dependencias -> ondas de paralelismo.

Ordenacao topologica (Kahn) com uma regra que o grafo declarado nao tem:
**duas tarefas com arquivo em comum em `owns` nunca vao na mesma onda**, mesmo
sem dependencia declarada. Sem isso o grafo mente e dois agentes escrevem na
mesma arvore.

Uso:
    5x-waves.py plano.json
    5x-waves.py plano.json --check-cycles
    5x-waves.py plano.json --max-parallel 5
    5x-waves.py --check                 # a onda corrente fechou? qual e a proxima?
    cat plano.json | 5x-waves.py -

Entrada:
    {"tasks": [{"id": "T1", "depends_on": [], "owns": ["src/a.py"]}]}

Exit 0 ondas resolvidas. Exit 1 ciclo ou dependencia inexistente. Exit 2 erro de uso.
"""
import argparse
import json
import os
import sys
from pathlib import Path

PLANO_PADRAO = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path.cwd()) / ".5x" / "plano.json"


def achar_ciclo(pendentes, deps):
    """DFS nos nos que sobraram do Kahn. Devolve o ciclo como lista de ids."""
    caminho, visitados = [], set()

    def dfs(no):
        if no in caminho:
            return caminho[caminho.index(no):] + [no]
        if no in visitados:
            return None
        visitados.add(no)
        caminho.append(no)
        for d in deps[no]:
            if d in pendentes:
                achou = dfs(d)
                if achou:
                    return achou
        caminho.pop()
        return None

    for no in sorted(pendentes):
        achou = dfs(no)
        if achou:
            return achou
    return sorted(pendentes)


def ondas(tasks, max_parallel=None):
    ids = [t["id"] for t in tasks]
    if len(set(ids)) != len(ids):
        dup = sorted({i for i in ids if ids.count(i) > 1})
        raise ValueError(f"ids duplicados: {', '.join(dup)}")

    deps = {t["id"]: list(t.get("depends_on", [])) for t in tasks}
    owns = {t["id"]: set(t.get("owns", [])) for t in tasks}

    faltando = {(i, d) for i, ds in deps.items() for d in ds if d not in deps}
    if faltando:
        detalhe = ", ".join(f"{i} depende de '{d}' que nao existe" for i, d in sorted(faltando))
        raise ValueError(detalhe)

    pendentes = set(deps)
    feitos = set()
    resultado = []

    while pendentes:
        prontos = sorted(i for i in pendentes if set(deps[i]) <= feitos)
        if not prontos:
            ciclo = achar_ciclo(pendentes, deps)
            raise ValueError("ciclo de dependencia: " + " -> ".join(ciclo))

        onda, arquivos_da_onda, adiados = [], set(), []
        for i in prontos:
            if max_parallel and len(onda) >= max_parallel:
                adiados.append(i)
                continue
            colisao = owns[i] & arquivos_da_onda
            if colisao:
                adiados.append(i)
                continue
            onda.append(i)
            arquivos_da_onda |= owns[i]

        resultado.append(onda)
        pendentes -= set(onda)
        feitos |= set(onda)

    return resultado


def concluidas(base):
    """Ids de tarefa com retorno `atendido: true` em .5x/tarefas.jsonl."""
    jsonl = base / ".5x" / "tarefas.jsonl"
    if not jsonl.exists():
        return set()
    feitas = set()
    for linha in jsonl.read_text(encoding="utf-8").splitlines():
        if not linha.strip():
            continue
        try:
            reg = json.loads(linha)
        except json.JSONDecodeError:
            continue
        if reg.get("atendido"):
            feitas.add(reg.get("tarefa"))
    return feitas


def checar_onda(resultado, base):
    """Onda corrente = primeira com tarefa pendente. Vazia em todas -> plano fechou."""
    feitas = concluidas(base)
    for i, onda in enumerate(resultado):
        faltando = [t for t in onda if t not in feitas]
        if faltando:
            return {
                "ok": True,
                "onda_corrente": i + 1,
                "total_ondas": len(resultado),
                "faltando": faltando,
                "proxima_onda": resultado[i + 1] if i + 1 < len(resultado) else [],
                "plano_completo": False,
            }
    return {"ok": True, "onda_corrente": len(resultado), "total_ondas": len(resultado),
            "faltando": [], "proxima_onda": [], "plano_completo": True}


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("plano", nargs="?", default=str(PLANO_PADRAO),
                   help="arquivo JSON do plano ('-' para stdin). Padrao: .5x/plano.json")
    p.add_argument("--check-cycles", action="store_true", help="so detecta ciclo, nao imprime ondas")
    p.add_argument("--check", action="store_true",
                   help="a onda corrente fechou? le .5x/tarefas.jsonl. Silencioso se nao ha plano")
    p.add_argument("--max-parallel", type=int, help="teto de tarefas por onda")
    args = p.parse_args()

    if args.plano != "-" and not Path(args.plano).exists():
        if args.check:
            return  # sem plano nao ha onda para encadear: hook sai quieto
        sys.exit(f"erro: plano '{args.plano}' nao encontrado")

    bruto = sys.stdin.read() if args.plano == "-" else Path(args.plano).read_text(encoding="utf-8")
    plano = json.loads(bruto)
    tasks = plano.get("tasks", [])

    try:
        resultado = ondas(tasks, args.max_parallel)
    except ValueError as e:
        print(json.dumps({"ok": False, "erro": str(e)}, ensure_ascii=False, indent=2), file=sys.stderr)
        sys.exit(1)

    if args.check_cycles:
        print(json.dumps({"ok": True, "ciclo": False}, ensure_ascii=False, indent=2))
        return

    if args.check:
        estado = checar_onda(resultado, Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path.cwd()))
        print(json.dumps(estado, ensure_ascii=False, indent=2))
        return

    print(json.dumps({
        "ok": True,
        "ondas": resultado,
        "total_ondas": len(resultado),
        "total_tarefas": len(tasks),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
