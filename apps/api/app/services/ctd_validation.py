"""CTD Module 3.2.S validation against scoped regulatory keywords."""

from __future__ import annotations

from app.data.ctd_module_32s import CTD_MODULE_32S_SEED
from app.models.document import Document

CTD_SECTION_SIGNALS: dict[str, list[str]] = {
    "3.2.S.1.1": ["nomenclature", "inn", "cas", "chemical name"],
    "3.2.S.1.2": ["structure", "stereochemistry", "molecular formula"],
    "3.2.S.1.3": ["general propert", "physicochemical", "solubility"],
    "3.2.S.2.1": ["manufacturer", "manufacturing site", "facility"],
    "3.2.S.2.2": ["manufacturing process", "process control", "synthesis"],
    "3.2.S.2.3": ["control of material", "raw material", "starting material"],
    "3.2.S.2.4": ["critical step", "intermediate", "in-process"],
    "3.2.S.2.5": ["process validation", "ppq"],
    "3.2.S.2.6": ["process development", "design space"],
    "3.2.S.3.1": ["elucidation", "characterisation", "spectroscop"],
    "3.2.S.3.2": ["impurit", "degradant", "genotoxic"],
    "3.2.S.4.1": ["specification", "acceptance criterion"],
    "3.2.S.4.2": ["analytical procedure", "hplc", "assay method"],
    "3.2.S.4.3": ["method validation", "ich q2", "linearity"],
    "3.2.S.4.4": ["batch analys", "batch result", "coa"],
    "3.2.S.4.5": ["justification of specification"],
    "3.2.S.5": ["reference standard", "reference material"],
    "3.2.S.6": ["container closure", "packaging"],
    "3.2.S.7.1": ["stability summary", "shelf life"],
    "3.2.S.7.2": ["stability protocol", "stability commitment"],
    "3.2.S.7.3": ["stability data", "accelerated", "long-term"],
}

REGULATORY_REFERENCES: list[dict[str, str]] = [
    {
        "regulation": "ICH Q2(R2)",
        "section": "Analytical validation",
        "keywords": "method validation analytical ich q2",
    },
    {
        "regulation": "ICH Q3A",
        "section": "Impurities",
        "keywords": "impurity degradant specification",
    },
    {
        "regulation": "ICH Q6A",
        "section": "Specifications",
        "keywords": "specification acceptance criterion",
    },
    {
        "regulation": "ICH Q7",
        "section": "API GMP",
        "keywords": "manufacturing process validation gmp",
    },
    {
        "regulation": "ICH Q1A",
        "section": "Stability",
        "keywords": "stability data shelf life protocol",
    },
    {
        "regulation": "FDA 21 CFR 211",
        "section": "cGMP",
        "keywords": "manufacture batch release specification",
    },
    {
        "regulation": "EU GMP Annex 15",
        "section": "Qualification",
        "keywords": "validation qualification process",
    },
    {
        "regulation": "ICH Q11",
        "section": "Development",
        "keywords": "process development design space",
    },
]


def section_signals(code: str, title: str) -> list[str]:
    if code in CTD_SECTION_SIGNALS:
        return CTD_SECTION_SIGNALS[code]
    return [w for w in title.lower().split() if len(w) > 3]


def leaf_sections() -> list[dict]:
    parents = {row["parent_code"] for row in CTD_MODULE_32S_SEED if row["parent_code"]}
    return [
        row
        for row in CTD_MODULE_32S_SEED
        if row["code"] != "3.2.S" and row["code"] not in parents
    ]


def filter_regulatory_refs(frameworks: list[str], jurisdictions: list[str]) -> list[dict[str, str]]:
    blob = " ".join(frameworks + jurisdictions).lower()
    if not frameworks and not jurisdictions:
        return REGULATORY_REFERENCES
    hits = []
    for ref in REGULATORY_REFERENCES:
        keywords = ref["keywords"].lower()
        if any(fw.lower() in keywords or keywords in fw.lower() for fw in frameworks):
            hits.append(ref)
        elif any(j.lower() in keywords for j in jurisdictions):
            hits.append(ref)
        elif "fda" in blob and "fda" in ref["regulation"].lower():
            hits.append(ref)
        elif ("eu" in blob or "european" in blob) and "eu" in ref["regulation"].lower():
            hits.append(ref)
        elif "ich" in blob and ref["regulation"].startswith("ICH"):
            hits.append(ref)
    return hits or REGULATORY_REFERENCES


def validate_ctd_documents(
    documents: list[Document],
    frameworks: list[str],
    jurisdictions: list[str],
) -> dict:
    house_blob = "\n".join(doc.full_extracted_text() for doc in documents).lower()
    scoped_refs = filter_regulatory_refs(frameworks, jurisdictions)
    mappings = []
    gaps: list[str] = []

    for section in leaf_sections():
        code = section["code"]
        title = section["title"]
        signals = section_signals(code, title)
        house_docs = [
            doc
            for doc in documents
            if any(sig in (doc.text_excerpt or "").lower() for sig in signals)
        ]
        house_hit = bool(house_docs) or (
            bool(house_blob.strip()) and any(sig in house_blob for sig in signals)
        )
        reg_hits = [
            ref
            for ref in scoped_refs
            if any(sig in ref["keywords"].lower() for sig in signals)
        ]
        if house_hit and reg_hits:
            coverage = "supports-section"
        elif house_hit:
            coverage = "partial"
        elif reg_hits:
            coverage = "placeholder-only"
        else:
            coverage = "gap"

        rationale = (
            f"Section {code} — coverage {coverage} under scope "
            f"{', '.join(frameworks) or 'all frameworks'} / "
            f"{', '.join(jurisdictions) or 'all jurisdictions'}."
        )
        mappings.append(
            {
                "mappingId": f"MAP-{code.replace('.', '')}",
                "ctdModule": "3",
                "ctdSection": code,
                "sectionTitle": title,
                "coverageLevel": coverage,
                "placementRationale": rationale,
                "sourceRefs": {
                    "inHouseDocuments": [
                        {"id": doc.id, "filename": doc.filename, "fileHash": doc.file_hash}
                        for doc in house_docs
                    ],
                    "regulatoryReferences": reg_hits[:4],
                },
            }
        )
        if coverage in {"gap", "partial"}:
            gaps.append(rationale)

    supported = sum(1 for m in mappings if m["coverageLevel"] == "supports-section")
    partial = sum(1 for m in mappings if m["coverageLevel"] == "partial")
    gap_count = sum(1 for m in mappings if m["coverageLevel"] == "gap")

    return {
        "schemaVersion": "maras.ctd-mapping.v1",
        "status": "needs-review",
        "packageStatus": "DRAFT_NOT_CONTROLLED",
        "scope": {
            "frameworks": frameworks,
            "jurisdictions": jurisdictions,
            "regulatoryReferencesInScope": len(scoped_refs),
        },
        "mappings": mappings,
        "gaps": gaps,
        "metrics": {
            "supported": supported,
            "partial": partial,
            "gapCount": gap_count,
            "houseDocCount": len(documents),
        },
    }
