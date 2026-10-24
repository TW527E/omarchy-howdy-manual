# Validation for v0.1.0

Checked on 2026-10-24 with Omarchy 4.0.6, Quickshell 0.3.2.r7.g2b4501a and Howdy Next 3.4.2 on Arch Linux.

## Automated checks

- `make test`: 16 PAM stack scenarios, 10 Python installer/lifecycle tests, and JavaScript assertions for prompt matching, empty-input rejection, busy states and language selection.
- PAM scenarios cover explicit face choice, password token preservation, cancellation, a null conversation response, and rejection when the selected authentication backend fails.
- Setup tests cover supported Howdy options, adoption of the original local prototype, rejection of unknown/custom authentication branches, atomic writes, install/remove round trips, preservation of pre-existing modules, rejection of later edits, and rollback after injected write failures.
- `omarchy plugin validate .`: passes on the installed shell.
- Qt 6 `qmllint` parses the QML with resolved shell imports. It reports tooling warnings for Quickshell's runtime-created PanelWindow and the host's dynamically typed theme properties. Native shell loading is the authoritative runtime check; this is not a claim of zero lint warnings.

Tests never use real passwords, a camera, or the host's active PAM files. Lifecycle tests redirect every system path into a temporary directory.

## Native rendering

The actual `PromptView.qml` was rendered by the existing Omarchy shell, not an HTML recreation and not a second production Quickshell process. A temporary, local-only preview capture handler saved the component itself; it is absent from the published plugin. The public images contain only deliberately labelled sample requests.

Inspected the final English ready state at 480 logical pixels, Traditional Chinese ready state at 358 pixels, scanning at 400 pixels, and failure at 358 pixels. Text wraps, controls fit, buttons retain at least 44 logical pixels of height, and the request remains above the authentication controls. Long request text scrolls; the live dialog also has an outer scroll area for small displays.

The taste-skill browser inspector and source lint do not support native QML. Native renders and Omarchy validation were used instead; no browser score or DOM measurements are claimed.

### Design critique

ROUND 3

Seen in one second: an authorization request with an explicit face button.

Idea (one sentence): keep the requested action above every way to approve it, with a visible camera consent step.

Live thing: the real Polkit response flow, plus a clearly labelled preview that does not authenticate.

Layout words by section: request=left-aligned text / face=full-width action / password=label and field / actions=cancel and submit.

Scores: design 8 · usability 8 · creativity 6 · content 9 → overall 7.7. This is a subjective native-interface critique, not an automated web score.

Caps applied: the layout intentionally follows a familiar authorization dialog; originality is not the goal. Marketing-page image and motion quotas do not apply to a native authentication component.

Top three problems addressed:

1. The first English render had low contrast on the hovered face button. Using the host's selected-button treatment preserves readable foreground colors across its states.
2. The initial component inherited a monospace face and small action labels. A system sans face, a CJK preference, and 14-pixel minimum action text improved readability.
3. The first error render inherited a low-contrast red from the theme. The final error is a clear bold message in the normal foreground; status is communicated in words.

No stock photography, generated images, animations, analytics, web server, or extra UI dependency was added. Colors, borders and button behavior use Omarchy's own components.

## Scope of manual checks

The original companion module and explicit Polkit button were confirmed by the user on real hardware before packaging. The terminal sudo prompt was also observed waiting with no Howdy comparison process, then cancelled successfully. The packaged dialog was registered in the running shell and its native preview was inspected. A subsequent request to adopt the existing PAM setup into the new installer was dismissed, so the previous working PAM configuration was left intact; a privileged install/remove round trip for this packaging was not performed on the host. Its lifecycle was exercised only in isolated tests.

Password-success, reboot/login, alternate Polkit agents, alternate themes and other machines are not comprehensively tested. This release targets the exact compatibility baseline documented above; it is not an independent security audit of PAM, Howdy or the shared desktop shell.
