
def jaccard(a: dict, b: dict) -> float:
    # União dos ids de usuários dos dois conjuntos
    todos_usuarios = set(a) | set(b)

    # Caso degenerado: nenhum leitor em nenhuma das duas notícias
    if not todos_usuarios:
        return 0.0

    soma_min = 0.0
    soma_max = 0.0

    for uid in todos_usuarios:
        peso_a = a.get(uid, 0.0)
        peso_b = b.get(uid, 0.0)
        soma_min += min(peso_a, peso_b)
        soma_max += max(peso_a, peso_b)

    # soma_max > 0 garantido: todos_usuarios não é vazio e pesos ≥ 0
    # mas defensivamente evitamos divisão por zero
    if soma_max == 0.0:
        return 0.0

    return soma_min / soma_max