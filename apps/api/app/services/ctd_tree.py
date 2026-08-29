"""Build nested CTD section tree from flat ORM rows."""

from app.models.ctd_section import CtdSection
from app.schemas.ctd_section import CtdSectionNode


def build_ctd_tree(sections: list[CtdSection]) -> list[CtdSectionNode]:
    nodes: dict[int, CtdSectionNode] = {}
    roots: list[CtdSectionNode] = []

    for section in sections:
        nodes[section.id] = CtdSectionNode(
            code=section.code,
            title=section.title,
            sort_order=section.sort_order,
            children=[],
        )

    for section in sections:
        node = nodes[section.id]
        if section.parent_id is None:
            roots.append(node)
        else:
            nodes[section.parent_id].children.append(node)

    for node in nodes.values():
        node.children.sort(key=lambda n: n.sort_order)

    roots.sort(key=lambda n: n.sort_order)
    return roots
