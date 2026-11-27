-- Fase 1: modelo de datos de la base de conocimiento del tutor.
-- Un solo motor (PostgreSQL + pgvector) para datos y vectores.
-- La dimensión 384 corresponde a los dos modelos de embeddings candidatos
-- (paraphrase-multilingual-MiniLM-L12-v2 y multilingual-e5-small). Si el benchmark
-- elige otro modelo con otra dimensión, se cambia aquí y se vuelven a calcular los embeddings.

-- Documento lógico validado por el CEE (un temario, una separata, un manual).
CREATE TABLE documentos (
    id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    titulo      text NOT NULL CHECK (length(trim(titulo)) > 0),
    curso       text,
    tipo        text NOT NULL CHECK (tipo IN ('temario', 'separata', 'presentacion', 'manual', 'reglamento', 'otro')),
    creado_en   timestamptz NOT NULL DEFAULT now()
);

-- Cada carga de un archivo es una versión. Solo una versión vigente por documento (RF-M05).
CREATE TABLE versiones_documento (
    id              bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    documento_id    bigint NOT NULL REFERENCES documentos (id) ON DELETE CASCADE,
    version         integer NOT NULL CHECK (version > 0),
    archivo         text NOT NULL,
    hash_sha256     char(64) NOT NULL,
    paginas         integer CHECK (paginas > 0),
    vigente_desde   date NOT NULL DEFAULT current_date,
    estado          text NOT NULL DEFAULT 'vigente' CHECK (estado IN ('vigente', 'retirado')),
    cargado_en      timestamptz NOT NULL DEFAULT now(),
    retirado_en     timestamptz,
    UNIQUE (documento_id, version),
    CHECK ((estado = 'retirado') = (retirado_en IS NOT NULL))
);

CREATE UNIQUE INDEX una_version_vigente_por_documento
    ON versiones_documento (documento_id) WHERE estado = 'vigente';

-- Fragmentos de texto de una versión, con su página para citar la fuente (RF-M02).
CREATE TABLE fragmentos (
    id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    version_id  bigint NOT NULL REFERENCES versiones_documento (id) ON DELETE CASCADE,
    orden       integer NOT NULL CHECK (orden >= 0),
    pagina      integer CHECK (pagina > 0),
    texto       text NOT NULL CHECK (length(trim(texto)) > 0),
    embedding   vector(384) NOT NULL,
    UNIQUE (version_id, orden)
);

-- Búsqueda por similitud coseno (operador <=>).
CREATE INDEX fragmentos_embedding_hnsw ON fragmentos USING hnsw (embedding vector_cosine_ops);

-- Preguntas frecuentes validadas: se responden sin LLM (RF-13, RNF-04).
CREATE TABLE faqs (
    id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pregunta    text NOT NULL CHECK (length(trim(pregunta)) > 0),
    respuesta   text NOT NULL CHECK (length(trim(respuesta)) > 0),
    fuente      text,
    activa      boolean NOT NULL DEFAULT true,
    embedding   vector(384) NOT NULL,
    creado_en   timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX faqs_embedding_hnsw ON faqs USING hnsw (embedding vector_cosine_ops);

-- Consultas que el bot no pudo resolver, para atención diferida (RF-M04).
-- Mínimos datos: el contacto es opcional y lo deja el alumno si quiere respuesta.
CREATE TABLE consultas_pendientes (
    id            bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pregunta      text NOT NULL CHECK (length(pregunta) BETWEEN 1 AND 1000),
    motivo        text NOT NULL CHECK (motivo IN ('sin_evidencia', 'fuera_de_alcance', 'error', 'pedido_del_alumno')),
    contacto      text CHECK (length(contacto) <= 200),
    creada_en     timestamptz NOT NULL DEFAULT now(),
    atendida_en   timestamptz,
    nota_atencion text
);

CREATE INDEX consultas_pendientes_sin_atender ON consultas_pendientes (creada_en) WHERE atendida_en IS NULL;

-- Registro técnico mínimo (RF-M07): tiempos y estados, sin texto de la pregunta ni datos personales.
CREATE TABLE eventos (
    id               bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    tipo             text NOT NULL CHECK (tipo IN ('consulta', 'ingesta', 'error', 'salud')),
    estado           text NOT NULL,
    ms_total         integer CHECK (ms_total >= 0),
    ms_primer_token  integer CHECK (ms_primer_token >= 0),
    modelo           text,
    creado_en        timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX eventos_por_fecha ON eventos (creado_en);

-- Lo único que el RAG debe buscar: fragmentos de versiones vigentes.
CREATE VIEW fragmentos_vigentes AS
SELECT f.id, f.texto, f.pagina, f.orden, f.embedding,
       d.id AS documento_id, d.titulo, d.curso, d.tipo, v.version
FROM fragmentos f
JOIN versiones_documento v ON v.id = f.version_id AND v.estado = 'vigente'
JOIN documentos d ON d.id = v.documento_id;

-- Registra una versión nueva y retira la anterior en la misma transacción (RF-M05).
CREATE FUNCTION registrar_version(
    p_documento_id bigint, p_archivo text, p_hash char(64), p_paginas integer
) RETURNS bigint
LANGUAGE plpgsql AS $$
DECLARE
    v_siguiente integer;
    v_id bigint;
BEGIN
    -- Bloquea el documento para que dos cargas simultáneas no choquen.
    PERFORM 1 FROM documentos WHERE id = p_documento_id FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'El documento % no existe', p_documento_id;
    END IF;

    IF EXISTS (SELECT 1 FROM versiones_documento
               WHERE documento_id = p_documento_id AND estado = 'vigente' AND hash_sha256 = p_hash) THEN
        RAISE EXCEPTION 'Ese archivo ya es la versión vigente del documento %', p_documento_id;
    END IF;

    UPDATE versiones_documento
       SET estado = 'retirado', retirado_en = now()
     WHERE documento_id = p_documento_id AND estado = 'vigente';

    SELECT coalesce(max(version), 0) + 1 INTO v_siguiente
      FROM versiones_documento WHERE documento_id = p_documento_id;

    INSERT INTO versiones_documento (documento_id, version, archivo, hash_sha256, paginas)
    VALUES (p_documento_id, v_siguiente, p_archivo, p_hash, p_paginas)
    RETURNING id INTO v_id;

    RETURN v_id;
END;
$$;
