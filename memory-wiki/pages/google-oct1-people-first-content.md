# Google Oct 1st People-First Content & First-Party Effort Doctrine

## 1. Architectural Context (`qMUAU7E3dCA` / Search Central Rewrite)
Google rewrote its core Search Central guidance ([Creating Helpful, Reliable, People-First Content](https://developers.google.com/search/docs/fundamentals/creating-helpful-content) and [Guidance on Generative AI Content](https://developers.google.com/search/docs/fundamentals/using-gen-ai-content)), explicitly importing **"Main Content" (MC)** and the **4 Quality Rater Pillars** (**Effort, Originality, Talent/Skill, and Accuracy**) into public ranking documentation.

Sworn DOJ antitrust trial testimony (*U.S. v. Google* — VP of Search Pandu Nayak and Prof. Douglas Oard) confirmed that Google's core deep-learning ranking system (**`RankEmbed BERT`**) is fine-tuned directly on human Information Satisfaction (IS) Quality Rater scores. Merely having a human proofread an AI draft that lacks original human effort or non-training data does not protect a domain from demotion.

---

## 2. The 6 Non-Negotiable Content Co-Agent Guardrails

All A.I.M. Content Co-Agents (`aim-ld-content`, `aim-skorbane-content`, `aim-tbsoftwash-content`, and future `content-node` / `content-wordpress` instances) and content skills (`aim-mega-article`, `aim-mega-guide`) enforce the following 6 rules:

1. **First-Party Non-Training Data Mandate ("No Meat Proxy Remixes"):**
   - Public YouTube transcripts and U.S. Census/Zillow statistics are secondary reinforcement—never the sole substance of an article or guide.
   - Every article MUST inject **proprietary first-party, non-training data** (Rilla Labs / Crutchfield standard):
     - **`aim-ld-content`:** Live aggregated SQLite/Sunbiz/DBPR/ABT/Permits telemetry (`NAL` commercial parcel counts, `DBPR` plan review velocities, `MULTI_HIT` ratios, redacted Day-Zero intercepts).
     - **`aim-tbsoftwash-content`:** Real Pinellas/Pasco/Hillsborough chemical metering ratios (`SH%`, Trident Protects coverage tests, `ASTM C-144` sand specs), real HOA/insurance field outcomes, and authentic `@tbsoftwash` jobsite photography/videos (`/home/kingb/tbsoftwash-content/`).
     - **`aim-skorbane-content`:** Live `tbsoftwash.com` production telemetry (`< 0.4s` TTFB, `150+` verified reviews, 38-city geo-mesh benchmarks), real territory availability via `tools/territory_validator.py`, and 5 Golden Rules field visuals.

2. **Interactive "Main Content" (MC) Micro-Tools (Effort & Talent/Skill):**
   - Google defines Main Content (MC) as anything on the page that helps fulfill its purpose—explicitly rewarding embedded interactive tools (calculators, selectors, interactive diagrams).
   - Content agents must pair or embed functional interactive tools inside Main Content where supported (e.g., SH% batch dilution and Trident sealer sq-ft calculators on `tbsoftwash.com`; County Permit-to-Opening lag/ROI calculators on `leaddeeds.com`; 3-Year DIY Sitebuilder vs. Skorbane WaaS TCO calculators on `skorbane.com`).

3. **Zero Scaled Templated Pages (Geo-Mesh & County Series Uniqueness Gate):**
   - Scaled templated pages (programmatic city/county pages with minor word swaps) are Google's #1 spam target.
   - Every city geo-mesh page (`aim-skorbane-content`, `aim-tbsoftwash-content`) or county report (`aim-ld-content` Issues `#420`–`#424`) must contain unique municipal code/ordinance rules, distinct local entity/permit data tables, and specific local architectural/environmental constraints.

4. **Anti-LLM Prose Filter (Practitioner Voice):**
   - Strip out classic LLM structural tells that human raters and `RankEmbed BERT` penalize: formulaic contrasts (*"It's not X, it's Y"*, *"Not just X, but Y"*), throat-clearing intros, weak hedging, and AI transition crutches (*"Moreover"*, *"Furthermore"*, *"Crucially"*, *"Delve"*).

5. **Real Verifiable Human Bylines & Zero Self-Serving Listicles:**
   - Inventing fake authors, AI headshots, or fabricated credentials is officially classified as deception. Always use real, full human bylines (`"Brian Vasquez"`, `"Jessica Lakins"`, or verified client owners) with clickable E-E-A-T bios and verifiable credentials.
   - Never publish self-promotional `"Best X Software / Companies"` vendor listicles (which ChatGPT and Google AI Overviews actively discount or invert in favor of competitors).

6. **Critical Metadata (`<title>`, `<meta description>`, `<img alt>`) & Live `HTTP 200` Link Fact-Checking:**
   - Google explicitly added `<title>` tags, meta descriptions, and image `alt` text to its "critical" AI fact-checking requirement.
   - Every inline outbound citation URL must be verified as a live `HTTP 200` link resolving to the cited claim before staging to `content-vault/queue/`.
