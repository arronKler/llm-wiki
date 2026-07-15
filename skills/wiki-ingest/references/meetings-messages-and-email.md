# Meetings, Messages, and Email Ingestion

Use this reference when the source is a meeting record, chat conversation, message thread, channel slice, email message or thread, or a conversational ticket discussion. Apply [source-handling.md](source-handling.md) during acquisition, then apply [integration-contract.md](integration-contract.md) before editing wiki pages. Keep generic capture safety, classification, page structure, conflict handling, and validation in those shared contracts; specialize only collaboration-record semantics here.

## Contents

- [Define the conversation boundary](#define-the-conversation-boundary)
- [Choose the ingestion intent](#choose-the-ingestion-intent)
- [Acquire records without side effects](#acquire-records-without-side-effects)
- [Preserve object identity and time](#preserve-object-identity-and-time)
- [Choose snapshot or incremental evidence](#choose-snapshot-or-incremental-evidence)
- [Preserve edits, deletions, and visibility](#preserve-edits-deletions-and-visibility)
- [Handle transcripts and attachments](#handle-transcripts-and-attachments)
- [Map collaboration evidence into capture](#map-collaboration-evidence-into-capture)
- [Distinguish statements, proposals, decisions, and actions](#distinguish-statements-proposals-decisions-and-actions)
- [Assign authority per artifact](#assign-authority-per-artifact)
- [Cite stable event locators](#cite-stable-event-locators)
- [Integrate and update records](#integrate-and-update-records)
- [Stop or accept](#stop-or-accept)

## Define the conversation boundary

Start from a stable collaboration object, not from every record the current account can see.

- For a meeting, include the calendar event plus only the available agenda, attendance, transcript, meeting chat, notes, recording, and attachments that belong to that occurrence.
- For a chat thread, include the root message and its replies. Include surrounding channel messages only when they are necessary to resolve a reference.
- For a channel slice, state the channel, inclusive time range, timezone, filters, and whether threads are expanded.
- For email, prefer provider thread identity or explicit reply headers. Do not group unrelated messages merely because their normalized subjects match.
- For a conversational ticket, preserve the ticket identity, scoped field state, comments, and relevant status events. Distinguish its discussion history from workflow state maintained by the ticket system.
- Preserve quoted-message relationships, forwards, cross-posts, and links without treating repeated quoted text as independent evidence.
- Treat a linked document, ticket, repository, dashboard, or external thread as a separate source. Follow it only when the user places it in scope or a material claim cannot otherwise be understood.
- Record missing parents, inaccessible replies, omitted attachments, pagination limits, and intentionally excluded side conversations.

Do not crawl an entire mailbox, workspace, channel, or organization to make a bounded request appear comprehensive. Route reusable or continuous synchronization to `wiki-configure`.

## Choose the ingestion intent

Choose one primary intent before acquiring records.

| Intent | Produce | Stop reading when |
| --- | --- | --- |
| Meeting record | Evidence-backed outcomes, decisions, actions, and open questions | The occurrence and its material artifacts are covered |
| Thread record | A coherent account of one discussion | The root, relevant replies, and referenced evidence are resolved |
| Time-bounded digest | Durable themes and changes from a declared interval | The stated channels, interval, and thread-expansion policy are covered |
| Decision or action extraction | Explicit commitments with actors and effective time | Each extracted item has direct event evidence |
| Revision refresh | Changes since a prior captured state | New, edited, deleted, and late-arriving events are reconciled |

## Acquire records without side effects

Use an approved connector, provider export, local export file, or user-supplied record in read-only mode.

1. Fetch only the authorized object IDs, thread, query, or time window.
2. Preserve the provider response or export before cleaning, summarizing, or flattening it.
3. Avoid sending messages, marking messages read, changing reactions, accepting invitations, editing notes, moving mail, changing labels, or acknowledging tickets as an ingestion side effect.
4. Record provider pagination, export limits, retention limits, and the identity scope used for access without storing credentials.

Treat a live meeting or still-active thread as provisional. Record the cutoff and avoid presenting it as a final record.

## Preserve object identity and time

Use provider identifiers as durable identity and display names as presentation snapshots.

- Preserve tenant, organization, workspace, mailbox scope, channel, conversation, thread-root, meeting-occurrence, ticket, comment, status-event, message, event, transcript, and attachment IDs when available.
- Preserve RFC `Message-ID`, `In-Reply-To`, and `References` for email when policy permits; retain provider IDs as well.
- Do not merge a person across providers from name or email similarity alone.
- Distinguish invited attendee, joined account, identified speaker, message author, sender, recipient, organizer, and note author.
- Preserve original timestamp and offset, then add normalized UTC time in derived output.
- Distinguish scheduled, started, ended, sent, received, edited, deleted, exported, and captured times.
- Preserve provider ordering keys or sequence numbers; do not use timestamps alone when concurrent events can reorder.
- Record the provider revision, change token, watermark, cursor, or maximum event ID that defines the snapshot boundary.

## Choose snapshot or incremental evidence

Choose the smallest immutable unit that preserves context and later updates.

- Capture one complete snapshot for a bounded meeting occurrence, chat thread, or email thread when the provider can export it coherently.
- Capture a time-bounded batch for a channel or mailbox query. Preserve the query, range, timezone, pagination, cursor, and included object IDs inside the batch.
- Capture non-overlapping incremental batches for append-only event streams. Do not mark one batch as superseding another merely because it is newer.
- Capture a replacement snapshot with `--supersedes` when it represents a later revision of the same complete evidence unit.
- Overlap incremental reads enough to detect late messages and edits, then deduplicate by stable object ID plus revision rather than timestamp or body text.
- Keep separate artifacts as separate sources when authority, classification, format, or retention differs.

When an agent creates a bundle manifest that links captured artifacts, store it as derived navigation by default and map it to the underlying source IDs. Capture it as a separate collaboration manifest only when immutable coverage or reconstruction requires it, set `--authority agent-provenance`, and cite it only for acquisition or coverage claims. Do not cite an agent-created manifest as primary evidence for substantive claims.

## Preserve edits, deletions, and visibility

Preserve history instead of rewriting the conversation into a timeless transcript.

- Retain original and edited versions when the provider exposes both, with edit timestamps and revision IDs.
- When only the latest body is available, mark prior content as unavailable rather than reconstructing it.
- Capture deletion, retraction, redaction, recall, and retention-expiry events as evidence; never delete an earlier immutable source to mirror the provider.
- Distinguish a deleted object's known metadata from unavailable deleted content.
- Record visibility boundaries such as private channel, direct message, Bcc, restricted attendee notes, or partial export.
- Avoid widening visibility in the wiki merely because multiple artifacts were available to the ingesting account.

## Handle transcripts and attachments

Keep original artifacts separate from derived interpretation.

- Preserve automated transcript text, timestamps, language, speaker labels, confidence data, and correction state when available.
- Treat speaker diarization and speech recognition as uncertain unless a human or authoritative mapping confirms them.
- Keep organizer notes, collaborative notes, transcript, chat, and recording as distinct evidence with distinct authority.
- Capture an attachment's approved original bytes separately, or use a stable pointer when copying is prohibited.
- Preserve the parent object ID, attachment ID, filename, MIME type, size, content hash, and revision in the attachment record.
- Cite a page, sheet, slide, region, or media timestamp inside an attachment rather than citing only the parent message.
- Record unavailable, expired, quarantined, or permission-blocked attachments as explicit coverage gaps.

## Map collaboration evidence into capture

Use the generic CLI and current capture flags. Treat `--adapter` as a provenance namespace, not as persistent connector configuration.

Capture a meeting export:

```text
python3 <wiki.py> --workspace <workspace-root> capture <meeting-export> --title <title> --origin <canonical-meeting-uri> --source-type meeting-record --adapter <provider> --external-key <tenant>:meeting:<occurrence-id>:snapshot:<revision> --published-at <ended-at> --classification <level> --authority <authority>
```

Capture a chat thread or bounded message batch:

```text
python3 <wiki.py> --workspace <workspace-root> capture <thread-export> --title <title> --origin <canonical-thread-uri> --source-type message-thread --adapter <provider> --external-key <tenant>:<channel>:<thread-root>:snapshot:<watermark> --published-at <last-event-at> --classification <level> --authority <authority>
python3 <wiki.py> --workspace <workspace-root> capture <batch-export> --title <title> --origin <canonical-channel-uri> --source-type message-batch --adapter <provider> --external-key <tenant>:<channel>:events:<range>:<cursor> --published-at <range-end> --classification <level> --authority <authority>
```

Capture an email thread:

```text
python3 <wiki.py> --workspace <workspace-root> capture <email-export> --title <title> --origin <canonical-thread-uri> --source-type email-thread --adapter <provider> --external-key <mailbox-scope>:thread:<thread-id>:snapshot:<revision> --published-at <last-message-at> --classification <level> --authority <authority>
```

Capture a conversational ticket:

```text
python3 <wiki.py> --workspace <workspace-root> capture <ticket-export> --title <title> --origin <canonical-ticket-uri> --source-type ticket-thread --adapter <provider> --external-key <tenant>:ticket:<ticket-id>:snapshot:<revision> --published-at <last-event-at> --classification <level> --authority <authority>
```

Capture connector text through standard input only when no approved export file exists:

```text
python3 <wiki.py> --workspace <workspace-root> capture --stdin --name <name>.json --title <title> --origin <canonical-object-uri> --source-type <type> --adapter <provider> --external-key <immutable-object-key> --published-at <effective-time> --classification <level> --authority <authority>
```

Capture an attachment or an unavailable recording:

```text
python3 <wiki.py> --workspace <workspace-root> capture <attachment-file> --title <title> --origin <canonical-attachment-uri> --source-type attachment --adapter <provider> --external-key <parent-object>:attachment:<attachment-id>:<revision> --classification <level> --authority <authority>
python3 <wiki.py> --workspace <workspace-root> capture <stable-recording-uri> --pointer-only --title <title> --source-type recording --adapter <provider> --external-key <meeting-id>:recording:<revision> --published-at <ended-at> --classification <level> --authority <authority>
```

Add `--supersedes <prior-source-id>` only to a corrected or replacement snapshot. Keep the canonical origin free of credentials, temporary download URLs, and session parameters.

## Distinguish statements, proposals, decisions, and actions

Classify conversational meaning from explicit evidence.

- Record a statement as what its author or speaker said, not as an independently verified fact.
- Record a proposal when someone suggests, recommends, requests, or volunteers an option that remains open.
- Record a decision only when the record shows an authorized choice, commitment, or accepted resolution.
- Do not infer a decision from silence, lack of objection, a reaction, meeting attendance, or an unchallenged automated summary.
- Preserve decision status such as proposed, decided, deferred, reversed, or superseded, plus decision-maker, scope, time, and rationale when explicit.
- Record an action only when the task and owner are explicit. Preserve due date, status, dependencies, and acceptance condition only when stated.
- Do not assign an action to a mentioned person or attendee by inference.
- Treat ticket status, assignment, and resolution fields as workflow evidence; do not infer agreement merely because a discussion appears inside a closed ticket.
- Keep unresolved questions, disagreements, reservations, and conditional commitments visible.

## Assign authority per artifact

Assign authority at claim level rather than treating a conversation bundle uniformly.

- Use a calendar event for planned time and invitees, not proof of attendance or agreement.
- Use attendance logs for account presence, not proof that a person listened or consented.
- Use a transcript for an attributed utterance with recognition uncertainty, not automatic factual truth.
- Use participant-authored messages and email for the author's statement and explicit commitments.
- Use organizer or collaborative notes for their recorded interpretation, not unanimous agreement.
- Use provider edit and deletion events for record state at that time.
- Require operational, metric, repository, or formal policy evidence for claims that a discussed change shipped, succeeded, or became binding.

## Cite stable event locators

Pair every material claim with its captured source ID and the strongest provider locator.

- Meeting speech: `meeting:<occurrence-id>/transcript:<transcript-id>#t=<start>-<end>;speaker=<speaker-id>`.
- Meeting chat: `meeting:<occurrence-id>/message:<message-id>@revision:<revision>`.
- Chat: `workspace:<workspace-id>/channel:<channel-id>/thread:<root-id>/message:<message-id>@revision:<revision>`.
- Email: `mailbox:<scope>/thread:<thread-id>/message:<provider-id-or-Message-ID>#part=<part>`.
- Ticket: `tenant:<tenant-id>/ticket:<ticket-id>/comment:<comment-id>@revision:<revision>` or the corresponding status-event ID.
- Attachment: cite the parent event, attachment ID, content hash, and its internal page, region, or timestamp locator.
- Revision or deletion: cite the object ID plus revision, edit, deletion, or tombstone event ID and time.

Never cite only a display name, normalized line number, inbox position, subject, search rank, or model-assigned speaker number when a stable object locator exists.

## Integrate and update records

Integrate outcomes into durable project, decision, process, person, or concept pages instead of creating one page per message or meeting by default.

- Keep communication evidence beside stronger implementation, policy, metric, and operational sources without collapsing their authority.
- Preserve the difference between discussion time, decision effective time, action completion time, and capture time.
- For a finalized transcript or corrected export, capture the new artifact and link it with `--supersedes`; retain the provisional source.
- For append-only updates, capture only new bounded batches and reconcile overlaps by object revision.
- Treat deletions, edits, late replies, action completion, and decision reversal as new evidence events.
- Stop one-time ingestion at the declared cutoff. Route scheduled polling, cursor persistence, and provider-wide sync configuration to `wiki-configure`.

## Stop or accept

Stop and report the boundary when:

- the meeting occurrence, thread, mailbox scope, channel, interval, or timezone is ambiguous;
- access would expose private participants, hidden recipients, restricted notes, or content outside the authorized scope;
- a supposedly complete export is materially truncated and the missing range cannot be identified;
- stable object identity, event ordering, or revision state cannot be established for material claims;
- speaker mapping is too uncertain for an attributed decision or commitment;
- the request requires sending, replying, reacting, editing, moving, labeling, inviting, or otherwise mutating collaboration state;
- the request is an unbounded mailbox, channel, or organization import without a defensible scope;
- the task requires reusable connector setup or continuous synchronization.

Accept the ingest only when:

- the conversation boundary, intent, cutoff, timezone, and material omissions are explicit;
- provider object identities, revisions, ordering, participants, and visibility limits are preserved;
- the selected snapshot or incremental strategy supports later updates without overwriting history;
- transcripts, notes, chat, recordings, and attachments retain separate provenance and authority;
- statements, proposals, decisions, actions, conflicts, and uncertainty remain distinguishable;
- each material conversational claim has a source ID and stable event locator;
- replacement snapshots and append-only batches use the correct update relationship;
- no collaboration state changed during acquisition;
- the normal rebuild, lint, and ingest acceptance checks pass.
