# Google Oct 1st People-First Content & First-Party Effort Doctrine

## 1. Architectural Context (`qMUAU7E3dCA` / Search Central Rewrite)
Google rewrote its core Search Central guidance ([Creating Helpful, Reliable, People-First Content](https://developers.google.com/search/docs/fundamentals/creating-helpful-content) and [Guidance on Generative AI Content](https://developers.google.com/search/docs/fundamentals/using-gen-ai-content)), explicitly importing **"Main Content" (MC)** and the **4 Quality Rater Pillars** (**Effort, Originality, Talent/Skill, and Accuracy**) into public ranking documentation.

Sworn DOJ antitrust trial testimony (*U.S. v. Google* — VP of Search Pandu Nayak and Prof. Douglas Oard) confirmed that Google's core deep-learning ranking system (**`RankEmbed BERT`**) is fine-tuned directly on human Information Satisfaction (IS) Quality Rater scores. Merely having a human proofread an AI draft that lacks original human effort or non-training data does not protect a domain from demotion.

---

## 2. The 6 Non-Negotiable Content Co-Agent Guardrails

All A.I.M. Content Co-Agents (`content-node` and `content-wordpress` instances) and content skills (`aim-mega-article`, `aim-mega-guide`) enforce the following 6 rules:

1. **First-Party Non-Training Data Mandate ("No Meat Proxy Remixes"):**
   - Public YouTube transcripts and U.S. Census/Zillow statistics are secondary reinforcement—never the sole substance of an article or guide.
   - Every article MUST inject **proprietary first-party, non-training data** (Rilla Labs / Crutchfield standard):
     - **`content-node` (B2B Data Nodes):** Live aggregated SQLite/telemetry records, regulatory plan review velocities, and redacted first-party datasets.
     - **`content-wordpress` (Field Service & WaaS Nodes):** Real field metering ratios, empirical coverage tests, municipal code compliance outcomes, live TTFB/Core Web Vitals telemetry, and authentic first-party jobsite photography/videos.

2. **Interactive "Main Content" (MC) Micro-Tools (Effort & Talent/Skill):**
   - Google defines Main Content (MC) as anything on the page that helps fulfill its purpose—explicitly rewarding embedded interactive tools (calculators, selectors, interactive diagrams).
   - Content agents must pair or embed functional interactive tools inside Main Content where supported (e.g., batch dilution and sq-ft estimators, permit-to-opening lag/ROI calculators, or 3-year TCO calculators).

3. **Zero Scaled Templated Pages (Geo-Mesh & County Series Uniqueness Gate):**
   - Scaled templated pages (programmatic city/county pages with minor word swaps) are Google's #1 spam target.
   - Every city geo-mesh page or county report must contain unique municipal code/ordinance rules, distinct local entity/permit data tables, and specific local architectural/environmental constraints.

4. **Anti-LLM Prose Filter (Practitioner Voice):**
   - Strip out classic LLM structural tells that human raters and `RankEmbed BERT` penalize: formulaic contrasts (*"It's not X, it's Y"*, *"Not just X, but Y"*), throat-clearing intros, weak hedging, and AI transition crutches (*"Moreover"*, *"Furthermore"*, *"Crucially"*, *"Delve"*).

5. **Real Verifiable Human Bylines & Zero Self-Serving Listicles:**
   - Inventing fake authors, AI headshots, or fabricated credentials is officially classified as deception. Always use real, full human bylines (`"Brian Vasquez"`, `"Jessica Lakins"`, or verified client owners) with clickable E-E-A-T bios and verifiable credentials.
   - Never publish self-promotional `"Best X Software / Companies"` vendor listicles (which ChatGPT and Google AI Overviews actively discount or invert in favor of competitors).

6. **Critical Metadata (`<title>`, `<meta description>`, `<img alt>`) & Live `HTTP 200` Link Fact-Checking:**
   - Google explicitly added `<title>` tags, meta descriptions, and image `alt` text to its "critical" AI fact-checking requirement.
   - Every inline outbound citation URL must be verified as a live `HTTP 200` link resolving to the cited claim before staging to `content-vault/queue/`.
