# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

.rcmetar.plot.bundle.suffixes <- c(
    om.data=".data", res=".res", params=".params", plot.data=".plotdata"
)

.rcmetar.plot.bundle.paths <- function(prefix, members) {
    setNames(paste0(prefix, .rcmetar.plot.bundle.suffixes[members]), members)
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
#' @param dpi The requested raster resolution in dots per inch.
#' @return Parameters, a mapping from destination paths to staged files, or the
#'   rendered path, respectively. Missing bundles return `NULL`.
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
            ticks=rcmetar.revman.axis.labels(data, plan$x$at),
            effect=rcmetar.metafor.effect.header(data))
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
        renderer$draw(renderer$build(bundle$om.data, bundle$res, candidate), staged.output)
        plot.data <- renderer$build(bundle$om.data, bundle$res, params)
        save.plot.data(plot.data, staged.prefix)
        destinations <- c(destinations, .rcmetar.plot.bundle.paths(prefix, "plot.data"))
        staged.paths <- c(staged.paths, .rcmetar.plot.bundle.paths(staged.prefix, "plot.data"))
    }
    save(params, file=.rcmetar.plot.bundle.paths(staged.prefix, "params"))
    setNames(c(staged.paths, staged.output), c(destinations, output.path))
}

#' @rdname rcmetar-plot-bundle
#' @export
rcmetar.render.plot.bundle <- function(prefix, regenerator, output.path) {
    if (identical(regenerator, "funnel")) {
        bundle <- .rcmetar.read.plot.bundle(prefix, .rcmetar.plot.analysis.members)
        if (is.null(bundle)) return(NULL)
        return(rcmetar.regenerate.small.study.funnel(
            bundle$om.data, bundle$res, bundle$params, output.path, dpi=600))
    }
    bundle <- .rcmetar.read.plot.bundle(prefix, "plot.data")
    if (is.null(bundle)) return(NULL)
    .rcmetar.plot.bundle.renderer(regenerator)$draw(bundle$plot.data, output.path)
    output.path
}

#' @rdname rcmetar-plot-bundle
#' @export
rcmetar.export.svg.artwork <- function(svg.path, output.path, width, height, dpi) {
    rcmetar.export.svg_render(svg.path, output.path, list(width=width, height=height, dpi=dpi))
}
