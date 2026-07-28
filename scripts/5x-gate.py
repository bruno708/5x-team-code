#!/usr/bin/env python3
"""Grep-gate de instrumentos. Marcador sem gate nao segura nada.

Uso:
    5x-gate.py            # git grep DIAG: -> exit 1 se achar
    5x-gate.py --justify  # lista as ocorrencias para o crivo, exit 0

Exit 0 limpo. Exit 1 instrumento sobrou. Exit 2 nao e repositorio git.
"""
import argparse
import json
import subprocess
import sys

MARCADOR = "DIAG:"


def ocorrencias():
    r = subprocess.run(["git", "grep", "-n", MARCADOR], capture_output=True, text=True)
    if r.returncode == 1 and not r.stdout:
        return []                      # git grep: 1 = nao achou nada
    if r.returncode > 1:
        sys.exit(f"erro: {r.stderr.strip() or 'git grep falhou — isto e um repositorio git?'}")
    linhas = []
    for linha in r.stdout.splitlines():
        arquivo, _, resto = linha.partition(":")
        numero, _, trecho = resto.partition(":")
        linhas.append({"arquivo": arquivo, "linha": numero, "trecho": trecho.strip()})
    return linhas


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--justify", action="store_true",
                   help="lista as ocorrencias para justificar no crivo, sem falhar")
    args = p.parse_args()

    achados = ocorrencias()
    print(json.dumps({
        "marcador": MARCADOR,
        "limpo": not achados,
        "total": len(achados),
        "ocorrencias": achados,
    }, ensure_ascii=False, indent=2))

    if args.justify:
        return
    sys.exit(1 if achados else 0)


if __name__ == "__main__":
    main()
