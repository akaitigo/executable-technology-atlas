"""Independent reflexive transitive closure; no collector imports."""
def reachable(objects,roots):
    names=sorted(obj['id'] for obj in objects);n=len(names)
    matrix=[[i==j for j in range(n)] for i in range(n)]
    for obj in objects:
        for dest in obj['refs']:matrix[names.index(obj['id'])][names.index(dest)]=True
    for via in range(n):
        for source in range(n):
            for dest in range(n):
                matrix[source][dest]=matrix[source][dest] or (matrix[source][via] and matrix[via][dest])
    return [name for j,name in enumerate(names) if any(matrix[names.index(root)][j] for root in roots)]
