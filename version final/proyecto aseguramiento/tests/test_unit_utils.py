# tests/test_unit_utils.py
import app as app_module

def test_normaliza_txt():
    assert app_module.normaliza_txt("  Hólá  ") == "hola"
    assert app_module.normaliza_txt("SeÑal") == "senal"

def test_tema_normalizado():
    assert app_module.tema_normalizado("No tengo señal de internet") == "sin señal"
    assert app_module.tema_normalizado("Mi conexión es lenta") == "conexión lenta"
    assert app_module.tema_normalizado("El wifi no conecta") == "wifi no conecta"
    assert app_module.tema_normalizado("algo raro") == "otro"

def test_sugerencias_keys():
    # Asegura que existan los temas predefinidos
    for k in ["sin señal", "caída de red", "conexión lenta", "wifi no conecta", "otro"]:
        assert k in app_module.SUGERENCIAS
        assert len(app_module.SUGERENCIAS[k]) >= 3
