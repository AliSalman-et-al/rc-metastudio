# Public R boundaries not reachable through the paired-limit GUI controls.
r02.path <- function(name) {
  root <- Sys.getenv("RCMS_RENDERING_EVIDENCE", unset=tempdir())
  dir.create(root, recursive=TRUE, showWarnings=FALSE)
  file.path(root, name)
}
r02.fixture <- function(style="revman") {
  d <- new("BinaryData", g1O1=c(4,6,3,62,33,180), g1O2=c(119,300,228,13536,5036,1361),
    g2O1=c(11,29,11,248,47,372), g2O2=c(128,274,209,12619,5761,1079),
    study.names=paste("Study", 1:6), years=as.integer(2001:2006),
    covariates=list(new("CovariateValues", cov.name="latitude", cov.vals=c(44,55,42,52,13,19), cov.type="continuous", ref.var="44")))
  p <- list(conf.level=95, digits=3, measure="OR", rm.method="DL", adjust=.5, to="only0",
    fp_style=style, fp_col1_str="Study", fp_col2_str="[default]", fp_col3_str="Treatment", fp_col4_str="Control",
    fp_plot_lb="[default]", fp_plot_ub="[default]", fp_xticks="[default]", fp_xlabel="[default]",
    fp_show_col1=TRUE, fp_show_col2=TRUE, fp_show_col3=TRUE, fp_show_col4=TRUE,
    fp_show_summary_line=TRUE, create.plot=FALSE, write.to.file=FALSE, cov_name="latitude")
  d <- rcmetar.prepare.analysis.data(d,p)
  list(data=d, params=p, res=metafor::rma.uni(d@y, sei=d@SE, method="DL"))
}
r02.text <- function(path) xml2::xml_text(xml2::xml_find_all(xml2::read_xml(path), "//*[local-name()='text']"))

test_that("G1B-001 partial bubble limits preserve the automatic counterpart", {
  b <- list(params=list(), moderator=list(values=c(10,20,30)))
  auto <- rcmetar.bubble.xlim(b)
  b$params$bp_plot_lb <- 0
  expect_equal(rcmetar.bubble.xlim(b), c(0, auto[2]))
  b$params <- list(bp_plot_ub=40)
  expect_equal(rcmetar.bubble.xlim(b), c(auto[1],40))
})
test_that("G1B-002 initial regression renders its configured label", {
  f <- r02.fixture()
  f$params$bp_xlabel <- "Custom initial latitude"
  f$params$bp_outpath <- r02.path("initial.svg")
  rcmetar.run.analysis(f$data, list(version=1, method="meta.regression", params=f$params, workflow="meta-regression"))
  expect_true("Custom initial latitude" %in% r02.text(f$params$bp_outpath))
})
test_that("G1B-004 clipped BMJ intervals draw outward continuation geometry", {
  path <- r02.path("clipped.svg")
  rcmetar.render.plot_svg(path,list(width=4,height=3),function() {
    graphics::par(mar=c(0,0,0,0))
    graphics::plot.new(); graphics::plot.window(xlim=c(0,1),ylim=c(0,5),xaxs="i",yaxs="i")
    rcmetar.draw.bmj.effects(list(yi=rep(.5,4),ci.lb=c(-1,.2,-1,.2),ci.ub=c(.8,2,2,.8)),
      1:4,c(0,1),"#123456",rep(1,4))
  })
  doc <- xml2::read_xml(path)
  lines <- xml2::xml_find_all(doc,"//*[local-name()='polyline']")
  points <- strsplit(xml2::xml_attr(lines,"points"),"[ ,]+")
  heads <- Filter(function(v) length(v)==6, points)
  expect_length(heads,4)
  if(length(heads)==4) {
    coords <- lapply(heads,as.numeric)
    expect_equal(sum(vapply(coords,function(v) v[3]<v[1] && v[3]<v[5],logical(1))),2)
    expect_equal(sum(vapply(coords,function(v) v[3]>v[1] && v[3]>v[5],logical(1))),2)
  }
})
test_that("G1B-005 pooled study sizes follow multiplier in both styles", {
  for(style in c("bmj","revman")) {
    f <- r02.fixture(style)
    b <- rcmetar.regenerate.plot.data(f$data,f$res,f$params)
    base <- get(paste0("rcmetar.",style,".summary.effect"))(b)$psize
    b$params$fp_point_size_multiplier <- 2
    expect_equal(get(paste0("rcmetar.",style,".summary.effect"))(b)$psize,2*base)
    widths <- list()
    for (mult in 1:2) {
      b$params$fp_point_size_multiplier <- mult
      path <- r02.path(paste0("markers-",style,"-",mult,".svg"))
      rcmetar.draw.forest.plot(b,path)
      doc <- xml2::read_xml(path)
      nodes <- xml2::xml_find_all(doc,"//*[local-name()='polygon']")
      widths[[mult]] <- vapply(strsplit(trimws(xml2::xml_attr(nodes,"points")),"[ ,]+"),
        function(v) diff(range(as.numeric(v)[seq(1,length(v),2)])), numeric(1))
    }
    expect_equal(length(widths[[1]]),length(widths[[2]]))
    expect_gte(sum(abs(widths[[2]]/widths[[1]] - 2) < .03),6)
  }
})
test_that("G1B-006 disabled RevMan annotations omit study and pooled estimates", {
  f <- r02.fixture()
  texts <- list()
  for(show in c(TRUE,FALSE)) {
    f$params$fp_show_col2 <- show
    b <- rcmetar.regenerate.plot.data(f$data,f$res,f$params)
    path <- r02.path(paste0("annotations-",show,".svg"))
    rcmetar.draw.forest.plot(b,path)
    texts[[as.character(show)]] <- r02.text(path)
  }
  estimates <- grep("^[0-9.]+ \\[.*[,].*\\]$",texts[["TRUE"]],value=TRUE)
  expect_gte(length(estimates),7)
  expect_false(any(estimates %in% texts[["FALSE"]]))
  expect_lt(sum(texts[["FALSE"]]=="Odds ratio"),sum(texts[["TRUE"]]=="Odds ratio"))
})
test_that("G1B-007 raw IRR arms independently follow visibility", {
  d <- new("RatioData",metric="IRR",study.names=c("A","B"),x1=c(3,4),x2=c(5,6),t1=c(100,200),t2=c(150,250),unit=rep("years",2))
  for(a in c(TRUE,FALSE)) for(b in c(TRUE,FALSE)) {
    cols <- rcmetar.revman.ilab.for.data(d,list(fp_show_col3=a,fp_show_col4=b))
    keys <- vapply(cols$columns,function(x) x$key,character(1))
    expect_equal("events1" %in% keys,a)
    expect_equal("person_time1" %in% keys,a)
    expect_equal("events2" %in% keys,b)
    expect_equal("person_time2" %in% keys,b)
  }
})
test_that("G1B-008 permutation regression matches the selected public authority", {
  d <- data.frame(yi=c(.2,.4,.1,.8,.5,1.1),vi=c(.03,.05,.06,.04,.07,.08),x=c(1,2,4,3,5,6),slab=letters[1:6])
  mods <- list(numeric="x",categorical=character(),interactions=list())
  for(intercept in c(FALSE,TRUE)) for(knha in c(FALSE,TRUE)) {
    ref <- metafor::rma.uni(yi,vi,mods=~x,intercept=intercept,test=if(knha) "knha" else "z",data=d,method="DL",digits=4)
    set.seed(71); expected <- metafor::permutest(ref,iter=99,digits=4)
    set.seed(71); actual <- permuted.meta.reg(d,"DL",mods,intercept=intercept,knha=knha,iter=99,retpermdist=TRUE,digits=4)
    for(field in c("beta","se","pval","QMp","zval.perm","QM.perm")) expect_equal(actual$res[[field]],expected[[field]],info=field)
    expect_match(actual[["Standard Meta Regression Summary"]],paste(capture.output(ref),collapse="\n"),fixed=TRUE)
    if (!intercept) expect_match(actual[["Standard Meta Regression Summary"]],"yi ~ x - 1",fixed=TRUE)
  }
})
test_that("G1B-009 MA exposes the requested permutation distribution", {
  d <- data.frame(yi=c(.2,.4,.1,.8,.5,1.1),vi=rep(.05,6),slab=letters[1:6])
  set.seed(71); ref <- metafor::permutest(metafor::rma.uni(yi,vi,data=d,method="DL"),iter=99)
  set.seed(71); actual <- permuted.ma(d,"DL",iter=99,retpermdist=TRUE)
  expect_gt(length(actual$res$zval.perm),0)
  expect_equal(actual$res$zval.perm,ref$zval.perm)
  expect_true("zval.perm" %in% names(actual$res.info))
  expect_null(permuted.ma(d,"DL",iter=99)$res$zval.perm)
})
test_that("G1B-010 separate display preserves publication PNG dimensions", {
  path <- r02.path("large.png")
  rcmetar.render.plot_file(path,list(width=20,height=10,dpi=600),function() {
    graphics::plot.new(); graphics::text(.5,.5,"Publication")
  },display.path=r02.path("large-display.svg"))
  bytes <- as.integer(readBin(path,"raw",n=24))
  expect_equal(sum(bytes[17:20]*256^(3:0)),12000)
  expect_equal(sum(bytes[21:24]*256^(3:0)),6000)
})
test_that("G1B-011 mixed SVG encoding matches each destination", {
  for(ext in c("svg","svgz")) {
    out <- r02.path(paste0("mixed-out.",ext))
    display <- r02.path(paste0("mixed-display.",if(ext=="svg") "svgz" else "svg"))
    rcmetar.render.plot_file(out,list(width=3,height=2),function() {
      graphics::plot.new(); graphics::text(.5,.5,"Encoding \u03c4 sentinel")
    },display.path=display)
    for(path in c(out,display)) {
      magic <- as.integer(readBin(path,"raw",n=2))
      expect_equal(identical(magic,c(31L,139L)),endsWith(path,"svgz"))
      con <- gzfile(path,"rb"); bytes <- readBin(con,"raw",n=1000000); close(con)
      expect_true("Encoding \u03c4 sentinel" %in% xml2::xml_text(xml2::xml_find_all(xml2::read_xml(bytes),"//*[local-name()='text']")))
    }
  }
})

