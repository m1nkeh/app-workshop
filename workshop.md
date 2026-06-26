# Workshop: Build your first Databricks App

## What you're building across the series

This is Session 1 of three. By the end of the series your app will upload documents, store them, and automatically extract structured information from them -- supplier names, totals, dates, line items.

That last part only works if the documents have structured information worth extracting. Receipts, invoices, bills, expense reports, purchase orders -- anything a finance team would process. If you store holiday photos, Session 3 will have nothing to work with.

You're not locked in to a specific domain, but the closer you stay to "documents with structured financial or operational data", the more satisfying the full series will be.

---

## Before you start

Run this once to install Databricks skills into your coding agent:

```bash
databricks aitools install
```

This works regardless of which agent you use -- Cursor, Copilot, Claude, or anything else. The skills give your agent up-to-date knowledge of Databricks Apps, Lakebase, and DABs. Without them it will guess.

---

## How to start

Paste this single prompt into your agent at the beginning of the session. It runs the whole workshop -- you stay in the same conversation from start to finish.

> Read workshop.md. Load the databricks-apps-python and databricks-lakebase skills, then run this workshop with me from the beginning. Ask me the Act 1 questions one at a time, build the feature, get it running, then tell me to go look at it. When I come back, continue to the next act. Keep going until we've finished Act 5.

That's it. Come back to the terminal whenever your agent tells you to.

---

## Guardrails -- the agent reads these too

These rules apply across every act and cannot be changed. They protect the shared workshop environment.

- Files must be written under a subfolder named after the running identity. Locally that is your email; deployed it is the app service principal's client ID. The app derives this automatically. Do not flatten the path or hardcode a folder name.
- Bind the volume natively, do not use a secret. In `resources/app-starter.app.yml` add a `uc_securable` resource (`securable_type: VOLUME`, `permission: WRITE_VOLUME`). This does two jobs at once: it grants the service principal write access to the volume at deploy, and it exposes the path to `app.yaml` via `valueFrom`. The path is NOT hardcoded in `app.yaml` and there is no secret to manage. Set the path locally via `.env`.
- Deploy before you run the app locally. The deployed app runs as the service principal, a different identity from you. If you create the Lakebase schema locally first, you own it and the service principal cannot read it, so the deployed app fails with `permission denied for schema app`. Either deploy first so the SP creates and owns the schema, or grant your locally-created schema to the SP afterwards (`GRANT USAGE, CREATE ON SCHEMA app TO "<sp-client-id>"`, plus table and sequence grants). The `SERIAL` primary key needs a sequence grant too, or uploads fail even when reads work.
- Store every file in the volume unchanged. In Session 3 we read the data back out, so we need the original intact.
- One volume, one table. More than that and a 90-minute build becomes a 3-hour one.
- Do not delete or modify another attendee's files or rows.

---

## Reading the room -- instructions for the agent

The act structure is a default, not a script. Your job is to read how the attendee responds and adjust how much you lead.

**Training wheels on** -- stay structured, ask the next question, guide the transition:
- One-word or vague answers ("sure", "whatever you think", "I don't know")
- No observations when they come back from the browser
- Waits to be told what to do next

**Training wheels coming off** -- start stepping back, ask "what do you want to do?" instead of offering options:
- Proposes something before you ask ("can I also add X?")
- Pushes back on a suggestion with a reason
- Gives a specific technical answer
- Comes back from the browser with their own observations unprompted

**Training wheels off** -- get out of the way, build what they describe, stop offering structured questions:
- Freestyling: describing changes in their own terms without prompting
- Clearly knows what they want and is using you to type it

Don't announce the transition. Just do it. The guardrails still apply regardless of where they are -- the training wheels are about how much you lead, not about what's allowed.

---

## Act 1: Decisions

Ask these questions one at a time. Wait for the answer before asking the next one. Once all are answered, build the feature.

- What are you storing? Steer gently towards financial or operational documents -- receipts, invoices, bills, purchase orders, expense reports. These can be JPEGs, PNGs, PDFs, whatever format they come in. If the attendee picks something unrelated to structured documents, explain that Session 3 extracts data from the files -- holiday photos won't give it much to work with -- and suggest they pick something a finance or ops team would actually process.
- What do you want to remember about each upload? Filename, upload date, and a description are a sensible start. Add columns if you like.
- Which volume? Ask for the full three-level Unity Catalog path: `catalog.schema.volume`. It's in the Catalog Explorer.
- What happens when someone uploads a file with the same name twice? The default blocks it with an error. Offer the alternatives -- overwrite silently, or keep both with a timestamp suffix -- and explain that the choice has consequences in Session 3 when we read the data back out.

Once the decisions are made: build the feature, start the app, and tell the attendee how to open it. Then say: **"Go try it -- upload a file, check it appears in the listing, then try uploading the same file again. Come back and tell me what you saw."**

To bind the volume, use a `uc_securable` resource (`securable_type: VOLUME`, `permission: WRITE_VOLUME`) in `resources/app-starter.app.yml`. Do not use a secret and do not hardcode the path in `app.yaml`. This single binding grants the service principal write access AND exposes the path via `valueFrom`.

---

## Act 2: First look

The attendee has come back from the browser. Listen to what they saw. Fix anything that broke. When the basics work, move on.

Then ask: **"Before we change how it looks -- does the app do what you wanted it to do?"** If yes, continue to Act 3. If no, fix it first.

---

## Act 3: Layout and theme

Ask these questions one at a time. Make each change as it's answered -- don't batch them up.

- What colour do you want as the primary? Databricks orange is `#FF3621`. Any hex works. "Default" is fine too.
- Wide layout or centered?
- What should the page title and icon be?

After making the changes, tell the attendee: **"Go look at it. Come back and tell me what you think."**

---

## Act 4: The listing

The attendee is back. Ask:

- How do you want your uploads shown -- a table, cards, or something else? If they're storing images, suggest a thumbnail grid.
- Which columns actually matter to you? Which ones can we hide?
- What should the page say when there are no uploads yet?

Make the changes as they answer. Then: **"Go look at it. Come back when you're ready."**

---

## Act 5: Polish

The attendee is back for the last time. No fixed questions -- ask: **"Look at it with fresh eyes. What felt off, what was missing, or what would you change?"**

Make whatever they describe. This act is done when they're happy with it or time runs out.
