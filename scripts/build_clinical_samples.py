"""Build the published clinical examples from their retained rows."""

import hashlib
import json
from pathlib import Path
from statistics import NormalDist
from typing import cast

from rc_metastudio.project.archive import JsonObject, load_project, save_project

SAMPLES = Path(__file__).resolve().parents[1] / "sample_projects"
METADAT = "metadat-clinical.json"
BARZA = "barza1996.json"


def sheet(index, name, family, subtype, metric, groups, studies, covariates=()):
    sheet_id = f"sheet:{index}"
    arms = [dict(id=f"{sheet_id}:arm:{i}", name=group) for i, group in enumerate(groups)]
    factors = [dict(id=f"{sheet_id}:cov:{i}", name=label, data_type=kind, stable_id=None)
               for i, (label, kind) in enumerate(covariates)]
    arm_ids = [arm["id"] for arm in arms]
    rows = []
    for i, (label, year, raw, values, notes, entered) in enumerate(studies):
        rows.append(dict(
            id=f"{sheet_id}:row:{i}", label=label, year=year, include=True,
            manually_excluded=False, sample_size=None, notes=notes,
            raw_data=dict(zip(arm_ids, raw, strict=True)),
            covariates={factor["id"]: value for factor, value in zip(factors, values, strict=True)},
            entered_effects=[dict(metric=metric, arms=arm_ids, values=entered)] if entered else [],
            ratio_inputs=[],
        ))
    return dict(
        id=sheet_id, name=name, family=family, sub_type=subtype,
        data_type={"binary": 0, "continuous": 1, "diagnostic": 2}[family],
        arms=arms, covariates=factors, rows=rows,
        settings=dict(metric=metric, arms=arm_ids, confidence_level=95.0),
    )


def project(kind, title, citation, doi, description, source, notes, sheets):
    path = SAMPLES / f"{kind} - {title}.rcms"
    document = dict(schema_version=3, title=title.rsplit(", ", 1)[0],
                    notes=f"{notes}\n\n{citation}\nhttps://doi.org/{doi}", sheets=sheets)
    state = dict(schema_version=3, current_sheet_id=sheets[0]["id"])
    save_project(path, cast(JsonObject, document), state)
    loaded = load_project(path)
    assert loaded.project == document and loaded.state == state
    canonical = json.dumps(document, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":"))
    return dict(file=path.name, scientific_name=path.stem, description="Use this for " + description,
                format_version=3, analysis_family=sheets[0]["family"],
                study_count=len(sheets[0]["rows"]), source_reference=citation,
                source_doi=f"https://doi.org/{doi}", source_file=f"sources/{source}",
                source_sha256=hashlib.sha256((SAMPLES / "sources" / source).read_bytes()).hexdigest(),
                sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                semantic_sha256=hashlib.sha256((canonical + "\n").encode()).hexdigest())


def build():
    data = json.loads((SAMPLES / "sources" / METADAT).read_text(encoding="utf-8"))["datasets"]
    bcg = [(r["author"], r["year"], [[r["tpos"], r["tpos"] + r["tneg"]],
                                    [r["cpos"], r["cpos"] + r["cneg"]]],
            [r["ablat"], r["alloc"].capitalize()], "", {}) for r in data["dat.bcg"]]
    yield project("Binary", "BCG vaccine and tuberculosis, Colditz 1994",
                  "Colditz GA, Brewer TF, Berkey CS, Wilson ME, Burdick E, Fineberg HV, Mosteller F. Efficacy of BCG vaccine in the prevention of tuberculosis: meta-analysis of the published literature. JAMA. 1994;271:698–702.",
                  "10.1001/jama.1994.03510330076038",
                  "two-arm event counts, latitude meta-regression and trial sequential analysis.", METADAT,
                  "The 13 trials compare BCG vaccination with unvaccinated controls. Latitude is absolute latitude in degrees.",
                  [sheet(0, "Tuberculosis", "binary", "proportions", "OR", ["BCG vaccine", "Unvaccinated control"],
                         bcg, [("Absolute latitude", 1), ("Allocation method", 4)])])

    barza = json.loads((SAMPLES / "sources" / BARZA).read_text(encoding="utf-8"))
    yield project("Binary", "Aminoglycoside dosing, Barza 1996",
                  "Barza M, Ioannidis JP, Cappelleri JC, Lau J. Single or multiple daily doses of aminoglycosides: a meta-analysis. BMJ. 1996;312:338–345.",
                  "10.1136/bmj.312.7027.338",
                  "Mantel–Haenszel and Peto with studies that have zero events in both arms.", BARZA,
                  "Table 2 reports clinical failure and nephrotoxicity separately. For clinical failure, denominators count episodes in trials that randomized more than one episode per patient.",
                  [sheet(i, title, "binary", "proportions", "OR", ["Single daily dose", "Multiple daily doses"],
                         [(r["study"], r["year"], r[key], [], "", {}) for r in barza["rows"]])
                   for i, (key, title) in enumerate((("failure", "Clinical failure"), ("nephrotoxicity", "Nephrotoxicity")))])

    poole = [(r["author"], r["year"], [[r["Ne"], r["Me"], r["Se"]], [r["Nc"], r["Mc"], r["Sc"]]],
              [r["duration"], r["year"]], "", {})
             for r in data["dat.poole2003"] if r["Se"] > 0 and r["Sc"] > 0]
    yield project("Continuous", "Monthly respiratory exacerbations, Poole 2003",
                  "Poole PJ, Black PN. Mucolytic agents for chronic bronchitis or chronic obstructive pulmonary disease. Cochrane Database Syst Rev. 2003;1:CD001287.",
                  "10.1002/14651858.CD001287",
                  "mean differences, trial-duration subgroups, meta-regression and small-study effects.", METADAT,
                  "The outcome is exacerbations per month. Two source studies with zero SD in both arms remain in the source table.",
                  [sheet(0, "Exacerbations per month", "continuous", "means", "MD", ["Mucolytic agent", "Placebo"],
                         poole, [("Trial duration", 4), ("Publication year", 1)])])

    kearon = []
    for r in data["dat.kearon1998"]:
        tp, np, tn, nn = (r[field] for field in ("tp", "np", "tn", "nn"))
        if None in (tp, np, tn, nn) or r["id"] in {20, 22, 30}:
            continue
        group = r["patients"].capitalize()
        label = r["study"]
        if label == "Mattos et al.":
            label = f"Mattos et al. ({group.lower()})"
        kearon.append((label, r["year"], [[tp, np - tp, nn - tn, tn]], [group, r["year"]],
                       f"metadat::dat.kearon1998, source row {r['id']}.", {}))
    assert len(kearon) == 27
    yield project("Diagnostic accuracy", "Ultrasound for deep vein thrombosis, Kearon 1998",
                  "Kearon C, Julian JA, Newman TE, Ginsberg JS. Noninvasive diagnosis of deep venous thrombosis. Ann Intern Med. 1998;128:663–677.",
                  "10.7326/0003-4819-128-8-199804150-00011",
                  "paired sensitivity and specificity, SROC, patient-group regression and Deeks’ test.", METADAT,
                  "Venous ultrasound is compared with contrast venography. The sheet keeps 16 symptomatic and 11 asymptomatic tables. Some source tables count limbs. Use the Patient group factor to compare groups or restrict Deeks to asymptomatic cohorts. See sources/README.md for omitted rows.",
                  [sheet(0, "Deep vein thrombosis", "diagnostic", None, "DOR", ["Venous ultrasound"],
                         kearon, [("Patient group", 4), ("Publication year", 1)])])

    reported = []
    for i, (subtype, name) in enumerate((("reg_coef", "Coefficient and confidence interval"),
                                         ("generic_effect", "Estimate and standard error"))):
        rows = []
        for r in data["dat.greenland1992"]:
            b, se = r["b"], r["SE"]
            margin = NormalDist().inv_cdf(.975) * se
            values = dict(est=b, lower=b - margin, upper=b + margin, SE=se,
                          display_est=b, display_lower=b - margin, display_upper=b + margin,
                          display_se=se, display_conf_level=95.0)
            note = "The 95% Wald bounds are derived from the published coefficient and SE."
            rows.append((r["author"], r["year"], [["", "", ""]], [], note if i == 0 else "", values))
        reported.append(sheet(i, name, "continuous", subtype, "Mean", ["Adjusted log risk ratio"], rows))
    yield project("Reported effects", "Alcohol intake and breast cancer, Greenland 1992",
                  "Greenland S, Longnecker MP. Methods for trend estimation from summarized dose-response data, with applications to meta-analysis. Am J Epidemiol. 1992;135:1301–1309.",
                  "10.1093/oxfordjournals.aje.a116237",
                  "pooling published coefficients with a confidence interval or a standard error.", METADAT,
                  "Both sheets use the adjusted log risk ratio per additional gram of alcohol per day from Table 3. Analyze the sheets separately.",
                  reported)

    feng = [(r["author"], r["year"], [[r["depr"], r["n"]]], [r["design"]],
             f"Assessment: {r.get('questionnaire') or r.get('interview')}. Timing: {r['timing']}.", {})
            for r in data["dat.feng2019"] if r["design"] != "RCT"]
    yield project("Single-arm proportion", "Depression after myocardial infarction, Feng 2019",
                  "Feng L, Li L, Liu W, Yang J, Wang Q, Shi L, Luo M. Prevalence of depression in myocardial infarction: A PRISMA-compliant meta-analysis. Medicine. 2019;98:e14596.",
                  "10.1097/MD.0000000000014596",
                  "pooling a prevalence from cases and totals and comparing proportion transformations.", METADAT,
                  "Includes 16 observational cohorts. Definitions and assessment times differ. The retained source table also records the three randomized studies.",
                  [sheet(0, "Depression after myocardial infarction", "binary", "proportion", "PR",
                         ["Patients after myocardial infarction"], feng, [("Study design", 4)])])


def update_manifest(additions):
    path = SAMPLES / "manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    entries = {item["file"]: item for item in manifest["projects"]}
    for item in additions:
        entries[item["file"]] = item
        print(f"Built {item['file']} ({item['study_count']} rows)")
    entries = {name: item for name, item in entries.items() if (SAMPLES / name).is_file()}
    manifest["projects"] = sorted(entries.values(), key=lambda item: item["file"].split(" - ", 1)[0].casefold())
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    update_manifest(build())
