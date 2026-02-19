import { useState, useEffect, useRef } from "react";

const COLORS = {
  bg: "#0a0f0d",
  bgCard: "#111916",
  bgCardHover: "#172019",
  border: "#1e2e25",
  borderActive: "#2d6b45",
  accent: "#3dd68c",
  accentDim: "#2a9d63",
  accentGlow: "rgba(61, 214, 140, 0.15)",
  text: "#e8f0ec",
  textDim: "#8fa89a",
  textMuted: "#5a7568",
  warning: "#f5a623",
  danger: "#e74c3c",
  info: "#4fa3d1",
  purple: "#a78bfa",
  gold: "#d4a843",
};

const sections = [
  { id: "overview", label: "Visión General", icon: "🌿" },
  { id: "architecture", label: "Arquitectura", icon: "🏗" },
  { id: "pathway1", label: "Vía 1: Imagen", icon: "📷" },
  { id: "pathway2", label: "Vía 2: Síntomas", icon: "🩺" },
  { id: "pathway3", label: "Vía 3: Fármaco", icon: "💊" },
  { id: "genomic", label: "Motor Genómico", icon: "🧬" },
  { id: "stack", label: "Tech Stack", icon: "⚙️" },
  { id: "apis", label: "APIs & Datos", icon: "📡" },
  { id: "confidence", label: "Confianza", icon: "📊" },
  { id: "deployment", label: "Despliegue", icon: "☁️" },
  { id: "roadmap", label: "Hoja de Ruta", icon: "🗺" },
];

const EvidenceBadge = ({ level }) => {
  const config = {
    1: { label: "Lit. Revisada", color: COLORS.accent, bg: "rgba(61,214,140,0.12)" },
    2: { label: "DB Fitoquímica", color: COLORS.info, bg: "rgba(79,163,209,0.12)" },
    3: { label: "Etnobotánica", color: COLORS.gold, bg: "rgba(212,168,67,0.12)" },
    4: { label: "Inferencia Genómica", color: COLORS.purple, bg: "rgba(167,139,250,0.12)" },
  };
  const c = config[level];
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: 6,
      padding: "3px 10px", borderRadius: 6,
      background: c.bg, color: c.color,
      fontSize: 12, fontWeight: 600, letterSpacing: 0.3,
      border: `1px solid ${c.color}33`,
    }}>
      <span style={{ width: 6, height: 6, borderRadius: "50%", background: c.color }} />
      Nivel {level}: {c.label}
    </span>
  );
};

const Card = ({ title, children, accent, span }) => (
  <div style={{
    background: COLORS.bgCard,
    border: `1px solid ${COLORS.border}`,
    borderRadius: 12,
    padding: "24px 28px",
    gridColumn: span ? `span ${span}` : undefined,
    borderTop: accent ? `3px solid ${accent}` : `3px solid ${COLORS.borderActive}`,
    transition: "border-color 0.3s, box-shadow 0.3s",
  }}>
    {title && (
      <h3 style={{
        margin: "0 0 16px 0",
        fontSize: 17,
        fontWeight: 700,
        color: COLORS.text,
        fontFamily: "'DM Sans', sans-serif",
      }}>{title}</h3>
    )}
    {children}
  </div>
);

const CodeBlock = ({ children }) => (
  <pre style={{
    background: "#080d0a",
    border: `1px solid ${COLORS.border}`,
    borderRadius: 8,
    padding: 16,
    margin: "12px 0",
    fontSize: 12.5,
    lineHeight: 1.65,
    color: COLORS.accentDim,
    fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
    overflowX: "auto",
    whiteSpace: "pre",
  }}>
    {children}
  </pre>
);

const P = ({ children, dim }) => (
  <p style={{
    margin: "0 0 12px 0",
    fontSize: 14.5,
    lineHeight: 1.75,
    color: dim ? COLORS.textDim : COLORS.text,
    fontFamily: "'DM Sans', sans-serif",
  }}>{children}</p>
);

const Tag = ({ children, color }) => (
  <span style={{
    display: "inline-block",
    padding: "2px 9px",
    borderRadius: 5,
    background: `${color || COLORS.accent}18`,
    color: color || COLORS.accent,
    fontSize: 12,
    fontWeight: 600,
    marginRight: 6,
    marginBottom: 4,
  }}>{children}</span>
);

const FlowArrow = () => (
  <div style={{
    textAlign: "center",
    color: COLORS.textMuted,
    fontSize: 20,
    margin: "8px 0",
  }}>↓</div>
);

const TableWrap = ({ children }) => (
  <div style={{ overflowX: "auto", margin: "12px 0" }}>
    <table style={{
      width: "100%",
      borderCollapse: "collapse",
      fontSize: 13,
      fontFamily: "'DM Sans', sans-serif",
    }}>
      {children}
    </table>
  </div>
);
const Th = ({ children }) => (
  <th style={{
    textAlign: "left",
    padding: "10px 14px",
    borderBottom: `2px solid ${COLORS.borderActive}`,
    color: COLORS.accent,
    fontWeight: 700,
    fontSize: 12,
    textTransform: "uppercase",
    letterSpacing: 0.5,
  }}>{children}</th>
);
const Td = ({ children, highlight }) => (
  <td style={{
    padding: "10px 14px",
    borderBottom: `1px solid ${COLORS.border}`,
    color: highlight ? COLORS.accent : COLORS.text,
    fontWeight: highlight ? 600 : 400,
  }}>{children}</td>
);

// ─── SECTION COMPONENTS ─────────────────────────────────────────────

const Overview = () => (
  <div style={{ display: "grid", gap: 20 }}>
    <Card title="Misión del Sistema" accent={COLORS.accent}>
      <P>Plataforma de inteligencia fitoquímica de grado de investigación, impulsada por IA, centrada en la biodiversidad de México. No es una aplicación de recomendaciones simples — es un motor de soporte de decisiones científicas que integra visión computacional, modelos de lenguaje, bases de datos fitoquímicas, registros etnobotánicos, análisis genómico e inferencia de similitud molecular.</P>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 12 }}>
        <Tag>Visión Computacional</Tag>
        <Tag>LLM + RAG</Tag>
        <Tag>Fitoquímica</Tag>
        <Tag>Genómica</Tag>
        <Tag>Etnobotánica</Tag>
        <Tag>Grafos de Conocimiento</Tag>
        <Tag>Inferencia Molecular</Tag>
      </div>
    </Card>
    <Card title="Jerarquía de Evidencia (Obligatoria)">
      <div style={{ display: "flex", flexDirection: "column", gap: 10, marginTop: 4 }}>
        <EvidenceBadge level={1} />
        <EvidenceBadge level={2} />
        <EvidenceBadge level={3} />
        <EvidenceBadge level={4} />
      </div>
      <P dim style={{ marginTop: 14 }}>Ninguna afirmación puede omitir esta jerarquía. Los resultados de inferencia genómica deben etiquetarse explícitamente como probabilísticos con puntaje de confianza y razonamiento computacional.</P>
    </Card>
    <Card title="Tres Vías Inteligentes de Recomendación">
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 16 }}>
        {[
          { icon: "📷", title: "Imagen → Planta", desc: "CV identifica especie → compuestos → propiedades → dosis → contraindicaciones → citas" },
          { icon: "🩺", title: "Síntomas → Plantas", desc: "NLP extrae entidades → mapeo ICD/MeSH → filtro regional → ranking con evidencia" },
          { icon: "💊", title: "Fármaco → Plantas", desc: "Compuesto → plantas que lo contienen → análogos biosintéticos → similitud molecular" },
        ].map((v, i) => (
          <div key={i} style={{
            background: COLORS.bg, borderRadius: 10,
            padding: 18, border: `1px solid ${COLORS.border}`,
          }}>
            <div style={{ fontSize: 28, marginBottom: 8 }}>{v.icon}</div>
            <div style={{ fontWeight: 700, color: COLORS.accent, fontSize: 14, marginBottom: 6 }}>{v.title}</div>
            <div style={{ color: COLORS.textDim, fontSize: 13, lineHeight: 1.6 }}>{v.desc}</div>
          </div>
        ))}
      </div>
    </Card>
  </div>
);

const Architecture = () => (
  <div style={{ display: "grid", gap: 20 }}>
    <Card title="Diagrama de Arquitectura — Capas del Sistema" span={2} accent={COLORS.accent}>
      <CodeBlock>{`
┌─────────────────────────────────────────────────────────────────────┐
│                    CAPA DE PRESENTACIÓN                             │
│  Next.js 14 (App Router) + React + TailwindCSS                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────────┐  │
│  │ Upload   │ │ Symptom  │ │ Drug     │ │ Results Explorer     │  │
│  │ Image    │ │ Input    │ │ Search   │ │ + Citation Viewer    │  │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └──────────────────────┘  │
│       │             │            │                                   │
├───────┴─────────────┴────────────┴──────────────────────────────────┤
│                    CAPA API (FastAPI + GraphQL)                      │
│  ┌────────────┐  ┌────────────────┐  ┌───────────────────────────┐ │
│  │ /identify  │  │ /recommend     │  │ /match-compound           │ │
│  │ (Vision)   │  │ (Symptoms)     │  │ (Drug→Plant)              │ │
│  └─────┬──────┘  └───────┬────────┘  └────────────┬──────────────┘ │
│        │                 │                         │                │
├────────┴─────────────────┴─────────────────────────┴────────────────┤
│                    CAPA DE ORQUESTACIÓN                              │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  LangChain / LangGraph — Agente Multi-Herramienta           │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐   │    │
│  │  │ RAG      │ │ Tool     │ │ Evidence │ │ Confidence   │   │    │
│  │  │ Pipeline │ │ Router   │ │ Ranker   │ │ Scorer       │   │    │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────────┘   │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                      │
├──────────────────────────────────────────────────────────────────────┤
│                    CAPA DE DATOS & CONOCIMIENTO                      │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────────┐   │
│  │ PostgreSQL │ │ Qdrant     │ │ Neo4j      │ │ Redis          │   │
│  │ + PostGIS  │ │ (Vectors)  │ │ (Grafo)    │ │ (Cache)        │   │
│  └────────────┘ └────────────┘ └────────────┘ └────────────────┘   │
│                                                                      │
├──────────────────────────────────────────────────────────────────────┤
│                    CAPA DE SERVICIOS ESPECIALIZADOS                   │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────────┐   │
│  │ PlantNet   │ │ NCBI BLAST │ │ PubMed     │ │ KEGG / ChEBI   │   │
│  │ + Custom   │ │ + Ensembl  │ │ + CrossRef │ │ + KNApSAcK     │   │
│  │ CV Model   │ │ Plants     │ │ + Semantic │ │ + PubChem      │   │
│  │            │ │            │ │ Scholar    │ │                │   │
│  └────────────┘ └────────────┘ └────────────┘ └────────────────┘   │
│                                                                      │
├──────────────────────────────────────────────────────────────────────┤
│                    CAPA DE INFERENCIA GENÓMICA                       │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  Biopython + RDKit + antiSMASH + HMMER                      │    │
│  │  ┌──────────────┐ ┌──────────────┐ ┌────────────────────┐   │    │
│  │  │ FASTA/BLAST  │ │ Pathway      │ │ Metabolite Cluster │   │    │
│  │  │ Alignment    │ │ Mapper       │ │ Analysis           │   │    │
│  │  └──────────────┘ └──────────────┘ └────────────────────┘   │    │
│  └─────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────┘
`}</CodeBlock>
    </Card>

    <Card title="Justificación de Decisiones Arquitectónicas">
      <div style={{ display: "grid", gap: 14 }}>
        {[
          { q: "¿Por qué FastAPI + GraphQL?", a: "FastAPI ofrece tipado estricto con Pydantic (validación científica de datos), async nativo para llamadas externas concurrentes (NCBI, PubMed, KEGG). GraphQL como capa complementaria permite queries flexibles sobre el grafo de conocimiento sin proliferación de endpoints REST." },
          { q: "¿Por qué LangGraph sobre LangChain puro?", a: "LangGraph permite orquestación de flujos cíclicos con estado — esencial cuando la Vía 1 no encuentra literatura y debe activar inferencia genómica como fallback. Los grafos de estado permiten ramas condicionales con trazabilidad completa." },
          { q: "¿Por qué Qdrant sobre Pinecone/Weaviate?", a: "Qdrant es open-source con filtrado de payload nativo (filtrar por región geográfica, nivel de evidencia), soporta embeddings densos + sparse (hybrid search), y permite self-hosting para soberanía de datos de investigación." },
          { q: "¿Por qué Neo4j para Knowledge Graph?", a: "Las relaciones planta→compuesto→pathway→enzima→gen son inherentemente grafos. Neo4j con GDS (Graph Data Science) permite algoritmos de centralidad, detección de comunidades, y caminos más cortos para inferencia de similitud molecular." },
          { q: "¿Por qué PostgreSQL + PostGIS?", a: "PostGIS permite consultas geoespaciales nativas para filtrar plantas por región mexicana, bioma, altitud. Combinado con datos de CONABIO permite recomendaciones hiperlocales." },
        ].map((item, i) => (
          <div key={i} style={{ background: COLORS.bg, borderRadius: 8, padding: 14, border: `1px solid ${COLORS.border}` }}>
            <div style={{ color: COLORS.accent, fontWeight: 700, fontSize: 13, marginBottom: 6 }}>{item.q}</div>
            <div style={{ color: COLORS.textDim, fontSize: 13, lineHeight: 1.7 }}>{item.a}</div>
          </div>
        ))}
      </div>
    </Card>
  </div>
);

const Pathway1 = () => (
  <div style={{ display: "grid", gap: 20 }}>
    <Card title="Vía 1 — Pipeline de Identificación por Imagen" accent={COLORS.accent}>
      <P>Pipeline completo desde captura de imagen hasta recomendación con evidencia:</P>
      {[
        { step: "1. Preprocesamiento", detail: "Resize, normalización, corrección de orientación, detección de calidad (blur, exposición). Si calidad < umbral → solicitar nueva imagen." },
        { step: "2. Identificación Primaria — Pl@ntNet API", detail: "API gratuita con >40k especies. Retorna top-K candidatos con probabilidad. Ventaja: entrenado con iNaturalist + herbarios europeos. Limitación: cobertura de endémicas mexicanas puede ser baja." },
        { step: "3. Modelo Complementario — Custom Fine-tuned", detail: "EfficientNet-V2 o ConvNeXt-V2 fine-tuned con dataset de herbarios mexicanos (MEXU-UNAM, CONABIO). Training data: imágenes geoetiquetadas de iNaturalist filtradas por México + digitalización de herbarios. Esto cubre el gap de endémicas." },
        { step: "4. Ensemble de Decisión", detail: "Weighted voting entre Pl@ntNet + modelo custom. Si ambos coinciden con >80% → alta confianza. Si divergen → presentar ambos candidatos con confianza individual." },
        { step: "5. Enriquecimiento Fitoquímico", detail: "Especie identificada → query a KNApSAcK, PubChem, ChEBI para compuestos activos conocidos. Cruce con base etnobotánica (BDMTM-UNAM, Biblioteca Digital de la Medicina Tradicional Mexicana)." },
        { step: "6. Recuperación de Literatura", detail: "PubMed E-utilities API: buscar por nombre científico + 'medicinal' OR 'phytochemical' OR 'pharmacological'. Semantic Scholar API como complemento para embeddings semánticos de papers." },
        { step: "7. Fallback Genómico", detail: "Si literatura insuficiente → activar Motor de Inferencia Genómica (ver sección dedicada). Estimar probabilidad de compuestos bioactivos por similitud de pathway." },
        { step: "8. Composición de Respuesta", detail: "LLM (Claude API via RAG) genera respuesta estructurada con: propiedades, compuestos, preparación, dosis, contraindicaciones, toxicología. Cada claim vinculado a fuente con nivel de evidencia." },
      ].map((s, i) => (
        <div key={i}>
          <div style={{
            background: COLORS.bg, borderRadius: 8, padding: "12px 16px",
            border: `1px solid ${COLORS.border}`, marginBottom: 4,
          }}>
            <span style={{ color: COLORS.accent, fontWeight: 700, fontSize: 13 }}>{s.step}</span>
            <div style={{ color: COLORS.textDim, fontSize: 13, lineHeight: 1.7, marginTop: 4 }}>{s.detail}</div>
          </div>
          {i < 7 && <FlowArrow />}
        </div>
      ))}
    </Card>

    <Card title="Comparativa: APIs de Identificación de Plantas">
      <TableWrap>
        <thead>
          <tr><Th>API / Modelo</Th><Th>Especies</Th><Th>Endémicas MX</Th><Th>Costo</Th><Th>Precisión</Th><Th>Decisión</Th></tr>
        </thead>
        <tbody>
          <tr><Td highlight>Pl@ntNet</Td><Td>~45,000</Td><Td>Media</Td><Td>Gratis (500/día)</Td><Td>~85% top-5</Td><Td><Tag color={COLORS.accent}>Primario</Tag></Td></tr>
          <tr><Td>Google Cloud Vision</Td><Td>Amplio</Td><Td>Baja</Td><Td>$1.50/1000</Td><Td>~70% plants</Td><Td><Tag color={COLORS.textMuted}>Descartado</Tag></Td></tr>
          <tr><Td>iNaturalist CV</Td><Td>~76,000</Td><Td>Alta</Td><Td>Uso interno</Td><Td>~90% top-5</Td><Td><Tag color={COLORS.info}>Dataset training</Tag></Td></tr>
          <tr><Td highlight>Custom ConvNeXt-V2</Td><Td>~5,000 MX</Td><Td>Muy Alta</Td><Td>GPU training</Td><Td>Target 92%</Td><Td><Tag color={COLORS.accent}>Complementario</Tag></Td></tr>
          <tr><Td>Plant.id</Td><Td>~33,000</Td><Td>Baja</Td><Td>$0.10/query</Td><Td>~82%</Td><Td><Tag color={COLORS.textMuted}>Respaldo</Tag></Td></tr>
        </tbody>
      </TableWrap>
      <P dim>Decisión: Ensemble Pl@ntNet + Custom Model. Pl@ntNet cubre cobertura global, el modelo custom cierra la brecha de endémicas mexicanas. iNaturalist Research-Grade como fuente de datos de entrenamiento.</P>
    </Card>
  </div>
);

const Pathway2 = () => (
  <div style={{ display: "grid", gap: 20 }}>
    <Card title="Vía 2 — Pipeline de Recomendación por Síntomas" accent={COLORS.info}>
      <P>Sistema de NLP médico → mapeo ontológico → filtro geoespacial → ranking con evidencia:</P>
      {[
        { step: "1. Extracción de Entidades Médicas (NER)", detail: "Modelo: SapBERT fine-tuned en corpus médico en español (ej. PharmaCoNER + corpus propio). Extrae síntomas, condiciones, partes del cuerpo, severidad. Fallback: SpaCy + diccionario médico curado." },
        { step: "2. Mapeo a Ontologías Médicas", detail: "Entidades extraídas → mapeo a: ICD-11 (diagnósticos), MeSH (descriptores PubMed), SNOMED-CT (terminología clínica), UMLS (unificado). Uso de MetaMap Lite o QuickUMLS para vinculación. Esto permite queries estandarizadas a PubMed y bases fitoquímicas." },
        { step: "3. Localización Geoespacial", detail: "GPS del usuario o selección manual de estado/municipio. PostGIS filtra plantas con distribución en esa región. Fuentes: CONABIO SNIBer (registros de colecta), GlobalBiodiversityInformationFacility (GBIF), NaturaLista (iNaturalist México)." },
        { step: "4. Consulta Multi-Base de Datos", detail: "Para cada condición mapeada → buscar en: BDMTM (Biblioteca Digital Medicina Tradicional Mexicana), NAPRALERT, Dr. Duke's Phytochemical DB, PubMed (nombre planta + condición). Retornar plantas candidatas con nivel de evidencia." },
        { step: "5. Ranking con Evidencia Ponderada", detail: "Score = Σ(w_nivel × relevancia × consistencia_fuentes). Nivel 1 (literatura): w=1.0, Nivel 2 (DB fitoquímica): w=0.7, Nivel 3 (etnobotánica): w=0.4, Nivel 4 (inferencia): w=0.2. Plantas rankeadas por score compuesto." },
        { step: "6. Verificación de Seguridad", detail: "Cada planta candidata pasa por check de: toxicidad conocida, interacciones farmacológicas, contraindicaciones (embarazo, lactancia, alergias). Fuente: Base de interacciones de Natural Medicines Comprehensive Database." },
        { step: "7. Fallback: Inferencia por Similitud Molecular", detail: "Si evidencia < umbral → identificar compuestos activos conocidos contra la condición → buscar plantas con compuestos molecularmente similares (Tanimoto > 0.7) via RDKit fingerprints." },
      ].map((s, i) => (
        <div key={i}>
          <div style={{
            background: COLORS.bg, borderRadius: 8, padding: "12px 16px",
            border: `1px solid ${COLORS.border}`, marginBottom: 4,
          }}>
            <span style={{ color: COLORS.info, fontWeight: 700, fontSize: 13 }}>{s.step}</span>
            <div style={{ color: COLORS.textDim, fontSize: 13, lineHeight: 1.7, marginTop: 4 }}>{s.detail}</div>
          </div>
          {i < 6 && <FlowArrow />}
        </div>
      ))}
    </Card>

    <Card title="Ontologías Médicas Integradas">
      <TableWrap>
        <thead>
          <tr><Th>Ontología</Th><Th>Propósito</Th><Th>Integración</Th><Th>Cobertura Español</Th></tr>
        </thead>
        <tbody>
          <tr><Td highlight>ICD-11</Td><Td>Clasificación diagnóstica</Td><Td>API REST OMS</Td><Td>Completa</Td></tr>
          <tr><Td highlight>MeSH</Td><Td>Descriptores PubMed</Td><Td>E-utilities NCBI</Td><Td>Parcial</Td></tr>
          <tr><Td>SNOMED-CT</Td><Td>Terminología clínica</Td><Td>FHIR Terminology Server</Td><Td>Completa</Td></tr>
          <tr><Td>UMLS</Td><Td>Unificación de ontologías</Td><Td>MetaMap / QuickUMLS</Td><Td>Parcial</Td></tr>
          <tr><Td>HPO</Td><Td>Fenotipo humano</Td><Td>API HPO</Td><Td>En progreso</Td></tr>
        </tbody>
      </TableWrap>
    </Card>
  </div>
);

const Pathway3 = () => (
  <div style={{ display: "grid", gap: 20 }}>
    <Card title="Vía 3 — Pipeline de Matching Fármaco→Planta" accent={COLORS.purple}>
      <P>Dado un medicamento o compuesto activo, encontrar plantas que contengan ese compuesto o análogos biosintéticos:</P>
      {[
        { step: "1. Resolución del Compuesto", detail: "Input (ej. 'ibuprofeno') → resolver a: PubChem CID, SMILES, InChIKey, fórmula molecular. APIs: PubChem PUG REST, ChEBI, DrugBank. Si input es nombre comercial → mapear a principio activo via DrugBank o RxNorm." },
        { step: "2. Búsqueda Directa en DBs Fitoquímicas", detail: "Buscar compuesto exacto en: KNApSAcK (compuesto→planta), Dr. Duke's (compuesto→planta→actividad), FooDB, NAPRALERT. Si encontrado → retornar plantas con nivel de evidencia 2." },
        { step: "3. Búsqueda de Análogos Estructurales", detail: "Si no hay match exacto → RDKit genera fingerprint molecular (Morgan/ECFP4). Calcular Tanimoto similarity contra biblioteca de ~50,000 fitoquímicos conocidos. Umbral: Tanimoto ≥ 0.7 para 'análogo probable'. Retornar plantas que contienen esos análogos." },
        { step: "4. Inferencia por Pathway Biosintético", detail: "Mapear compuesto target a pathway KEGG. Identificar enzimas clave del pathway. Buscar homólogos de esas enzimas en genomas de plantas mexicanas (BLAST). Si enzimas presentes → la planta puede producir compuestos en esa ruta metabólica." },
        { step: "5. Análisis de Cluster de Metabolitos Secundarios", detail: "Usando antiSMASH, identificar clusters de genes biosintéticos en genomas disponibles. Predecir capacidad de producción de clases de compuestos (terpenoides, alcaloides, flavonoides, etc.)." },
        { step: "6. Scoring Compuesto de Confianza", detail: "Score final = f(match_directo, similitud_tanimoto, homología_enzimática, presencia_pathway, evidencia_literatura). Cada componente con peso y justificación. Resultado clasificado en: Confirmado / Probable / Inferido / Especulativo." },
      ].map((s, i) => (
        <div key={i}>
          <div style={{
            background: COLORS.bg, borderRadius: 8, padding: "12px 16px",
            border: `1px solid ${COLORS.border}`, marginBottom: 4,
          }}>
            <span style={{ color: COLORS.purple, fontWeight: 700, fontSize: 13 }}>{s.step}</span>
            <div style={{ color: COLORS.textDim, fontSize: 13, lineHeight: 1.7, marginTop: 4 }}>{s.detail}</div>
          </div>
          {i < 5 && <FlowArrow />}
        </div>
      ))}
    </Card>
  </div>
);

const Genomic = () => (
  <div style={{ display: "grid", gap: 20 }}>
    <Card title="Motor de Inferencia Genómica — Diseño Completo" accent={COLORS.gold}>
      <P>Este motor se activa como fallback cuando la evidencia de literatura y bases de datos es insuficiente. Funciona como un asistente de bioinformática semi-automatizado.</P>

      <div style={{ background: COLORS.bg, borderRadius: 10, padding: 20, border: `1px solid ${COLORS.border}`, marginTop: 12 }}>
        <div style={{ color: COLORS.gold, fontWeight: 700, fontSize: 14, marginBottom: 12 }}>Workflow de Inferencia</div>
        <CodeBlock>{`
INPUT: Especie_planta + Compuesto_target
                    │
    ┌───────────────┴───────────────┐
    ▼                               ▼
[Ruta A: BLAST]              [Ruta B: Pathway]
    │                               │
    ▼                               ▼
Obtener secuencias         Mapear compuesto a
de enzimas clave           KEGG pathway
del pathway target              │
    │                           ▼
    ▼                    Obtener lista de
BLASTP contra            enzimas del pathway
proteoma de la                  │
planta target                   ▼
    │                    Buscar homólogos
    ▼                    en genoma/transcriptoma
Evaluar:                 de la planta
- E-value                       │
- % identidad                   ▼
- % cobertura            Evaluar completitud
    │                    del pathway
    └───────────┬───────────────┘
                ▼
    [Ruta C: antiSMASH]
    Análisis de clusters
    biosintéticos (BGC)
                │
                ▼
    ┌───────────────────┐
    │ SCORE COMPUESTO   │
    │                   │
    │ BLAST:    0-100   │
    │ Pathway:  0-100   │
    │ BGC:      0-100   │
    │ ─────────────     │
    │ Confianza: X%     │
    │ Categoría: [C/P/I/E]│
    └───────────────────┘
`}</CodeBlock>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14, marginTop: 16 }}>
        {[
          { title: "BLAST / FASTA", tools: "NCBI BLAST+ CLI, Biopython", desc: "Alineamiento de secuencias para identificar enzimas homólogas. E-value < 1e-30 + identidad > 40% = homólogo probable." },
          { title: "KEGG Pathway", tools: "KEGG REST API, KEGGTools", desc: "Mapear compuesto → pathway → enzimas (EC numbers). Verificar presencia de cada enzima en el organismo target." },
          { title: "antiSMASH", tools: "antiSMASH 7.0 API/CLI", desc: "Predicción de clusters de genes biosintéticos. Detecta capacidad de producir terpenoides, alcaloides, policétidos, etc." },
          { title: "HMMER / Pfam", tools: "HMMER3, Pfam DB", desc: "Búsqueda de dominios proteicos conservados. Más sensible que BLAST para detectar homología distante." },
        ].map((t, i) => (
          <div key={i} style={{ background: COLORS.bg, borderRadius: 8, padding: 14, border: `1px solid ${COLORS.border}` }}>
            <div style={{ color: COLORS.gold, fontWeight: 700, fontSize: 13 }}>{t.title}</div>
            <div style={{ color: COLORS.accent, fontSize: 11, marginTop: 4, fontFamily: "monospace" }}>{t.tools}</div>
            <div style={{ color: COLORS.textDim, fontSize: 12, lineHeight: 1.6, marginTop: 6 }}>{t.desc}</div>
          </div>
        ))}
      </div>
    </Card>

    <Card title="Fuentes de Datos Genómicos">
      <TableWrap>
        <thead>
          <tr><Th>Base de Datos</Th><Th>Contenido</Th><Th>Acceso</Th><Th>Uso en Sistema</Th></tr>
        </thead>
        <tbody>
          <tr><Td highlight>NCBI GenBank</Td><Td>Secuencias nucleótidos/proteínas</Td><Td>E-utilities API</Td><Td>BLAST queries</Td></tr>
          <tr><Td highlight>Ensembl Plants</Td><Td>Genomas completos de plantas</Td><Td>REST API</Td><Td>Genomas de referencia</Td></tr>
          <tr><Td highlight>KEGG</Td><Td>Pathways metabólicos</Td><Td>REST API</Td><Td>Mapeo compound→pathway</Td></tr>
          <tr><Td>UniProt</Td><Td>Proteomas curados</Td><Td>REST API</Td><Td>Anotación de enzimas</Td></tr>
          <tr><Td>PhytoMine / Phytozome</Td><Td>Genómica comparativa plantas</Td><Td>InterMine API</Td><Td>Búsqueda de homólogos</Td></tr>
          <tr><Td>MIBiG</Td><Td>Clusters biosintéticos</Td><Td>API REST</Td><Td>Referencia BGC</Td></tr>
          <tr><Td>PlantCyc</Td><Td>Pathways de plantas</Td><Td>Flatfiles</Td><Td>Pathways metabólicos</Td></tr>
        </tbody>
      </TableWrap>
    </Card>
  </div>
);

const Stack = () => (
  <div style={{ display: "grid", gap: 20 }}>
    <Card title="Tech Stack Completo — Justificado" accent={COLORS.accent}>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 14 }}>
        {[
          { cat: "Frontend", items: ["Next.js 14 (App Router, RSC)", "React 18 + TypeScript", "TailwindCSS + shadcn/ui", "React Query (cache + sync)", "Mapbox GL (visualización geoespacial)"], why: "RSC para SEO y carga rápida de resultados. TypeScript para tipado estricto en interfaces científicas." },
          { cat: "Backend / API", items: ["FastAPI (Python 3.12)", "Strawberry GraphQL", "Celery + Redis (tareas async)", "Pydantic v2 (validación)", "gRPC (servicios internos)"], why: "FastAPI es el estándar para APIs de ML. Celery para BLAST jobs de larga duración. Pydantic asegura integridad de datos científicos." },
          { cat: "LLM / Agentes", items: ["Claude API (Sonnet 4)", "LangGraph (orquestación)", "LangSmith (observabilidad)", "Custom RAG pipeline", "Guardrails AI (anti-hallucination)"], why: "Claude como LLM principal por su capacidad de razonamiento científico. LangGraph para flujos condicionales con estado. Guardrails para verificación factual." },
          { cat: "Bases de Datos", items: ["PostgreSQL 16 + PostGIS", "Qdrant (vector DB)", "Neo4j (knowledge graph)", "Redis (cache + message broker)", "MinIO (object storage imágenes)"], why: "PostgreSQL como source-of-truth relacional. Qdrant para búsqueda semántica. Neo4j para relaciones moleculares. MinIO para imágenes de plantas." },
          { cat: "ML / Visión", items: ["PyTorch 2.x", "Hugging Face Transformers", "ConvNeXt-V2 (custom CV)", "SapBERT (NER médico)", "RDKit (cheminformatics)"], why: "PyTorch para training custom. HF para NER pre-entrenado. RDKit es el estándar de oro para fingerprints moleculares y similitud." },
          { cat: "Bioinformática", items: ["Biopython 1.83", "NCBI BLAST+ 2.15", "HMMER 3.4", "antiSMASH 7.0", "Open Babel (conversión molecular)"], why: "Stack estándar de bioinformática. BLAST+ local para latencia predecible. antiSMASH para predicción de clusters biosintéticos." },
          { cat: "Infraestructura", items: ["Kubernetes (GKE/EKS)", "Terraform (IaC)", "GitHub Actions (CI/CD)", "Prometheus + Grafana", "OpenTelemetry (tracing)"], why: "K8s para escalar servicios de inferencia. Terraform para reproducibilidad. OTEL para tracing de pipelines complejos." },
          { cat: "Data Pipelines", items: ["Apache Airflow 2.x", "dbt (transformación)", "Great Expectations (calidad)", "Scrapy (web scraping)", "Delta Lake (versionamiento)"], why: "Airflow orquesta ingesta de NCBI, PubMed, KEGG. dbt transforma datos crudos. Great Expectations valida calidad de datos científicos." },
        ].map((s, i) => (
          <div key={i} style={{ background: COLORS.bg, borderRadius: 10, padding: 16, border: `1px solid ${COLORS.border}` }}>
            <div style={{ color: COLORS.accent, fontWeight: 800, fontSize: 14, marginBottom: 10, textTransform: "uppercase", letterSpacing: 0.5 }}>{s.cat}</div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 5, marginBottom: 10 }}>
              {s.items.map((it, j) => <Tag key={j}>{it}</Tag>)}
            </div>
            <div style={{ color: COLORS.textMuted, fontSize: 12, lineHeight: 1.6, fontStyle: "italic" }}>{s.why}</div>
          </div>
        ))}
      </div>
    </Card>
  </div>
);

const Apis = () => (
  <div style={{ display: "grid", gap: 20 }}>
    <Card title="APIs Externas & Fuentes de Datos — Catálogo Completo" accent={COLORS.info}>
      <TableWrap>
        <thead>
          <tr><Th>Fuente</Th><Th>Tipo</Th><Th>Datos</Th><Th>Acceso</Th><Th>Rate Limit</Th><Th>Rol</Th></tr>
        </thead>
        <tbody>
          {[
            ["Pl@ntNet", "API REST", "ID de plantas por imagen", "Gratis (500/día)", "500/día", "Identificación primaria"],
            ["NCBI E-utilities", "API REST", "GenBank, PubMed, Taxonomy", "Gratis (API key)", "10/seg", "BLAST, literatura, taxonomía"],
            ["PubChem PUG REST", "API REST", "Compuestos químicos, SMILES", "Gratis", "5/seg", "Resolución de compuestos"],
            ["KEGG REST", "API REST", "Pathways, enzimas, compuestos", "Gratis (académico)", "10/seg", "Mapeo metabólico"],
            ["ChEBI", "API + OLS", "Ontología de entidades químicas", "Gratis", "Sin límite", "Clasificación de compuestos"],
            ["KNApSAcK", "Web + dump", "Compuesto↔Planta (51K+)", "Gratis", "Scraping/dump", "Matching fitoquímico"],
            ["UniProt", "API REST", "Proteomas, anotación funcional", "Gratis", "Sin límite", "Anotación de enzimas"],
            ["Ensembl Plants", "REST API", "Genomas de plantas", "Gratis", "15/seg", "Genomas de referencia"],
            ["GBIF", "API REST", "Distribución de especies", "Gratis", "3/seg", "Geolocalización de especies"],
            ["CONABIO SNIB", "WMS/WFS", "Biodiversidad mexicana", "Gratis", "Variable", "Distribución regional MX"],
            ["Semantic Scholar", "API REST", "Papers académicos", "Gratis (API key)", "100/5min", "Búsqueda semántica de papers"],
            ["CrossRef", "API REST", "Metadatos DOI", "Gratis", "50/seg (cortesía)", "Verificación de citas"],
            ["DrugBank", "API REST", "Interacciones fármacos", "Académico", "Variable", "Drug matching, interacciones"],
            ["ICD-11 API (OMS)", "API REST", "Clasificación diagnóstica", "Gratis", "Sin límite", "Mapeo de diagnósticos"],
          ].map((row, i) => (
            <tr key={i}>
              <Td highlight>{row[0]}</Td>
              <Td>{row[1]}</Td>
              <Td>{row[2]}</Td>
              <Td>{row[3]}</Td>
              <Td>{row[4]}</Td>
              <Td>{row[5]}</Td>
            </tr>
          ))}
        </tbody>
      </TableWrap>
    </Card>

    <Card title="Fuentes Etnobotánicas Mexicanas">
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
        {[
          { name: "BDMTM", full: "Biblioteca Digital de la Medicina Tradicional Mexicana (UNAM)", desc: "La fuente más completa sobre uso tradicional de plantas medicinales en México. Monografías detalladas por especie.", access: "Web (scraping estructurado)" },
          { name: "Herbario MEXU", full: "Herbario Nacional de México (UNAM)", desc: "Mayor herbario de Latinoamérica. >1.8M especímenes. Datos de colecta con georreferencia.", access: "Base de datos + digitalización" },
          { name: "NAPRALERT", full: "Natural Products Alert (UIC)", desc: "Base de datos de actividad biológica de productos naturales. Relaciones compuesto↔actividad↔organismo.", access: "Suscripción académica" },
          { name: "Atlas de Plantas Medicinales", full: "Atlas de las Plantas de la Medicina Tradicional Mexicana", desc: "Compilación de uso tradicional con información geográfica por región. >3,000 especies documentadas.", access: "Publicación + digitalización" },
        ].map((s, i) => (
          <div key={i} style={{ background: COLORS.bg, borderRadius: 8, padding: 14, border: `1px solid ${COLORS.border}` }}>
            <div style={{ color: COLORS.gold, fontWeight: 700, fontSize: 14 }}>{s.name}</div>
            <div style={{ color: COLORS.textDim, fontSize: 11, marginTop: 2, marginBottom: 6 }}>{s.full}</div>
            <div style={{ color: COLORS.text, fontSize: 12, lineHeight: 1.6 }}>{s.desc}</div>
            <div style={{ marginTop: 8 }}><Tag color={COLORS.info}>{s.access}</Tag></div>
          </div>
        ))}
      </div>
    </Card>
  </div>
);

const Confidence = () => (
  <div style={{ display: "grid", gap: 20 }}>
    <Card title="Algoritmo de Scoring de Confianza" accent={COLORS.warning}>
      <P>Cada recomendación del sistema incluye un puntaje de confianza compuesto. El algoritmo combina múltiples señales con pesos calibrados:</P>

      <CodeBlock>{`
CONFIDENCE SCORE ALGORITHM
══════════════════════════════════════════════════

Score_final = Σ (w_i × score_i) / Σ (w_i)

Componentes y pesos:
─────────────────────────────────────
Componente                  │ Peso (w)  │ Rango
─────────────────────────────────────
Literatura peer-reviewed    │ 1.00      │ 0-100
  - # papers con evidencia  │           │
  - Impact Factor medio     │           │
  - Tipo estudio (RCT>obs)  │           │
─────────────────────────────────────
DB Fitoquímica confirmada   │ 0.80      │ 0-100
  - # bases que confirman   │           │
  - Cuantificación disp.    │           │
─────────────────────────────────────
Registro etnobotánico       │ 0.40      │ 0-100
  - # fuentes independientes│           │
  - Consistencia regional   │           │
─────────────────────────────────────
BLAST / homología           │ 0.25      │ 0-100
  - E-value (log scale)     │           │
  - % identidad             │           │
  - % cobertura             │           │
─────────────────────────────────────
Pathway completeness        │ 0.20      │ 0-100
  - % enzimas presentes     │           │
  - Gaps en pathway         │           │
─────────────────────────────────────
Similitud molecular         │ 0.15      │ 0-100
  - Tanimoto coefficient    │           │
  - Scaffold similarity     │           │
─────────────────────────────────────

CLASIFICACIÓN FINAL:
  Score ≥ 85  →  CONFIRMADO   (alta confianza)
  Score 65-84 →  PROBABLE     (evidencia fuerte)
  Score 40-64 →  INFERIDO     (evidencia moderada)
  Score < 40  →  ESPECULATIVO (requiere validación)

CADA resultado incluye:
  ✓ Puntaje numérico (0-100)
  ✓ Categoría de clasificación
  ✓ Desglose por componente
  ✓ Fuentes citadas por componente
  ✓ Nivel de evidencia (1-4)
  ✓ Limitaciones explícitas
`}</CodeBlock>
    </Card>

    <Card title="Anti-Alucinación & Validación Científica">
      <div style={{ display: "grid", gap: 12 }}>
        {[
          { title: "Guardrails AI Integration", desc: "Validadores custom: cada claim del LLM se verifica contra la base de conocimiento vectorial. Si un claim no tiene embedding cercano (cosine < 0.7) → se marca como no verificado o se elimina." },
          { title: "Citation Grounding", desc: "Cada afirmación médica debe tener al menos una cita trazable. El sistema rechaza outputs del LLM que contienen claims sin fuente." },
          { title: "Contradiction Detection", desc: "Pipeline de detección de contradicciones: si fuente A dice 'seguro' y fuente B dice 'tóxico', el sistema presenta ambas perspectivas con metadatos de calidad." },
          { title: "Toxicity Red Flags", desc: "Base de datos de plantas con toxicidad conocida (LD50, hepatotoxicidad, nefrotoxicidad). Cualquier planta con flag de toxicidad genera warning prominente independientemente del score." },
          { title: "Human-in-the-Loop", desc: "Para scores < 40 (especulativo), el sistema sugiere validación por experto. Se incluye mecanismo de feedback para que investigadores corrijan o validen inferencias." },
        ].map((item, i) => (
          <div key={i} style={{ background: COLORS.bg, borderRadius: 8, padding: 14, border: `1px solid ${COLORS.border}` }}>
            <div style={{ color: COLORS.warning, fontWeight: 700, fontSize: 13, marginBottom: 4 }}>{item.title}</div>
            <div style={{ color: COLORS.textDim, fontSize: 13, lineHeight: 1.7 }}>{item.desc}</div>
          </div>
        ))}
      </div>
    </Card>
  </div>
);

const Deployment = () => (
  <div style={{ display: "grid", gap: 20 }}>
    <Card title="Arquitectura de Despliegue" accent={COLORS.accent}>
      <CodeBlock>{`
              ┌─────────────────────────────┐
              │     CDN (CloudFlare)        │
              │     + WAF + DDoS            │
              └─────────────┬───────────────┘
                            │
              ┌─────────────▼───────────────┐
              │   Load Balancer (L7)         │
              │   NGINX / Envoy              │
              └─────────────┬───────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼──────┐  ┌────────▼────────┐  ┌───────▼──────┐
│  Frontend    │  │  API Gateway    │  │  WebSocket   │
│  Next.js     │  │  Kong / Envoy   │  │  Server      │
│  (Vercel)    │  │                 │  │  (streaming) │
└──────────────┘  └────────┬────────┘  └──────────────┘
                           │
            ┌──────────────┼──────────────┐
            │              │              │
     ┌──────▼─────┐ ┌─────▼──────┐ ┌────▼──────┐
     │ FastAPI    │ │ FastAPI    │ │ FastAPI   │
     │ (Vision)  │ │ (NLP/Rec)  │ │ (Drug)    │
     │ Pod x3    │ │ Pod x3     │ │ Pod x2    │
     └──────┬─────┘ └─────┬──────┘ └────┬──────┘
            │              │              │
            └──────────────┼──────────────┘
                           │
     ┌─────────────────────┼─────────────────────┐
     │                     │                     │
┌────▼─────┐  ┌───────────▼──────────┐  ┌──────▼─────┐
│PostgreSQL│  │ Qdrant (3-node       │  │ Neo4j      │
│+ PostGIS │  │ cluster)             │  │ (Cluster)  │
│ (HA)     │  │                      │  │            │
└──────────┘  └──────────────────────┘  └────────────┘

     ┌──────────────────────────────────────────┐
     │  GPU Node Pool (A100 / L4)               │
     │  ┌────────────┐ ┌─────────────────────┐  │
     │  │ CV Model   │ │ BLAST+ / antiSMASH  │  │
     │  │ Inference  │ │ Batch Processing    │  │
     │  └────────────┘ └─────────────────────┘  │
     └──────────────────────────────────────────┘
`}</CodeBlock>
    </Card>

    <Card title="Estimación de Costos Mensuales (Producción)">
      <TableWrap>
        <thead>
          <tr><Th>Servicio</Th><Th>Especificación</Th><Th>Costo/mes (USD)</Th></tr>
        </thead>
        <tbody>
          {[
            ["GKE / EKS Cluster", "3 nodes e2-standard-4 + 1 GPU L4", "$800-1,200"],
            ["PostgreSQL (Cloud SQL)", "4 vCPU, 16GB RAM, 500GB SSD", "$200-350"],
            ["Qdrant Cloud", "3-node cluster, 50GB", "$150-300"],
            ["Neo4j Aura", "Professional, 8GB RAM", "$200-400"],
            ["Redis (Memorystore)", "Standard, 5GB", "$50-80"],
            ["MinIO / Cloud Storage", "500GB images + backups", "$30-50"],
            ["Claude API", "~200K requests/mes", "$300-600"],
            ["Vercel (Frontend)", "Pro plan", "$20"],
            ["Monitoring (Grafana Cloud)", "Pro plan", "$50"],
            ["Total estimado", "", "$1,800 - $3,050"],
          ].map((row, i) => (
            <tr key={i} style={{ fontWeight: i === 9 ? 700 : 400 }}>
              <Td highlight={i === 9}>{row[0]}</Td>
              <Td>{row[1]}</Td>
              <Td highlight={i === 9}>{row[2]}</Td>
            </tr>
          ))}
        </tbody>
      </TableWrap>
      <P dim>Nota: Costos reducibles significativamente con spot instances para BLAST jobs y caching agresivo de resultados de APIs externas.</P>
    </Card>
  </div>
);

const Roadmap = () => (
  <div style={{ display: "grid", gap: 20 }}>
    <Card title="Hoja de Ruta — Fases de Desarrollo" accent={COLORS.accent}>
      {[
        { phase: "Fase 1 — Fundación (Meses 1-3)", color: COLORS.accent, items: [
          "Infraestructura base: PostgreSQL + PostGIS, Qdrant, Redis",
          "Ingesta inicial: KNApSAcK, BDMTM, GBIF México (pipelines Airflow)",
          "API core: FastAPI con endpoints básicos de consulta",
          "Knowledge Graph v1: Neo4j con relaciones planta→compuesto→actividad",
          "RAG pipeline v1: embeddings de monografías etnobotánicas en Qdrant",
          "Frontend: Next.js scaffold con las 3 vías de entrada",
        ]},
        { phase: "Fase 2 — Inteligencia Visual (Meses 4-6)", color: COLORS.info, items: [
          "Integración Pl@ntNet API",
          "Dataset de entrenamiento: scraping iNaturalist Research-Grade (México)",
          "Fine-tuning ConvNeXt-V2 para endémicas mexicanas",
          "Ensemble de decisión (Pl@ntNet + custom)",
          "Pipeline de enriquecimiento fitoquímico post-identificación",
          "Búsqueda de literatura PubMed/Semantic Scholar",
        ]},
        { phase: "Fase 3 — NLP Médico & Geoespacial (Meses 7-9)", color: COLORS.purple, items: [
          "NER médico: fine-tune SapBERT para síntomas en español",
          "Integración ontologías: ICD-11, MeSH, QuickUMLS",
          "Motor geoespacial: PostGIS + CONABIO + GBIF para filtro regional",
          "Scoring de evidencia v1",
          "Vía 2 funcional end-to-end",
          "Visualización de mapa con distribución de plantas recomendadas",
        ]},
        { phase: "Fase 4 — Motor Genómico (Meses 10-14)", color: COLORS.gold, items: [
          "Setup BLAST+ local con genomas de plantas mexicanas",
          "Integración KEGG pathway mapper",
          "Pipeline RDKit para similitud molecular (fingerprints, Tanimoto)",
          "Integración antiSMASH para predicción BGC",
          "Scoring de confianza compuesto v2",
          "Vía 3 (Drug matching) funcional end-to-end",
          "Fallback genómico activado para Vías 1 y 2",
        ]},
        { phase: "Fase 5 — Refinamiento & Publicación (Meses 15-18)", color: COLORS.danger, items: [
          "Validación con panel de expertos (etnobotánicos, farmacólogos)",
          "Calibración de scores de confianza con datos reales",
          "Documentación para reproducibilidad de investigación",
          "Paper académico: metodología + validación",
          "API pública para investigadores",
          "Expansión de cobertura: Centroamérica, Caribe",
        ]},
      ].map((p, i) => (
        <div key={i} style={{
          background: COLORS.bg, borderRadius: 10, padding: 18,
          border: `1px solid ${COLORS.border}`,
          borderLeft: `4px solid ${p.color}`,
          marginBottom: 4,
        }}>
          <div style={{ color: p.color, fontWeight: 800, fontSize: 15, marginBottom: 10 }}>{p.phase}</div>
          <div style={{ display: "grid", gap: 6 }}>
            {p.items.map((it, j) => (
              <div key={j} style={{ color: COLORS.textDim, fontSize: 13, lineHeight: 1.5, paddingLeft: 16, position: "relative" }}>
                <span style={{ position: "absolute", left: 0, color: p.color }}>›</span>
                {it}
              </div>
            ))}
          </div>
        </div>
      ))}
    </Card>

    <Card title="Análisis de Riesgos">
      <TableWrap>
        <thead>
          <tr><Th>Riesgo</Th><Th>Impacto</Th><Th>Probabilidad</Th><Th>Mitigación</Th></tr>
        </thead>
        <tbody>
          {[
            ["Cobertura baja de endémicas en APIs de CV", "Alto", "Alta", "Modelo custom + ensemble"],
            ["Rate limits de NCBI/KEGG", "Medio", "Media", "Cache agresivo + batch processing nocturno"],
            ["Datos etnobotánicos no estructurados", "Alto", "Alta", "Pipeline de scraping + NER + validación manual"],
            ["Genomas incompletos de plantas MX", "Alto", "Media", "Transcriptómica como alternativa + inferencia por taxón cercano"],
            ["Hallucinations del LLM", "Crítico", "Media", "Guardrails + citation grounding + human-in-the-loop"],
            ["Responsabilidad médica", "Crítico", "Baja", "Disclaimers prominentes + no reemplaza consejo médico"],
            ["Costos de GPU para BLAST/CV", "Medio", "Media", "Spot instances + caching + procesamiento batch"],
          ].map((row, i) => (
            <tr key={i}>
              <Td>{row[0]}</Td>
              <Td><Tag color={row[1] === "Crítico" ? COLORS.danger : row[1] === "Alto" ? COLORS.warning : COLORS.info}>{row[1]}</Tag></Td>
              <Td>{row[2]}</Td>
              <Td>{row[3]}</Td>
            </tr>
          ))}
        </tbody>
      </TableWrap>
    </Card>

    <Card title="Disclaimer Ético Obligatorio" accent={COLORS.danger}>
      <div style={{
        background: `${COLORS.danger}10`,
        border: `1px solid ${COLORS.danger}40`,
        borderRadius: 8,
        padding: 16,
      }}>
        <P>⚠️ Este sistema NO es un sustituto del consejo médico profesional. Todas las recomendaciones son de carácter informativo y educativo. Los resultados de inferencia genómica son probabilísticos y requieren validación experimental. Las preparaciones de plantas medicinales pueden tener interacciones con medicamentos y efectos adversos. Consulte siempre a un profesional de la salud antes de utilizar plantas medicinales con fines terapéuticos.</P>
      </div>
    </Card>
  </div>
);

// ─── MAIN APP ───────────────────────────────────────────────────────

export default function App() {
  const [active, setActive] = useState("overview");
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const h = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", h);
    return () => window.removeEventListener("scroll", h);
  }, []);

  const renderSection = () => {
    switch (active) {
      case "overview": return <Overview />;
      case "architecture": return <Architecture />;
      case "pathway1": return <Pathway1 />;
      case "pathway2": return <Pathway2 />;
      case "pathway3": return <Pathway3 />;
      case "genomic": return <Genomic />;
      case "stack": return <Stack />;
      case "apis": return <Apis />;
      case "confidence": return <Confidence />;
      case "deployment": return <Deployment />;
      case "roadmap": return <Roadmap />;
      default: return <Overview />;
    }
  };

  return (
    <div style={{
      minHeight: "100vh",
      background: COLORS.bg,
      color: COLORS.text,
      fontFamily: "'DM Sans', sans-serif",
    }}>
      <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet" />

      {/* Header */}
      <header style={{
        position: "sticky",
        top: 0,
        zIndex: 100,
        background: scrolled ? `${COLORS.bg}ee` : COLORS.bg,
        backdropFilter: scrolled ? "blur(12px)" : "none",
        borderBottom: `1px solid ${scrolled ? COLORS.border : "transparent"}`,
        transition: "all 0.3s",
        padding: "16px 24px",
      }}>
        <div style={{ maxWidth: 1200, margin: "0 auto" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <span style={{ fontSize: 28 }}>🌿</span>
            <div>
              <h1 style={{
                margin: 0,
                fontSize: 20,
                fontWeight: 800,
                color: COLORS.accent,
                letterSpacing: -0.5,
              }}>
                PhytoMX Intelligence
              </h1>
              <div style={{ fontSize: 11, color: COLORS.textMuted, fontWeight: 500, letterSpacing: 0.5, textTransform: "uppercase" }}>
                Arquitectura del Sistema · Blueprint Técnico
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav style={{
        position: "sticky",
        top: 65,
        zIndex: 90,
        background: `${COLORS.bg}ee`,
        backdropFilter: "blur(12px)",
        borderBottom: `1px solid ${COLORS.border}`,
        overflowX: "auto",
        WebkitOverflowScrolling: "touch",
      }}>
        <div style={{
          maxWidth: 1200,
          margin: "0 auto",
          display: "flex",
          gap: 2,
          padding: "0 24px",
        }}>
          {sections.map((s) => (
            <button
              key={s.id}
              onClick={() => setActive(s.id)}
              style={{
                background: active === s.id ? COLORS.accentGlow : "transparent",
                border: "none",
                borderBottom: active === s.id ? `2px solid ${COLORS.accent}` : "2px solid transparent",
                color: active === s.id ? COLORS.accent : COLORS.textMuted,
                padding: "12px 14px",
                fontSize: 12.5,
                fontWeight: active === s.id ? 700 : 500,
                cursor: "pointer",
                whiteSpace: "nowrap",
                transition: "all 0.2s",
                fontFamily: "'DM Sans', sans-serif",
                display: "flex",
                alignItems: "center",
                gap: 6,
              }}
            >
              <span style={{ fontSize: 14 }}>{s.icon}</span>
              {s.label}
            </button>
          ))}
        </div>
      </nav>

      {/* Content */}
      <main style={{
        maxWidth: 1200,
        margin: "0 auto",
        padding: "28px 24px 60px",
      }}>
        {renderSection()}
      </main>

      {/* Footer */}
      <footer style={{
        borderTop: `1px solid ${COLORS.border}`,
        padding: "20px 24px",
        textAlign: "center",
        color: COLORS.textMuted,
        fontSize: 12,
      }}>
        PhytoMX Intelligence Platform · Blueprint v1.0 · Diseñado para rigor científico y expansión a largo plazo
      </footer>
    </div>
  );
}
