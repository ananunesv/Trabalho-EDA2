# newsgraph/database/repositorio.py
from conexao import obter_conexao

class RepositorioFinancas:
    """
    Responsável por realizar consultas de persistência direta, resgatando as arestas 
    e nós da tabela do banco de dados relacional para popular o motor de grafos.
    """
    
    def carregar_grafo_bipartido(self, objeto_grafo):
        """
        Busca todas as interações de leitura da tabela de associação para preencher 
        a estrutura em dicionário do Grafo Bipartido Usuário-Texto.
        """
        conexao = obter_conexao()
        cursor = conexao.cursor()
        
        # Conforme mapeamento da arquitetura v2.0: leituras (usuario_id, noticia_id)
        query = "SELECT usuario_id, noticia_id FROM leituras;"
        
        try:
            cursor.execute(query)
            linhas = cursor.fetchall()
            
            for usuario_id, noticia_id in linhas:
                # O método adicionar_aresta cuida internamente da criação dos vértices
                objeto_grafo.adicionar_aresta(f"User_{usuario_id}", f"News_{noticia_id}")
                
            print(f"Sucesso: {len(linhas)} arestas bipartidas migradas do banco para a memória.")
        except Exception as e:
            print(f"Erro ao popular grafo a partir do banco: {e}")
        finally:
            cursor.close()
            conexao.close()

    def obter_conteudo_noticia(self, noticia_id):
        """Recupera metadados textuais do banco para alimentação do PLN do Dev 1."""
        conexao = obter_conexao()
        # Usando cursor de dicionário para facilitar legibilidade dos campos
        cursor = conexao.cursor(cursor_factory=RealDictCursor)
        
        query = "SELECT id, titulo, conteudo FROM noticias WHERE id = %s;"
        try:
            cursor.execute(query, (noticia_id,))
            return cursor.fetchone()
        except Exception as e:
            print(f"Erro ao obter texto da notícia {noticia_id}: {e}")
            return None
        finally:
            cursor.close()
            conexao.close()