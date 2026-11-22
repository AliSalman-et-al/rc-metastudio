rcmetar.plot.file.extension <- function(outpath) {
    path <- tolower(as.character(outpath))
    if (grepl("[.]svg[.]gz$", path)) {
        return("svgz")
    }
    filename <- basename(path)
    ext <- sub("^.*[.]", "", filename)
    if (identical(ext, filename)) {
        return("pdf")
    }
    if (!nzchar(ext)) {
        return("pdf")
    }
    ext
}


rcmetar.plot.scalar_path <- function(path) {
    if (is.null(path) || length(path) != 1 || is.na(path) ||
            !nzchar(as.character(path))) {
        return(NULL)
    }
    as.character(path)
}

rcmetar.plot.paths.equal <- function(left, right) {
    left <- rcmetar.plot.scalar_path(left)
    right <- rcmetar.plot.scalar_path(right)
    if (is.null(left) || is.null(right)) {
        return(FALSE)
    }
    identical(
        normalizePath(as.character(left), winslash="/", mustWork=FALSE),
        normalizePath(as.character(right), winslash="/", mustWork=FALSE)
    )
}

rcmetar.plot.display_path_for_bundle <- function(bundle, outpath, prefix) {
    params <- bundle$params
    if (is.null(params)) {
        return(NULL)
    }
    requested.outpath <- rcmetar.plot.scalar_path(
        params[[paste0(prefix, "_outpath")]]
    )
    display.path <- rcmetar.plot.scalar_path(
        params[[paste0(prefix, "_display_path")]]
    )
    if (!rcmetar.plot.paths.equal(requested.outpath, outpath) || is.null(display.path)) {
        return(NULL)
    }
    display.path
}

rcmetar.plot.export.dpi <- function(size) {
    if (!is.null(size$dpi) && is.finite(size$dpi) && size$dpi > 0) {
        return(size$dpi)
    }
    600
}

rcmetar.plot.pixel.size <- function(size) {
    dpi <- rcmetar.plot.export.dpi(size)
    c(
        width=max(1, ceiling(size$width * dpi)),
        height=max(1, ceiling(size$height * dpi))
    )
}

rcmetar.plot.raster.size <- function(size, keep.display, extension) {
    # Analysis previews stay bounded; an explicit publication DPI is never reduced.
    if (keep.display && is.null(size$dpi) && extension %in% c("png", "tif", "tiff") &&
            (max(rcmetar.plot.pixel.size(size)) > 32000 ||
             prod(rcmetar.plot.pixel.size(size)) * 4 > 256 * 1024^2)) {
        size$dpi <- min(120, sqrt(32 * 1024^2 / (size$width * size$height)))
    }
    size
}

rcmetar.open.svg_device <- function(outpath, size) {
    bg <- if (!is.null(size$bg)) size$bg else "white"
    svglite::svglite(
        filename=outpath,
        width=size$width,
        height=size$height,
        bg=bg,
        standalone=TRUE,
        fix_text_size=TRUE
    )
    invisible(NULL)
}

rcmetar.materialize.svg.properties <- function(nodes, defaults) {
    styles <- xml2::xml_attr(nodes, "style")
    for (property in names(defaults)) {
        missing <- is.na(xml2::xml_attr(nodes, property)) &
            !grepl(paste0("(^|;)[[:space:]]*", property, "[[:space:]]*:"),
                   styles, ignore.case=TRUE, perl=TRUE)
        xml2::xml_set_attr(nodes[missing], property, defaults[[property]])
    }
}

rcmetar.sanitize.svg.xml <- function(svg) {
    # XML 1.0 permits tab, LF, and CR below U+0020, but not the other
    # control characters or references that graphics devices can occasionally
    # emit. Filter bytes first: an invalid control byte can survive in an R
    # character vector with an unknown encoding and evade a character regex.
    # Remove both forms before libxml2 expands character references.
    if (!is.raw(svg)) {
        svg <- charToRaw(svg)
    }
    bytes <- as.integer(svg)
    svg <- rawToChar(svg[!(bytes <= 8L | bytes %in% c(11L, 12L) | bytes >= 14L & bytes <= 31L)])
    svg <- gsub("[\\x00-\\x08\\x0B\\x0C\\x0E-\\x1F]", "", svg, perl=TRUE)
    svg <- gsub("&#0*(?:[0-8]|1[124-9]|2[0-9]|3[01]);", "", svg, perl=TRUE)
    gsub("&#[xX]0*(?:[0-8]|[bBcC]|[eEfF]|1[0-9a-fA-F]);", "", svg, perl=TRUE)
}

rcmetar.normalize.svglite.svg <- function(svg.path) {
    compressed <- grepl("[.]svgz$", tolower(svg.path))
    # svglite declares UTF-8. Reading through the native Windows code page can
    # corrupt non-ASCII labels before libxml2 sees them, especially when R's
    # requested UTF-8 locale is unavailable.
    input <- if (compressed) {
        gzfile(svg.path, open="rb")
    } else {
        file(svg.path, open="rb")
    }
    svg <- rawToChar(readBin(input, what="raw", n=100000000L))
    close(input)
    Encoding(svg) <- "bytes"
    svg <- rcmetar.sanitize.svg.xml(svg)

    document <- xml2::read_xml(charToRaw(svg), options="NOBLANKS")
    # Keep the primary face, but let Windows rasterizers find mathematical glyphs.
    text <- xml2::xml_find_all(document,
        "//*[local-name()='text' and contains(@style, 'font-family:') and not(contains(@style, 'Segoe UI Symbol'))]")
    styles <- xml2::xml_attr(text, "style")
    xml2::xml_set_attr(text, "style",
        sub("(font-family:[^;]+)", '\\1, "Segoe UI Symbol", sans-serif', styles))
    shapes <- xml2::xml_find_all(
        document,
        "//*[local-name()='g' and contains(concat(' ', normalize-space(@class), ' '), ' svglite ')]//*[local-name()='line' or local-name()='polyline' or local-name()='polygon' or local-name()='path' or local-name()='rect' or local-name()='circle']"
    )
    glyph.paths <- xml2::xml_find_all(
        document,
        "//*[local-name()='g' and contains(concat(' ', normalize-space(@class), ' '), ' svglite ')]//*[local-name()='g' and contains(concat(' ', normalize-space(@class), ' '), ' glyphgroup ')]//*[local-name()='path']"
    )
    if (length(glyph.paths) > 0) {
        shapes <- shapes[!(xml2::xml_path(shapes) %in% xml2::xml_path(glyph.paths))]
    }
    defaults <- c(
        fill="none",
        stroke="#000000",
        `stroke-linecap`="round",
        `stroke-linejoin`="round",
        `stroke-miterlimit`="10.00"
    )
    rcmetar.materialize.svg.properties(shapes, defaults)
    rcmetar.materialize.svg.properties(glyph.paths, c(fill="inherit", stroke="none"))

    normalized <- as.character(document)

    output <- if (compressed) gzfile(svg.path, open="wt") else file(svg.path, open="wt")
    writeLines(normalized, output, useBytes=TRUE)
    close(output)
    invisible(svg.path)
}

rcmetar.close.plot.device <- function(device) {
    if (device %in% grDevices::dev.list()) grDevices::dev.off(device)
}

rcmetar.write.plot.atomically <- function(path, write) {
    dir.create(dirname(path), recursive=TRUE, showWarnings=FALSE)
    temporary <- tempfile(".rcmetar-", tmpdir=dirname(path),
                          fileext=paste0(".", rcmetar.plot.file.extension(path)))
    on.exit(unlink(temporary))
    result <- write(temporary)
    if (!file.rename(temporary, path)) {
        stop(sprintf("Could not replace plot file: %s", path), call.=FALSE)
    }
    invisible(result)
}

rcmetar.render.plot_svg <- function(svg.path, size, draw) {
    rcmetar.write.plot.atomically(svg.path, function(temporary) {
        rcmetar.open.svg_device(temporary, size)
        device <- grDevices::dev.cur()
        on.exit(rcmetar.close.plot.device(device))
        result <- draw()
        rcmetar.close.plot.device(device)
        rcmetar.normalize.svglite.svg(temporary)
        result
    })
}

rcmetar.export.svg_render <- function(svg.path, outpath, size) {
    rcmetar.write.plot.atomically(outpath, function(temporary) {
        .rcmetar.export.svg_render(svg.path, temporary, size)
    })
}

.rcmetar.export.svg_render <- function(svg.path, outpath, size) {
    .rcmetar.require.package("rsvg")
    ext <- rcmetar.plot.file.extension(outpath)
    pixels <- rcmetar.plot.pixel.size(size)
    if (ext %in% c("png", "tif", "tiff") && (max(pixels) > 32000 || prod(pixels) > 150e6))
        stop("The bitmap is too large. Use a lower DPI or export a vector PDF or SVG.", call.=FALSE)
    if (identical(ext, "png")) {
        if (is.null(size$dpi)) {
            rsvg::rsvg_png(svg.path, outpath, width=pixels[["width"]], height=pixels[["height"]])
        } else {
            .rcmetar.require.package("png")
            bitmap <- png::readPNG(rsvg::rsvg_png(svg.path, width=pixels[["width"]],
                height=pixels[["height"]]), native=TRUE)
            png::writePNG(bitmap, outpath, dpi=rcmetar.plot.export.dpi(size))
        }
        return(invisible(ext))
    }
    if (identical(ext, "tif") || identical(ext, "tiff")) {
        .rcmetar.require.package("png")
        # Keep publication rasters packed: a floating-point RGBA array plus
        # channel copies exhausts memory for large subgroup figures.
        bitmap <- png::readPNG(rsvg::rsvg_png(svg.path, width=pixels[["width"]], height=pixels[["height"]]), native=TRUE)
        grDevices::tiff(
            filename=outpath,
            width=pixels[["width"]],
            height=pixels[["height"]],
            units="px",
            res=rcmetar.plot.export.dpi(size),
            compression="lzw",
            bg="white"
        )
        device <- grDevices::dev.cur()
        on.exit(rcmetar.close.plot.device(device))
        grid::grid.raster(bitmap, interpolate=FALSE)
        return(invisible(ext))
    }
    # The PDF device defaults to the viewBox extent even when the SVG
    # declares a different physical viewport. Give Cairo its page in points.
    rsvg::rsvg_pdf(svg.path, outpath, width=round(size$width * 72),
                  height=round(size$height * 72))
    invisible(ext)
}

.rcmetar.wrap.plot.caption <- function(caption, width, cex) {
    rcmetar.forest.with.measurement.device({
        words <- strsplit(caption, "[[:space:]]+")[[1]]
        wrapped <- character(0)
        line <- ""
        for (word in words) {
            candidate <- trimws(paste(line, word))
            if (nzchar(line) && graphics::strwidth(candidate, units="inches", cex=cex) > width) {
                wrapped <- c(wrapped, line)
                line <- word
            } else line <- candidate
        }
        c(wrapped, line)
    })
}

.rcmetar.copy.plot.svg <- function(source, outpath, extension) {
    input <- gzfile(source, open="rb")
    svg <- tryCatch(readLines(input, warn=FALSE, encoding="UTF-8"), finally=close(input))
    output <- if (identical(extension, "svgz")) gzfile(outpath, open="wb") else file(outpath, open="wb")
    tryCatch(writeLines(svg, output, useBytes=TRUE), finally=close(output))
}

.rcmetar.plot.caption.layout <- function(caption, size) {
    if (!length(caption) || is.na(caption[[1]]) || !nzchar(caption[[1]])) return(NULL)
    text <- gsub("[\r\n]+", " \u00b7 ", as.character(caption[[1]]))
    cex <- size$caption.cex %||% 1.08
    compact <- !is.null(size$caption.cex)
    lines <- .rcmetar.wrap.plot.caption(text, size$width - if (compact) .15 else .6, cex)
    height <- if (compact) .13 * length(lines) + .09 else .24 * length(lines) + .4
    list(text=paste(lines, collapse="\n"), height=height, cex=cex, line=if (compact) .25 else 1)
}

rcmetar.render.plot_file <- function(outpath, size, draw, display.path=NULL, caption=NULL) {
    caption <- .rcmetar.plot.caption.layout(caption, size)
    if (!is.null(caption)) {
        if (!isTRUE(size$caption.in.height)) size$height <- size$height + caption$height
        draw.plot <- draw
        draw <- function() {
            graphics::par(omi=c(0, 0, caption$height, 0))
            result <- draw.plot()
            graphics::mtext(caption$text, side=3, outer=TRUE,
                            line=caption$line, at=0.02, adj=0, cex=caption$cex, font=1, family="sans")
            result
        }
    }
    ext <- rcmetar.plot.file.extension(outpath)
    display.path <- rcmetar.plot.scalar_path(display.path)
    if (identical(ext, "svg") || identical(ext, "svgz")) {
        if (is.null(display.path)) {
            return(rcmetar.render.plot_svg(outpath, size, draw))
        }
        dir.create(dirname(display.path), recursive=TRUE, showWarnings=FALSE)
        result <- rcmetar.render.plot_svg(display.path, size, draw)
        if (!rcmetar.plot.paths.equal(display.path, outpath))
            rcmetar.write.plot.atomically(outpath, function(temporary) {
                .rcmetar.copy.plot.svg(display.path, temporary, ext)
            })
        return(invisible(result))
    }

    keep.display <- !is.null(display.path)
    svg.path <- if (keep.display) as.character(display.path) else tempfile(
        pattern="rcmetar-plot-", fileext=".svg"
    )
    if (keep.display) {
        dir.create(dirname(svg.path), recursive=TRUE, showWarnings=FALSE)
    }
    if (!keep.display) {
        on.exit(unlink(svg.path), add=TRUE)
    }
    result <- rcmetar.render.plot_svg(svg.path, size, draw)
    rcmetar.export.svg_render(svg.path, outpath, rcmetar.plot.raster.size(size, keep.display, ext))
    invisible(result)
}
