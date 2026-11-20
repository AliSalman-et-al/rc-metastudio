args <- commandArgs(trailingOnly=TRUE)
for (source in list.files(args[1], pattern="[.]plotdata$", full.names=TRUE)) {
    data <- new.env()
    load(source, envir=data)
    plot <- data$plot.data
    if (!identical(plot$kind, "sroc") || length(plot$study.names) < 10L) next
    cat("Input:", source, "\n")
    plot$display.path <- NULL
    plot$style$show.labels <- TRUE
    plot$style$caption <- NULL
    n <- length(plot$study.names)
    plot$fpr[] <- .2
    plot$sensitivity[] <- .75
    plot$study.names <- paste0("Trial ", seq_len(n), " in a multicentre diagnostic cohort")
    RCMetaR::rcmetar.draw.sroc.plot(plot, args[2])
    svg <- xml2::read_xml(args[2])
    labels <- xml2::xml_text(xml2::xml_find_all(svg, "//*[local-name()='text']"))
    expected <- paste(seq_len(n), plot$study.names, sep=". ")
    stopifnot(all(expected %in% labels))
    cat(n, "numbered key entries for coincident input points\n")
    quit(status=0L)
}
stop('No stress input with at least ten studies')
