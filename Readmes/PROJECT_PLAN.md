# Telegram Sleep and Food Diary — Project Plan

## Product goal

Make it easy to notice patterns between sleep, eating, stomach discomfort, and mood. A daily entry should take about a minute when everything is fine, with extra questions only when the user wants to record a problem or detail. The bot is a personal diary, not a diagnostic tool.

## Product principles

- Ask short questions and offer tap-to-answer choices wherever possible.
- Let people skip a question, finish later, and edit past dates. Missing a day must not feel like failure.
- Keep the normal daily check-in short; ask follow-up questions only when relevant.
- Use clear, calm language. Do not infer medical conditions or claim that food caused a symptom.
- Make each person's reminder time and time zone explicit and editable.

## Main user journeys

### 1. Morning sleep check-in

The bot sends one private Telegram reminder at the user's chosen local time. The check-in asks:

1. When did you go to bed, and when did you wake up? Offer a quick time picker plus manual entry. Save the actual sleep interval, including when it crosses midnight.
2. How was your sleep? Use a small scale, for example five labeled choices from “very poor” to “very good,” plus “skip.”
3. Did you have stomach pain or a noticeable mood change since the last check-in? Offer “No” and “Yes.” “No” completes the check-in. “Yes” opens short follow-ups to choose what happened, roughly when, and optionally add a note.

Associate the sleep interval with the date the user woke up. This keeps one night's sleep together in the calendar day the user starts.

### 2. Food logging

Provide a persistent “Log food” button and a `/meal` command. A quick log uses the current local time by default and asks for meal size (for example, small / medium / large), with an optional short description. Let the user change the time, edit, or delete an entry.

Use logged meal times to calculate how many eating occasions were recorded, the longest gap between them, and whether the last meal was within four hours of bedtime. If the day has no food logs, ask at the evening review whether the user wants to add meals or mark the day as not tracked. Do not require nutrition or calorie details for the first version.

### 3. Calendar and past dates

Show a monthly Telegram message with an inline-button calendar, inspired by the attached screenshot. Tapping a date opens that day's sleep, meals, symptoms, and notes. Provide previous/next month controls and a clear way to add or edit a past entry. Use a small, consistent marker set: complete, partial, and no entry; add symptom markers only if they remain easy to understand. Include a text legend so color or emoji is not the only signal.

### 4. Statistics

Start with simple weekly and monthly summaries: average sleep duration, sleep-quality trend, number of logged meals, meal gaps, and days with reported discomfort or mood changes. Allow users to open the days behind a summary. Describe these as patterns in the diary, not proof of cause and effect.

## Scope by milestone

### Milestone 0 — Agree on the product rules

- Confirm the wording and timing of the morning check-in.
- Decide whether to include a separate evening reminder or rely on quick meal logging plus an optional evening review.
- Choose the sleep-quality scale, meal-size choices, and symptom choices.
- Agree on the date rule: sleep belongs to wake-up date; meals and daytime symptoms use the user's local calendar date.

### Milestone 1 — Working diary foundation

- Start/help flow, per-user settings, local time zone, and reminder time.
- Persist entries so a restart does not lose data.
- Morning sleep questions, quality score, yes/no symptom gate, and conditional details.
- Resume or safely finish an interrupted check-in; prevent duplicate reminders and duplicate submissions.

### Milestone 2 — Food and day review

- Quick meal logging with editable time, size, and optional description.
- Edit/delete today's entries and record the optional evening review.
- Calculate meal count, gaps, and food within four hours before sleep from the saved times.

### Milestone 3 — Calendar and history

- Monthly inline-keyboard calendar, navigation, legend, date detail, and past-date edits.
- Clear markers for complete, partial, and empty days.

### Milestone 4 — Useful statistics and release readiness

- Weekly/monthly summaries with links back to the dates used.
- Export and delete-my-data controls, backup/restore plan, and clear privacy text.
- Check flows on mobile Telegram, including interrupted conversations, daylight-saving changes, and users in different time zones.

## First-version data to save

- User settings: Telegram user ID, time-zone name, reminder time, reminder enabled/paused.
- Sleep entry: wake-up date, bedtime, wake time, quality, completion state.
- Meal entry: local date/time, size, optional description.
- Symptom entry: date/time, selected category, optional intensity and note.
- Day note: optional “what was unusual?” text.

Keep timestamps consistently stored and convert them using each user's time zone when showing reminders, dates, and statistics. Store only what the product needs. Give users a way to export and delete their diary.

## Success criteria for the first usable release

- A user can complete an ordinary sleep check-in with a few taps and no typing.
- A “No” to the symptom question ends the flow immediately; a “Yes” asks only relevant follow-ups.
- The user can log food quickly, view and correct past entries, and understand the monthly calendar without instructions.
- A reminder arrives once at the chosen local time and can be paused or changed.
- Statistics link back to their source dates and do not present diary correlations as medical conclusions.

## Collaboration and VS Code

This Codex chat edits files in its current workspace. The current workspace contains no bot source files yet. Open `C:\Users\Влад\Documents\ChatGPT\Программирование` in VS Code to edit this plan alongside future code, or open the actual bot repository as the Codex workspace if it lives elsewhere. Once the code is in the shared workspace, we can implement one milestone at a time: I inspect and change the files, explain the changes, and you review or continue editing them in VS Code. I will follow the stack already in your project; if starting fresh, we can choose it together before writing the bot foundation.
