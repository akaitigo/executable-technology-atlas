"""Independent all-simple-path enumeration; does not import runner or use reverse BFS."""
def paths(graph):
    found = []
    def walk(path):
        found.append(path)
        for node in graph[path[-1]]:
            if node in path:
                raise ValueError('cycle')
            walk(path + [node])
    for start in graph:
        walk([start])
    return found

def impact(graph, changed):
    ps = paths(graph)
    witnesses = [p for p in ps if p[-1] in changed]
    return sorted({p[0] for p in witnesses}), witnesses

# Separate fixed expected values from equations in the implementation.
EXPECTED = {
 'config': {'config': 20, 'price': 120, 'invoice': 120, 'report': 120, 'audit': 'ok'},
 'price': {'config': 10, 'price': 100, 'invoice': 100, 'report': 100, 'audit': 'ok'},
 'invoice': {'config': 10, 'price': 110, 'invoice': 220, 'report': 220, 'audit': 'ok'},
 'report': {'config': 10, 'price': 110, 'invoice': 110, 'report': 0, 'audit': 'ok'},
 'audit': {'config': 10, 'price': 110, 'invoice': 110, 'report': 110, 'audit': 'broken'},
 'nochange': {'config': 10, 'price': 110, 'invoice': 110, 'report': 110, 'audit': 'ok'}
}
