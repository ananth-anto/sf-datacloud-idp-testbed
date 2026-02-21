# Document AI API Testbed – Update

**Salesforce Data Cloud Document AI API Testbed** is a reference web app that lets you try the Document AI extract-data API with your own documents and schemas. Here’s what’s new and improved.

---

## What’s New

**Unified result view**  
You can switch between **Formatted** (tree view with optional confidence badges) and **Raw JSON** for every extraction. Same behavior with or without confidence scores. Raw JSON shows only the extracted data and metadata, not internal request details.

**Developer reference (API snippet)**  
After each successful extraction, a **“Show API request”** section lets you copy the exact **curl** and **Apex** calls used for that request. Useful for wiring the same call into your app or Apex. The section is collapsed by default and includes Copy buttons.

**Reliability and compatibility**  
- Default API version set to **v65.0** so the extract-data endpoint works on instances where v66 returns 404.  
- Optional **path override** (`DOCUMENT_AI_EXTRACT_PATH` in `.env`) and automatic retry with an alternate path when the default returns 404.  
- Clear **404 handling** with short, actionable hints (e.g. try v65, check Document AI in Setup).

**Schema-level prompt fix**  
The **Schema-Level Prompt** field is now sent correctly: it’s set as the schema’s **root-level `description`**, as in the [Document AI API spec](https://developer.salesforce.com/docs/data/connectapi/references/spec?meta=extractDocumentAIConfigData). Previously it was sent as a separate `prompt` property, which the API does not use. Your global extraction instructions are now applied by the service as intended. See the [Config prompt release notes](https://help.salesforce.com/s/articleView?id=release-notes.rn_cdp_2026_spring_config_prompt_document_ai.htm&release=260&type=5) for the feature.

---

## Document AI features in this testbed

The testbed demonstrates three Document AI capabilities, each backed by official Spring ’26 release notes:

**1. Schema-level prompt (config prompt)**  
Global instructions that apply to the whole extraction (e.g. “Extract only English text”, “Ignore sections in red”). In this app you enter them in the **Schema-Level Prompt** field; they are sent as the schema’s **root-level `description`** in the request, per the [extractDocumentAIConfigData](https://developer.salesforce.com/docs/data/connectapi/references/spec?meta=extractDocumentAIConfigData) API.  
→ [Release notes: Config prompt for Document AI](https://help.salesforce.com/s/articleView?id=release-notes.rn_cdp_2026_spring_config_prompt_document_ai.htm&release=260&type=5)

**2. Confidence scores**  
When enabled, the API returns a confidence score (0–1) per extracted field. The testbed shows these in a **Formatted** view with color-coded badges (e.g. green for high, yellow for medium, red for low) so you can quickly see which values may need review.  
→ [Release notes: Confidence score for Document AI](https://help.salesforce.com/s/articleView?id=release-notes.rn_cdp_2026_spring_confidence_score_document_ai.htm&release=260&type=5)

**3. Page range (start/end)**  
For PDFs, you can limit extraction to specific pages (e.g. 1–5 or 3–10) via **Total Pages** and **Page Range**. This reduces processing time and cost and helps when only part of the document is relevant.  
→ [Release notes: Page start and end for Document AI](https://help.salesforce.com/s/articleView?id=release-notes.rn_cdp_2026_spring_page_start_end_document_ai.htm&release=260&type=5)

**API reference**  
[Extract Document AI Config Data](https://developer.salesforce.com/docs/data/connectapi/references/spec?meta=extractDocumentAIConfigData) – Data 360 Connect API spec for the extract-data request and schema.

---

## Other features

- OAuth 2.0 (PKCE) with Salesforce  
- Document AI extract-data: PDF and images  
- **Formatted** vs **Raw JSON** result toggle (same for with/without confidence)  
- **Developer reference**: copy-paste **curl** and **Apex** for the last successful request  

---

## Try it

1. Clone the repo, add your `.env` (see `.env.example`), and run the app.  
2. Authenticate with Salesforce, upload a document, enter a JSON schema (and optional schema-level prompt).  
3. Run extraction, then use **Formatted** / **Raw JSON** and **Show API request** to inspect results and reuse the API call.

Repo: [sf-datacloud-idp-testbed](https://github.com/ananth-anto/sf-datacloud-idp-testbed) (update the link if your repo URL differs)

---

*Built as a reference for developers using the Salesforce Data Cloud Document AI extract-data API.*
