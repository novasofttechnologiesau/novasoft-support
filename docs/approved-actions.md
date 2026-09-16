# Actions in the community preview

| Action | v0.1.0 behavior |
| --- | --- |
| `escalate_ticket` | Implemented on the server; moves an owned ticket to waiting for a technician |
| Restart Print Spooler / flush DNS / restart OneDrive | Disabled; no native implementations or bridge registrations shipped |
| Collect diagnostic actions in the registry | Disabled as action runs; use the consent-based Diagnostics screen instead |
| All other registry entries | Design placeholders; disabled and rejected if requested |

The registry describes potential future actions. It is not a claim they are supported.
The server checks implementation availability as well as enabled state and role permissions.
Any future repair release needs native authorization, local user confirmation and Windows
hardware tests. Approval flags in a JavaScript UI alone are not an adequate boundary.

There is no arbitrary command endpoint, remote shell, unattended repair or automatic AI execution.
