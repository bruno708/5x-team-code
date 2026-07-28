#!/usr/bin/env python3
"""Estado do ciclo, derivado do vault. Nunca narrado.

Hipotese com `status: viva` no frontmatter *e* pendencia. O script le o vault e
monta o bloco. Nao pede pro modelo lembrar, e nao inventa: se o vault nao diz, o
campo fica vazio.

Uso:
    5x-state.py --write     # deriva do vault, sobrescreve memory/ESTADO.md
    5x-state.py --read      # imprime INDEX.md + ESTADO.md para injecao
    5x-state.py --restore   # pos-compactacao: reescreve e imprime

ESTADO.md e sobrescrito, nao acumulado. Historico ja vive nas hipoteses e
experimentos.
"""
import argparse
import json
import os
import sys
from pathlib import Path


def raiz():
    return Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path.cwd())


def frontmatter(texto):
    """Parser minimo de frontmatter YAML: `chave: valor` entre delimitadores ---.

    ponytail: PyYAML nao e stdlib e o frontmatter do protocolo e plano.
    Se algum campo virar lista ou aninhado, troque por PyYAML.
    """
    linhas = texto.splitlines()
    if not linhas or linhas[0].strip() != "---":
        return {}
    dados = {}
    for linha in linhas[1:]:
        if linha.strip() == "---":
            break
        if ":" not in linha or linha.lstrip().startswith("#"):
            continue
        chave, _, valor = linha.partition(":")
        dados[chave.strip()] = valor.split("#")[0].strip()
    return dados


def titulo(caminho, texto):
    for linha in texto.splitlines():
        if linha.startswith("# "):
            return linha[2:].strip()
    return caminho.stem


def ler_vault(base):
    hipoteses, experimentos = [], []
    for md in sorted((base / "memory" / "hipoteses").glob("*.md")):
        texto = md.read_text(encoding="utf-8", errors="replace")
        fm = frontmatter(texto)
        hipoteses.append({
            "arquivo": md.name,
            "id": fm.get("id", md.stem),
            "status": fm.get("status", ""),
            "confianca": fm.get("confianca", ""),
            "ciclo": fm.get("ciclo", ""),
            "titulo": titulo(md, texto),
        })
    for md in sorted((base / "memory" / "experimentos").glob("*.md")):
        texto = md.read_text(encoding="utf-8", errors="replace")
        fm = frontmatter(texto)
        experimentos.append({
            "arquivo": md.name,
            "id": fm.get("id", md.stem),
            "ciclo": fm.get("ciclo", ""),
            "titulo": titulo(md, texto),
        })
    return hipoteses, experimentos


def ler_json(caminho, default):
    try:
        return json.loads(caminho.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def tarefas_pendentes(base):
    plano = ler_json(base / ".5x" / "plano.json", {})
    if not plano.get("tasks"):
        return []
    fechadas = set()
    jsonl = base / ".5x" / "tarefas.jsonl"
    if jsonl.exists():
        for linha in jsonl.read_text(encoding="utf-8").splitlines():
            reg = ler_json_linha(linha)
            if reg and reg.get("atendido"):
                fechadas.add(reg.get("tarefa"))
    return [t for t in plano["tasks"] if t.get("id") not in fechadas]


def ler_json_linha(linha):
    try:
        return json.loads(linha)
    except json.JSONDecodeError:
        return None


def montar(base):
    hipoteses, experimentos = ler_vault(base)
    ciclo = ler_json(base / ".5x" / "ciclo.json", {})
    pendentes_tarefa = tarefas_pendentes(base)

    vivas = [h for h in hipoteses if h["status"] == "viva"]
    fechadas = [h for h in hipoteses if h["status"] in ("confirmada", "refutada")]

    fase = ciclo.get("fase", "")
    if not fase and not (base / "memory").is_dir():
        fase = "bootstrap pendente"

    linhas = ["<!-- derivado por 5x-state.py. Nao edite a mao: e sobrescrito. -->", ""]
    linhas += ["## Onde estamos", ""]
    linhas += [f"Fase: {fase or '<nao registrada>'}"]
    linhas += [f"Ciclo: {ciclo.get('ciclo') or '<nao registrado>'}", ""]

    linhas += ["## Feito", ""]
    if not fechadas and not experimentos:
        linhas.append("- (vault sem hipotese fechada nem experimento)")
    for h in fechadas:
        linhas.append(f"- [x] {h['id']} {h['status']} — {h['titulo']} (`memory/hipoteses/{h['arquivo']}`)")
    for e in experimentos:
        linhas.append(f"- [x] {e['id']} — {e['titulo']} (`memory/experimentos/{e['arquivo']}`)")
    linhas.append("")

    linhas += ["## Pendente", ""]
    if not vivas and not pendentes_tarefa:
        linhas.append("- (nenhuma hipotese viva, nenhuma tarefa aberta)")
    for h in vivas:
        linhas.append(f"- [ ] {h['id']} viva — {h['titulo']} (`memory/hipoteses/{h['arquivo']}`)")
    for t in pendentes_tarefa:
        criterio = t.get("criterio", "")
        linhas.append(f"- [ ] {t.get('id')} — {criterio or '<sem criterio de aceite>'}")
    linhas.append("")

    linhas += ["## Proximo passo", ""]
    proximo = ciclo.get("proximo_passo")
    custo = ciclo.get("custo_estimado")
    if proximo:
        linhas.append(proximo + (f" (custo estimado: {custo})" if custo else ""))
        linhas += ["", "Rodo?"]
    else:
        linhas.append("<nao registrado — o vault nao diz>")
    linhas.append("")

    return "\n".join(linhas)


def escrever(base):
    destino = base / "memory" / "ESTADO.md"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(montar(base), encoding="utf-8")
    return destino


def imprimir(base, cabecalho):
    """Deriva o estado na hora e imprime. Nao le foto velha do disco: o vault pode
    ter mudado fora desta sessao, e o ESTADO.md pode nem existir ainda."""
    index = base / "memory" / "INDEX.md"
    if not index.exists() and not (base / "memory").is_dir():
        return  # sem vault: nada a injetar, silencio e a resposta certa
    partes = [cabecalho]
    if index.exists():
        partes += ["", "### memory/INDEX.md", "", index.read_text(encoding="utf-8")]
    partes += ["", "### memory/ESTADO.md", "", montar(base)]
    print("\n".join(partes))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true", help="deriva do vault e sobrescreve memory/ESTADO.md")
    g.add_argument("--read", action="store_true", help="imprime INDEX.md + ESTADO.md")
    g.add_argument("--restore", action="store_true", help="pos-compactacao: reescreve e imprime")
    p.add_argument("--json", action="store_true", help="--write: reporta o caminho em JSON")
    args = p.parse_args()

    base = raiz()
    if not (base / "memory").is_dir() and not (base / ".5x").is_dir():
        return  # protocolo nao instalado neste projeto: nao ha o que fazer

    if args.write:
        destino = escrever(base)
        if args.json:
            print(json.dumps({"ok": True, "estado": str(destino)}, ensure_ascii=False))
    elif args.read:
        imprimir(base, "## Estado do protocolo 5x (injetado no inicio da sessao)")
    else:
        escrever(base)
        imprimir(base, "## Estado do protocolo 5x (reinjetado apos compactacao)")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # hook nunca quebra sessao
        print(f"5x-state: {e}", file=sys.stderr)
        sys.exit(0)
