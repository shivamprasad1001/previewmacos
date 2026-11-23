# Code Signing Policy

This project plans to use free code signing provided by the SignPath Foundation. This document describes the project's code signing policy, roles, privacy statement, and build provenance in compliance with the SignPath Foundation conditions.

---

## 1. Attribution

As required by the [SignPath Foundation conditions for Open Source projects](https://signpath.org/terms):

> "Free code signing provided by SignPath.io, certificate by SignPath Foundation"

---

## 2. Project Roles and Transparency

Per the SignPath Foundation terms, project roles and responsibilities are assigned as follows:

* **Project Repository:** [https://github.com/shivamprasad1001/previewmacos](https://github.com/shivamprasad1001/previewmacos)
* **Author / Committer:** Shivam Prasad ([@shivamprasad1001](https://github.com/shivamprasad1001))
* **Reviewer:** Shivam Prasad ([@shivamprasad1001](https://github.com/shivamprasad1001))
* **Approver:** Shivam Prasad ([@shivamprasad1001](https://github.com/shivamprasad1001))

Any code changes submitted via pull requests from outside contributors must be reviewed by the maintainer before merging. Signing requests must be approved by the designated approver.

---

## 3. Current Signing Status and Future Trusted Build System

* **Current Status (Today):** Releases are currently not code-signed. Installers are distributed unsigned alongside SHA-256 checksums on GitHub Releases.
* **Planned Workflow Integration:** Once SignPath Foundation approval is granted and repository credentials are configured, the signing step will be integrated into `.github/workflows/build_releases.yml`.
* **Tag Restriction:** Once added, automated code signing requests will be strictly restricted to official release tags matching `refs/tags/v*` on the main branch.
* **Build Provenance:** All binaries will be compiled exclusively on official GitHub-hosted runners using GitHub Actions as a Trusted Build System ([SignPath GitHub Actions Documentation](https://docs.signpath.io/trusted-build-systems/github)). Local developer builds will never be submitted for signing.

---

## 4. Privacy Statement and Network Communication

Per the SignPath Foundation terms:

> "This program will not transfer any information to other networked systems unless specifically requested by the user or the person installing or operating it."

The application handles network communication strictly as follows:
* **No Telemetry or User Data Collection:** The application does not collect, track, or transmit any user documents, personal data, or telemetry.
* **Software Update Checks:** The application checks the public GitHub REST API (`https://api.github.com/repos/shivamprasad1001/previewmacos/releases/latest`) to determine whether a newer version is available. Users can also manually trigger this check from the Help menu. No personal or document data is transmitted during update checks.
* **Third-Party Services:** Update requests communicate directly with GitHub's public API and are subject to [GitHub's Privacy Statement](https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement).

---

## 5. Technical and Licensing Compliance

* **OSI-Approved License:** The project is open source under the [MIT License](LICENSE).
* **No Proprietary Code:** The repository contains no closed-source components or commercial dual-licensing.
* **No Malware:** Binaries are compiled directly from source and are free of malware, adware, or potentially unwanted programs.
