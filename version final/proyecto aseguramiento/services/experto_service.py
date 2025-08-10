from pyswip import Prolog
import os

class ExpertoService:
    def __init__(self):
        self.prolog = Prolog()
        ruta_pl = os.path.join("sistemaexperto", "sistemaexperto.pl")
        if os.path.exists(ruta_pl):
            self.prolog.consult(ruta_pl)
        else:
            print(f"⚠ No se encontró el archivo {ruta_pl}")

    def responder_pregunta(self, pregunta):
        try:
            consulta = f"responder('{pregunta.lower()}', R)."
            resultados = list(self.prolog.query(consulta))
            if resultados:
                return resultados[0]['R']
            else:
                return "No tengo información sobre ese problema, asignaré tu ticket a un técnico."
        except Exception as e:
            return f"Error al procesar la consulta: {str(e)}"
