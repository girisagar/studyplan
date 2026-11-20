import nh3


def sanitize_note_html(value):
    """Keep the formatting supported by the shared description editor."""
    return nh3.clean(
        value,
        tags={
            "p",
            "br",
            "h2",
            "h3",
            "h4",
            "strong",
            "b",
            "em",
            "i",
            "a",
            "ul",
            "ol",
            "li",
            "blockquote",
            "pre",
            "code",
        },
        attributes={"a": {"href", "title"}, "code": {"class"}},
        url_schemes={"http", "https", "mailto"},
    )


# Formatting the shared CKEditor 5 description editor can produce (headings,
# lists, links, code, tables, images). Scripts, event handlers, iframes and
# unknown attributes are dropped; inline styles keep only layout-safe properties.
DESCRIPTION_TAGS = {
    "p",
    "br",
    "hr",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "strong",
    "b",
    "em",
    "i",
    "u",
    "s",
    "sub",
    "sup",
    "mark",
    "small",
    "span",
    "a",
    "ul",
    "ol",
    "li",
    "blockquote",
    "pre",
    "code",
    "table",
    "thead",
    "tbody",
    "tfoot",
    "tr",
    "th",
    "td",
    "caption",
    "colgroup",
    "col",
    "figure",
    "figcaption",
    "img",
}
DESCRIPTION_ATTRIBUTES = {
    "a": {"href", "title"},
    "img": {"src", "alt", "width", "height"},
    "td": {"colspan", "rowspan"},
    "th": {"colspan", "rowspan", "scope"},
    "code": {"class"},
    "figure": {"class"},
    "ol": {"start", "reversed"},
    "*": {"style"},
}
DESCRIPTION_STYLES = {
    "text-align",
    "margin-left",
    "padding",
    "padding-left",
    "list-style-type",
    "width",
}


def sanitize_description_html(value):
    """Sanitize staff-authored rich text (course/chapter/topic/roadmap descriptions)."""
    return nh3.clean(
        value or "",
        tags=DESCRIPTION_TAGS,
        attributes=DESCRIPTION_ATTRIBUTES,
        filter_style_properties=DESCRIPTION_STYLES,
        url_schemes={"http", "https", "mailto"},
        link_rel="noopener noreferrer",
    )
