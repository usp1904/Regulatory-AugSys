"""CTD Module 3.2.S Drug Substance taxonomy seed rows.

Each row: code, title, parent_code (None for root), sort_order among siblings.
"""

from typing import TypedDict


class CtdSeedRow(TypedDict):
    code: str
    title: str
    parent_code: str | None
    sort_order: int


CTD_MODULE_32S_SEED: list[CtdSeedRow] = [
    {"code": "3.2.S", "title": "Drug Substance", "parent_code": None, "sort_order": 1},
    {"code": "3.2.S.1", "title": "General Information", "parent_code": "3.2.S", "sort_order": 1},
    {"code": "3.2.S.1.1", "title": "Nomenclature", "parent_code": "3.2.S.1", "sort_order": 1},
    {"code": "3.2.S.1.2", "title": "Structure", "parent_code": "3.2.S.1", "sort_order": 2},
    {"code": "3.2.S.1.3", "title": "General Properties", "parent_code": "3.2.S.1", "sort_order": 3},
    {"code": "3.2.S.2", "title": "Manufacture", "parent_code": "3.2.S", "sort_order": 2},
    {"code": "3.2.S.2.1", "title": "Manufacturer(s)", "parent_code": "3.2.S.2", "sort_order": 1},
    {
        "code": "3.2.S.2.2",
        "title": "Description of Manufacturing Process and Process Controls",
        "parent_code": "3.2.S.2",
        "sort_order": 2,
    },
    {
        "code": "3.2.S.2.3",
        "title": "Control of Materials",
        "parent_code": "3.2.S.2",
        "sort_order": 3,
    },
    {
        "code": "3.2.S.2.4",
        "title": "Controls of Critical Steps and Intermediates",
        "parent_code": "3.2.S.2",
        "sort_order": 4,
    },
    {
        "code": "3.2.S.2.5",
        "title": "Process Validation and/or Evaluation",
        "parent_code": "3.2.S.2",
        "sort_order": 5,
    },
    {
        "code": "3.2.S.2.6",
        "title": "Manufacturing Process Development",
        "parent_code": "3.2.S.2",
        "sort_order": 6,
    },
    {"code": "3.2.S.3", "title": "Characterisation", "parent_code": "3.2.S", "sort_order": 3},
    {
        "code": "3.2.S.3.1",
        "title": "Elucidation of Structure and Other Characteristics",
        "parent_code": "3.2.S.3",
        "sort_order": 1,
    },
    {"code": "3.2.S.3.2", "title": "Impurities", "parent_code": "3.2.S.3", "sort_order": 2},
    {
        "code": "3.2.S.4",
        "title": "Control of Drug Substance",
        "parent_code": "3.2.S",
        "sort_order": 4,
    },
    {"code": "3.2.S.4.1", "title": "Specification", "parent_code": "3.2.S.4", "sort_order": 1},
    {
        "code": "3.2.S.4.2",
        "title": "Analytical Procedures",
        "parent_code": "3.2.S.4",
        "sort_order": 2,
    },
    {
        "code": "3.2.S.4.3",
        "title": "Validation of Analytical Procedures",
        "parent_code": "3.2.S.4",
        "sort_order": 3,
    },
    {"code": "3.2.S.4.4", "title": "Batch Analyses", "parent_code": "3.2.S.4", "sort_order": 4},
    {
        "code": "3.2.S.4.5",
        "title": "Justification of Specification",
        "parent_code": "3.2.S.4",
        "sort_order": 5,
    },
    {
        "code": "3.2.S.5",
        "title": "Reference Standards or Materials",
        "parent_code": "3.2.S",
        "sort_order": 5,
    },
    {
        "code": "3.2.S.6",
        "title": "Container Closure System",
        "parent_code": "3.2.S",
        "sort_order": 6,
    },
    {"code": "3.2.S.7", "title": "Stability", "parent_code": "3.2.S", "sort_order": 7},
    {
        "code": "3.2.S.7.1",
        "title": "Stability Summary and Conclusions",
        "parent_code": "3.2.S.7",
        "sort_order": 1,
    },
    {
        "code": "3.2.S.7.2",
        "title": "Post-approval Stability Protocol and Stability Commitment",
        "parent_code": "3.2.S.7",
        "sort_order": 2,
    },
    {"code": "3.2.S.7.3", "title": "Stability Data", "parent_code": "3.2.S.7", "sort_order": 3},
]
