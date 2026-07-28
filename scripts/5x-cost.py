#!/usr/bin/env python3
"""Custo real por tarefa e por ciclo. Serve o Principio 9.

E este script que responde "o caveman compensa neste projeto?" com numero em vez
de opiniao. Tabela de preco em `precos.json`, com a data da consulta no cabecalho.

Uso:
    5x-cost.py record --ciclo c1 --tarefa T1 --modelo sonnet --tokens-in 3000 --tokens-out 800
    5x-cost.py summary --ciclo c1
    5x-cost.py estimate --tarefas 5 --modelo sonnet --avg-in 3000 --avg-out 800
    5x-cost.py precos

Registro em `.5x/custo.jsonl` na raiz do projeto (append-only).
"""
import argparse
import json
import os
import sys
from datetime import date, datetime
from pathlib import Path

PRECOS = Path(__file__).resolve().parent / "precos.json"


def raiz():
    return Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path.cwd())


def tabela():
    return json.loads(PRECOS.read_text(encoding="utf-8"))


def preco(modelo):
    t = tabela()
    nome = t["aliases"].get(modelo, modelo)
    if nome not in t["modelos"]:
        sys.exit(f"erro: modelo '{modelo}' fora da tabela. Disponiveis: "
                 f"{', '.join(sorted(t['modelos']))} (aliases: {', '.join(sorted(t['aliases']))})")
    p = dict(t["modelos"][nome])
    validade = p.get("_valido_ate")
    if validade and date.fromisoformat(validade) < date.today():
        print(f"aviso: preco de {nome} expirou em {validade}; usando a faixa seguinte", file=sys.stderr)
        p.update(p["_depois"])
    return nome, p


def calcular(p, tin, tout, cache_read=0, cache_write=0):
    return round(
        tin / 1e6 * p["entrada"]
        + tout / 1e6 * p["saida"]
        + cache_read / 1e6 * p.get("cache_read", 0)
        + cache_write / 1e6 * p.get("cache_write_5m", 0),
        6,
    )


def cmd_record(a):
    nome, p = preco(a.modelo)
    reg = {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "ciclo": a.ciclo,
        "tarefa": a.tarefa,
        "modelo": nome,
        "tokens_in": a.tokens_in,
        "tokens_out": a.tokens_out,
        "cache_read": a.cache_read,
        "cache_write": a.cache_write,
        "usd": calcular(p, a.tokens_in, a.tokens_out, a.cache_read, a.cache_write),
        "preco_consultado_em": tabela()["_consultado_em"],
    }
    destino = raiz() / ".5x" / "custo.jsonl"
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("a", encoding="utf-8") as f:
        f.write(json.dumps(reg, ensure_ascii=False) + "\n")
    print(json.dumps(reg, ensure_ascii=False, indent=2))


def cmd_summary(a):
    origem = raiz() / ".5x" / "custo.jsonl"
    if not origem.exists():
        sys.exit("erro: nenhum custo registrado (.5x/custo.jsonl nao existe)")

    regs = [json.loads(l) for l in origem.read_text(encoding="utf-8").splitlines() if l.strip()]
    if a.ciclo:
        regs = [r for r in regs if r.get("ciclo") == a.ciclo]
    if not regs:
        sys.exit(f"erro: nenhum registro para o ciclo '{a.ciclo}'")

    por_tarefa, por_modelo = {}, {}
    for r in regs:
        por_tarefa[r["tarefa"]] = round(por_tarefa.get(r["tarefa"], 0) + r["usd"], 6)
        por_modelo[r["modelo"]] = round(por_modelo.get(r["modelo"], 0) + r["usd"], 6)

    print(json.dumps({
        "ciclo": a.ciclo or "(todos)",
        "registros": len(regs),
        "total_usd": round(sum(r["usd"] for r in regs), 6),
        "tokens_in": sum(r["tokens_in"] for r in regs),
        "tokens_out": sum(r["tokens_out"] for r in regs),
        "por_tarefa": por_tarefa,
        "por_modelo": por_modelo,
    }, ensure_ascii=False, indent=2))


def cmd_estimate(a):
    nome, p = preco(a.modelo)
    unitario = calcular(p, a.avg_in, a.avg_out)
    print(json.dumps({
        "modelo": nome,
        "tarefas": a.tarefas,
        "usd_por_tarefa": unitario,
        "usd_total": round(unitario * a.tarefas, 6),
        "aviso": "estimativa, nao medicao. Principio 9: so numero medido entra no crivo.",
    }, ensure_ascii=False, indent=2))


def cmd_precos(a):
    print(json.dumps(tabela(), ensure_ascii=False, indent=2))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("record", help="registra o custo medido de uma tarefa")
    r.add_argument("--ciclo", required=True)
    r.add_argument("--tarefa", required=True)
    r.add_argument("--modelo", required=True)
    r.add_argument("--tokens-in", type=int, required=True)
    r.add_argument("--tokens-out", type=int, required=True)
    r.add_argument("--cache-read", type=int, default=0)
    r.add_argument("--cache-write", type=int, default=0)
    r.set_defaults(func=cmd_record)

    s = sub.add_parser("summary", help="soma o custo de um ciclo")
    s.add_argument("--ciclo")
    s.set_defaults(func=cmd_summary)

    e = sub.add_parser("estimate", help="estima antes de disparar o fan-out")
    e.add_argument("--tarefas", type=int, required=True)
    e.add_argument("--modelo", required=True)
    e.add_argument("--avg-in", type=int, required=True)
    e.add_argument("--avg-out", type=int, required=True)
    e.set_defaults(func=cmd_estimate)

    t = sub.add_parser("precos", help="imprime a tabela de preco e a data da consulta")
    t.set_defaults(func=cmd_precos)

    a = p.parse_args()
    a.func(a)


if __name__ == "__main__":
    main()
