#!/usr/bin/env python3
"""Cria a estrutura do protocolo no projeto. Deterministico, entao e script.

O modelo nao consegue LER os assets do plugin: o harness gateia acesso a arquivo
fora do diretorio do projeto. Este script roda como subprocess e le do proprio
plugin root, entao nao depende de permissao de leitura externa.

Uso:
    5x-bootstrap.py                 # cria o que falta no cwd
    5x-bootstrap.py --dir /caminho
    5x-bootstrap.py --dry-run       # so diz o que faria

NAO REORGANIZA NADA. Bootstrap e diagnostico, e diagnostico nao muda o objeto
observado. Escreve so os artefatos do protocolo, e nunca sobrescreve o que ja
existe. Idempotente: rodar duas vezes nao duplica.
"""
import argparse
import json
import sys
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent
ASSETS = PLUGIN / "skills" / "5x-team-code" / "assets"
VERSAO = json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))["version"]
MARCADOR = "<!-- 5x-team protocolo v"


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--dir", default=".", help="raiz do projeto (padrao: cwd)")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    base = Path(args.dir).resolve()
    criados, pulados, avisos = [], [], []

    def escrever(rel, conteudo):
        alvo = base / rel
        if alvo.exists():
            pulados.append(rel)
            return
        criados.append(rel)
        if not args.dry_run:
            alvo.parent.mkdir(parents=True, exist_ok=True)
            alvo.write_text(conteudo, encoding="utf-8")

    for pasta in ("memory/hipoteses", "memory/experimentos", "memory/decisoes", "design"):
        alvo = base / pasta
        if alvo.is_dir():
            pulados.append(pasta + "/")
        else:
            criados.append(pasta + "/")
            if not args.dry_run:
                alvo.mkdir(parents=True, exist_ok=True)
                (alvo / ".gitkeep").touch()

    escrever("memory/INDEX.md", (ASSETS / "INDEX.template.md").read_text(encoding="utf-8"))
    escrever("memory/templates/hipotese.md", (ASSETS / "hipotese.template.md").read_text(encoding="utf-8"))
    escrever("memory/templates/experimento.md", (ASSETS / "experimento.template.md").read_text(encoding="utf-8"))

    # CLAUDE.md: dois blocos. O de protocolo e importado e igual em todo projeto;
    # o de projeto e do usuario. Nunca sobrescrevemos um arquivo existente.
    protocolo = (ASSETS / "CLAUDE-protocolo.md").read_text(encoding="utf-8")
    claude_md = base / "CLAUDE.md"
    if not claude_md.exists():
        criados.append("CLAUDE.md")
        if not args.dry_run:
            claude_md.write_text(protocolo, encoding="utf-8")
    else:
        atual = claude_md.read_text(encoding="utf-8")
        if MARCADOR not in atual:
            avisos.append("CLAUDE.md existe sem bloco de protocolo. Nao foi tocado — "
                          "insira o bloco no topo voce mesmo, preservando o conteudo atual.")
        elif f"{MARCADOR}{VERSAO} -->" not in atual:
            velha = atual.split(MARCADOR, 1)[1].split(" -->", 1)[0]
            avisos.append(f"CLAUDE.md esta com o bloco de protocolo v{velha}; o plugin e v{VERSAO}. "
                          "Nao foi tocado — atualize o bloco de protocolo, preservando o bloco do projeto.")
        else:
            pulados.append("CLAUDE.md")

    if not (base / ".git").is_dir():
        avisos.append("Nao e repositorio git. Worktrees e grep-gate ficam indisponiveis ate rodar `git init`.")

    print(json.dumps({
        "ok": True,
        "dry_run": args.dry_run,
        "projeto": str(base),
        "versao_protocolo": VERSAO,
        "criados": criados,
        "ja_existiam": pulados,
        "avisos": avisos,
        "nada_foi_movido": True,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(json.dumps({"ok": False, "erro": str(e)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
