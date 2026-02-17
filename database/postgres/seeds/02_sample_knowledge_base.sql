-- Sample Knowledge Base for Chatbot RAG
-- These are example entries for the chatbot's knowledge base

INSERT INTO chatbot_knowledge_documents (
    title, content, document_type, category, language, is_active
) VALUES
(
    'Introducción a Plantas Medicinales Mexicanas',
    'México posee una de las floras medicinales más ricas del mundo, con más de 4,000 especies de plantas utilizadas con fines terapéuticos. La medicina tradicional mexicana tiene raíces prehispánicas que se han transmitido de generación en generación.',
    'KNOWLEDGE_BASE',
    'general',
    'es',
    TRUE
),
(
    'Uso Seguro de Plantas Medicinales',
    'ADVERTENCIA: Las plantas medicinales pueden interactuar con medicamentos farmacéuticos. Siempre consulte a un profesional de salud antes de utilizar plantas medicinales, especialmente si está embarazada, amamantando o tomando medicamentos. Esta plataforma proporciona información educativa y no sustituye el consejo médico profesional.',
    'SAFETY_NOTICE',
    'safety',
    'es',
    TRUE
),
(
    'Sobre la Verificación Científica',
    'Los datos en esta plataforma son verificados por investigadores calificados. Cada planta tiene un nivel de verificación que indica la calidad de la evidencia científica disponible. Los niveles van desde "No verificado" hasta "Verificado por expertos".',
    'KNOWLEDGE_BASE',
    'verification',
    'es',
    TRUE
);
