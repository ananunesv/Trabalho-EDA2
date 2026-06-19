
from core.grafo import Grafo


class GrafoBipartido:
    def __init__(self):
        # Conjuntos de vértices dos dois lados do bipartido
        self.usuarios: set = set()
        self.noticias: set = set()

        # {noticia_id: {usuario_id: peso}}  — alimenta o Jaccard
        self._leitores: dict = {}

        # {usuario_id: {noticia_id: peso}}  — alimenta as sementes do motor
        self._leituras: dict = {}

        # Notícias que receberam dislike de cada usuário — excluídas das sementes
        # {usuario_id: set(noticia_id)}
        self._dislikes: dict = {}

    def adicionar_interacao(self, usuario_id, noticia_id, peso: int) -> None:
        self.usuarios.add(usuario_id)
        self.noticias.add(noticia_id)

        if peso <= 0:
            # Dislike: registra para exclusão futura, não cria aresta positiva
            self._dislikes.setdefault(usuario_id, set()).add(noticia_id)
            return

        # Aresta positiva: notícia → leitor com peso
        self._leitores.setdefault(noticia_id, {})[usuario_id] = float(peso)

        # Aresta positiva: usuário → notícia com peso (para as sementes)
        self._leituras.setdefault(usuario_id, {})[noticia_id] = float(peso)

    @classmethod
    def construir(cls, usuarios: list, noticias: list, interacoes: list) -> "GrafoBipartido":
        """Factory: constrói o bipartido a partir dos dados do repositório.

        Args:
            usuarios:   Lista de dicts {'id': ..., 'nome': ...}.
            noticias:   Lista de dicts {'id': ..., 'titulo': ...}.
            interacoes: Lista de dicts {'usuario_id', 'noticia_id', 'peso'}.

        Returns:
            GrafoBipartido pronto para uso pelo motor e pela projeção.
        """
        g = cls()

        # Registra todos os vértices mesmo que não tenham interações
        for u in usuarios:
            g.usuarios.add(u["id"])
        for n in noticias:
            g.noticias.add(n["id"])
            g._leitores.setdefault(n["id"], {})

        for inter in interacoes:
            g.adicionar_interacao(
                inter["usuario_id"],
                inter["noticia_id"],
                inter["peso"],
            )

        return g

    def leitores_de(self, noticia_id) -> dict:
        return dict(self._leitores.get(noticia_id, {}))

    def leituras_de(self, usuario_id) -> dict:
        return dict(self._leituras.get(usuario_id, {}))

    def dislikes_de(self, usuario_id) -> set:
        return set(self._dislikes.get(usuario_id, set()))

    def num_usuarios(self) -> int:
        return len(self.usuarios)

    def num_noticias(self) -> int:
        return len(self.noticias)

    def num_interacoes_positivas(self) -> int:
        return sum(len(v) for v in self._leitores.values())