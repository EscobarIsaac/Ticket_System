from pyswip import Prolog

def consultar_experto(palabras_clave):
    prolog = Prolog()
    prolog.consult("sistema_experto/experto.pl")

    for result in prolog.query(f"ayuda({palabras_clave}, Respuesta).", maxresult=1):
        return result["Respuesta"]
    return "No se encontró solución, se asignará a un técnico."
