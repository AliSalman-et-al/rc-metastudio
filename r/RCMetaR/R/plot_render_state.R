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

rcmetar.render.state.summary <- function(result) {
    fields <- c("b", "ci.lb", "ci.ub", "QE", "k", "p", "QEp", "I2", "tau2", "method", "zval", "pval")
    summary <- list()
    for (field in fields) {
        value <- result[[field]]
        if (!is.null(value) && length(value) > 0) {
            summary[[field]] <- rcmetar.render.state.atomic(value[[1]], field)
        }
    }
    names(summary)[names(summary) == "ci.lb"] <- "ci_lb"
    names(summary)[names(summary) == "ci.ub"] <- "ci_ub"
    summary
}

rcmetar.render.state.subgroups <- function(subgroups) {
    summary <- rcmetar.render.state.summary
    difference <- subgroups$difference_test
    if (!is.null(difference)) {
        difference <- lapply(c("QM", "QMp", "df"), function(field) {
            rcmetar.render.state.atomic(difference[[field]], field)
        }) |>
            stats::setNames(c("QM", "QMp", "df"))
    }
    list(
        names=as.character(subgroups$names),
        results=lapply(subgroups$results, summary),
        overall=summary(subgroups$overall),
        study_rows=as.numeric(subgroups$study_rows),
        header_rows=as.numeric(subgroups$header_rows),
        polygon_rows=as.numeric(subgroups$polygon_rows),
        overall_row=as.numeric(subgroups$overall_row),
        difference_test=difference,
        ylim=as.numeric(subgroups$ylim)
    )
}

rcmetar.frozen.forest.subgroups <- function(state, studies) {
    groups <- state$subgroups
    required <- c(
        "names", "results", "overall", "study_rows", "header_rows",
        "polygon_rows", "overall_row", "difference_test", "ylim"
    )
    if (!is.list(groups) || !identical(sort(names(groups)), sort(required)) ||
            !is.list(groups$results) || length(groups$results) != length(groups$names) ||
            length(groups$study_rows) != length(studies$labels) ||
            length(groups$header_rows) != length(groups$names) ||
            length(groups$polygon_rows) != length(groups$names) ||
            length(groups$ylim) != 2) {
        stop("Saved subgroup forest renderer data are malformed.", call.=FALSE)
    }
    result <- function(summary) {
        summary$ci.lb <- summary$ci_lb
        summary$ci.ub <- summary$ci_ub
        summary
    }
    groups$results <- lapply(groups$results, result)
    groups$overall <- result(groups$overall)
    groups
}

rcmetar.forest.render.effect.geometry <- function(effect) {
    if (!is.null(effect)) {
        effect$vi <- as.numeric(effect$sei)^2
    }
    required <- c("yi", "vi", "ci.lb", "ci.ub", "slab")
    if (!is.list(effect) || any(vapply(required, function(field) is.null(effect[[field]]), logical(1)))) {
        return(NULL)
    }
    n <- length(effect$yi)
    if (n == 0 || any(vapply(required[-1], function(field) length(effect[[field]]) != n, logical(1)))) {
        return(NULL)
    }
    effect
}

rcmetar.forest.render.display.geometry <- function(bundle, effect) {
    if (is.null(bundle$effect_display) || !is.list(bundle$effect_display)) {
        return(NULL)
    }
    n <- length(effect$yi)
    subgroup <- identical(bundle$forest_variant, "subgroup")
    displayed <- if (subgroup) {
        transform <- rcmetar.bundle.transform(bundle)
        lapply(list(effect$yi, effect$ci.lb, effect$ci.ub), function(values) {
            transform$display.scale(as.numeric(values), ni=bundle$sample_sizes)
        })
    } else {
        lapply(c("y.disp", "lb.disp", "ub.disp"), function(field) {
            values <- as.numeric(bundle$effect_display[[field]])
            if (length(values) == n + 1) values[-length(values)] else values
        })
    }
    if (any(lengths(displayed) != n)) {
        return(NULL)
    }
    stats::setNames(displayed, c("y_disp", "lb_disp", "ub_disp"))
}

rcmetar.project.forest.render.state <- function(bundle, figure.key) {
    if (!rcmetar.is.metafor.forest.bundle(bundle) ||
            !bundle$fp_style %in% c("default", "revman", "bmj")) {
        return(NULL)
    }
    res <- bundle$res
    effect <- rcmetar.forest.render.effect.geometry(bundle$effect)
    if (is.null(effect)) return(NULL)
    n <- length(effect$yi)
    summary <- rcmetar.render.state.summary(res)
    required.summary <- c("b", "ci_lb", "ci_ub")
    if (!all(required.summary %in% names(summary))) {
        return(NULL)
    }
    displayed <- rcmetar.forest.render.display.geometry(bundle, effect)
    if (is.null(displayed)) return(NULL)
    subgroup <- identical(bundle$forest_variant, "subgroup")
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
            y_disp=displayed$y_disp,
            lb_disp=displayed$lb_disp,
            ub_disp=displayed$ub_disp
        )
    )
    if (subgroup) {
        state$subgroups <- rcmetar.render.state.subgroups(bundle$subgroups)
    }
    state
}

rcmetar.frozen.forest.params <- function(saved, presentation, outpath, display.path) {
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
    if (length(presentation) > 0 && (is.null(names(presentation)) || any(!names(presentation) %in% presentation.fields))) {
        stop("Saved forest appearance settings are malformed.", call.=FALSE)
    }
    if (is.null(names(saved)) || any(!names(saved) %in% allowed.params)) {
        stop("Saved forest renderer parameters are malformed.", call.=FALSE)
    }
    params <- saved
    for (name in names(presentation)) {
        params[[name]] <- presentation[[name]]
    }
    params$fp_outpath <- outpath
    if (!is.null(display.path)) params$fp_display_path <- display.path
    rcmetar.normalize.plot.text.params(params)
}

rcmetar.frozen.forest.ilab.matrix <- function(ilab, n) {
    if (length(ilab$headers) == 0) {
        return(matrix(character(0), nrow=n, ncol=0))
    }
    result <- do.call(rbind, lapply(ilab$matrix, as.character))
    colnames(result) <- ilab$headers
    result
}

rcmetar.render.state.numeric <- function(value) {
    if (is.null(value)) NULL else as.numeric(value)
}

rcmetar.frozen.forest.numeric.bundle <- function(state, params) {
    studies <- state$studies
    n <- length(studies$labels)
    ilab.matrix <- rcmetar.frozen.forest.ilab.matrix(state$ilab, n)
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
            matrix=ilab.matrix,
            columns=state$ilab$columns,
            headers=as.character(state$ilab$headers),
            groups=as.character(state$ilab$groups)
        ),
        slab=as.character(studies$labels),
        weights=rcmetar.render.state.numeric(state$weights),
        sample_sizes=rcmetar.render.state.numeric(state$sample_sizes),
        params=params,
        plot_range=as.numeric(state$plot_range),
        changed.params=list(),
        effect_display=list(
            y.disp=as.numeric(state$effect_display$y_disp),
            lb.disp=as.numeric(state$effect_display$lb_disp),
            ub.disp=as.numeric(state$effect_display$ub_disp)
        )
    )
    bundle
}

rcmetar.frozen.forest.bundle <- function(state, presentation, figure.key, outpath, display.path=NULL) {
    if (!is.list(state) || !identical(state$version, 1L) ||
            !identical(state$renderer, "rcmetar_forest_v1") ||
            !identical(state$figure_key, figure.key) ||
            !is.list(state$studies) || !is.list(state$summary) ||
            !is.list(state$params) || !is.list(presentation) ||
            (identical(state$variant, "subgroup") && !is.list(state$subgroups))) {
        stop("Saved forest renderer state is malformed.", call.=FALSE)
    }
    params <- rcmetar.frozen.forest.params(state$params, presentation, outpath, display.path)
    bundle <- rcmetar.frozen.forest.numeric.bundle(state, params)
    if (identical(state$variant, "subgroup")) {
        bundle$subgroups <- rcmetar.frozen.forest.subgroups(state, state$studies)
        bundle$single_study <- TRUE
    }
    rcmetar.decorate.metafor.bundle(bundle)
}

rcmetar.draw.saved.forest <- function(state, presentation, figure.key, outpath, display.path=NULL) {
    bundle <- rcmetar.frozen.forest.bundle(state, presentation, figure.key, outpath, display.path)
    rcmetar.draw.metafor.forest(bundle, outpath)
}
