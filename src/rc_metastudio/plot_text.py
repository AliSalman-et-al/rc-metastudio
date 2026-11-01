"""Lossless plot text and automatic-heading placeholders."""

# These values are emitted by the generated Qt forms for an untouched plot
# option.  Keep the list at the presentation boundary so renderers receive a
# real unset value rather than having to know about a GUI placeholder.
PLOT_DEFAULT_TEXT_SENTINELS = frozenset(
    ("", "[default]", "<default>", "(default)", "default")
)


def configure_plot_text_inputs(surface):
    """Configure plot-only labels without constraining investigator text."""
    for name in (
        "col1_str_edit",
        "col2_str_edit",
        "col3_str_edit",
        "col4_str_edit",
        "x_lbl_le",
    ):
        widget = getattr(surface, name, None)
        if widget is None:
            continue
        widget.setProperty("plotTextWasEdited", False)
        widget.setToolTip("Automatic headings preserve the complete group name; long headings wrap in the figure.")
        if widget.text() == "[default]":
            set_plot_text_value(widget, "[default]")
        widget.textEdited.connect(
            lambda _text, w=widget: w.setProperty("plotTextWasEdited", True)
        )


def set_plot_text_value(widget, value):
    """Load complete generated or saved text."""
    text = str(value)
    if text == "[default]":
        text = ""
        widget.setPlaceholderText("Automatic")
        widget.setToolTip(widget.toolTip() + " Automatic: determined by the plotted data.")
    widget.setProperty("plotTextWasEdited", False)
    widget.setText(text)


def plot_text_value(widget):
    """Return the complete label or its automatic placeholder."""
    return widget.text() or ("[default]" if widget.placeholderText() == "Automatic" else "")


def normalize_plot_text_value(value, *, was_edited=False):
    """Convert an untouched GUI default placeholder to an unset value.

    A researcher may deliberately use one of these strings as a label.  Such
    an edited value is therefore retained; only an untouched form default is
    normalized.  The pure value-level helper is also useful to non-Qt callers
    that already know whether a value came from an edited control.
    """
    if value is None:
        return None
    text = str(value)
    if not was_edited and text.strip().casefold() in PLOT_DEFAULT_TEXT_SENTINELS:
        return None
    return value


def plot_parameter_text_value(widget):
    """Return a plot text control's value with default placeholders unset."""
    return normalize_plot_text_value(
        plot_text_value(widget),
        was_edited=bool(widget.property("plotTextWasEdited")),
    )


def size_plot_text_editor(surface):
    """Give heading fields the spare width in the screen-bounded editor."""
    from PyQt6.QtWidgets import QGridLayout, QLineEdit, QSizePolicy
    from rc_metastudio import adaptive_window

    widest = 0
    for field in surface.findChildren(QLineEdit):
        field.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        widest = max(widest, field.fontMetrics().horizontalAdvance(field.text() or field.placeholderText()))
        layout = field.parentWidget().layout()
        if isinstance(layout, QGridLayout):
            index = layout.indexOf(field)
            if index >= 0:
                _, column, _, _ = layout.getItemPosition(index)
                layout.setColumnStretch(column, 1)
    adaptive_window.set_content_preferred_width(surface, 360, max(680, widest + 240))
