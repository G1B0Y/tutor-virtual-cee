import pytest

from app.diagnostico import cargar_y_generar
from app.rag.llm import ErrorLLM


class LLMFalso:
    nombre = "qwen3:4b-instruct-2507-q4_K_M"

    def __init__(self, carga: bool):
        self.carga = carga
        self.pasos: list[str] = []

    def precargar(self) -> bool:
        self.pasos.append("precargar")
        return self.carga

    def generar(self, mensajes) -> str:
        self.pasos.append("generar")
        return "Es un documento formal."


def test_el_diagnostico_carga_el_modelo_antes_de_generar():
    # 10/11/2026: qwen3 tardaba ~3 min en cargar y el diagnóstico se cortaba con ReadTimeout.
    llm = LLMFalso(carga=True)
    assert cargar_y_generar(llm, []) == "Es un documento formal."
    assert llm.pasos == ["precargar", "generar"]


def test_si_el_modelo_no_carga_no_se_genera():
    llm = LLMFalso(carga=False)
    with pytest.raises(ErrorLLM, match="No se pudo cargar"):
        cargar_y_generar(llm, [])
    assert llm.pasos == ["precargar"]
