from __future__ import annotations

import re
import unicodedata
from collections import Counter
from dataclasses import dataclass, field

import streamlit as st

st.set_page_config(page_title="AI Content Analyzer", page_icon=":material/text_fields:", layout="centered")

MIN_WORDS_FOR_REVIEW = 120


@dataclass
class Finding:
    label: str
    detail: str
    excerpts: list[str] = field(default_factory=list)
    strength: str = "Weak style cue"


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?।॥])\s+|\n+", text) if s.strip()]


def language_summary(text: str) -> tuple[str, str]:
    chars = [c for c in text if c.isalpha()]
    if not chars:
        return "Undetermined", "Too few letters to estimate script."
    devanagari = sum("DEVANAGARI" in unicodedata.name(c, "") for c in chars)
    latin = sum("LATIN" in unicodedata.name(c, "") for c in chars)
    total = len(chars)
    if devanagari / total >= 0.25 and latin / total >= 0.25:
        return "Mixed scripts", f"Approx. {latin / total:.0%} Latin-script and {devanagari / total:.0%} Devanagari-script letters. Script does not establish language."
    if devanagari / total >= 0.5:
        return "Devanagari-script text", f"Approx. {devanagari / total:.0%} of letters use Devanagari. Hindi is possible, but script alone cannot identify language; other Devanagari languages and mixed text may be present."
    if latin / total >= 0.7:
        return "Latin-script text", f"Approx. {latin / total:.0%} of letters use Latin. English or Romanized Hindi may be present; script alone cannot distinguish them."
    return "Mixed or uncertain scripts", "Script proportions do not support a clear label. Romanized Hindi and code-switching may be missed."


def evidence(text: str, pattern: str, flags: int = re.I, limit: int = 3) -> list[str]:
    found: list[str] = []
    for sentence in sentences(text):
        if re.search(pattern, sentence, flags):
            found.append(sentence[:260])
        if len(found) >= limit:
            break
    return found


def assess(text: str) -> dict:
    text = normalize(text)
    sents = sentences(text)
    words = re.findall(r"\b[\w’'-]+\b", text, flags=re.UNICODE)
    findings: list[Finding] = []
    sentence_flags: dict[str, set[str]] = {}

    def flag_matches(pattern: str, label: str, flags: int = re.I) -> None:
        for sentence in sents:
            if re.search(pattern, sentence, flags):
                sentence_flags.setdefault(sentence, set()).add(label)

    if len(sents) >= 8:
        lengths = [len(re.findall(r"\b[\w’'-]+\b", s)) for s in sents]
        average = sum(lengths) / len(lengths)
        cv = (sum((x - average) ** 2 for x in lengths) / len(lengths)) ** 0.5 / average if average else 0
        finding = "Sentence lengths are relatively uniform" if cv < 0.30 else "Sentence lengths vary"
        note = "Low variation is a weak, genre- and language-sensitive cue. It is common in edited prose and is not evidence of authorship." if cv < 0.30 else "This describes rhythm only. Both people and language models can produce varied sentence lengths."
        findings.append(Finding(finding, f"Sentence-length variation (coefficient of variation) is {cv:.2f}. {note}"))

    formal = r"\b(furthermore|moreover|in conclusion|it is important to note|it is crucial to remember|additionally|in summary|at its core|delve into)\b|इसके अतिरिक्त|निष्कर्षतः|यह ध्यान रखना महत्वपूर्ण है"
    flag_matches(formal, "Listed transition/phrase")
    hits = evidence(text, formal)
    if hits:
        findings.append(Finding("Listed transition or phrase", "A phrase mentioned in the collected articles appears here. Such wording is also ordinary human language; frequency and context matter, and the sources do not validate it as an authorship marker.", hits))

    listed_words = r"\b(delves?|testament|beacon|tapestry|revolutioniz\w*|seamless|dynamic|elevat\w*|underscore\w*|illuminate|realm)\b"
    flag_matches(listed_words, "Listed vocabulary")
    hits = evidence(text, listed_words)
    if hits:
        findings.append(Finding("Word on a source-provided example list", "This word appeared in articles discussing perceived AI-style wording. A word choice alone is not evidence of AI authorship; topic and author preference affect vocabulary.", hits))

    # Repeated non-function words are only shown as descriptive context on longer passages.
    stop = {"which", "therefore", "because", "without", "between", "should", "would", "could", "their", "these", "those", "about", "where", "while", "after", "before", "being", "other", "might", "still", "under", "above", "there", "through", "first", "often", "every", "using", "however", "people", "human"}
    content_words = [w.lower() for w in re.findall(r"\b[\w'-]{5,}\b", text) if w.lower() not in stop]
    repeated = [(word, count) for word, count in Counter(content_words).most_common() if count >= 5]
    if len(words) >= MIN_WORDS_FOR_REVIEW and repeated:
        word, count = repeated[0]
        flag_matches(rf"\b{re.escape(word)}\b", "Repeated vocabulary")
        hits = evidence(text, rf"\b{re.escape(word)}\b")
        findings.append(Finding("Repeated topic vocabulary", f"“{word}” occurs {count} times. Repetition may reflect the topic or terminology; this is descriptive and not an authorship marker.", hits))

    if not findings:
        findings.append(Finding("No listed surface cues found", "The simple checks found no items from the collected examples. This does not mean the text is human-written or AI-written."))

    language, language_detail = language_summary(text)
    flagged = [{"text": sentence, "reasons": sorted(reasons)} for sentence, reasons in sentence_flags.items()]
    flagged_share = round(100 * len(flagged) / len(sents)) if sents else 0
    return {"word_count": len(words), "sentence_count": len(sents), "language": language, "language_detail": language_detail, "findings": findings, "flagged_sentences": flagged, "flagged_sentence_share": flagged_share}


def show_result(text: str, source: str) -> None:
    text = normalize(text)
    if not text:
        st.error("No readable text was found. Add text or try a text-based PDF.")
        return
    result = assess(text)
    st.subheader("Assessment")
    st.caption("Caution: Results are based on published articles and simple rules; accuracy is not guaranteed.")
    st.progress(result["flagged_sentence_share"], text=f"{result['flagged_sentence_share']}% of sentences matched listed style rules")
    has_surface_cue = any(item.excerpts for item in result["findings"])
    if has_surface_cue:
        st.markdown(f"**Result:** The checks found listed style patterns in {source}. See the matched sentences and rule labels below.")
    else:
        st.markdown(f"**Result:** The simple checks found no specific listed style patterns in {source}. That is an inconclusive result: it does not support either human or AI authorship.")
    if result["word_count"] < MIN_WORDS_FOR_REVIEW:
        st.info(f"Short sample: {result['word_count']} words across {result['sentence_count']} sentences. The repeated-vocabulary check applies to passages of at least {MIN_WORDS_FOR_REVIEW} words.")
    else:
        st.caption("Sample length is sufficient for these basic descriptive checks, but it still cannot establish authorship.")
    c1, c2, c3 = st.columns(3)
    c1.metric("Script estimate", result["language"], border=True)
    c2.metric("Words", result["word_count"], border=True)
    c3.metric("Sentences", result["sentence_count"], border=True)
    st.caption(result["language_detail"])
    st.markdown("#### Flagged passages")
    if result["flagged_sentences"]:
        st.caption("The highlighted sentences matched one or more listed phrase or repetition rules.")
        for item in result["flagged_sentences"]:
            with st.container(border=True):
                st.warning(item["text"], icon=":material/format_quote:")
                for reason in item["reasons"]:
                    st.badge(reason, icon=":material/search:", color="orange")
    else:
        st.write("No sentence matched the current phrase or repetition rules.")
    for item in result["findings"]:
        with st.container(border=True):
            st.markdown(f"**{item.label}** · {item.strength}")
            st.write(item.detail)
            if item.excerpts:
                st.caption("Matching excerpts from the supplied text")
                for line in item.excerpts:
                    st.markdown(f"> {line}")
            else:
                st.caption("This is a general interpretation of the checks, not a quoted signal.")
    with st.container(border=True):
        st.markdown("**What to do next**")
        st.write("If authorship matters, review the writing process where appropriate: drafts or version history, notes, cited sources, and the writer’s explanation of their choices. Check factual claims separately. Style patterns alone cannot verify authorship.")
    with st.expander("Interpretation and limitations"):
        st.write("The percentage above is the share of sentences matched by a small, hand-written list of phrases or repetition rules. It is not an AI probability, confidence score, or accuracy estimate. The prototype does not calculate model perplexity, train a classifier, or compare against labeled examples.")
        st.write("Research and university reporting in the source set discuss false positives, false negatives, paraphrase evasion, and the limits of watermarking. Vendor accuracy claims are vendor-reported and were not independently reproduced here. No validation dataset was provided, so no accuracy or confidence percentage is reported.")
        st.write("Script detection is not language detection. Devanagari can represent languages other than Hindi, English script may contain Romanized Hindi, and code-switching is common. This prototype has not been validated for Hindi or English separately. PDF extraction can lose layout, tables, or text encoded as images.")
        st.write("Checking whether claims are true is a separate fact-checking task; factual errors do not establish AI authorship. Plagiarism detection also addresses a different question from authorship.")


st.title("AI Content Analyzer")
st.caption("Explore writing patterns in English, Hindi, or mixed-script text. Paste a passage or upload a PDF to begin.")
st.badge("Text + PDF", icon=":material/description:", color="blue")
st.badge("Sentence highlights", icon=":material/format_quote:", color="green")
st.badge("Article-informed rules", icon=":material/menu_book:", color="violet")

text_tab, pdf_tab, sources_tab = st.tabs([":material/edit_note: Text review", ":material/picture_as_pdf: PDF review", ":material/menu_book: Sources and method"])
with text_tab:
    with st.form("text_review"):
        content = st.text_area("Paste the text to review", height=250, placeholder="Paste English, Hindi, or mixed-language text here…")
        submitted = st.form_submit_button("Review text", type="primary")
    if submitted:
        show_result(content, "The pasted text")

with pdf_tab:
    st.write("Upload a text-based PDF. Scanned pages need OCR; this prototype does not run OCR.")
    uploaded = st.file_uploader("Choose a PDF", type=["pdf"])
    if uploaded:
        try:
            import fitz
            doc = fitz.open(stream=uploaded.getvalue(), filetype="pdf")
            pages = [page.get_text("text") for page in doc]
            extracted = "\n".join(pages)
            count = sum(bool(page.strip()) for page in pages)
            st.caption(f"Extracted text from {count} of {len(pages)} pages. Check the preview before interpreting the result.")
            with st.expander("Preview extracted text"):
                st.text(extracted[:12000] if extracted.strip() else "No selectable text found. This may be a scanned PDF.")
            if st.button("Review extracted text", type="primary", disabled=not extracted.strip()):
                show_result(extracted, "The extracted PDF text")
        except Exception as exc:
            st.error(f"Could not read this PDF: {exc}")

with sources_tab:
    st.markdown("""
    ### What informed this prototype

    The approach was shaped by several kinds of material about AI-text detection:

    - **Research and university perspectives** discussing how text classifiers work, why false positives and false negatives occur, and how paraphrasing or mixed human–AI editing can affect results. This includes research coverage from the University of Maryland and research references summarized in the collected material.
    - **News and educational explainers** from sources such as *The Hindu*, Scribbr, Coursera, and QuillBot. These describe common detection concepts, including predictability, sentence rhythm, repeated phrasing, and the difference between AI detection and plagiarism checking.
    - **Detector-company and product material** from GPTZero, Grammarly, Scribbr, Solvely, Screpy, VisibleAI, Surfer, and other services. These sources describe their own products and may include promotional performance claims; those claims have not been independently tested for this prototype.
    - **Practitioner and community discussion**, including a developer-community thread and an opinion article, which offer examples of perceived AI-like wording while also cautioning that style alone cannot prove authorship.

    ### How the current review works

    The app extracts text from the pasted passage or selectable text in a PDF, then reports its length, sentence count, and rough writing-script mix. It checks for sentence-length uniformity, selected phrases and words mentioned in the reading material, and repeated topic vocabulary in longer passages. When a sentence matches a phrase or repetition rule, the app highlights it and names the rule that matched.

    The displayed percentage is **the share of sentences matched by these simple rules**. It is not an AI probability, confidence score, or measured accuracy rate. The rule list is small and has not been calibrated against labeled human-written, AI-written, or mixed-authorship examples.

    ### What this review cannot establish

    The prototype does not run a trained AI detector, calculate model perplexity, verify watermarks, inspect document history, fact-check claims, or determine who wrote a passage. The collected material does not validate this method for Hindi. Latin and Devanagari proportions are only rough script clues; they cannot reliably distinguish English from Romanized Hindi or identify Hindi from Devanagari alone.

    Detector research and reporting describe false positives, false negatives, short-sample limits, paraphrase evasion, and difficulty with mixed authorship. For that reason, flagged text is only a prompt for careful review. It should not be used by itself to accuse, rank, reject, or penalize anyone. Draft history, notes, citations, and a writer's explanation may provide useful context when it is appropriate to review them.
    """)
