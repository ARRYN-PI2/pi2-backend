<<<<<<< HEAD
def parse_details(detalles_str: str) -> dict:
    detalles = {}
    for line in detalles_str.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
        elif " " in line:
            key, value = line.split(" ", 1)
        else:
            continue
        detalles[key.strip()] = value.strip()
    return detalles
=======
def parse_details(detalles_str: str) -> dict:
    detalles = {}
    for line in detalles_str.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
        elif " " in line:
            key, value = line.split(" ", 1)
        else:
            continue
        detalles[key.strip()] = value.strip()
    return detalles
>>>>>>> origin/feature/SCRUM-125-Implementar-identificador-de-ofertas-por-categoría
