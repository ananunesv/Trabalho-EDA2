"""Gerador de dados fictícios (offline) — via LLM (Google Gemini).

CRÍTICO para o projeto: sem isto a projeção nasce vazia (duas notícias nunca
teriam um leitor em comum). Gera ~40 usuários fictícios com perfis coerentes e,
para cada um, interações com as notícias do seu interesse — produzindo a
coocorrência de leitores que alimenta o Jaccard.

Roda UMA vez na carga inicial, NÃO no cron. Precisa de:
  - notícias já no banco (rode a coleta antes);
  - GEMINI_API_KEY no ambiente / .env (chave do Google AI Studio).

Uso:  PYTHONPATH=. python -m pipeline.gerador_dados [--force]
"""

import argparse
import os
from typing import Literal

from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel

import config
from persistencia.conexao import get_conexao
from persistencia import repositorio

load_dotenv()

SYSTEM = (
    "Você gera dados fictícios coerentes para um sistema de recomendação de "
    "notícias financeiras brasileiras. Responda apenas no formato JSON pedido."
)


# --- Esquemas de saída estruturada (a LLM é obrigada a respeitá-los) ---

class Usuario(BaseModel):
    nome: str
    perfil: str


class ListaUsuarios(BaseModel):
    usuarios: list[Usuario]


class Interacao(BaseModel):
    usuario_indice: int
    noticia_id: int
    tipo_acao: Literal["clique", "like", "compartilhar", "dislike"]


class ListaInteracoes(BaseModel):
    interacoes: list[Interacao]


def _gerar(cliente, modelo_saida, prompt, max_tokens):
    """Faz uma chamada com saída estruturada e devolve a instância Pydantic."""
    resp = cliente.models.generate_content(
        model=config.MODELO_LLM,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM,
            response_mime_type="application/json",
            response_schema=modelo_saida,
            max_output_tokens=max_tokens,
            # Desliga o "thinking" do 2.5-flash: mais rápido/barato e evita que o
            # raciocínio consuma o orçamento de tokens da resposta.
            thinking_config=types.ThinkingConfig(thinking_budget=0),
        ),
    )
    if resp.parsed is not None:
        return resp.parsed
    return modelo_saida.model_validate_json(resp.text)


def gerar_usuarios(cliente, quantidade):
    """Pede à LLM uma lista de personas (nome + perfil de interesse)."""
    prompt = (
        f"Crie {quantidade} usuários fictícios brasileiros de uma newsletter de "
        "notícias financeiras. Cada um deve ter um nome e um 'perfil' curto que "
        "descreva seus interesses (ex.: 'investidor em renda fixa, acompanha Selic "
        "e Tesouro Direto'; 'trader de ações, foca em Ibovespa e techs'; "
        "'interessado em cripto e câmbio'). Varie os perfis para que grupos de "
        "usuários compartilhem interesses — é isso que cria coocorrência de leitura."
    )
    return _gerar(cliente, ListaUsuarios, prompt, max_tokens=8192).usuarios


def gerar_interacoes_do_lote(cliente, personas_indexadas, contexto_noticias):
    """Para um lote de usuários, pede as interações coerentes com seus perfis.

    `personas_indexadas`: lista de (indice_global, Usuario).
    `contexto_noticias`: bloco de texto 'id | título | fonte'.
    """
    linhas_usuarios = "\n".join(
        f"  [{idx}] {p.nome} — {p.perfil}" for idx, p in personas_indexadas
    )
    prompt = (
        "Notícias disponíveis (use exatamente esses noticia_id):\n"
        f"{contexto_noticias}\n\n"
        "Usuários deste lote (use exatamente esses usuario_indice):\n"
        f"{linhas_usuarios}\n\n"
        "Para CADA usuário, gere de 8 a 20 interações com notícias coerentes com o "
        "perfil dele. Use os tipos: 'clique' (interesse leve), 'like' (gostou), "
        "'compartilhar' (gostou muito) e, ocasionalmente, 'dislike' (não tem a ver "
        "com o perfil). Usuários com perfis parecidos devem ler notícias parecidas "
        "(coocorrência). Não invente noticia_id que não esteja na lista."
    )
    return _gerar(cliente, ListaInteracoes, prompt, max_tokens=16384).interacoes


def main(force=False):
    chave = os.environ.get("GEMINI_API_KEY")
    if not chave:
        print("GEMINI_API_KEY não definida. Pegue a chave no Google AI Studio e ponha no .env.")
        return
    cliente = genai.Client(api_key=chave)

    conn = get_conexao()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM usuarios;")
            if cur.fetchone()[0] > 0 and not force:
                print("Já existem usuários no banco. Use --force para gerar mesmo assim.")
                return

            noticias = repositorio.buscar_noticias(cur)
            if not noticias:
                print("Sem notícias no banco. Rode a coleta antes (pipeline.run_coleta).")
                return
            print(f"{len(noticias)} notícias carregadas.")
            ids_validos = {n["id"] for n in noticias}
            contexto = "\n".join(
                f"{n['id']} | {n['titulo']} | {n['fonte']}" for n in noticias
            )

            print(f"Gerando {config.USUARIOS_FICTICIOS} usuários via {config.MODELO_LLM}...")
            personas = gerar_usuarios(cliente, config.USUARIOS_FICTICIOS)
            ids_usuarios = [repositorio.salvar_usuario(cur, p.nome) for p in personas]
            print(f"  {len(ids_usuarios)} usuários inseridos.")

            indexadas = list(enumerate(personas))
            lote = config.USUARIOS_POR_LOTE
            total_interacoes = 0
            for inicio in range(0, len(indexadas), lote):
                grupo = indexadas[inicio:inicio + lote]
                print(f"Gerando interações para usuários {inicio}–{inicio + len(grupo) - 1}...")
                interacoes = gerar_interacoes_do_lote(cliente, grupo, contexto)
                for it in interacoes:
                    if not (0 <= it.usuario_indice < len(ids_usuarios)):
                        continue
                    if it.noticia_id not in ids_validos:
                        continue
                    peso = config.PESOS[it.tipo_acao]
                    repositorio.registrar_interacao(
                        cur, ids_usuarios[it.usuario_indice], it.noticia_id, it.tipo_acao, peso
                    )
                    total_interacoes += 1

        conn.commit()
        print(f"OK. {len(ids_usuarios)} usuários e {total_interacoes} interações gravados.")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gera usuários e interações fictícias via LLM.")
    parser.add_argument("--force", action="store_true", help="gera mesmo se já houver usuários")
    args = parser.parse_args()
    main(force=args.force)
