-- Analytics Functions
-- Sistema Inteligente de Análisis de Plantas Medicinales de México

-- Function to calculate plant popularity score
CREATE OR REPLACE FUNCTION calculate_plant_popularity(p_plant_id UUID)
RETURNS NUMERIC AS $$
DECLARE
    v_score NUMERIC;
BEGIN
    SELECT
        (COALESCE(view_count, 0) * 0.1 +
         COALESCE(favorite_count, 0) * 0.3 +
         COALESCE(usage_report_count, 0) * 0.4 +
         COALESCE(comment_count, 0) * 0.2)
    INTO v_score
    FROM plants
    WHERE id = p_plant_id;

    RETURN COALESCE(v_score, 0);
END;
$$ LANGUAGE plpgsql;

-- Function to get top plants by region
CREATE OR REPLACE FUNCTION get_top_plants_by_state(
    p_state VARCHAR,
    p_limit INTEGER DEFAULT 10
)
RETURNS TABLE (
    plant_id UUID,
    scientific_name VARCHAR,
    popularity_score NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        p.id,
        p.scientific_name,
        calculate_plant_popularity(p.id) as popularity_score
    FROM plants p
    WHERE p.mexican_states @> jsonb_build_array(p_state)
      AND p.is_published = TRUE
      AND p.deleted_at IS NULL
    ORDER BY popularity_score DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Function to get compound usage statistics
CREATE OR REPLACE FUNCTION get_compound_statistics(p_compound_id UUID)
RETURNS JSONB AS $$
DECLARE
    v_result JSONB;
BEGIN
    SELECT jsonb_build_object(
        'plant_count', COUNT(DISTINCT pc.plant_id),
        'activity_count', COUNT(DISTINCT pa.id),
        'article_count', COUNT(DISTINCT aca.article_id)
    )
    INTO v_result
    FROM chemical_compounds cc
    LEFT JOIN plant_compounds pc ON pc.compound_id = cc.id
    LEFT JOIN plant_activities pa ON pa.plant_id = pc.plant_id
    LEFT JOIN article_compound_associations aca ON aca.compound_id = cc.id
    WHERE cc.id = p_compound_id;

    RETURN COALESCE(v_result, '{}'::jsonb);
END;
$$ LANGUAGE plpgsql;
