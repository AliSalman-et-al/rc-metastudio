# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

.rcmetar.plot.bundle.suffixes <- c(
    om.data=".data", res=".res", params=".params", plot.data=".plotdata"
)

.rcmetar.plot.bundle.paths <- function(prefix, members) {
    setNames(paste0(prefix, .rcmetar.plot.bundle.suffixes[members]), members)
}

save.plot.data <- function(plot.data, out.path=NULL) {
    out.path <- out.path %||% tempfile("plot-", tmpdir=rcmetar.scratch.path())
    save(plot.data, file=.rcmetar.plot.bundle.paths(out.path, "plot.data"))
    out.path
}

save.data <- function(om.data, res, params, plot.data=NULL, out.path=NULL) {
    out.path <- out.path %||% tempfile("plot-", tmpdir=rcmetar.scratch.path())
    save(om.data, file=.rcmetar.plot.bundle.paths(out.path, "om.data"))
    if (inherits(plot.data$regeneration_state, "rcmetar_forest_regeneration_state")) {
        res <- plot.data$regeneration_state
        for (name in names(res$param_overrides)) params[[name]] <- res$param_overrides[[name]]
    }
    save(res, file=.rcmetar.plot.bundle.paths(out.path, "res"))
    save(params, file=.rcmetar.plot.bundle.paths(out.path, "params"))
    if (!is.null(plot.data)) save.plot.data(plot.data, out.path)
    out.path
}

.rcmetar.read.plot.bundle <- function(prefix, members, optional=character()) {
    paths <- .rcmetar.plot.bundle.paths(prefix, c(members, optional))
    present <- file.exists(paths)
    if (!all(present[seq_along(members)])) return(NULL)
    bundle <- new.env(parent=emptyenv())
    for (member in names(paths[present])) {
        loaded <- load(paths[[member]], envir=bundle)
        if (!identical(loaded, member)) {
            stop(sprintf("Invalid plot bundle member: %s", paths[[member]]), call.=FALSE)
        }
    }
    as.list(bundle, all.names=TRUE)
}

.rcmetar.plot.analysis.members <- c("om.data", "res", "params")

#' Read, edit, and render persisted plot bundles
#'
#' @param prefix The base path of an existing RCMetaR plot bundle.
#' @param regenerator One of `forest`, `regression`, `sroc`, `funnel`, or `trial_sequential`.
#' @param changed A named list of edited plot parameters.
#' @param output.path The requested plot destination.
#' @param staging.directory A caller-owned directory for staged files.
#' @param svg.path The path to SVG artwork.
#' @param width,height The requested width and height in inches.
#' @param page_height Maximum height in inches of a forest SVG panel.
#' @param dpi The requested raster resolution in dots per inch.
#' @param include_title Whether to draw the figure's title line on export.
#' @param outline_text Whether to outline text in trial sequential SVG exports.
#' @return Parameters, forest height and minimum width in inches, staged file
#'   mappings, or rendered paths, depending on the function. Missing bundles
#'   return `NULL`.
#' @name rcmetar-plot-bundle
NULL

#' @rdname rcmetar-plot-bundle
#' @export
rcmetar.plot.bundle.params <- function(prefix) {
    bundle <- .rcmetar.read.plot.bundle(
        prefix, .rcmetar.plot.analysis.members, optional="plot.data")
    if (is.null(bundle)) return(NULL)
    params <- bundle$params
    data <- bundle$plot.data
    if (!is.null(data$fp_style) && !rcmetar.is.reitsma.coefficient.bundle(data)) {
        plan <- rcmetar.forest.layout.preflight(data)
        params$resolved.defaults <- list(
            xlabel=plan$x$xlab, lower=plan$x$alim[[1]], upper=plan$x$alim[[2]],
            ticks=rcmetar.forest.axis.labels(data, plan$x$at),
            effect=rcmetar.metafor.effect.header(data))
    }
    if (!is.null(params$funnel.kind)) {
        x <- .small.study.funnel.x(bundle$om.data, params)
        params$resolved.funnel.ratio <- .small.study.funnel.ratio(params)
        params$resolved.funnel.x <- if (params$resolved.funnel.ratio) exp(x) else x
    }
    params
}

.rcmetar.plot.bundle.renderer <- function(regenerator) {
    switch(regenerator,
        forest=list(draw=rcmetar.draw.forest.plot, build=rcmetar.regenerate.plot.data, prefix="fp"),
        regression=list(draw=rcmetar.draw.regression.plot, build=rcmetar.regenerate.regression.plot.data, prefix="bp"),
        sroc=list(draw=rcmetar.draw.sroc.plot, build=rcmetar.regenerate.plot.data, prefix="fp"),
        trial_sequential=list(draw=rcmetar.draw.tsa.plot, build=rcmetar.tsa.plot.data, prefix="fp"),
        stop(sprintf("Unknown plot regenerator: %s", regenerator), call.=FALSE))
}

#' @rdname rcmetar-plot-bundle
#' @export
rcmetar.forest.export.dimensions <- function(prefix, width, include_title=FALSE) {
    bundle <- .rcmetar.read.plot.bundle(prefix, "plot.data")$plot.data
    if (is.null(bundle) || !rcmetar.is.metafor.forest.bundle(bundle)) return(NULL)
    plan <- rcmetar.forest.layout.preflight(bundle, width=width, measure.minimum=TRUE)
    caption <- if (include_title) .rcmetar.plot.caption.layout(bundle$params$plot_caption, plan$device)
    height <- plan$device$height + (caption$height %||% 0)
    c(height=round(height * 72, 2) / 72, minimum_width=plan$device$min_width)
}

#' @rdname rcmetar-plot-bundle
#' @export
rcmetar.prepare.plot.bundle.edit <- function(prefix, regenerator, changed, output.path, staging.directory) {
    bundle <- .rcmetar.read.plot.bundle(prefix, .rcmetar.plot.analysis.members)
    if (is.null(bundle)) return(NULL)
    params <- bundle$params
    for (name in names(changed)) params[[name]] <- changed[[name]]

    stage <- function(name) file.path(staging.directory, name)
    extension <- tools::file_ext(output.path)
    if (!nzchar(extension)) extension <- "png"
    staged.output <- stage(paste0("render.", extension))
    staged.prefix <- stage("plot")
    destinations <- .rcmetar.plot.bundle.paths(prefix, "params")
    staged.paths <- .rcmetar.plot.bundle.paths(staged.prefix, "params")

    if (identical(regenerator, "funnel")) {
        rcmetar.regenerate.small.study.funnel(bundle$om.data, bundle$res, params, staged.output)
    } else {
        renderer <- .rcmetar.plot.bundle.renderer(regenerator)
        output.param <- paste0(renderer$prefix, "_outpath")
        display.param <- paste0(renderer$prefix, "_display_path")
        params[[output.param]] <- output.path
        display.target <- rcmetar.plot.scalar_path(params[[display.param]])
        candidate <- params
        candidate[[output.param]] <- staged.output
        candidate[[display.param]] <- NULL
        if (!is.null(display.target)) {
            if (rcmetar.plot.paths.equal(display.target, output.path)) {
                candidate[[display.param]] <- staged.output
            } else {
                staged.display <- stage("display.svg")
                candidate[[display.param]] <- staged.display
                destinations <- c(destinations, display.target)
                staged.paths <- c(staged.paths, staged.display)
            }
        }
        plot.data <- renderer$build(bundle$om.data, bundle$res, params)
        edit.data <- plot.data
        edit.data$params[[output.param]] <- candidate[[output.param]]
        edit.data$params[[display.param]] <- candidate[[display.param]]
        if (identical(regenerator, "sroc")) edit.data$display.path <- candidate[[display.param]]
        renderer$draw(edit.data, staged.output)
        save.plot.data(plot.data, staged.prefix)
        destinations <- c(destinations, .rcmetar.plot.bundle.paths(prefix, "plot.data"))
        staged.paths <- c(staged.paths, .rcmetar.plot.bundle.paths(staged.prefix, "plot.data"))
    }
    save(params, file=.rcmetar.plot.bundle.paths(staged.prefix, "params"))
    setNames(c(staged.paths, staged.output), c(destinations, output.path))
}

#' @rdname rcmetar-plot-bundle
#' @export
rcmetar.render.plot.bundle <- function(prefix, regenerator, output.path, width=NULL, height=NULL, dpi=600,
                                       include_title=TRUE, outline_text=TRUE, page_height=NULL) {
    if (identical(regenerator, "funnel")) {
        bundle <- .rcmetar.read.plot.bundle(prefix, .rcmetar.plot.analysis.members)
        if (is.null(bundle)) return(NULL)
        if (!include_title) bundle$params$plot_caption <- NULL
        return(rcmetar.regenerate.small.study.funnel(
            bundle$om.data, bundle$res, bundle$params, output.path, dpi=dpi, width=width, height=height))
    }
    bundle <- .rcmetar.read.plot.bundle(prefix, "plot.data")
    if (is.null(bundle)) return(NULL)
    if (identical(regenerator, "sroc")) bundle$plot.data$display.path <- NULL
    if (!include_title) {
        bundle$plot.data$params$plot_caption <- NULL
        if (identical(regenerator, "sroc")) bundle$plot.data$style$caption <- NULL
    }
    if (identical(regenerator, "forest") && rcmetar.is.metafor.forest.bundle(bundle$plot.data)) {
        if (!is.null(page_height) && !rcmetar.plot.file.extension(output.path) %in% c("svg", "svgz"))
            stop("Paged forests require SVG output paths.", call.=FALSE)
        rcmetar.forest <- rcmetar.draw.metafor.forest(bundle$plot.data, output.path, width, dpi, page_height)
        return(if (is.null(page_height)) output.path else rcmetar.forest)
    }
    switch(regenerator,
        trial_sequential=rcmetar.draw.tsa.plot(
            bundle$plot.data, output.path, width, height, dpi, export=isTRUE(outline_text)),
        regression=rcmetar.draw.metafor.bubble(bundle$plot.data, output.path, width, height, dpi),
        sroc=rcmetar.reitsma.draw(bundle$plot.data, output.path, width, height, dpi),
        .rcmetar.plot.bundle.renderer(regenerator)$draw(bundle$plot.data, output.path))
    output.path
}

#' @rdname rcmetar-plot-bundle
#' @export
rcmetar.export.svg.artwork <- function(svg.path, output.path, width, height, dpi) {
    rcmetar.export.svg_render(svg.path, output.path, list(width=width, height=height, dpi=dpi))
}
