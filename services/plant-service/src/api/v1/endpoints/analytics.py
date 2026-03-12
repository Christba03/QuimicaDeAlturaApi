from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select, text
from src.dependencies import get_db
from src.models.plant import Plant
from src.models.compound import ChemicalCompound
from src.models.ethnobotanical import EthnobotanicalRecord
from src.models.genomic_data import GenomicData
from src.models.drug_reference import DrugReference
from src.models.regional_availability import RegionalAvailability

router = APIRouter()

@router.get("/biodiversity")
async def biodiversity(db: AsyncSession = Depends(get_db)):
    by_region = (await db.execute(
        select(Plant.region, func.count(Plant.id)).group_by(Plant.region)
    )).all()
    by_category = (await db.execute(
        select(Plant.category, func.count(Plant.id)).group_by(Plant.category)
    )).all()
    by_family = (await db.execute(
        select(Plant.family, func.count(Plant.id)).group_by(Plant.family).order_by(func.count(Plant.id).desc()).limit(10)
    )).all()
    return {
        "speciesByRegion": [{"region": r, "count": c} for r, c in by_region],
        "speciesByCategory": [{"category": c, "count": n} for c, n in by_category],
        "topFamilies": [{"family": f, "count": c} for f, c in by_family],
    }

@router.get("/phytochemical")
async def phytochemical(db: AsyncSession = Depends(get_db)):
    by_class = (await db.execute(
        select(ChemicalCompound.compound_class, func.count(ChemicalCompound.id)).group_by(ChemicalCompound.compound_class)
    )).all()
    avg_mw = (await db.execute(select(func.avg(ChemicalCompound.molecular_weight)))).scalar()
    return {
        "compoundClassDistribution": [{"class": c, "count": n} for c, n in by_class],
        "averageMolecularWeight": float(avg_mw) if avg_mw else None,
    }

@router.get("/evidence-quality")
async def evidence_quality(db: AsyncSession = Depends(get_db)):
    by_level = (await db.execute(
        select(EthnobotanicalRecord.evidence_level, func.count(EthnobotanicalRecord.id)).group_by(EthnobotanicalRecord.evidence_level)
    )).all()
    return {"evidenceLevelDistribution": [{"level": str(l), "count": c} for l, c in by_level]}

@router.get("/genomic-tracker")
async def genomic_tracker(db: AsyncSession = Depends(get_db)):
    by_status = (await db.execute(
        select(GenomicData.status, func.count(GenomicData.id)).group_by(GenomicData.status)
    )).all()
    return {"genomicStatusBreakdown": [{"status": str(s), "count": c} for s, c in by_status]}

@router.get("/epidemiology")
async def epidemiology(db: AsyncSession = Depends(get_db)):
    by_condition_region = (await db.execute(
        select(EthnobotanicalRecord.condition_treated, EthnobotanicalRecord.region, func.count(EthnobotanicalRecord.id))
        .group_by(EthnobotanicalRecord.condition_treated, EthnobotanicalRecord.region)
        .order_by(func.count(EthnobotanicalRecord.id).desc())
        .limit(20)
    )).all()
    by_year = (await db.execute(
        select(EthnobotanicalRecord.year, func.count(EthnobotanicalRecord.id))
        .where(EthnobotanicalRecord.year.isnot(None))
        .group_by(EthnobotanicalRecord.year)
        .order_by(EthnobotanicalRecord.year)
    )).all()
    return {
        "conditionsByRegion": [{"condition": c, "region": r, "count": n} for c, r, n in by_condition_region],
        "recordsByYear": [{"year": y, "count": c} for y, c in by_year],
    }

@router.get("/drug-analogs")
async def drug_analogs(db: AsyncSession = Depends(get_db)):
    top = (await db.execute(
        select(DrugReference.drug_name, DrugReference.similarity_score)
        .where(DrugReference.similarity_score.isnot(None))
        .order_by(DrugReference.similarity_score.desc())
        .limit(10)
    )).all()
    avg_sim = (await db.execute(select(func.avg(DrugReference.similarity_score)))).scalar()
    return {
        "topDrugAnalogs": [{"drugName": d, "similarityScore": s} for d, s in top],
        "averageSimilarityScore": float(avg_sim) if avg_sim else None,
    }

@router.get("/research-gaps")
async def research_gaps(db: AsyncSession = Depends(get_db)):
    from src.models.compound import PlantCompound
    # Plants with no compounds
    subq = select(PlantCompound.plant_id).distinct()
    no_compounds = (await db.execute(
        select(Plant.scientific_name, Plant.region).where(Plant.id.not_in(subq)).limit(20)
    )).all()
    # Regions with few records
    by_region = (await db.execute(
        select(RegionalAvailability.region, func.count(RegionalAvailability.id))
        .group_by(RegionalAvailability.region)
        .order_by(func.count(RegionalAvailability.id))
        .limit(10)
    )).all()
    return {
        "plantsWithNoCompounds": [{"scientificName": n, "region": r} for n, r in no_compounds],
        "regionsWithFewRecords": [{"region": r, "count": c} for r, c in by_region],
    }
