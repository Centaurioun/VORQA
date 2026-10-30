# Security policy

**Status:** pre-release repository foundation. No production version is supported or certified.

## Reporting

Do not post exploit details or credentials in public issues. Use GitHub private vulnerability reporting if enabled; otherwise request a secure private contact route from the maintainer without disclosing sensitive details publicly.

## Threat model

Agent rules and host hooks are not OS sandboxes. Shared-user processes can potentially access the same credentials, signing keys and files. A local HMAC signature does not establish independent human identity, and a review flag does not establish reviewer independence. Browser access requires real network/filesystem containment.

No production data, real financial transactions or production credentials should be supplied until the concrete deployment's isolation and approval controls have been independently verified.
