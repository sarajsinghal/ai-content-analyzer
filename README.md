# AI Content Analyzer

A local Streamlit prototype for reviewing observable writing patterns in pasted text or selectable text extracted from a PDF. It shows matching excerpts, sample length, sentence count, and a rough script estimate. It does not issue an AI-authorship verdict or probability.

## GitHub repository

- **Repository name:** `ai-content-analyzer`
- **Description:** A cautious Streamlit app that reviews English and Hindi text for article-informed writing patterns, with PDF text extraction and explainable highlights.

## Run locally

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

## What the prototype checks

- Sentence-length variation, reported descriptively and only when there are at least eight sentences.
- A short list of phrases and words mentioned in the collected articles, always shown as weak style cues with text excerpts.
- Repeated topic vocabulary in passages of at least 120 words.
- Script proportions (Latin and Devanagari) for rough context only. This is not language identification: Hindi can be written in Latin script, Devanagari is used for languages other than Hindi, and mixed-language writing is common.

The source articles also discuss perplexity, burstiness, learned classifiers, watermarks, and authorship tracking. This app does not calculate model perplexity, train or query a classifier, verify watermarks, inspect document history, or compare against labeled examples. The source set does not establish that individual words, grammar quality, missing typos, personal anecdotes, or factual errors can identify authorship, so the app does not treat those as authorship signals.

## Sources and method

The prototype was informed by several kinds of public-facing material about AI-text detection:

- Research and university perspectives, including University of Maryland reporting and research references, discuss text classifiers, false positives and negatives, paraphrase evasion, and limits to authorship detection.
- News coverage and educational explainers, including The Hindu, Scribbr, Coursera, and QuillBot, describe concepts such as predictability, sentence rhythm, repeated phrasing, and the difference between AI detection and plagiarism checking.
- Detector-company and product pages, including GPTZero, Grammarly, Solvely, Screpy, VisibleAI, Surfer, and others, describe their own systems. Their accuracy claims are promotional or vendor-reported claims and were not independently tested or used to calibrate this prototype.
- Practitioner and community material, including a developer-community discussion and an opinion article, shares perceived style cues while also warning that style cannot prove authorship. These observations are not treated as research validation.

The current review reports sample length, sentence count, and rough script proportions. It checks sentence-length uniformity, selected phrases and words mentioned in the reading material, and repeated topic vocabulary in longer samples. Matching sentences are highlighted with the rule that matched.

The displayed percentage is the **share of sentences matched by the simple rules**. It is not an AI probability, confidence score, or measured accuracy rate. The rule list has not been calibrated against a labeled dataset of human-written, AI-written, and mixed-authorship examples.

The source material repeatedly describes false positives and negatives, short-sample limits, paraphrase evasion, mixed human/AI editing, changing model behavior, and the risk of relying on a detector alone. It also describes statistical classifiers used by commercial detectors, but no detector model or labeled English/Hindi corpus was provided to train or evaluate one here.

**AI authorship cannot be reliably proven from text alone.** The reported cues are weak and genre-sensitive. Results are prompts for human review, not evidence for accusations, rankings, or consequential decisions. Factual accuracy is a separate fact-checking task; plagiarism checks address overlap with known sources, not authorship.

The prototype has not been validated in English or Hindi and has no measured accuracy. It does not calculate model perplexity, inspect document history, verify watermarks, fact-check claims, or determine authorship. Script proportions cannot reliably distinguish English from Romanized Hindi or identify Hindi from Devanagari alone. Scanned PDFs need OCR, which is not included. PDF extraction may lose tables, layout, or unusual text encoding; review the extracted preview.

## Deploy privately

Keep the GitHub repository private and give collaborators no write access unless they should edit the code. Deploy it through Streamlit Community Cloud, then keep the app private and invite viewers by email. A private Streamlit app can be viewed by invited people without giving them GitHub repository access. Community Cloud currently allows one private app per workspace; check the account's current plan and workspace limits before deploying. People who can view the app can still copy visible text, take screenshots, or reproduce its behavior, so privacy settings protect repository access rather than preventing all copying of the app's output.

The root `.gitignore` excludes the demo PDF, scratch files, Python caches, virtual environments, and Streamlit secrets. Commit the app source, `requirements.txt`, README, and `.streamlit/config.toml` only.
