"""Muestra por qué el tutor respondió (o no) una pregunta, sin guardar nada en la base.

Uso (dentro del contenedor de la API):
    docker compose exec api python -m app.diagnostico "¿Cómo se calcula el OEE?"
    docker compose exec api python -m app.diagnostico "¿Qué es el MAPE?" --sin-llm   # solo la búsqueda

Imprime los fragmentos encontrados con su distancia, la parte de palabras de la pregunta que tienen (L) y el puntaje
de la búsqueda híbrida; cuáles se eligen para el modelo; la respuesta del modelo tal cual y lo que deja el control de
respaldo. Sirve para calibrar UMBRAL_DISTANCIA, PESO_LEXICO, MARGEN_PUNTAJE y MINIMO_RESPALDO con el material real.
"""

import argparse
import sys

import psycopg

from app.config import obtener_configuracion
from app.consulta import _con_continuacion, seleccionar, texto_para_buscar
from app.rag.busqueda import buscar_fragmentos, indice_lexico, terminos
from app.rag.embeddings import crear_embeddings
from app.rag.llm import ErrorLLM, LLMOllama
from app.rag.prompt import armar_mensajes, es_sin_evidencia, limpiar_respuesta
from app.rag.respaldo import revisar


def _lugar(f) -> str:
    return f"{f.titulo[:70]}, pág. {f.pagina}"


def cargar_y_generar(llm, mensajes) -> str:
    """Cargar el modelo puede tardar más que TIMEOUT_LLM (qwen3:4b, ~3 min en la PC de Alfredo, 10/11/2026, y el
    diagnóstico daba ReadTimeout): se carga antes con su propio plazo y después se genera."""
    print(f"\nCargando {llm.nombre} (la primera vez puede tardar unos minutos)...", flush=True)
    if not llm.precargar():
        raise ErrorLLM(f"No se pudo cargar {llm.nombre} (¿está descargado? ¿hay RAM libre?)")
    return llm.generar(mensajes)


def main(argumentos: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.diagnostico", description=__doc__.splitlines()[0])
    parser.add_argument("pregunta")
    parser.add_argument("--sin-llm", action="store_true", help="Solo la búsqueda, sin llamar al modelo")
    parser.add_argument("--candidatos", type=int, default=10, help="Cuántos fragmentos mostrar")
    parser.add_argument("--llm", help="Otro modelo de Ollama en vez de LLM_MODELO (p. ej. qwen3:4b-instruct-2507-q4_K_M)")
    args = parser.parse_args(argumentos)

    config = obtener_configuracion()
    emb = crear_embeddings(config.embeddings_proveedor, config.embeddings_modelo)
    vector = emb.codificar([texto_para_buscar(args.pregunta)], es_consulta=True)[0]
    with psycopg.connect(config.database_url) as conexion:
        consulta = terminos(args.pregunta)
        indice = indice_lexico(conexion)
        print(f"Palabras que se buscan (peso IDF): "
              + ", ".join(f"{t} ({indice.idf(t):.2f})" for t in consulta))
        print(f"\nUmbral {config.umbral_distancia} · peso léxico {config.peso_lexico} · margen {config.margen_puntaje}")
        print("\nPor significado (como antes):")
        for f in buscar_fragmentos(conexion, vector, args.candidatos):
            print(f"  d={f.distancia:.4f}  {_lugar(f)}")
        print("\nBúsqueda híbrida (la que usa el chat):")
        encontrados = buscar_fragmentos(conexion, vector, args.candidatos, texto=args.pregunta,
                                        umbral=config.umbral_distancia, peso_lexico=config.peso_lexico)
        for f in encontrados:
            fuera = "  (sobre el umbral)" if f.distancia > config.umbral_distancia else ""
            print(f"  puntaje={f.puntaje:.3f}  d={f.distancia:.4f}  {_lugar(f)}{fuera}")
        elegidos = seleccionar(encontrados[:config.fragmentos_por_consulta], config.umbral_distancia,
                               config.margen_puntaje)
        # Igual que el chat: si el mejor termina en el tema o en ":", se le pega el fragmento siguiente.
        antes = elegidos[0].texto if elegidos else ""
        elegidos = _con_continuacion(conexion, vector, args.pregunta, elegidos)
        print("\nVan al modelo:" if elegidos else "\nNinguno pasa el umbral: el tutor se abstiene.")
        for n, f in enumerate(elegidos):
            unido = "  (con el fragmento siguiente pegado)" if n == 0 and f.texto != antes else ""
            print(f"  {_lugar(f)}{unido}")
        if args.sin_llm or not elegidos:
            return 0

        llm = LLMOllama(config.ollama_url, args.llm or config.llm_modelo, config.timeout_llm,
                        config.max_tokens_respuesta)
        try:
            texto = cargar_y_generar(llm, armar_mensajes(args.pregunta, elegidos, None))
        except ErrorLLM as error:
            print(f"\nEl modelo no respondió: {error}")
            return 1
        print(f"\nRespuesta del modelo (tal cual):\n{texto}")
        if es_sin_evidencia(texto):
            print("\nEl modelo se abstuvo (SIN_EVIDENCIA).")
            return 0
        vistos = [f"[{n}] {f.titulo}, página {f.pagina or ''}. {f.texto}" for n, f in enumerate(elegidos, 1)]
        revisado, motivo = revisar(limpiar_respuesta(texto), vistos,
                                   f"{args.pregunta} {texto_para_buscar(args.pregunta)}", config.minimo_respaldo)
        if revisado is None:
            print(f"\nControl de respaldo: DESCARTADA ({motivo}). El tutor se abstiene.")
        else:
            print(f"\nControl de respaldo: {'recortada (' + motivo + ')' if motivo else 'pasa entera'}:\n{revisado}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
