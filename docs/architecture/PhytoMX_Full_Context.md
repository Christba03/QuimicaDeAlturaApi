# PhytoMX Intelligence Platform - Full Context Documentation

> **Purpose**: This document provides complete architectural and technical context for the PhytoMX Intelligence Platform. Use this as a reference when working on any part of the system.

---

## Table of Contents

1. [System Overview & Mission](#system-overview--mission)
2. [Architecture Layers](#architecture-layers)
3. [Three Intelligent Pathways](#three-intelligent-pathways)
4. [Genomic Inference Engine](#genomic-inference-engine)
5. [Tech Stack](#tech-stack)
6. [APIs & Data Sources](#apis--data-sources)
7. [Confidence Scoring System](#confidence-scoring-system)
8. [Database Strategy](#database-strategy)
9. [Redis Schema](#redis-schema)
10. [Deployment Architecture](#deployment-architecture)
11. [Development Roadmap](#development-roadmap)

---

## System Overview & Mission

### Mission Statement

PhytoMX is a **research-grade phytochemical intelligence platform** powered by AI, focused on Mexico's biodiversity. It is **not a simple recommendation app** — it is a scientific decision support engine that integrates:

- Computer vision
- Large language models
- Phytochemical databases
- Ethnobotanical records
- Genomic analysis
- Molecular similarity inference

### Core Principles

1. **Evidence Hierarchy (Mandatory)**: All claims must follow a strict evidence hierarchy:
   - **Level 1**: Peer-reviewed literature
   - **Level 2**: Phytochemical databases
   - **Level 3**: Ethnobotanical records
   - **Level 4**: Genomic inference (must be explicitly labeled as probabilistic)

2. **No Hallucinations**: Every medical claim must have traceable citations. Genomic inference results must include confidence scores and computational reasoning.

3. **Geographic Focus**: Hyperlocal recommendations for Mexican biodiversity using CONABIO, GBIF, and regional distribution data.

---

## Architecture Layers

### Complete System Architecture

```
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
```

### Architectural Decisions

| Decision | Justification |
|----------|---------------|
| **FastAPI + GraphQL** | FastAPI offers strict typing with Pydantic (scientific data validation), native async for concurrent external calls (NCBI, PubMed, KEGG). GraphQL as complementary layer enables flexible queries over knowledge graph without REST endpoint proliferation. |
| **LangGraph over LangChain** | LangGraph enables orchestration of cyclic flows with state — essential when Pathway 1 finds insufficient literature and must activate genomic inference as fallback. State graphs allow conditional branches with complete traceability. |
| **Qdrant over Pinecone/Weaviate** | Qdrant is open-source with native payload filtering (filter by geographic region, evidence level), supports dense + sparse embeddings (hybrid search), and allows self-hosting for research data sovereignty. |
| **Neo4j for Knowledge Graph** | Plant→compound→pathway→enzyme→gene relationships are inherently graphs. Neo4j with GDS (Graph Data Science) enables centrality algorithms, community detection, and shortest paths for molecular similarity inference. |
| **PostgreSQL + PostGIS** | PostGIS enables native geospatial queries to filter plants by Mexican region, biome, altitude. Combined with CONABIO data enables hyperlocal recommendations. |

---

## Three Intelligent Pathways

### Pathway 1: Image → Plant

**Flow**: CV identifies species → compounds → properties → dosage → contraindications → citations

**Pipeline Steps**:

1. **Preprocessing**: Resize, normalization, orientation correction, quality detection (blur, exposure). If quality < threshold → request new image.

2. **Primary Identification — Pl@ntNet API**: Free API with >40k species. Returns top-K candidates with probability. Advantage: trained on iNaturalist + European herbaria. Limitation: coverage of Mexican endemics may be low.

3. **Complementary Model — Custom Fine-tuned**: EfficientNet-V2 or ConvNeXt-V2 fine-tuned with Mexican herbarium dataset (MEXU-UNAM, CONABIO). Training data: geo-tagged images from iNaturalist filtered by Mexico + digitized herbaria. This covers the endemic gap.

4. **Ensemble Decision**: Weighted voting between Pl@ntNet + custom model. If both agree with >80% → high confidence. If they diverge → present both candidates with individual confidence.

5. **Phytochemical Enrichment**: Identified species → query KNApSAcK, PubChem, ChEBI for known active compounds. Cross-reference with ethnobotanical database (BDMTM-UNAM, Biblioteca Digital de la Medicina Tradicional Mexicana).

6. **Literature Retrieval**: PubMed E-utilities API: search by scientific name + 'medicinal' OR 'phytochemical' OR 'pharmacological'. Semantic Scholar API as complement for semantic embeddings of papers.

7. **Genomic Fallback**: If literature insufficient → activate Genomic Inference Engine (see dedicated section). Estimate probability of bioactive compounds by pathway similarity.

8. **Response Composition**: LLM (Claude API via RAG) generates structured response with: properties, compounds, preparation, dosage, contraindications, toxicology. Each claim linked to source with evidence level.

**API Comparison**:

| API / Model | Species | Mexican Endemics | Cost | Accuracy | Decision |
|-------------|---------|------------------|------|----------|----------|
| **Pl@ntNet** | ~45,000 | Medium | Free (500/day) | ~85% top-5 | **Primary** |
| Google Cloud Vision | Broad | Low | $1.50/1000 | ~70% plants | Discarded |
| iNaturalist CV | ~76,000 | High | Internal use | ~90% top-5 | Training dataset |
| **Custom ConvNeXt-V2** | ~5,000 MX | Very High | GPU training | Target 92% | **Complementary** |
| Plant.id | ~33,000 | Low | $0.10/query | ~82% | Backup |

**Decision**: Ensemble Pl@ntNet + Custom Model. Pl@ntNet covers global coverage, custom model closes the gap for Mexican endemics. iNaturalist Research-Grade as training data source.

---

### Pathway 2: Symptoms → Plants

**Flow**: NLP extracts entities → ICD/MeSH mapping → regional filter → evidence-ranked results

**Pipeline Steps**:

1. **Medical Entity Extraction (NER)**: Model: SapBERT fine-tuned on Spanish medical corpus (e.g., PharmaCoNER + custom corpus). Extracts symptoms, conditions, body parts, severity. Fallback: SpaCy + curated medical dictionary.

2. **Mapping to Medical Ontologies**: Extracted entities → mapping to: ICD-11 (diagnoses), MeSH (PubMed descriptors), SNOMED-CT (clinical terminology), UMLS (unified). Use MetaMap Lite or QuickUMLS for linking. This enables standardized queries to PubMed and phytochemical databases.

3. **Geospatial Localization**: User GPS or manual state/municipality selection. PostGIS filters plants with distribution in that region. Sources: CONABIO SNIBer (collection records), GlobalBiodiversityInformationFacility (GBIF), NaturaLista (iNaturalist Mexico).

4. **Multi-Database Query**: For each mapped condition → search in: BDMTM (Biblioteca Digital Medicina Tradicional Mexicana), NAPRALERT, Dr. Duke's Phytochemical DB, PubMed (plant name + condition). Return candidate plants with evidence level.

5. **Evidence-Weighted Ranking**: Score = Σ(w_level × relevance × source_consistency). Level 1 (literature): w=1.0, Level 2 (phytochemical DB): w=0.7, Level 3 (ethnobotany): w=0.4, Level 4 (inference): w=0.2. Plants ranked by composite score.

6. **Safety Verification**: Each candidate plant passes check for: known toxicity, pharmacological interactions, contraindications (pregnancy, lactation, allergies). Source: Natural Medicines Comprehensive Database interaction base.

7. **Fallback: Molecular Similarity Inference**: If evidence < threshold → identify known active compounds against condition → search plants with molecularly similar compounds (Tanimoto > 0.7) via RDKit fingerprints.

**Medical Ontologies Integrated**:

| Ontology | Purpose | Integration | Spanish Coverage |
|----------|---------|-------------|------------------|
| **ICD-11** | Diagnostic classification | WHO REST API | Complete |
| **MeSH** | PubMed descriptors | NCBI E-utilities | Partial |
| SNOMED-CT | Clinical terminology | FHIR Terminology Server | Complete |
| UMLS | Ontology unification | MetaMap / QuickUMLS | Partial |
| HPO | Human phenotype | HPO API | In progress |

---

### Pathway 3: Drug → Plants

**Flow**: Given medication or active compound, find plants containing that compound or biosynthetic analogs

**Pipeline Steps**:

1. **Compound Resolution**: Input (e.g., 'ibuprofen') → resolve to: PubChem CID, SMILES, InChIKey, molecular formula. APIs: PubChem PUG REST, ChEBI, DrugBank. If input is brand name → map to active ingredient via DrugBank or RxNorm.

2. **Direct Search in Phytochemical DBs**: Search exact compound in: KNApSAcK (compound→plant), Dr. Duke's (compound→plant→activity), FooDB, NAPRALERT. If found → return plants with evidence level 2.

3. **Structural Analog Search**: If no exact match → RDKit generates molecular fingerprint (Morgan/ECFP4). Calculate Tanimoto similarity against library of ~50,000 known phytochemicals. Threshold: Tanimoto ≥ 0.7 for 'probable analog'. Return plants containing those analogs.

4. **Biosynthetic Pathway Inference**: Map target compound to KEGG pathway. Identify key enzymes of pathway. Search homologs of those enzymes in Mexican plant genomes (BLAST). If enzymes present → plant can produce compounds in that metabolic route.

5. **Secondary Metabolite Cluster Analysis**: Using antiSMASH, identify biosynthetic gene clusters in available genomes. Predict capacity to produce compound classes (terpenoids, alkaloids, flavonoids, etc.).

6. **Composite Confidence Scoring**: Final score = f(direct_match, tanimoto_similarity, enzyme_homology, pathway_presence, literature_evidence). Each component with weight and justification. Result classified as: Confirmed / Probable / Inferred / Speculative.

---

## Genomic Inference Engine

### Purpose

This engine activates as **fallback** when literature and database evidence is insufficient. Functions as a semi-automated bioinformatics assistant.

### Workflow

```
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
```

### Tools & Technologies

| Tool | Technology | Description |
|------|------------|-------------|
| **BLAST / FASTA** | NCBI BLAST+ CLI, Biopython | Sequence alignment to identify homologous enzymes. E-value < 1e-30 + identity > 40% = probable homolog. |
| **KEGG Pathway** | KEGG REST API, KEGGTools | Map compound → pathway → enzymes (EC numbers). Verify presence of each enzyme in target organism. |
| **antiSMASH** | antiSMASH 7.0 API/CLI | Prediction of biosynthetic gene clusters. Detects capacity to produce terpenoids, alkaloids, polyketides, etc. |
| **HMMER / Pfam** | HMMER3, Pfam DB | Search for conserved protein domains. More sensitive than BLAST for detecting distant homology. |

### Genomic Data Sources

| Database | Content | Access | System Usage |
|----------|---------|--------|--------------|
| **NCBI GenBank** | Nucleotide/protein sequences | E-utilities API | BLAST queries |
| **Ensembl Plants** | Complete plant genomes | REST API | Reference genomes |
| **KEGG** | Metabolic pathways | REST API | Compound→pathway mapping |
| UniProt | Curated proteomes | REST API | Enzyme annotation |
| PhytoMine / Phytozome | Comparative plant genomics | InterMine API | Homolog search |
| MIBiG | Biosynthetic clusters | REST API | BGC reference |
| PlantCyc | Plant pathways | Flatfiles | Metabolic pathways |

---

## Tech Stack

### Frontend
- **Next.js 14** (App Router, RSC)
- **React 18** + TypeScript
- **TailwindCSS** + shadcn/ui
- **React Query** (cache + sync)
- **Mapbox GL** (geospatial visualization)

**Why**: RSC for SEO and fast result loading. TypeScript for strict typing in scientific interfaces.

### Backend / API
- **FastAPI** (Python 3.12)
- **Strawberry GraphQL**
- **Celery + Redis** (async tasks)
- **Pydantic v2** (validation)
- **gRPC** (internal services)

**Why**: FastAPI is standard for ML APIs. Celery for long-running BLAST jobs. Pydantic ensures scientific data integrity.

### LLM / Agents
- **Claude API** (Sonnet 4)
- **LangGraph** (orchestration)
- **LangSmith** (observability)
- **Custom RAG pipeline**
- **Guardrails AI** (anti-hallucination)

**Why**: Claude as primary LLM for scientific reasoning capability. LangGraph for conditional flows with state. Guardrails for factual verification.

### Databases
- **PostgreSQL 16** + PostGIS
- **Qdrant** (vector DB)
- **Neo4j** (knowledge graph)
- **Redis** (cache + message broker)
- **MinIO** (object storage for images)

**Why**: PostgreSQL as relational source-of-truth. Qdrant for semantic search. Neo4j for molecular relationships. MinIO for plant images.

### ML / Vision
- **PyTorch 2.x**
- **Hugging Face Transformers**
- **ConvNeXt-V2** (custom CV)
- **SapBERT** (medical NER)
- **RDKit** (cheminformatics)

**Why**: PyTorch for custom training. HF for pre-trained NER. RDKit is gold standard for molecular fingerprints and similarity.

### Bioinformatics
- **Biopython 1.83**
- **NCBI BLAST+ 2.15**
- **HMMER 3.4**
- **antiSMASH 7.0**
- **Open Babel** (molecular conversion)

**Why**: Standard bioinformatics stack. Local BLAST+ for predictable latency. antiSMASH for biosynthetic cluster prediction.

### Infrastructure
- **Kubernetes** (GKE/EKS)
- **Terraform** (IaC)
- **GitHub Actions** (CI/CD)
- **Prometheus + Grafana**
- **OpenTelemetry** (tracing)

**Why**: K8s to scale inference services. Terraform for reproducibility. OTEL for tracing complex pipelines.

### Data Pipelines
- **Apache Airflow 2.x**
- **dbt** (transformation)
- **Great Expectations** (quality)
- **Scrapy** (web scraping)
- **Delta Lake** (versioning)

**Why**: Airflow orchestrates ingestion from NCBI, PubMed, KEGG. dbt transforms raw data. Great Expectations validates scientific data quality.

---

## APIs & Data Sources

### External APIs Catalog

| Source | Type | Data | Access | Rate Limit | Role |
|--------|------|------|--------|------------|------|
| **Pl@ntNet** | API REST | Plant ID by image | Free (500/day) | 500/day | Primary identification |
| **NCBI E-utilities** | API REST | GenBank, PubMed, Taxonomy | Free (API key) | 10/sec | BLAST, literature, taxonomy |
| **PubChem PUG REST** | API REST | Chemical compounds, SMILES | Free | 5/sec | Compound resolution |
| **KEGG REST** | API REST | Pathways, enzymes, compounds | Free (academic) | 10/sec | Metabolic mapping |
| **ChEBI** | API + OLS | Chemical entity ontology | Free | No limit | Compound classification |
| **KNApSAcK** | Web + dump | Compound↔Plant (51K+) | Free | Scraping/dump | Phytochemical matching |
| **UniProt** | API REST | Proteomes, functional annotation | Free | No limit | Enzyme annotation |
| **Ensembl Plants** | REST API | Plant genomes | Free | 15/sec | Reference genomes |
| **GBIF** | API REST | Species distribution | Free | 3/sec | Species geolocation |
| **CONABIO SNIB** | WMS/WFS | Mexican biodiversity | Free | Variable | Regional distribution MX |
| **Semantic Scholar** | API REST | Academic papers | Free (API key) | 100/5min | Semantic paper search |
| **CrossRef** | API REST | DOI metadata | Free | 50/sec (courtesy) | Citation verification |
| **DrugBank** | API REST | Drug interactions | Academic | Variable | Drug matching, interactions |
| **ICD-11 API (WHO)** | API REST | Diagnostic classification | Free | No limit | Diagnostic mapping |

### Mexican Ethnobotanical Sources

| Name | Full Name | Description | Access |
|------|-----------|-------------|--------|
| **BDMTM** | Biblioteca Digital de la Medicina Tradicional Mexicana (UNAM) | Most complete source on traditional use of medicinal plants in Mexico. Detailed monographs by species. | Web (structured scraping) |
| **Herbario MEXU** | Herbario Nacional de México (UNAM) | Largest herbarium in Latin America. >1.8M specimens. Collection data with georeference. | Database + digitization |
| **NAPRALERT** | Natural Products Alert (UIC) | Database of biological activity of natural products. Compound↔activity↔organism relationships. | Academic subscription |
| **Atlas de Plantas Medicinales** | Atlas de las Plantas de la Medicina Tradicional Mexicana | Compilation of traditional use with geographic information by region. >3,000 documented species. | Publication + digitization |

---

## Confidence Scoring System

### Algorithm

Each system recommendation includes a **composite confidence score**. The algorithm combines multiple signals with calibrated weights:

```
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
```

### Anti-Hallucination & Scientific Validation

1. **Guardrails AI Integration**: Custom validators: each LLM claim verified against vector knowledge base. If claim has no close embedding (cosine < 0.7) → marked as unverified or removed.

2. **Citation Grounding**: Every medical claim must have at least one traceable citation. System rejects LLM outputs containing claims without source.

3. **Contradiction Detection**: Contradiction detection pipeline: if source A says 'safe' and source B says 'toxic', system presents both perspectives with quality metadata.

4. **Toxicity Red Flags**: Database of plants with known toxicity (LD50, hepatotoxicity, nephrotoxicity). Any plant with toxicity flag generates prominent warning regardless of score.

5. **Human-in-the-Loop**: For scores < 40 (speculative), system suggests expert validation. Includes feedback mechanism for researchers to correct or validate inferences.

---

## Database Strategy

### Overview

The platform uses a **hybrid database strategy** with domain-separated PostgreSQL instances, Redis for caching/sessions, and Elasticsearch for full-text search.

### Why Separate Databases?

1. **Independent scaling** - Each domain can scale independently based on load
2. **Fault isolation** - A problem in the chatbot DB doesn't affect plant data
3. **Security boundaries** - Auth data is physically separated from application data
4. **Optimized configuration** - Each DB can be tuned for its specific workload

### Database Instances

#### postgres-core (Port 5432)
**Owner:** Plant Service  
**Contains:** Core domain data
- `taxonomic_families` / `taxonomic_genera` - Taxonomy hierarchy
- `plants` / `plant_versions` / `plant_names` - Plant records with versioning
- `plant_verification_workflow` - Verification audit trail
- `chemical_compounds` / `plant_compounds` - Chemical data
- `medicinal_activities` / `plant_activities` - Medicinal uses
- `scientific_articles` + association tables - Literature references
- `genomic_sequences` / `blast_alignments` - Genomic data
- `data_sources` / `api_cache` - External data management
- `probability_weight_schemas` - Analytics weights

#### postgres-auth (Port 5434)
**Owner:** Auth Service  
**Contains:** Authentication & authorization
- `users` - User accounts with profile data
- `roles` / `permissions` / `role_permissions` - RBAC system
- `user_roles` - User-role assignments with temporal validity
- `user_sessions` - Session tracking (coordinated with Redis)

#### postgres-chatbot (Port 5436)
**Owner:** Chatbot Service  
**Contains:** Conversation data
- `conversations` / `messages` - Chat history
- `chatbot_knowledge_documents` - RAG knowledge base
- `chatbot_quick_replies` - Predefined responses
- `conversation_context` - Multi-turn context
- `chatbot_feedback` - User feedback on responses
- `intent_classification_log` - NLU analytics
- `conversation_flow_patterns` - Flow analytics

#### postgres-user (Port 5435)
**Owner:** User Service  
**Contains:** User interaction data
- `user_search_history` / `user_plant_views` - Browsing history
- `user_plant_favorites` - Saved plants
- `user_plant_usage_reports` - User experience reports
- `user_comments` / `comment_votes` - Community content
- `user_effectiveness_reports` / `user_side_effect_reports` - Health reports
- `sponsors` / `sponsored_plants` / `sponsored_compounds` - Sponsorship
- `recommendation_logs` - ML recommendation tracking
- `audit_log` / `data_quality_metrics` - System auditing

### Elasticsearch (Port 9200)

Used by the Search Service for:
- Full-text search across plants, compounds, and activities
- Autocomplete/suggest functionality
- Faceted search and filtering
- Relevance-ranked results

### Cross-Service Data Access

Services that need data from another domain use **HTTP API calls** (not direct DB access):
- Chatbot Service -> Plant Service API for plant data
- User Service -> Auth Service API for user verification
- Search Service indexes data from Plant Service events

### Migration Strategy

Each service manages its own migrations using **Alembic**:
```bash
cd services/auth-service && alembic upgrade head
cd services/plant-service && alembic upgrade head
cd services/chatbot-service && alembic upgrade head
cd services/user-service && alembic upgrade head
```

---

## Redis Schema

Redis is partitioned by database number:

| DB | Service | Use Case |
|----|---------|----------|
| 0 | Auth | Sessions, token blacklist, rate limiting |
| 1 | Plants | Plant data cache, search cache, view counters |
| 2 | Chatbot | Conversation context, RAG cache, presence |
| 3 | User | Profile cache, favorites cache, recent views |
| 4 | Search | Search results cache, autocomplete, popular terms |

### DB 0 - Auth Service

**Session Management**:
```
sessions:user:{user_id}          HASH    Full session data (TTL: 24h)
    - session_id: string
    - email: string
    - roles: json_string
    - created_at: timestamp
    - last_activity: timestamp

sessions:token:{session_token}   STRING  Maps token -> user_id (TTL: 24h)
sessions:active:{user_id}        SET     Set of active session tokens
```

**Rate Limiting**:
```
ratelimit:login:{ip_address}     SORTED_SET  Sliding window rate limit (TTL: 60s)
ratelimit:register:{ip_address}  SORTED_SET  Registration rate limit (TTL: 300s)
```

**Token Blacklist**:
```
blacklist:token:{jti}            STRING  Blacklisted JWT (TTL: matches token expiry)
```

### DB 1 - Plant Service

**Plant Data Cache**:
```
cache:plant:{plant_id}           STRING  JSON-serialized plant data (TTL: 1h)
cache:plant:list:{page}:{size}   STRING  Paginated plant list (TTL: 5m)
cache:compound:{compound_id}     STRING  JSON-serialized compound data (TTL: 1h)
```

**Search Cache**:
```
cache:search:{query_hash}        STRING  Cached search results (TTL: 5m)
```

**Counters** (async update to DB):
```
counter:plant:views:{plant_id}   STRING  View count buffer (flushed periodically)
```

### DB 2 - Chatbot Service

**Conversation Context**:
```
conv:user:{user_id}:active       SORTED_SET  Active conversations sorted by last activity
conv:{conversation_id}:context   HASH        Current conversation context
    - intent: string
    - entities: json_string
    - turn_count: int
    - last_plant_id: string
conv:{conversation_id}:history   LIST        Recent message IDs (max 50)
```

**RAG Cache**:
```
cache:rag:{query_hash}           STRING  Cached RAG retrieval results (TTL: 30m)
```

**Rate Limiting**:
```
ratelimit:chatbot:{user_id}      STRING  Chatbot rate limit counter (TTL: 60s)
```

**User Presence**:
```
presence:user:{user_id}          STRING  "online" (TTL: 5m, refreshed on activity)
presence:online_count             STRING  Total online users
```

### DB 3 - User Service

**User Preferences Cache**:
```
cache:user:profile:{user_id}     STRING  JSON user profile (TTL: 15m)
cache:user:favorites:{user_id}   STRING  JSON favorites list (TTL: 5m)
```

**Recently Viewed**:
```
user:recent:{user_id}            LIST   Recently viewed plant IDs (max 50)
```

### DB 4 - Search Service

**Search Results Cache**:
```
cache:search:results:{query_hash}     STRING  Full search results (TTL: 5m)
cache:search:facets:{query_hash}      STRING  Facet/filter counts (TTL: 10m)
```

**Autocomplete**:
```
autocomplete:plants              SORTED_SET  Plant names for autocomplete
autocomplete:compounds           SORTED_SET  Compound names for autocomplete
```

**Popular Searches**:
```
popular:searches:daily           SORTED_SET  Daily search term frequency
popular:searches:weekly          SORTED_SET  Weekly search term frequency
```

### Key Naming Conventions

- Use colons `:` as separators
- Use lowercase for all key names
- Include the entity type after the namespace
- Include the ID as the last segment
- Always set TTL on cache keys
- Use `cache:` prefix for cacheable data
- Use `ratelimit:` prefix for rate limiting keys

---

## Deployment Architecture

```
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
```

### Monthly Cost Estimation (Production)

| Service | Specification | Cost/month (USD) |
|---------|---------------|------------------|
| GKE / EKS Cluster | 3 nodes e2-standard-4 + 1 GPU L4 | $800-1,200 |
| PostgreSQL (Cloud SQL) | 4 vCPU, 16GB RAM, 500GB SSD | $200-350 |
| Qdrant Cloud | 3-node cluster, 50GB | $150-300 |
| Neo4j Aura | Professional, 8GB RAM | $200-400 |
| Redis (Memorystore) | Standard, 5GB | $50-80 |
| MinIO / Cloud Storage | 500GB images + backups | $30-50 |
| Claude API | ~200K requests/month | $300-600 |
| Vercel (Frontend) | Pro plan | $20 |
| Monitoring (Grafana Cloud) | Pro plan | $50 |
| **Total estimated** | | **$1,800 - $3,050** |

**Note**: Costs significantly reducible with spot instances for BLAST jobs and aggressive caching of external API results.

---

## Development Roadmap

### Fase 1 — Fundación (Meses 1-3)
- Infrastructure base: PostgreSQL + PostGIS, Qdrant, Redis
- Initial ingestion: KNApSAcK, BDMTM, GBIF México (Airflow pipelines)
- Core API: FastAPI with basic query endpoints
- Knowledge Graph v1: Neo4j with plant→compound→activity relationships
- RAG pipeline v1: embeddings of ethnobotanical monographs in Qdrant
- Frontend: Next.js scaffold with the 3 input pathways

### Fase 2 — Inteligencia Visual (Meses 4-6)
- Pl@ntNet API integration
- Training dataset: scraping iNaturalist Research-Grade (México)
- Fine-tuning ConvNeXt-V2 for Mexican endemics
- Decision ensemble (Pl@ntNet + custom)
- Post-identification phytochemical enrichment pipeline
- PubMed/Semantic Scholar literature search

### Fase 3 — NLP Médico & Geoespacial (Meses 7-9)
- Medical NER: fine-tune SapBERT for symptoms in Spanish
- Ontology integration: ICD-11, MeSH, QuickUMLS
- Geospatial engine: PostGIS + CONABIO + GBIF for regional filter
- Evidence scoring v1
- Pathway 2 functional end-to-end
- Map visualization with distribution of recommended plants

### Fase 4 — Motor Genómico (Meses 10-14)
- BLAST+ local setup with Mexican plant genomes
- KEGG pathway mapper integration
- RDKit pipeline for molecular similarity (fingerprints, Tanimoto)
- antiSMASH integration for BGC prediction
- Composite confidence scoring v2
- Pathway 3 (Drug matching) functional end-to-end
- Genomic fallback activated for Pathways 1 and 2

### Fase 5 — Refinamiento & Publicación (Meses 15-18)
- Validation with expert panel (ethnobotanists, pharmacologists)
- Confidence score calibration with real data
- Documentation for research reproducibility
- Academic paper: methodology + validation
- Public API for researchers
- Coverage expansion: Central America, Caribbean

### Risk Analysis

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Low coverage of endemics in CV APIs | High | High | Custom model + ensemble |
| NCBI/KEGG rate limits | Medium | Medium | Aggressive cache + nightly batch processing |
| Unstructured ethnobotanical data | High | High | Scraping pipeline + NER + manual validation |
| Incomplete genomes of Mexican plants | High | Medium | Transcriptomics as alternative + inference by close taxon |
| LLM hallucinations | Critical | Medium | Guardrails + citation grounding + human-in-the-loop |
| Medical liability | Critical | Low | Prominent disclaimers + does not replace medical advice |
| GPU costs for BLAST/CV | Medium | Medium | Spot instances + caching + batch processing |

---

## Ethical Disclaimer

⚠️ **This system is NOT a substitute for professional medical advice.** All recommendations are informational and educational. Genomic inference results are probabilistic and require experimental validation. Medicinal plant preparations may have interactions with medications and adverse effects. Always consult a healthcare professional before using medicinal plants for therapeutic purposes.

---

## Document Version

**Version**: 1.0  
**Last Updated**: 2024  
**Purpose**: Complete architectural and technical context for PhytoMX Intelligence Platform

---

*This document should be referenced when working on any component of the PhytoMX system to ensure architectural consistency and understanding of the complete system design.*



