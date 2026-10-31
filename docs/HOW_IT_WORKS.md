# How it works, in plain English

## The problem
AI is good at summarizing lecture slides. It's also capable of stating something false with total
confidence: a wrong number, a function that doesn't exist, a fact credited to the wrong slide. When you're
studying for an exam, a confident wrong note is worse than no note.

## The idea
Think of an AI that writes your notes, and a strict fact-checker who reads every line before you see it. The
writer must say which slide each statement came from. The fact-checker goes to that slide and checks. If a
statement fails, it goes back to the writer with the reason. If it still fails after a couple of tries, it's
deleted. You only see what survived.

## What happens to one lecture
1. **Slides come in.** You upload a PDF or PowerPoint, or it's pulled from Canvas.
2. **The slides are read.** Plain code pulls out each slide's text and saves a picture of each slide. It also
   removes footers and page numbers, so a page number can't be mistaken for a fact.
3. **The AI writes notes.** It has to fill in a strict form: each statement plus its slide numbers.
4. **The fact-checker runs,** cheapest checks first:
   - *Does that slide exist?* Catches invented citations.
   - *Is the exact fact on that slide?* Numbers, quoted terms, and code names must really appear on the cited
     slide. It's smart about format, so `1,000` matches `1000` and `5 ms` matches `5ms`, but `4` doesn't match
     `40`.
   - *Does the slide really say this?* A second, cheaper AI acts as a judge, for claims with no number to check.
5. **Failures go back.** The writer gets a list of what failed and why, and tries again, up to a limit.
6. **Anything still failing is deleted,** never shown.
7. **You read the result.** Click a citation and the note lights up in yellow while its slide appears beside it,
   so checking takes one click.

Asking a question works the same way. The app finds the most relevant slides by keyword, the AI answers from
only those, and the answer gets fact-checked. If the slides don't cover it, you see "Not covered in the slides"
rather than a guess.

## Why not just ask the AI to be careful?
Because the rule lives outside the AI. The checks for slides and exact facts are ordinary code, so they can't
be talked out of anything, they give the same result every time, and they cost nothing to run. The AI only does
what needs judgment, and everything else is plain code.

## How do we know it works?
There's a test set: 40 statements with deliberate mistakes, plus 18 true ones to catch false alarms.

| Result without any AI judge | Score |
|---|---|
| Mechanical mistakes caught (wrong number, wrong slide, invented slide, renamed term) | 29 of 29 |
| Mistakes of meaning caught (number attached to the wrong thing, unsupported statements) | 0 of 11 |
| True statements wrongly rejected | 0 of 18 |

That 0 of 11 is expected. It shows exactly why the AI judge exists, and the code alone can't catch those.

## What isn't proven yet
- **The real AI hasn't been run.** Everything so far used a stand-in that copies lines from slides. How well
  the AI writes, and how much the judge catches, are unknown until a live run, which costs a little money.
- **Those test sets are drafts.** The same author wrote them and the fact-checker, which flatters the score, until
  a person reviews them.
- **Canvas sync has only been tested against a simulated Canvas,** not a real school's.
- **Passing doesn't mean the slide is right.** The app checks that notes match the slides, not that the
  slides are correct. A number can also be on the slide but attached to the wrong thing, if the judge misses it.
- **Some PDFs have garbled text.** Their hidden text layer can be scrambled even when the slide looks fine.
- **Scanned slides can't be read yet.** They're flagged rather than guessed at.

## The parts, in everyday terms
| Part | What it does |
|---|---|
| Backend (`app/`) | The kitchen: reads slides, runs the writer and fact-checker, stores results |
| Web app (`web/`) | The dining room: the page you read and ask questions on |
| Tests and CI | A robot that re-checks everything on every change, and blocks the merge if anything breaks |
| Evals (`evals/`) | The report card: measures accuracy with known right answers |
| Demo mode | A read-only copy for the public, with sample lectures only, safe to share |
