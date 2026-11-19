for (name in c("forest.rma", "forest.default")) {
    cat(name, "\n")
    cat(grep("shade|rect", deparse(body(getFromNamespace(name, "metafor"))), value=TRUE), sep="\n")
}
