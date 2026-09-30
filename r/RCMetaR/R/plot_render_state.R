# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

rcmetar.render.state.atomic <- function(value, label) {
    if (is.null(value)) {
        return(NULL)
    }
    if (!is.atomic(value) || is.object(value) || !is.null(dim(value))) {
        stop(sprintf("Saved plot %s is not plain data.", label), call.=FALSE)
    }
    if (length(value) > 10000) {
        stop(sprintf("Saved plot %s exceeds the renderer limit.", label), call.=FALSE)
    }
    unname(value)
}

rcmetar.render.state.params <- function(params) {
    if (!is.list(params) || is.null(names(params))) {
        stop("Saved forest plot parameters are malformed.", call.=FALSE)
    }
    allowed <- c(
        "measure", "conf.level", "digits", "rm.method", "create.plot",
        "fp_style", "fp_accent_color", "fp_col1_str", "fp_col2_str",
        "fp_col3_str", "fp_col4_str", "fp_plot_lb", "fp_plot_ub",
        "fp_xlabel", "fp_xticks", "fp_point_size_multiplier",
        "fp_show_annotation", "fp_show_col1", "fp_show_col2",
        "fp_show_col3", "fp_show_col4", "fp_show_headers",
        "fp_show_raw_counts", "fp_show_summary_line"
    )
    params <- params[names(params) %in% allowed]
    lapply(names(params), function(name) rcmetar.render.state.atomic(params[[name]], name)) |>
        stats::setNames(names(params))
}

rcmetar.render.state.ilab <- function(ilab, n) {
    if (!is.list(ilab) || !is.matrix(ilab$matrix) || nrow(ilab$matrix) != n) {
        stop("Saved forest plot columns are malformed.", call.=FALSE)
    }
    rows <- if (ncol(ilab$matrix) == 0) {
        replicate(n, character(0), simplify=FALSE)
    } else {
        lapply(seq_len(n), function(index) as.character(ilab$matrix[index, , drop=TRUE]))
    }
    columns <- lapply(ilab$columns, function(column) {
        list(
            key=as.character(column$key)[1],
            group=as.character(column$group)[1],
            header=as.character(column$header)[1],
            values=as.character(column$values)
        )
    })
    list(
        matrix=rows,
        columns=columns,
        headers=as.character(ilab$headers),
        groups=as.character(ilab$groups)
    )
}

rcmetar.project.forest.render.state <- function(bundle, figure.key) {
    if (!rcmetar.is.metafor.forest.bundle(bundle) ||
            !bundle$fp_style %in% c("default", "revman", "bmj") ||
            identical(bundle$forest_variant, "subgroup")) {
        return(NULL)
    }
    res <- bundle$res
    effect <- bundle$effect
    if (!is.null(effect)) {
        effect$vi <- as.numeric(effect$sei)^2
    }
    if (!is.list(effect) || any(vapply(
        c("yi", "vi", "ci.lb", "ci.ub", "slab"),
        function(field) is.null(effect[[field]]),
        logical(1)
    ))) {
        return(NULL)
    }
    n <- length(effect$yi)
    if (n == 0 || any(vapply(
        c("vi", "ci.lb", "ci.ub", "slab"),
        function(field) length(effect[[field]]) != n,
        logical(1)
    ))) {
        return(NULL)
    }
    summary <- list()
    for (field in c("b", "QE", "k", "p", "QEp", "I2", "tau2", "method", "zval", "pval")) {
        value <- if (is.list(res)) res[[field]] else NULL
        if (!is.null(value) && length(value) > 0) {
            summary[[field]] <- rcmetar.render.state.atomic(value[[1]], field)
        }
    }
    summary$ci_lb <- if (is.null(res$ci.lb)) NULL else rcmetar.render.state.atomic(res$ci.lb[[1]], "ci.lb")
    summary$ci_ub <- if (is.null(res$ci.ub)) NULL else rcmetar.render.state.atomic(res$ci.ub[[1]], "ci.ub")
    summary <- summary[!vapply(summary, is.null, logical(1))]
    required.summary <- c("b", "ci_lb", "ci_ub")
    if (!all(required.summary %in% names(summary))) {
        return(NULL)
    }
    if (is.null(bundle$effect_display) || !is.list(bundle$effect_display)) {
        return(NULL)
    }
    displayed <- lapply(c("y.disp", "lb.disp", "ub.disp"), function(field) {
        values <- as.numeric(bundle$effect_display[[field]])
        if (length(values) == n + 1) values[-length(values)] else values
    })
    if (any(lengths(displayed) != n)) {
        return(NULL)
    }
    state <- list(
        version=1L,
        renderer="rcmetar_forest_v1",
        figure_key=as.character(figure.key),
        data_type=as.character(bundle$data_type),
        style=as.character(bundle$fp_style),
        variant=if (is.null(bundle$forest_variant)) "standard" else as.character(bundle$forest_variant),
        single_study=isTRUE(bundle$single_study),
        studies=list(
            yi=as.numeric(effect$yi),
            vi=as.numeric(effect$vi),
            ci_lb=as.numeric(effect$ci.lb),
            ci_ub=as.numeric(effect$ci.ub),
            labels=as.character(effect$slab)
        ),
        summary=summary,
        weights=if (is.null(bundle$weights)) NULL else as.numeric(bundle$weights),
        ilab=rcmetar.render.state.ilab(bundle$ilab, n),
        sample_sizes=if (is.null(bundle$sample_sizes)) NULL else as.numeric(bundle$sample_sizes),
        params=rcmetar.render.state.params(bundle$params),
        plot_range=as.numeric(bundle$plot_range),
        effect_display=list(
            y_disp=displayed[[1]],
            lb_disp=displayed[[2]],
            ub_disp=displayed[[3]]
        )
    )
    state
}

rcmetar.frozen.forest.bundle <- function(state, presentation, figure.key, outpath, display.path=NULL) {
    if (!is.list(state) || !identical(state$version, 1L) ||
            !identical(state$renderer, "rcmetar_forest_v1") ||
            !identical(state$figure_key, figure.key) ||
            !is.list(state$studies) || !is.list(state$summary) ||
            !is.list(state$params) || !is.list(presentation)) {
        stop("Saved forest renderer state is malformed.", call.=FALSE)
    }
    allowed.params <- c(
        "measure", "conf.level", "digits", "rm.method", "create.plot",
        "fp_style", "fp_accent_color", "fp_col1_str", "fp_col2_str",
        "fp_col3_str", "fp_col4_str", "fp_plot_lb", "fp_plot_ub",
        "fp_xlabel", "fp_xticks", "fp_point_size_multiplier",
        "fp_show_annotation", "fp_show_col1", "fp_show_col2",
        "fp_show_col3", "fp_show_col4", "fp_show_headers",
        "fp_show_raw_counts", "fp_show_summary_line"
    )
    presentation.fields <- c(
        "fp_style", "fp_accent_color", "fp_col1_str", "fp_col2_str",
        "fp_col3_str", "fp_col4_str", "fp_plot_lb", "fp_plot_ub",
        "fp_xlabel", "fp_xticks", "fp_point_size_multiplier",
        "fp_show_annotation", "fp_show_col1", "fp_show_col2",
        "fp_show_col3", "fp_show_col4", "fp_show_headers",
        "fp_show_raw_counts", "fp_show_summary_line"
    )
    if (length(presentation) > 0 &&
            (is.null(names(presentation)) || any(!names(presentation) %in% presentation.fields))) {
        stop("Saved forest appearance settings are malformed.", call.=FALSE)
    }
    params <- state$params
    if (is.null(names(params)) || any(!names(params) %in% allowed.params)) {
        stop("Saved forest renderer parameters are malformed.", call.=FALSE)
    }
    for (name in names(presentation)) {
        if (!grepl("(outpath|display_path)$", name)) {
            params[[name]] <- presentation[[name]]
        }
    }
    params$fp_outpath <- outpath
    if (!is.null(display.path)) params$fp_display_path <- display.path
    params <- rcmetar.normalize.plot.text.params(params)
    studies <- state$studies
    n <- length(studies$labels)
    matrix <- if (length(state$ilab$headers) == 0) {
        matrix(character(0), nrow=n, ncol=0)
    } else {
        do.call(rbind, lapply(state$ilab$matrix, as.character))
    }
    if (length(state$ilab$headers) > 0) colnames(matrix) <- state$ilab$headers
    res <- state$summary
    res$ci.lb <- res$ci_lb
    res$ci.ub <- res$ci_ub
    res$yi <- as.numeric(studies$yi)
    res$vi <- as.numeric(studies$vi)
    bundle <- list(
        render_engine="metafor",
        frozen_numeric=TRUE,
        data_type=state$data_type,
        forest_variant=if (identical(state$variant, "standard")) NULL else state$variant,
        fp_style=rcmetar.forest.style(params),
        res=res,
        effect=list(
            yi=as.numeric(studies$yi),
            vi=as.numeric(studies$vi),
            sei=sqrt(as.numeric(studies$vi)),
            ci.lb=as.numeric(studies$ci_lb),
            ci.ub=as.numeric(studies$ci_ub),
            slab=as.character(studies$labels)
        ),
        single_study=isTRUE(state$single_study),
        ilab=list(
            matrix=matrix,
            columns=state$ilab$columns,
            headers=as.character(state$ilab$headers),
            groups=as.character(state$ilab$groups)
        ),
        slab=as.character(studies$labels),
        weights=if (is.null(state$weights)) NULL else as.numeric(state$weights),
        sample_sizes=if (is.null(state$sample_sizes)) NULL else as.numeric(state$sample_sizes),
        params=params,
        plot_range=as.numeric(state$plot_range),
        changed.params=list(),
        effect_display=list(
            y.disp=as.numeric(state$effect_display$y_disp),
            lb.disp=as.numeric(state$effect_display$lb_disp),
            ub.disp=as.numeric(state$effect_display$ub_disp)
        )
    )
    rcmetar.decorate.metafor.bundle(bundle)
}

rcmetar.draw.saved.forest <- function(state, presentation, figure.key, outpath, display.path=NULL) {
    bundle <- rcmetar.frozen.forest.bundle(state, presentation, figure.key, outpath, display.path)
    rcmetar.draw.metafor.forest(bundle, outpath)
}
