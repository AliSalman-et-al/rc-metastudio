# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Application and organization identity."""

from rc_metastudio import __version__


APPLICATION_NAME = "RCMetaStudio"


APPLICATION_DISPLAY_NAME = "RC MetaStudio"


ORGANIZATION_NAME = "Research Consultancy"


ORGANIZATION_DOMAIN = "rcmetastudio.org"


VERSION = __version__

CITATION_TITLE = "RC MetaStudio: open-source desktop software for meta-analysis"
CITATION_DOI = "10.5281/zenodo.23118556"
CITATION_AUTHORS = (
    "Salman, Ali", "Fatima, Kaneez", "Khan, Muhammad Shahzeb",
    "Siddiqi, Tariq Jamal", "Usman, Muhammad Shariq",
)

CITATION_YEAR = '2026'
CITATION_URL = 'https://doi.org/' + CITATION_DOI


def citation_text() -> str:
    return f"{'; '.join(CITATION_AUTHORS)} ({CITATION_YEAR}). {CITATION_TITLE} (Version {VERSION}). Zenodo. {CITATION_URL}"
