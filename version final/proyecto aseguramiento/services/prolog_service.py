from pyswip import Prolog
import os

prolog = Prolog()
prolog.consult(os.path.join("sistemaexperto", "sistemaexperto.pl"))

def consultar_experto(problema):
    resultados = list(prolog.query(f"responder('{problema}', R)."))
    if resultados:
        return resultados[0]["R"]
    return "No tengo información, asignaré un técnico para ayudarte."
