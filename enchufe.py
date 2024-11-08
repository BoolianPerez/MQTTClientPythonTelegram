import json

class Enchufe:
    def __init__(self, nombre, topico, estado=False):
        self.nombre = nombre
        self.topico = topico
        self.estado = estado

def guardar_enchufes(enchufes, filename='enchufes.json'):
    with open(filename, 'w') as f:
        json.dump([enchufe.__dict__ for enchufe in enchufes], f)

def cargar_enchufes(filename='enchufes.json'):
    try:
        with open(filename, 'r') as f:
            enchufes_data = json.load(f)
            return [Enchufe(**data) for data in enchufes_data]
    except FileNotFoundError:
        return []