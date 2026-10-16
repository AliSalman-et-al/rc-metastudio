args <- commandArgs(trailingOnly=TRUE)
dir.create(args[[1]], recursive=TRUE, showWarnings=FALSE)
for (family in c('sans','serif','Arial','Liberation Sans')) {
  for (height in seq(2, 2.1, by=.01)) {
    path <- file.path(args[[1]], paste0(gsub(' ','-',family), '-',height,'.svg'))
    svglite::svglite(path, width=6, height=height, fix_text_size=TRUE)
    graphics::par(mar=c(0,0,0,0), family=family)
    graphics::plot.new(); graphics::plot.window(xlim=c(-.1,1.1),ylim=c(0,1))
    values <- seq(0,1,by=.2)
    graphics::text(values,.5,as.character(values))
    grDevices::dev.off()
  }
}
