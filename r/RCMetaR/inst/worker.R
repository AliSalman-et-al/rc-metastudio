# SPDX-License-Identifier: GPL-3.0-or-later

local({
    input <- file("stdin", "rb")
    sink(stderr())
    options(warn=1)
    limit <- 16L * 1024L^2
    magic <- "\x1eRCMS"

    if (!requireNamespace("jsonlite", quietly=TRUE)) {
        message("The R worker requires the jsonlite package. Reinstall the configured R runtime.")
        quit(save="no", status=1L)
    }

    read_exact <- function(size) {
        result <- raw(size)
        offset <- 0L
        while (offset < size) {
            chunk <- readBin(input, "raw", size - offset)
            if (!length(chunk)) return(result[seq_len(offset)])
            result[offset + seq_along(chunk)] <- chunk
            offset <- offset + length(chunk)
        }
        result
    }

    read_frame <- function() {
        header <- read_exact(nchar(magic) + 8L)
        if (!length(header)) return(NULL)
        if (length(header) != nchar(magic) + 8L) stop("Truncated frame header")
        header <- rawToChar(header)
        if (!startsWith(header, magic)) stop("Invalid frame marker")
        size <- strtoi(substring(header, nchar(magic) + 1L), base=16L)
        if (is.na(size) || size < 1L || size > limit) stop("Invalid frame length")
        bytes <- read_exact(size)
        if (length(bytes) != size) stop("Truncated frame")
        text <- rawToChar(bytes)
        Encoding(text) <- "UTF-8"
        jsonlite::fromJSON(text, simplifyVector=FALSE)
    }

    reply <- function(id, status, result=NULL, message=NULL) {
        body <- enc2utf8(jsonlite::toJSON(
            list(protocol=1L, id=id, status=status, result=result, message=message),
            auto_unbox=TRUE, digits=I(17), null="null"
        ))
        size <- nchar(body, type="bytes")
        if (size > limit) stop("The R worker response exceeds the 16 MiB frame limit.", call.=FALSE)
        # R's stdout is text-only. JSON escapes control bytes, and useBytes
        # preserves UTF-8 without locale conversion.
        while (sink.number() > 0L) sink()
        on.exit(sink(stderr()))
        writeLines(paste0(magic, sprintf("%08x", size), body), stdout(), sep="", useBytes=TRUE)
        flush(stdout())
    }

    warm <- function(expected) {
        path <- find.package("RCMetaR")
        stamp_file <- file.path(path, "source.sha256")
        stamp <- if (file.exists(stamp_file)) {
            tryCatch(suppressWarnings(readLines(stamp_file, n=1L, warn=FALSE))[1L],
                     error=function(error) NA_character_)
        } else NA_character_
        version <- utils::packageDescription("RCMetaR", lib.loc=dirname(path), fields="Version")
        if (!identical(version, expected$version) || !identical(stamp, expected$source))
            stop("The installed RCMetaR does not match this version of RC MetaStudio.")
        if (as.character(getRversion()) != expected$pins$R)
            stop("The R worker has the wrong R version.")
        packages <- setdiff(names(expected$pins), "R")
        for (package in packages) {
            actual <- suppressWarnings(utils::packageDescription(package, fields="Version"))
            if (!identical(actual, expected$pins[[package]]))
                stop(sprintf("%s requires version %s, found %s.", package, expected$pins[[package]],
                             if (is.na(actual)) "no installed package" else actual), call.=FALSE)
        }
        library("RCMetaR", lib.loc=dirname(path))
        for (package in c(packages, "grid")) loadNamespace(package)
        warm_graphics()
        RCMetaR:::rcmetar.warm.small.study.effects()
    }

    warm_graphics <- function() {
        RCMetaR:::rcmetar.warm.plot_devices()
        files <- paste0(tempfile("rcms-worker-devices"), c(".svg", ".png", ".tiff", ".pdf"))
        on.exit(unlink(files))
        size <- list(width=2, height=2, dpi=72)
        RCMetaR:::rcmetar.render.plot_svg(files[1L], size, function() {
            graphics::par(mar=rep(0, 4))
            graphics::plot.new()
            graphics::text(.5, .5, "RC MetaStudio")
        })
        for (path in files[-1L]) RCMetaR:::rcmetar.export.svg_render(files[1L], path, size)
    }

    decode_wire <- function(value) {
        if (!is.list(value)) return(value)
        if ("$num" %in% names(value)) {
            tag <- value[["$num"]]
            if (length(value) == 1L && identical(tag, "+Inf")) return(Inf)
            if (length(value) == 1L && identical(tag, "-Inf")) return(-Inf)
            stop("Invalid wire number", call.=FALSE)
        }
        lapply(value, decode_wire)
    }

    number <- function(value) {
        if (is.null(value)) return(NA_real_)
        if (!is.numeric(value) || length(value) != 1L) stop("Expected a number", call.=FALSE)
        value
    }

    numeric_array <- function(values) vapply(values, number, numeric(1))

    wire_value <- function(value) {
        if (is.null(value)) return(NULL)
        if (is.list(value) || length(value) != 1L || !is.null(names(value)))
            return(lapply(value, wire_value))
        if (is.numeric(value) && is.infinite(value))
            return(list("$num"=if (value > 0) "+Inf" else "-Inf"))
        if (is.na(value)) return(NULL)
        unname(value)
    }

    as_row <- function(fields) do.call(data.frame, fields)

    calculate <- function(job) {
        args <- job$args
        answer <- switch(job$kind,
            binary_effect=do.call(rcmetar.binary.study.effect, args),
            continuous_effect=do.call(rcmetar.continuous.study.effect, args),
            diagnostic_effect={
                args$metrics <- unlist(args$metrics, use.names=FALSE)
                do.call(rcmetar.diagnostic.study.effects, args)
            },
            scale={
                if (isTRUE(job$vector)) {
                    args$x <- numeric_array(args$x)
                    if (!is.null(args$n1)) args$n1 <- rep(args$n1, length(args$x))
                } else {
                    args$x <- number(args$x)
                }
                values <- rcmetar.convert.scale(args$x, args$metric, args$data.type, args$convert.to, args$n1)
                if (isTRUE(job$vector)) as.list(values) else values[[1L]]
            },
            binary_impute=rcmetar.impute.binary(as_row(args$data)),
            diagnostic_impute=rcmetar.impute.diagnostic(as_row(args$data)),
            continuous_impute=rcmetar.impute.continuous.study(as_row(args$data), args$alpha),
            pre_post=rcmetar.impute.continuous.prepost(as_row(args$data), args$correlation, args$alpha),
            back_calculate=rcmetar.back.calculate.continuous(
                as_row(args$group1), as_row(args$group2), as_row(args$effect), args$confidence),
            stop("Unknown calculator operation")
        )
        wire_value(answer)
    }

    previews <- function(job) {
        result <- RCMetaR:::rcmetar.study.effect.previews(
            lapply(job$rows, numeric_array), job$family, job$metric,
            unlist(job$metrics, use.names=FALSE), job$two_arm, job$confidence
        )
        lapply(result, function(row) lapply(unname(row), function(effect) {
            lapply(unname(effect), wire_value)
        }))
    }

    plot_job <- function(job, checkpoint) {
        old <- options(rcmetar.sequential.progress=checkpoint)
        on.exit(options(old))
        checkpoint(0L, 0L)
        result <- switch(job$type,
            plot_parameters=rcmetar.plot.bundle.params(job$prefix),
            plot_geometry=as.list(unname(rcmetar.forest.export.dimensions(
                job$prefix, job$width, job$include_title))),
            plot_edit=rcmetar.prepare.plot.bundle.edit(
                job$prefix, job$regenerator, RCMetaR:::.rcmetar.worker.params(job$changed),
                job$output, job$stage),
            plot_render=as.list(rcmetar.render.plot.bundle(
                job$prefix, job$regenerator, job$output, width=job$width,
                dpi=if (is.null(job$dpi)) 600L else job$dpi,
                page_height=job$page_height, include_title=job$include_title,
                outline_text=job$outline_text)),
            artwork_export={
                rcmetar.export.svg.artwork(job$source, job$output, job$width, job$height, job$dpi)
                NULL
            })
        checkpoint(1L, 1L)
        if (job$type %in% c("plot_geometry", "plot_render") && !length(result)) return(NULL)
        wire_value(result)
    }

    startup <- read_frame()
    stopifnot(identical(startup$protocol, 1L), identical(startup$id, 0L))
    ready <- tryCatch({ warm(startup$job); TRUE }, error=function(error) {
        reply(0L, "error", message=conditionMessage(error))
        FALSE
    })
    if (!ready) quit(save="no", status=1L)
    reply(0L, "ok")

    tsa <- new.env(parent=emptyenv())
    repeat {
        request <- read_frame()
        if (is.null(request)) break
        stopifnot(identical(request$protocol, 1L), is.integer(request$id), request$id > 0L)
        marker <- file.path(Sys.getenv("RCMS_WORKER_CONTROL"), paste0(request$id, ".cancel"))
        if (file.exists(marker)) {
            reply(request$id, "cancelled")
            next
        }
        checkpoint <- local({
            last <- -Inf
            function(index, total) {
                if (file.exists(marker)) stop("R job cancelled", call.=FALSE)
                now <- proc.time()[["elapsed"]]
                if (now - last >= .1) {
                    reply(request$id, "progress", list(index=index, total=total))
                    last <<- now
                }
                TRUE
            }
        })
        tryCatch({
            request$job <- decode_wire(request$job)
            value <- if (identical(request$job$type, "previews")) {
                previews(request$job)
            } else if (identical(request$job$type, "calculator")) {
                calculate(request$job)
            } else if (request$job$type %in% c("fit", "diagnostic_fit", "small_study",
                                              "tsa_preview", "tsa_conclusion", "tsa_run")) {
                outcome <- RCMetaR:::.rcmetar.worker.fit(request$job, checkpoint, tsa)
                RCMetaR:::.rcmetar.worker.result.vector(outcome, wire_value)
            } else if (request$job$type %in% c("plot_parameters", "plot_geometry", "plot_edit",
                                              "plot_render", "artwork_export")) {
                plot_job(request$job, checkpoint)
            } else stop("Unknown R worker job")
            if (file.exists(marker)) reply(request$id, "cancelled")
            else reply(request$id, "ok", result=value)
        }, error=function(error) {
            if (file.exists(marker)) reply(request$id, "cancelled")
            else reply(request$id, "error", message=conditionMessage(error))
        })
    }
})
