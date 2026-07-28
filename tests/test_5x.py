#!/usr/bin/env python3
"""Testes do plugin 5x-team. stdlib apenas.

    python3 -m unittest discover -s tests -v
"""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SCRIPTS = RAIZ / "scripts"


def carregar(nome):
    """Importa um script com hifen no nome (nao e identificador Python)."""
    spec = importlib.util.spec_from_file_location(nome.replace("-", "_"), SCRIPTS / f"{nome}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


waves = carregar("5x-waves")
validate = carregar("5x-validate")


def rodar(script, *args, cwd=None):
    return subprocess.run([sys.executable, str(SCRIPTS / script), *args],
                          capture_output=True, text=True, cwd=cwd)


class TestOndas(unittest.TestCase):
    def test_independentes_vao_juntas(self):
        tasks = [{"id": "T1", "owns": ["a.py"]}, {"id": "T2", "owns": ["b.py"]}]
        self.assertEqual(waves.ondas(tasks), [["T1", "T2"]])

    def test_dependencia_vira_sequencia(self):
        tasks = [
            {"id": "T1", "depends_on": [], "owns": ["a.py"]},
            {"id": "T2", "depends_on": [], "owns": ["b.py"]},
            {"id": "T3", "depends_on": ["T1"], "owns": ["c.py"]},
        ]
        self.assertEqual(waves.ondas(tasks), [["T1", "T2"], ["T3"]])

    def test_ownership_separa_mesmo_sem_dependencia(self):
        """A regra que o grafo declarado nao tem: arquivo em comum -> ondas diferentes."""
        tasks = [
            {"id": "T1", "depends_on": [], "owns": ["src/a.py"]},
            {"id": "T2", "depends_on": [], "owns": ["src/a.py", "src/b.py"]},
        ]
        resultado = waves.ondas(tasks)
        self.assertEqual(resultado, [["T1"], ["T2"]])
        for onda in resultado:
            self.assertLessEqual(len(onda), 1)

    def test_ownership_transitivo_na_mesma_onda(self):
        # T1 e T3 nao colidem entre si, mas T2 colide com os dois.
        tasks = [
            {"id": "T1", "owns": ["a.py"]},
            {"id": "T2", "owns": ["a.py", "c.py"]},
            {"id": "T3", "owns": ["c.py"]},
        ]
        ondas = waves.ondas(tasks)
        for onda in ondas:
            arquivos = []
            for tid in onda:
                arquivos += next(t["owns"] for t in tasks if t["id"] == tid)
            self.assertEqual(len(arquivos), len(set(arquivos)), f"colisao na onda {onda}")

    def test_max_parallel(self):
        tasks = [{"id": f"T{i}", "owns": [f"{i}.py"]} for i in range(1, 6)]
        ondas = waves.ondas(tasks, max_parallel=2)
        self.assertTrue(all(len(o) <= 2 for o in ondas))
        self.assertEqual(sum(len(o) for o in ondas), 5)

    def test_ciclo_detectado(self):
        tasks = [
            {"id": "T1", "depends_on": ["T2"], "owns": []},
            {"id": "T2", "depends_on": ["T1"], "owns": []},
        ]
        with self.assertRaises(ValueError) as ctx:
            waves.ondas(tasks)
        self.assertIn("ciclo", str(ctx.exception))

    def test_dependencia_inexistente(self):
        with self.assertRaises(ValueError) as ctx:
            waves.ondas([{"id": "T1", "depends_on": ["T9"], "owns": []}])
        self.assertIn("T9", str(ctx.exception))

    def test_cli_ciclo_sai_1(self):
        with tempfile.TemporaryDirectory() as d:
            plano = Path(d) / "plano.json"
            plano.write_text(json.dumps({"tasks": [
                {"id": "T1", "depends_on": ["T2"], "owns": []},
                {"id": "T2", "depends_on": ["T1"], "owns": []},
            ]}))
            r = rodar("5x-waves.py", str(plano))
            self.assertEqual(r.returncode, 1)
            self.assertIn("ciclo", r.stderr)

    def test_check_sinaliza_proxima_onda_e_fechamento(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            (base / ".5x").mkdir()
            (base / ".5x" / "plano.json").write_text(json.dumps({"tasks": [
                {"id": "T1", "depends_on": [], "owns": ["a.py"]},
                {"id": "T2", "depends_on": [], "owns": ["b.py"]},
                {"id": "T3", "depends_on": ["T1"], "owns": ["c.py"]},
            ]}))
            env = {**os.environ, "CLAUDE_PROJECT_DIR": str(base)}
            jsonl = base / ".5x" / "tarefas.jsonl"

            def check():
                r = subprocess.run([sys.executable, str(SCRIPTS / "5x-waves.py"), "--check"],
                                   capture_output=True, text=True, env=env)
                self.assertEqual(r.returncode, 0, r.stderr)
                return json.loads(r.stdout)

            jsonl.write_text('{"tarefa":"T1","atendido":true}\n')
            meio = check()
            self.assertEqual(meio["onda_corrente"], 1)
            self.assertEqual(meio["faltando"], ["T2"])

            with jsonl.open("a") as f:
                f.write('{"tarefa":"T2","atendido":true}\n')
            fechada = check()                       # onda 1 fechou, onda 2 vira corrente
            self.assertEqual(fechada["onda_corrente"], 2)
            self.assertEqual(fechada["faltando"], ["T3"])
            self.assertFalse(fechada["plano_completo"])

            with jsonl.open("a") as f:
                f.write('{"tarefa":"T3","atendido":true}\n')
            self.assertTrue(check()["plano_completo"])

    def test_check_sem_plano_sai_quieto(self):
        with tempfile.TemporaryDirectory() as d:
            env = {**os.environ, "CLAUDE_PROJECT_DIR": d}
            r = subprocess.run([sys.executable, str(SCRIPTS / "5x-waves.py"), "--check"],
                               capture_output=True, text=True, env=env, cwd=d)
            self.assertEqual(r.returncode, 0)
            self.assertEqual(r.stdout.strip(), "")

    def test_cli_ondas_sai_0(self):
        with tempfile.TemporaryDirectory() as d:
            plano = Path(d) / "plano.json"
            plano.write_text(json.dumps({"tasks": [
                {"id": "T1", "depends_on": [], "owns": ["a.py"]},
                {"id": "T2", "depends_on": [], "owns": ["a.py"]},
            ]}))
            r = rodar("5x-waves.py", str(plano))
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(json.loads(r.stdout)["ondas"], [["T1"], ["T2"]])


class TestValidacao(unittest.TestCase):
    def diagnostico_valido(self):
        return {
            "hipotese": "H3",
            "veredito": "confirmada",
            "evidencia": {"observado": "decode roda 2x", "onde": "src/dec.py:41"},
            "fatos_novos": ["cache desligado em dev"],
        }

    def test_aceita_retorno_valido(self):
        schema = json.loads((RAIZ / "skills/5x-team-code/schemas/diagnostico.schema.json").read_text())
        self.assertEqual(validate.validar(self.diagnostico_valido(), schema), [])

    def test_rejeita_sem_fatos_novos(self):
        """fatos_novos e o motor de convergencia. Sem ele o contrato nao vale."""
        schema = json.loads((RAIZ / "skills/5x-team-code/schemas/diagnostico.schema.json").read_text())
        dado = self.diagnostico_valido()
        del dado["fatos_novos"]
        erros = validate.validar(dado, schema)
        self.assertTrue(any("fatos_novos" in e for e in erros), erros)
        self.assertTrue(any("Campos presentes" in e for e in erros), erros)

    def test_rejeita_veredito_fora_do_enum(self):
        schema = json.loads((RAIZ / "skills/5x-team-code/schemas/diagnostico.schema.json").read_text())
        dado = self.diagnostico_valido()
        dado["veredito"] = "provavelmente"
        erros = validate.validar(dado, schema)
        self.assertTrue(any("enum" in e for e in erros), erros)

    def test_rejeita_campo_desconhecido(self):
        schema = json.loads((RAIZ / "skills/5x-team-code/schemas/diagnostico.schema.json").read_text())
        dado = self.diagnostico_valido()
        dado["conclusao_livre"] = "acho que e o cache"
        erros = validate.validar(dado, schema)
        self.assertTrue(any("conclusao_livre" in e for e in erros), erros)

    def test_implementacao_exige_prova(self):
        schema = json.loads((RAIZ / "skills/5x-team-code/schemas/implementacao.schema.json").read_text())
        erros = validate.validar({"tarefa": "T1", "criterio": "x", "atendido": True}, schema)
        self.assertTrue(any("prova" in e for e in erros), erros)

    def test_cli_exit_1_em_invalido(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "r.json"
            dado = self.diagnostico_valido()
            del dado["fatos_novos"]
            f.write_text(json.dumps(dado))
            r = rodar("5x-validate.py", str(f), "--schema", "diagnostico")
            self.assertEqual(r.returncode, 1)
            self.assertFalse(json.loads(r.stdout)["valido"])

    def test_cli_exit_0_em_valido(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "r.json"
            f.write_text(json.dumps(self.diagnostico_valido()))
            r = rodar("5x-validate.py", str(f), "--schema", "diagnostico")
            self.assertEqual(r.returncode, 0, r.stdout)


class TestEstado(unittest.TestCase):
    def montar_projeto(self, d):
        base = Path(d)
        (base / "memory" / "hipoteses").mkdir(parents=True)
        (base / "memory" / "experimentos").mkdir(parents=True)
        (base / "memory" / "hipoteses" / "H1.md").write_text(
            "---\nstatus: viva\nid: H1\n---\n\n# H1 — decode roda duas vezes\n", encoding="utf-8")
        (base / "memory" / "hipoteses" / "H2.md").write_text(
            "---\nstatus: refutada\nid: H2\n---\n\n# H2 — limite do multipart\n", encoding="utf-8")
        return base

    def test_deriva_pendencia_do_frontmatter(self):
        with tempfile.TemporaryDirectory() as d:
            base = self.montar_projeto(d)
            env = {**os.environ, "CLAUDE_PROJECT_DIR": str(base)}
            r = subprocess.run([sys.executable, str(SCRIPTS / "5x-state.py"), "--write"],
                               capture_output=True, text=True, env=env)
            self.assertEqual(r.returncode, 0, r.stderr)
            texto = (base / "memory" / "ESTADO.md").read_text(encoding="utf-8")
            self.assertIn("- [ ] H1 viva", texto)
            self.assertIn("- [x] H2 refutada", texto)

    def test_nao_inventa_proximo_passo(self):
        with tempfile.TemporaryDirectory() as d:
            base = self.montar_projeto(d)
            env = {**os.environ, "CLAUDE_PROJECT_DIR": str(base)}
            subprocess.run([sys.executable, str(SCRIPTS / "5x-state.py"), "--write"],
                           capture_output=True, text=True, env=env)
            texto = (base / "memory" / "ESTADO.md").read_text(encoding="utf-8")
            self.assertIn("<nao registrado — o vault nao diz>", texto)
            self.assertNotIn("Rodo?", texto)

    def test_sobrescreve_nao_acumula(self):
        with tempfile.TemporaryDirectory() as d:
            base = self.montar_projeto(d)
            env = {**os.environ, "CLAUDE_PROJECT_DIR": str(base)}
            for _ in range(2):
                subprocess.run([sys.executable, str(SCRIPTS / "5x-state.py"), "--write"],
                               capture_output=True, text=True, env=env)
            texto = (base / "memory" / "ESTADO.md").read_text(encoding="utf-8")
            self.assertEqual(texto.count("## Onde estamos"), 1)

    def test_read_deriva_mesmo_sem_estado_md_no_disco(self):
        """SessionStart nao pode injetar vazio so porque ESTADO.md ainda nao existe."""
        with tempfile.TemporaryDirectory() as d:
            base = self.montar_projeto(d)
            self.assertFalse((base / "memory" / "ESTADO.md").exists())
            env = {**os.environ, "CLAUDE_PROJECT_DIR": str(base)}
            r = subprocess.run([sys.executable, str(SCRIPTS / "5x-state.py"), "--read"],
                               capture_output=True, text=True, env=env)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("- [ ] H1 viva", r.stdout)
            self.assertFalse((base / "memory" / "ESTADO.md").exists(),
                             "--read nao pode escrever no disco")

    def test_read_reflete_mudanca_no_vault_sem_write(self):
        with tempfile.TemporaryDirectory() as d:
            base = self.montar_projeto(d)
            env = {**os.environ, "CLAUDE_PROJECT_DIR": str(base)}
            subprocess.run([sys.executable, str(SCRIPTS / "5x-state.py"), "--write"],
                           capture_output=True, text=True, env=env)
            (base / "memory" / "hipoteses" / "H1.md").write_text(
                "---\nstatus: confirmada\nid: H1\n---\n\n# H1 — decode roda duas vezes\n",
                encoding="utf-8")
            r = subprocess.run([sys.executable, str(SCRIPTS / "5x-state.py"), "--read"],
                               capture_output=True, text=True, env=env)
            self.assertIn("- [x] H1 confirmada", r.stdout)
            self.assertNotIn("- [ ] H1 viva", r.stdout)

    def test_silencioso_sem_vault(self):
        with tempfile.TemporaryDirectory() as d:
            env = {**os.environ, "CLAUDE_PROJECT_DIR": d}
            r = subprocess.run([sys.executable, str(SCRIPTS / "5x-state.py"), "--read"],
                               capture_output=True, text=True, env=env)
            self.assertEqual(r.returncode, 0)
            self.assertEqual(r.stdout.strip(), "")


class TestBootstrap(unittest.TestCase):
    def rodar(self, base, *extra):
        r = rodar("5x-bootstrap.py", "--dir", str(base), *extra)
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout)

    def test_cria_estrutura_em_projeto_vazio(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            self.rodar(base)
            for esperado in ("CLAUDE.md", "memory/INDEX.md", "memory/hipoteses",
                             "memory/experimentos", "memory/decisoes", "design",
                             "memory/templates/hipotese.md", "memory/templates/experimento.md"):
                self.assertTrue((base / esperado).exists(), esperado)
            self.assertIn("5x-team protocolo v", (base / "CLAUDE.md").read_text(encoding="utf-8"))

    def test_idempotente(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            self.rodar(base)
            segunda = self.rodar(base)
            self.assertEqual(segunda["criados"], [])
            self.assertIn("CLAUDE.md", segunda["ja_existiam"])

    def test_nao_move_nem_sobrescreve_arquivo_do_usuario(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            (base / "src").mkdir()
            (base / "src" / "app.py").write_text("print('meu codigo')\n", encoding="utf-8")
            (base / "CLAUDE.md").write_text("# Meu CLAUDE.md antigo\n", encoding="utf-8")
            (base / "memory").mkdir()
            (base / "memory" / "INDEX.md").write_text("# meu index\n", encoding="utf-8")
            antes = {p: p.read_bytes() for p in base.rglob("*") if p.is_file()}

            saida = self.rodar(base)

            for caminho, conteudo in antes.items():
                self.assertTrue(caminho.exists(), f"{caminho} sumiu")
                self.assertEqual(caminho.read_bytes(), conteudo, f"{caminho} foi alterado")
            self.assertTrue(any("sem bloco de protocolo" in a for a in saida["avisos"]), saida["avisos"])

    def test_avisa_bloco_de_versao_velha(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            (base / "CLAUDE.md").write_text("<!-- 5x-team protocolo v0.1.0 -->\n# velho\n", encoding="utf-8")
            saida = self.rodar(base)
            self.assertTrue(any("v0.1.0" in a for a in saida["avisos"]), saida["avisos"])
            self.assertIn("v0.1.0", (base / "CLAUDE.md").read_text(encoding="utf-8"))

    def test_dry_run_nao_escreve(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            saida = self.rodar(base, "--dry-run")
            self.assertTrue(saida["criados"])
            self.assertFalse((base / "CLAUDE.md").exists())


class TestGate(unittest.TestCase):
    def repo(self, d, conteudo):
        base = Path(d)
        subprocess.run(["git", "init", "-q"], cwd=base, check=True)
        (base / "app.py").write_text(conteudo, encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=base, check=True)
        return base

    def test_exit_1_com_instrumento(self):
        with tempfile.TemporaryDirectory() as d:
            base = self.repo(d, "x = 1  # DIAG: contador temporario\n")
            r = rodar("5x-gate.py", cwd=base)
            self.assertEqual(r.returncode, 1)
            self.assertEqual(json.loads(r.stdout)["total"], 1)

    def test_exit_0_limpo(self):
        with tempfile.TemporaryDirectory() as d:
            base = self.repo(d, "x = 1\n")
            r = rodar("5x-gate.py", cwd=base)
            self.assertEqual(r.returncode, 0, r.stdout)
            self.assertTrue(json.loads(r.stdout)["limpo"])

    def test_justify_lista_sem_falhar(self):
        with tempfile.TemporaryDirectory() as d:
            base = self.repo(d, "x = 1  # DIAG: contador\n")
            r = rodar("5x-gate.py", "--justify", cwd=base)
            self.assertEqual(r.returncode, 0)
            self.assertEqual(json.loads(r.stdout)["ocorrencias"][0]["arquivo"], "app.py")


class TestCusto(unittest.TestCase):
    def test_record_e_summary(self):
        with tempfile.TemporaryDirectory() as d:
            env = {**os.environ, "CLAUDE_PROJECT_DIR": d}
            r = subprocess.run([sys.executable, str(SCRIPTS / "5x-cost.py"), "record",
                                "--ciclo", "c1", "--tarefa", "T1", "--modelo", "sonnet",
                                "--tokens-in", "1000000", "--tokens-out", "1000000"],
                               capture_output=True, text=True, env=env)
            self.assertEqual(r.returncode, 0, r.stderr)
            reg = json.loads(r.stdout)
            self.assertEqual(reg["modelo"], "claude-sonnet-5")
            self.assertGreater(reg["usd"], 0)

            s = subprocess.run([sys.executable, str(SCRIPTS / "5x-cost.py"), "summary", "--ciclo", "c1"],
                               capture_output=True, text=True, env=env)
            self.assertEqual(json.loads(s.stdout)["total_usd"], reg["usd"])

    def test_modelo_desconhecido_falha_com_lista(self):
        r = rodar("5x-cost.py", "estimate", "--tarefas", "1", "--modelo", "gpt",
                  "--avg-in", "1", "--avg-out", "1")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("Disponiveis", r.stderr)

    def test_tabela_tem_data_de_consulta(self):
        tabela = json.loads((SCRIPTS / "precos.json").read_text(encoding="utf-8"))
        self.assertIn("_consultado_em", tabela)
        self.assertIn("_fonte", tabela)


class TestManifestos(unittest.TestCase):
    def test_nome_da_skill_bate_com_a_pasta_e_e_minusculo(self):
        pasta = RAIZ / "skills" / "5x-team-code"
        frontmatter = (pasta / "SKILL.md").read_text(encoding="utf-8").split("---")[1]
        nome = next(l.split(":", 1)[1].strip() for l in frontmatter.splitlines() if l.startswith("name:"))
        self.assertEqual(nome, pasta.name)
        self.assertEqual(nome, nome.lower())

    def test_plugin_json_valido(self):
        m = json.loads((RAIZ / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(m["name"], "5x-team")
        self.assertRegex(m["version"], r"^\d+\.\d+\.\d+$")

    def test_marketplace_json_valido(self):
        m = json.loads((RAIZ / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
        self.assertEqual(m["name"], "5x-team")
        self.assertIn("name", m["owner"])
        self.assertEqual([p["name"] for p in m["plugins"]], ["5x-team"])

    def test_hooks_usam_plugin_root_e_timeout_curto(self):
        h = json.loads((RAIZ / "hooks" / "hooks.json").read_text(encoding="utf-8"))
        for evento, grupos in h["hooks"].items():
            for grupo in grupos:
                for hook in grupo["hooks"]:
                    self.assertIn("${CLAUDE_PLUGIN_ROOT}", hook["command"], evento)
                    self.assertLessEqual(hook["timeout"], 3, evento)
                    self.assertIn("|| true", hook["command"], f"{evento} precisa ser fail-silent")

    def test_comandos_e_assets_que_o_init_precisa_existem(self):
        for nome in ("5x-init", "5x-diag", "5x-build", "5x-estado", "5x-custo", "5x-crivo", "5x-deps"):
            self.assertTrue((RAIZ / "commands" / f"{nome}.md").is_file(), nome)
        for asset in ("CLAUDE-protocolo.md", "INDEX.template.md", "ESTADO.template.md",
                      "hipotese.template.md", "experimento.template.md"):
            self.assertTrue((RAIZ / "skills/5x-team-code/assets" / asset).is_file(), asset)

    def test_init_nao_manda_mover_arquivo_do_usuario(self):
        texto = (RAIZ / "commands" / "5x-init.md").read_text(encoding="utf-8")
        self.assertIn("Não mova, renomeie nem reorganize", texto)

    def test_versao_marcada_no_bloco_de_protocolo(self):
        bloco = (RAIZ / "skills/5x-team-code/assets/CLAUDE-protocolo.md").read_text(encoding="utf-8")
        plugin = json.loads((RAIZ / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertIn(f"<!-- 5x-team protocolo v{plugin['version']} -->", bloco)


class TestWorktree(unittest.TestCase):
    def test_add_duas_vezes_cria_branches_diferentes(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d) / "repo"
            base.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=base, check=True)
            subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t",
                            "commit", "-q", "--allow-empty", "-m", "raiz"], cwd=base, check=True)

            saidas = []
            for tid in ("T1", "T2"):
                r = subprocess.run(["bash", str(SCRIPTS / "5x-worktree.sh"), "add", tid],
                                   capture_output=True, text=True, cwd=base)
                self.assertEqual(r.returncode, 0, r.stderr)
                saidas.append(json.loads(r.stdout.strip().splitlines()[-1]))

            self.assertNotEqual(saidas[0]["branch"], saidas[1]["branch"])
            self.assertNotEqual(saidas[0]["worktree"], saidas[1]["worktree"])
            for s in saidas:
                self.assertTrue(Path(s["worktree"]).is_dir())

    def test_branch_repetida_e_recusada(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d) / "repo"
            base.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=base, check=True)
            subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t",
                            "commit", "-q", "--allow-empty", "-m", "raiz"], cwd=base, check=True)
            subprocess.run(["bash", str(SCRIPTS / "5x-worktree.sh"), "add", "T1", "task/x"],
                           capture_output=True, text=True, cwd=base)
            r = subprocess.run(["bash", str(SCRIPTS / "5x-worktree.sh"), "add", "T2", "task/x"],
                               capture_output=True, text=True, cwd=base)
            self.assertEqual(r.returncode, 1)
            self.assertIn("Uma branch por worktree", r.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
