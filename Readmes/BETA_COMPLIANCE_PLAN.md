# FoodBot — Adult Private Beta Privacy and Launch Checklist

**Prepared:** 2 November 2026.  
**Confirmed scope:** Russia-based operator; primarily adult users in Russia; free private beta; Russian hosting provider.  
**Purpose:** A practical, source-backed planning document and implementation backlog. This is not a legal opinion, a compliance certification, or a guarantee against claims. A closed/free beta does not by itself establish an exemption.

## 1. The immediate issue for this bot

FoodBot links a Telegram identity to pain, medications, mood and other diary information. Treat the symptom/medication records as health-related personal data. An ordinary consent checkbox must not be assumed sufficient for this category: the health-data consent route in Article 10 requires written consent, and Article 9 addresses signed electronic equivalents and prescribed consent contents. Have a Russian privacy lawyer validate a workable method before collecting other people's real health records. Do not add passport uploads to Telegram as a DIY fix. [152-FZ, Articles 9–10, official government text](https://mintrud.gov.ru/docs/laws/130); [current Article 9](https://www.consultant.ru/document/cons_doc_LAW_61801/6c94959bc017ac80140621762d2ac59f6006b08c/); [current Article 10](https://www.consultant.ru/document/cons_doc_LAW_61801/26edb2934b899bf9c74c3a8f7e574651c6565e6d/)

Build and exercise the controls below with synthetic records while this is settled. A timestamped Telegram click is useful evidence of a UI choice; it is not automatically a legally sufficient written health-data consent or electronic signature.

Russian hosting addresses the location of your own application database only when the actual storage, backups and processing arrangements meet the applicable rules. Telegram is also part of the data flow. Its cloud handling needs a separate localization/cross-border assessment; do not claim that putting SQLite in Russia makes the entire service compliant. [Article 18(5)](https://www.consultant.ru/document/cons_doc_LAW_61801/cbf4e15b7c330f9372e876cdf2bc928bad7950ef/), [Article 12](https://www.consultant.ru/document/cons_doc_LAW_61801/e4ebbe1780de623c7cf32a59ca82a7bb523a25dd/), [Telegram message storage](https://telegram.org/privacy#3-3-your-messages)

## 2. All 20 items in the supplied image

These mix legal duties, platform terms, commercial policies and good design. “Now” below is a priority for this release, not a claim that every item is universally mandated by law.

| # | Item in the image | Priority for FoodBot | Practical action |
| --- | --- | --- | --- |
| 1 | Privacy policy | Critical now | Publish an accurate policy, accessible before onboarding and through `/privacy`; configure the policy in BotFather. |
| 2 | Terms of service | Useful now | Short rules for an adults-only, free beta: operator, purpose, support, availability, changes and limits. Do not claim a template removes statutory rights. |
| 3 | Refund policy | Before charging | No payments in this beta. State that clearly; design purchase/cancellation/refund rules if charging later. |
| 4 | Cookie policy | Not presently applicable | The inspected product is a native Telegram bot, not your own cookie-using website/Mini App. Reassess if one is added. |
| 5 | Cookie consent banner | Not presently applicable | Do not add a fake banner to chat. Assess any later website's actual cookies, audience and applicable rules. |
| 6 | Check form consents | Critical now | Separate privacy information, terms acknowledgement, health-data authorization and optional reminders. Validate health-consent form, not merely the button. |
| 7 | No unnecessary data | Critical now | Remove mandatory gender/birth-year questions unless a documented need justifies them. Make nickname optional. Use an adult eligibility check rather than collecting a full birth date by default. |
| 8 | Audit third-party SDKs | Now | Inventory Telegram, hosting/backups/logging, direct and transitive packages, analytics and future AI services. Record who receives which data. |
| 9 | Remove dark patterns | Now | Clear decline, pause, stop-reminders and deletion paths. No preselected optional consent or misleading “Cancel” behavior. |
| 10 | Remove hidden fees | Maintain now | No fees in the beta. If that changes, disclose pricing and obtain a fresh purchase decision. |
| 11 | Remove fake reviews | Maintain now | Do not fabricate testimonials, doctor endorsements or user counts. |
| 12 | Remove unsupported claims | Critical now | Describe recording and descriptive statistics. Avoid unproven treatment, diagnosis or guaranteed sleep-improvement claims. |
| 13 | Accessibility alt text | Improve now | All essential onboarding instructions must be text; add meaningful image captions/descriptions. |
| 14 | Fix color contrast | Improve what you control | Telegram controls much native styling. Never make a color/emoji the only way to understand a result. |
| 15 | Keyboard navigation | Improve what you control | Clear command names and button text; exercise desktop keyboard/screen-reader paths. Do not claim full accessibility certification without checking it. |
| 16 | Add business details | Critical now | Identify the actual operator and privacy/support contact. Use your real legal status; do not invent a company. Include legally required operator details in documents. |
| 17 | Age consent for kids' data | Exclude minors for this beta | Adults-only eligibility and invitations. An “18+” button is a declaration, not verified age or a complete minors-compliance solution. |
| 18 | Unsubscribe link in emails | No email feature; adapt now | Add `/stop` for Telegram reminders and an explicit re-enable control. Reassess unsubscribe requirements if email/marketing is introduced. |
| 19 | License fonts/images | Now | Establish provenance/permission for assets in `Images` and required notices for reused code/packages. Replace assets with unclear rights. |
| 20 | Data deletion requests | Critical now | `/delete_me` plus a contact route; delete across all relevant stores, address backups, and explain Telegram-message limits. |

Telegram requires an accessible privacy policy, necessary-data handling, deletion handling and security safeguards. Its developer terms also expressly require encryption at rest with the key stored separately. These obligations are independent of whether users pay. [Telegram Bot Developer Terms, sections 4–4.4](https://telegram.org/tos/bot-developers#4-privacy)

## 3. Findings from the inspected code

Inspection was read-only. `Archive`, `.env`, personal database rows and hosting configuration were excluded.

- The current command list includes diary, calendar, meals, statistics and settings; no dedicated privacy/terms/consent/full-account-deletion controls were found in the reviewed active modules.
- Setup currently requests language, nickname, gender, birth year, UTC offset and reminder choices. Birth year accepts a wide range and does not implement an adults-only gate.
- The application stores data in `data/calendar.sqlite3` using standard `aiosqlite`. No application database encryption layer was visible. This does **not** establish whether the future host's disk/backups are encrypted.
- Six current tables are relevant to deletion: `calendar_answers`, `day_ratings`, `user_profiles`, `diary_entries`, `day_medications`, and `meals`.
- `reminders_enabled` already exists and `disable_reminders()` already disables it. However, profile creation/update on `/start` can re-enable reminders; a durable user opt-out must not be undone that way.
- The dependency file lists aiogram, python-dotenv and aiosqlite. No analytics/AI integration appeared in the reviewed files; transitive dependencies and provider services have not been comprehensively audited.
- `Images` contains onboarding/profile assets whose licensing was not established by this inspection.
- The calendar currently classifies days using five preset conditions. Present these as tracking targets, not as proof of health, a diagnosis or clinically validated thresholds.

## 4. What to implement now

### A. Public information and a real contact route

Provide `/privacy`, `/terms`, `/contact`, and a short privacy link in `/help` and onboarding. These must work without completing a profile or entering health information. Provide Russian-language information for this initial Russian audience; English can be supplementary.

The privacy policy needs actual facts, not placeholders presented as a finished policy:

- The operator's identity/status and a working rights-request contact.
- Collected categories: Telegram IDs/chat routing data, settings, diary symptoms/medicines/notes, meal records, and necessary security metadata.
- Each purpose and its legal basis, including the separate basis/form for health data.
- Hosting/storage location and the actual service providers/data recipients; explain Telegram's role and relevant transfers accurately.
- Which fields are optional; how declining health processing affects the available service.
- Actual retention and backup-deletion arrangements, access/correction/withdrawal/deletion routes, and response handling.
- A truthful security description and policy version/date. Do not claim “anonymous,” “end-to-end encrypted bot chat,” or “only you can access it” without a matching implementation.

Configure the custom policy in BotFather as well as the bot command. A Telegram default policy is not a substitute for checking that your health-data practices are accurately covered. [Telegram policy requirements](https://telegram.org/tos/bot-developers#4-privacy)

Do not publish draft documents with an invented operator name, address, provider, retention period, or compliance claim.

### B. Eligibility and data minimization

Before profile/diary collection, show a concise free-beta explanation and adult eligibility choice. For this small beta, use an invitation allowlist as an additional audience restriction; it does not replace lawful processing.

Make gender and birth year optional or remove them from onboarding for the current features. Make nickname optional or use a neutral greeting. Keep only identifiers necessary to separate users and deliver the requested service. A nickname or hashed Telegram ID does not by itself make health records anonymous.

An age declaration is a pragmatic eligibility control for an adults-only beta, not proof of age. If a known minor attempts access, do not collect their diary. Review the process separately before ever admitting minors.

### C. Separate consent choices and enforce them

Use separate screens/actions for terms acknowledgement, personal-data consent where relied on, legally validated health-data consent, and optional reminders. Keep them distinct from merely opening the privacy notice. The separate-consent requirement has applied since September 2025. [Prosecutor's Office explanation](https://epp.genproc.gov.ru/ru/proc_39/activity/legal-education/explain/protecting_rights_entrepreneurs/e5874598/)

Suggested initial sequence:

```text
Free private beta information + operator/contact + Privacy / Terms links
    → adult eligibility
    → separate necessary account-data authorization, where relied on
    → legally validated health-data authorization
    → minimal profile settings
    → optional reminders, default off
    → diary
```

Do not mark health authorization valid merely because a user pressed “I agree.” The UI can initially keep health features pending while an appropriately signed consent process is put in place. Use a Russian-lawyer-reviewed paper/electronic process suitable for the beta; do not create a passport-collection flow in bot chat.

Enforce authorization in ordinary shared guard functions before **every** health read/write entry point, including `/meal`, `/makenote`, old callback buttons and free-text handlers. Update existing users too; `/start` is not the only entry point. Do not log or echo unsolicited health text before the relevant authorization is established. Keep privacy/rights/support routes accessible.

Store evidence sufficient for the chosen process: purpose, document version/hash, exact archived text or document reference, method, time, verified signature-evidence reference where required, and revocation time. A UI click log supports evidence; it does not create signature validity.

### D. Stop reminders, withdraw consent, and delete data

| Control | Required behavior |
| --- | --- |
| `/stop` | Disable optional reminders persistently. `/start`, settings changes, time-zone changes and restarts must not undo that opt-out. Diary use can remain available if otherwise authorized. |
| Reminders setting | Explicitly enable reminders again. No marketing permission is inferred. |
| `/withdraw` | Explain the scope; stop the affected consent-based processing and reminders, then initiate the applicable erasure/retention procedure. Keep rights/support requests available. |
| `/delete_me` | Show a clear confirmation/cancel step. Authenticate from Telegram's actual sender ID; do not accept an arbitrary target user ID from a command/callback. |
| `/mydata` or contact request | Provide access to the user's own records through an implemented download or a documented manual process. A ready-made XLSX exporter is not necessary for the first privacy release. |

For full deletion, stop pending writes/reminders, clear the user's FSM state, then remove their health/profile/meal/legacy rows transactionally in a safe child-before-parent order. Include any tables subsequently introduced, temporary exports and relevant application/provider logs. Review minimal evidence that has a separate lawful retention basis rather than deleting or retaining it indiscriminately.

Handle deletion against the reminder loop too: it runs outside the ordinary dialogue. An in-flight reminder or old button must not recreate the profile/diary or restart messages after deletion. Make repeated deletion requests safe.

Define a workable encrypted-backup rotation and erasure/restore process. Restoring a backup must not silently resurrect erased users; maintain only the restricted deletion metadata justified for this purpose. A proposed beta operational target is immediate active-store erasure and no more than seven days of rolling backup retention, but adopt/publish it only after the host and applicable erasure duties are checked. Do not promise instantaneous erasure from every backup.

Explain that FoodBot-controlled storage deletion and Telegram chat-history deletion are different. The bot cannot promise removal of every Telegram-held message or a file the user downloaded. Tell users how to clear their Telegram history; attempt bot-owned message cleanup only where supported. [Telegram privacy policy](https://telegram.org/privacy#10-2-messages)

### E. Hosting and security controls

Before real beta data:

- Confirm actual Russian data-center, database, backup, logging and support-access arrangements—not just the provider's company address.
- Ask for appropriate processing/security terms and the included safeguards. Your provider does not automatically certify your application.
- Arrange encryption at rest for active storage and backups, with separate key management; verify restore works. Standard SQLite alone supplies no encryption-at-rest guarantee. Use established provider/OS/database tooling, not home-grown cryptography.
- Keep the SQLite file outside public web paths, restrict access to the bot's service account, restrict administrative access and protect administrative accounts.
- Keep tokens and data outside Git; do not send production databases or real diary examples to coding agents, error trackers or support channels.
- Limit logs to necessary metadata. Scrub tokens, symptom text, notes and medication details from exceptions and request traces.
- Use synthetic records for tests and check two-user isolation, authenticated callbacks and read-only view/export paths.
- Record dependency and service inventory, including transitive packages and provider defaults. Review licences and obtain permission for every image you ship.
- Have the applicable Russian information-security requirements assessed for this particular health-data system; generic encryption and passwords alone are not a complete legal assessment.

### F. Accurate product claims and accessible screens

Suggested descriptive wording, after confirming it matches the final implementation:

```text
FoodBot is a personal diary for recording your own sleep, meals,
symptoms and observations. It shows descriptive summaries of your entries.
It does not diagnose conditions, prescribe treatment, or monitor emergencies.
```

Describe suspected triggers as the user's observations. Label the five calendar conditions as personal tracking targets. Avoid “clinically proven,” “detects food intolerances,” “guarantees better sleep,” or “doctor approved” without appropriate substantiation.

A disclaimer does not decide medical-device status. If future functionality interprets symptoms, recommends treatment or supports clinical decisions, assess the actual intended purpose/functionality before launch. [Roszdravnadzor on software classification](https://roszdravnadzor.gov.ru/medproducts/licensingmedtech/faq/c1033/153)

Use descriptive text with every meaningful color/emoji marker, accessible command names, understandable button labels, and complete text instructions alongside onboarding images. Telegram controls parts of native contrast and keyboard behavior; improve and test the parts you control.

## 5. Operator tasks that code does not replace

1. Establish the operator's real identity/contact details and complete applicable policy/processing documentation.
2. Generally plan to notify Roskomnadzor before automated processing unless a specific exception is confirmed for the actual operation. A free/private label is not itself an Article 22 exception. [Article 22](https://www.consultant.ru/document/cons_doc_LAW_61801/d996966e22e1320c9de1ab82d9f6be12c3d9d765/)
3. Resolve the health-data written/electronic-consent mechanism and its required contents.
4. Assess Telegram and other actual cross-border flows, including any separate notification/restrictions; general operator notification and transfer notification are not interchangeable. [Article 12](https://www.consultant.ru/document/cons_doc_LAW_61801/e4ebbe1780de623c7cf32a59ca82a7bb523a25dd/)
5. Finalize hosting/backup/security arrangements and retention/deletion procedures.
6. Keep an incident contact/process. The law includes 24-hour initial and 72-hour follow-up notifications for qualifying personal-data incidents; prepare a procedure rather than discovering the process during a leak. Confirm the exact trigger and other duties with the legal/security review. [152-FZ, Article 21(3.1)](https://mintrud.gov.ru/docs/laws/130)

Do not assume that a consent fixes an otherwise prohibited collection architecture, or that a generic “not medical advice” sentence makes health-data rules disappear. No forms were submitted and no legal documents were published by this planning task.

## 6. A small implementation backlog for the coding agent

Preserve the existing simple style and the `Archive` exclusion. Implement privacy controls as one focused stage; keep product features separate.

| Existing / proposed location | Change |
| --- | --- |
| Proposed `Handlers/privacy.py` | Privacy/terms/contact views, eligibility/choice screens, stop/withdraw/delete/access requests. |
| Proposed `privacy_storage.py` | Plain functions for privacy status/evidence, revocation and full-account deletion. |
| Proposed `Keyboards/privacy.py` | Separate choices and clearly labeled destructive-action confirmation. |
| `database.py` | A small versioned migration for privacy status/consent evidence; keep existing diary/legacy data intact during migration. |
| `Handlers/profile.py`, `Forms/profile.py` | Minimize required setup fields; run the new eligibility/authorization step before new collection. |
| All active handlers | Shared checks before health processing; stale callbacks cannot bypass authorization. |
| `reminders.py` and profile writes | Opt-in sending, persistent opt-out, and protection against send/delete races and silent `/start` re-enabling. |
| `Handlers/commands.py` | Discoverable privacy, contact, stop, withdrawal, deletion and data-access controls. |
| `Readmes` | Reviewed policy/rules documents, file map, data inventory and operational erasure/incident instructions. |

Suggested stored evidence, without a universal consent engine:

- One current privacy-status row per user: adult declaration time, account-authorization status where applicable, health-authorization status/method/evidence reference, and relevant document versions.
- Append-only consent events: purpose, version/hash, method, evidence reference, accepted/revoked times. Restrict access and define lawful retention.
- Reuse the current reminder flag rather than keeping conflicting copies. Keep ordinary privacy notice acknowledgement separate from consent.
- Do not store passport scans, invented signatures or unnecessary IP/device fingerprints to make the evidence table look stronger.

The exact table/column names should be chosen after inspecting the source at implementation time. The signature method and legal texts remain owner/legal inputs; the coding agent must not certify a generic Telegram click as sufficient.

## 7. Acceptance checks for that implementation

- [ ] `/privacy`, `/terms` and `/contact` work before onboarding and contain real reviewed information.
- [ ] No diary/meal entry point or old button bypasses the current authorization requirement.
- [ ] Required profile fields are limited to justified data; adult eligibility is enforced for known minors.
- [ ] Declining health authorization does not create a health record.
- [ ] Consent events preserve document version, purpose, method/evidence and revocation.
- [ ] `/stop` persists across `/start`, settings/time-zone changes and restarts.
- [ ] Withdrawal prevents further affected processing and optional reminders.
- [ ] Full deletion covers all current and future user-owned tables; other users remain untouched.
- [ ] An old callback, background job or backup restore does not silently resurrect erased data.
- [ ] Deletion/access requests have an operational contact, backup procedure and honest confirmation.
- [ ] Logs do not contain diary bodies, doses, notes or bot tokens.
- [ ] Active storage/backups are actually encrypted, and keys are separated.
- [ ] Privacy texts accurately distinguish Telegram cloud handling from the operator's own storage.
- [ ] Image/code licence provenance and descriptive text labels are recorded.
- [ ] Owner-side notification, consent-form and Telegram data-flow questions are resolved before admitting real health-data beta users.

## 8. What has and has not been checked here

The supplied image was transcribed, all 20 items were mapped to the confirmed release, relevant current code/documents were inspected, and legal/platform sources were browsed. This is a prioritized assessment, not a penetration test or deployment audit. No bot code, production data, hosting configuration, consent process or regulator submission was changed. Operator identity, hosting contract, encryption/key settings, actual transfer assessment, and image licences still require evidence.
