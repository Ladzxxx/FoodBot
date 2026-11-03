# Daily questionnaire — approved plan

Approved by the user in this chat on 1 November 2026. The calendar changes are independent. The new questionnaire needs different
storage from the existing sleep/food/mood 1–7 records.

## Implementation for approval

- Keep aiogram, ordinary functions and SQLite, without an ORM or a new framework.
- Add `diary_entries`: one user/date, bedtime, wake time, sleep satisfaction 1–10,
  mood stability 1–10, stomach pain Yes/No, optional comments, pain details and
  the next unanswered question.
- Add `day_medications`: medication name/dose and effect, linked to one user/date.
  Separate rows allow the repeated medication questions.
- Put the new daily SQLite functions in `day_storage.py`; create the tables in
  `database.py`. Keep handlers, questions and keyboards in their existing folders.
- Preserve old Yes/No and 1–7 records without converting them to 1–10.
- Save each answer immediately, as requested. Cancel keeps recorded answers;
  incomplete entries resume at the next question. Mark the entry complete when
  the dialogue finishes. Reminders still count time since a completed entry.
- Append `Answer recorded` and the value to the original question message;
  remove its buttons and send the next question below it.
- Show only sleep times, sleep satisfaction, mood control and ache Yes/No on the
  selected day's calendar. Comments, pain details and medication lists stay out.

## English dialogue

1. What time did you go to bed yesterday?
2. What time did you wake up today?
   Both accept hourly buttons or typed HH:MM for exact minutes.
3. How satisfied were you with your sleep? (1–10)
4. How stable was your mood throughout the day?
   1 = extremely unstable, 10 = very stable.
5. Did you have stomach pain today? (Yes/No)
6. If Yes: how intense was the pain compared with the worst pain you have ever
   felt? (1–10)
7. Did you take any painkillers? (Yes/No)
8. If Yes: which medication did you take, and at what dose? (typed text)
9. Did it help? (Yes/No/A little)
10. Did you take anything else? If Yes, repeat medication and effect questions.
    If No, show all recorded medications.
11. Would you like to add a note about the day? If Yes, accept a short text.
12. For days with pain: would you like to describe what the pain felt like?
    Ask Yes/No, then skip the detailed questionnaire, as requested.
13. Would you like to add a note about the pain episode? If Yes, accept a short text.
14. Entry saved! Show the day summary and Calendar/Statistics buttons.

Offer the optional day comment on both the pain and no-pain branches.
Food logging, calorie estimates and charts are outside this change.
