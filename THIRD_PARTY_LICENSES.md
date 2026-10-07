# Third-party licences — aicowork-tools 0.0.1

_Read from each installed package's own metadata (`License-Expression`, classifiers) on 2026-10-01, versions as locked in `98_tools/uv.lock`. The kernel (`99_system/`) contains no third-party code._

## Shipped with the tools (runtime)

| Package                                                                                    | Version | Licence (as declared)                                           | Why                           |
| ------------------------------------------------------------------------------------------ | ------- | --------------------------------------------------------------- | ----------------------------- |
| fastapi                                                                                    | 0.141.1 | MIT                                                             | viewer web app                |
| starlette                                                                                  | 1.6.0   | BSD-3-Clause                                                    | fastapi dependency            |
| uvicorn                                                                                    | 0.52.4  | BSD-3-Clause                                                    | viewer server (loopback only) |
| markdown                                                                                   | 3.10.3  | BSD-3-Clause                                                    | Markdown → HTML in the viewer |
| pydantic                                                                                   | 2.13.4  | MIT                                                             | fastapi dependency            |
| pydantic_core                                                                              | 2.46.4  | MIT                                                             | pydantic dependency           |
| anyio                                                                                      | 4.14.2  | MIT                                                             | starlette dependency          |
| h11                                                                                        | 0.16.0  | MIT                                                             | uvicorn dependency            |
| click                                                                                      | 8.4.2   | BSD-3-Clause                                                    | uvicorn dependency            |
| colorama                                                                                   | 0.4.6   | BSD (classifier)                                                | click dependency on Windows   |
| idna                                                                                       | 3.19    | BSD-3-Clause                                                    | anyio dependency              |
| annotated-types                                                                            | 0.8.0   | MIT                                                             | pydantic dependency           |
| annotated-doc                                                                              | 0.0.5   | MIT                                                             | fastapi dependency            |
| typing-inspection                                                                          | 0.4.4   | MIT                                                             | pydantic dependency           |
| typing_extensions                                                                          | 4.16.0  | PSF-2.0                                                         | several                       |
| **ECharts** (vendored, `98_tools/apps/viewer/src/viewer/web/vendor/echarts.common.min.js`) | 5.6.1   | **Apache-2.0** — licence header kept in the file; see NOTICE.md | energy chart                  |

## Development only (tests; not needed to run anything)

| Package   | Version   | Licence                                                       |
| --------- | --------- | ------------------------------------------------------------- |
| pytest    | 9.1.1     | MIT                                                           |
| pluggy    | 1.6.0     | MIT                                                           |
| iniconfig | 2.3.0     | MIT                                                           |
| packaging | 26.3      | Apache-2.0 OR BSD-2-Clause                                    |
| pygments  | 2.21.0    | BSD-2-Clause                                                  |
| httpx     | 0.28.1    | BSD-3-Clause                                                  |
| httpcore  | 1.0.9     | BSD-3-Clause                                                  |
| certifi   | 2026.7.22 | MPL-2.0 (unmodified, not redistributed in the tools artifact) |

The stdlib-only commands (`python -m aicowork …` except `viz`) need none of the above.
Regenerate this table and the SBOM (`aicowork sbom`) whenever `uv.lock` changes.
