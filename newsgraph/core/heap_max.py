"""Heap Max — fila de prioridade própria (heap binário de máximo).

Estrutura de dados adicional obrigatória. Insere notícias com score e extrai o
Top-N para o feed recomendado.
"""
# newsgraph/core/heap_max.py

class MaxHeap:
    """
    Implementação de uma árvore binária de Heap de Máximo estruturada em uma lista dinâmica.
    Ideal para extração em tempo O(log N) dos elementos de maior relevância/peso.
    """
    def __init__(self):
        self.heap = []

    def _pai(self, i): return (i - 1) // 2
    def _filho_esquerdo(self, i): return 2 * i + 1
    def _filho_direito(self, i): return 2 * i + 2

    def inserir(self, item, peso):
        """Insere um item no heap associado a um determinado peso/prioridade."""
        # Armazena como dicionário ou tupla para fácil desestruturação
        elemento = {"item": item, "peso": peso}
        self.heap.append(elemento)
        self._subir(len(self.heap) - 1)

    def extrair_max(self):
        """Remove e retorna o elemento de maior prioridade (raiz) do heap."""
        if not self.heap:
            return None
        
        raiz = self.heap[0]
        ultimo_elemento = self.heap.pop()
        
        if self.heap:
            self.heap[0] = ultimo_elemento
            self._descer(0)
            
        return raiz

    def _subir(self, i):
        """Flutua o elemento para cima mantendo a propriedade do Max-Heap."""
        while i > 0 and self.heap[i]["peso"] > self.heap[self._pai(i)]["peso"]:
            pai_idx = self._pai(i)
            self.heap[i], self.heap[pai_idx] = self.heap[pai_idx], self.heap[i]
            i = pai_idx

    def _descer(self, i):
        """Flutua o elemento para baixo corrigindo violações da propriedade do heap."""
        maior = i
        esq = self._filho_esquerdo(i)
        dir = self._filho_direito(i)
        n = len(self.heap)

        if esq < n and self.heap[esq]["peso"] > self.heap[maior]["peso"]:
            maior = esq
        if dir < n and self.heap[dir]["peso"] > self.heap[maior]["peso"]:
            maior = dir

        if maior != i:
            self.heap[i], self.heap[maior] = self.heap[maior], self.heap[i]
            self._descer(maior)

    def top_n(self, n):
        """
        Retorna as N maiores recomendações do Heap de forma ordenada.
        Atenção: Consome/esvazia o estado atual do Heap.
        """
        resultados = []
        for _ in range(n):
            max_elem = self.extrair_max()
            if max_elem:
                resultados.append(max_elem)
            else:
                break
        return resultados

    def esta_vazio(self):
        return len(self.heap) == 0


# ==============================================================================
# TESTES UNITÁRIOS DO HEAP
# ==============================================================================
if __name__ == "__main__":
    print("Iniciando testes unitários de heap_max.py...")
    heap = MaxHeap()
    heap.inserir("Noticia_A", 0.45)
    heap.inserir("Noticia_B", 0.92)
    heap.inserir("Noticia_C", 0.12)
    heap.inserir("Noticia_D", 0.78)

    # O topo deve obrigatoriamente ser a Noticia_B (peso 0.92)
    topo = heap.extrair_max()
    assert topo["item"] == "Noticia_B"
    
    # O top_n residual deve retornar Noticia_D (0.78) seguido por Noticia_A (0.45)
    restantes = heap.top_n(2)
    assert restantes[0]["item"] == "Noticia_D"
    assert restantes[1]["item"] == "Noticia_A"
    
    print("Todos os testes de heap_max.py passaram perfeitamente!\n")