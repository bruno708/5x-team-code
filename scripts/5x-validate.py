#!/usr/bin/env python3
"""Valida retorno de subagent contra o JSON Schema do modo.

Schema sem validador e honra. Este script torna o contrato real.

Uso:
    5x-validate.py retorno.json --schema diagnostico
    5x-validate.py retorno.json --schema implementacao
    5x-validate.py retorno.json --schema ./caminho/custom.schema.json
    cat retorno.json | 5x-validate.py - --schema diagnostico

Exit 0 valido. Exit 1 invalido, com os campos apontados. Exit 2 erro de uso.
"""
import argparse
import json
import sys
from pathlib import Path

SCHEMA_DIR = Path(__file__).resolve().parent.parent / "skills" / "5x-team-code" / "schemas"

# ponytail: subconjunto de JSON Schema (type/required/enum/properties/items/
# additionalProperties) — o que os dois schemas do protocolo usam. Se um schema
# futuro precisar de allOf/$ref/pattern, troque por jsonschema (dep externa).
TYPES = {
    "object": dict,
    "array": list,
    "string": str,
    "integer": int,
    "number": (int, float),
    "boolean": bool,
    "null": type(None),
}


def tipo_ok(valor, esperado):
    if esperado == "integer":
        return isinstance(valor, int) and not isinstance(valor, bool)
    if esperado in ("number",):
        return isinstance(valor, (int, float)) and not isinstance(valor, bool)
    if esperado == "boolean":
        return isinstance(valor, bool)
    return isinstance(valor, TYPES[esperado])


def validar(dado, schema, caminho="$", erros=None):
    if erros is None:
        erros = []

    esperado = schema.get("type")
    if esperado and not tipo_ok(dado, esperado):
        erros.append(f"{caminho}: esperava tipo '{esperado}', veio '{type(dado).__name__}'")
        return erros

    if "enum" in schema and dado not in schema["enum"]:
        erros.append(f"{caminho}: valor {dado!r} fora do enum {schema['enum']}")

    if isinstance(dado, dict):
        props = schema.get("properties", {})
        for campo in schema.get("required", []):
            if campo not in dado:
                disponiveis = sorted(dado.keys()) or ["(objeto vazio)"]
                erros.append(
                    f"{caminho}: campo obrigatorio '{campo}' ausente. "
                    f"Campos presentes: {', '.join(disponiveis)}"
                )
        if schema.get("additionalProperties") is False:
            for campo in dado:
                if campo not in props:
                    erros.append(
                        f"{caminho}: campo '{campo}' nao existe no schema. "
                        f"Campos aceitos: {', '.join(sorted(props))}"
                    )
        for campo, sub in props.items():
            if campo in dado:
                validar(dado[campo], sub, f"{caminho}.{campo}", erros)

    elif isinstance(dado, list) and "items" in schema:
        for i, item in enumerate(dado):
            validar(item, schema["items"], f"{caminho}[{i}]", erros)

    return erros


def resolver_schema(nome):
    candidato = Path(nome)
    if candidato.suffix == ".json" and candidato.exists():
        return candidato
    embutido = SCHEMA_DIR / f"{nome}.schema.json"
    if embutido.exists():
        return embutido
    disponiveis = sorted(p.name.replace(".schema.json", "") for p in SCHEMA_DIR.glob("*.schema.json"))
    sys.exit(f"erro: schema '{nome}' nao encontrado. Disponiveis: {', '.join(disponiveis)}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("retorno", help="arquivo JSON do subagent, ou '-' para stdin")
    p.add_argument("--schema", required=True, help="diagnostico | implementacao | caminho .json")
    args = p.parse_args()

    schema_path = resolver_schema(args.schema)
    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    bruto = sys.stdin.read() if args.retorno == "-" else Path(args.retorno).read_text(encoding="utf-8")
    try:
        dado = json.loads(bruto)
    except json.JSONDecodeError as e:
        print(json.dumps({"valido": False, "erros": [f"JSON malformado: {e}"]}, ensure_ascii=False, indent=2))
        sys.exit(1)

    erros = validar(dado, schema)
    print(json.dumps({"valido": not erros, "schema": schema_path.name, "erros": erros},
                     ensure_ascii=False, indent=2))
    sys.exit(1 if erros else 0)


if __name__ == "__main__":
    main()
