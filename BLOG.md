# How I Built ShipSeg: A Zero-API Local ML Pipeline for Maritime Logistics

Every day, shipbrokers and maritime chartering desks receive thousands of emails. These aren't your typical newsletters—they are unstructured, highly localized listings containing multi-million dollar deals: **available vessels (Tonnage)** and **cargo requirements (Voyage/Time Charters)**.

Historically, this has meant hours of manual data entry. Missing a single email could mean missing a critical vessel-to-cargo match.

To solve this, I built **[ShipSeg](https://huggingface.co/spaces/archittmittal/Email-Segregation)**, an automated pipeline that instantly ingests, classifies, and extracts commercial data from these unstructured emails using purely **local Machine Learning models and heuristic extractors**.

Here's how I did it, and why I deliberately avoided using expensive LLM APIs like OpenAI or Claude.

---

## 🚫 The Problem with Cloud APIs in Maritime

When faced with parsing unstructured text, the modern developer reflex is to throw an LLM API at it. However, the maritime industry has strict constraints:
1. **Absolute Privacy:** Voyage contracts, freight rates, and client negotiations are strictly confidential. Sending this data to external AI providers is often a non-starter.
2. **Speed & Scale:** Chartering desks process tens of thousands of emails during peak market hours. API rate limits and network latency are unacceptable.
3. **Cost Efficiency:** Running expensive LLM inference on thousands of generic emails just to extract a few dates and locations is financially unviable.

This led to my core architectural constraint: **Zero Third-Party LLM Dependency.** Everything had to run locally, securely, and instantly on standard hardware.

---

## 🏗️ Architecture of ShipSeg

ShipSeg operates as a robust, sequential pipeline consisting of four major stages:

### 1. Ingestion & Deduplication
ShipSeg accepts raw pasted text, `.eml` files, `.txt`, and even `.pdf` attachments. As these enter the system, a **SHA-256 Fingerprinting Layer** sanitizes and hashes the content. This prevents broker circulars and forwarded email chains from cluttering the database with duplicate records.

### 2. Smart Classification (The Local ML Engine)
Once ingested, the text hits the classification engine, which categorizes the email into one of three strict groups: **Tonnage** (vessels), **Cargo VC** (Voyage Charters), or **Cargo TC** (Time Charters).

To do this efficiently, I trained a custom **Multinomial Logistic Regression** model layered over a **TF-IDF Vectorizer** using a localized dataset of shipping emails. This executes in milliseconds.

If the ML confidence falls below `0.55` (e.g., heavily misspelled or obfuscated text), a **Heuristic Fallback Engine** takes over, utilizing highly optimized RegEx rules targeting maritime keywords like `laycan`, `dwt`, and `tct` to ensure no email slips through the cracks.

### 3. Deep Extraction
After classification, dedicated extractors pull out the essential commercial details. Because brokers write emails like *"MV OCEAN 50K DWT OPEN VUNG ANG O/A 08-12 JUNE"*, the extractors utilize intelligent chunking and Regex parsing to accurately map:
* Ports (Loading, Discharge, Delivery)
* Laycan (Date availability ranges)
* Deadweight Tonnage (DWT) & Quantities
* Vessel constraints

### 4. The Matching Engine
The true value of ShipSeg lies in its ability to immediately connect the dots. The backend **Local Matching Engine** computes compatibility scores (0–100) between open vessels and pending cargo requirements.
* It leverages **Port Proximity Scoring** (exact string, token prefix, partial containment).
* It parses textual dates and grades **Laycan Overlap**.
* It validates the **Vessel Size vs. Cargo Quantity** ratio to ensure physical compatibility.

---

## 🎨 The User Experience

A backend is only as good as its interface. ShipSeg features a highly responsive, dark-themed Single Page Application (SPA) designed specifically for traders and brokers.

One of the standout features is the **Traceability Modal**. 
Instead of a black box where data magically appears in tables, users can click a ✉️ icon next to any extracted record. This triggers a split-screen view showing the exact raw source email on the left, and the structured, extracted data on the right. This maintains absolute data provenance and allows brokers to manually verify the extraction accuracy instantly.

## 🚀 Try It Out

ShipSeg is open-source and deployed as a live interactive demo. 

You can test the extraction and matching engine yourself right here:
👉 **[ShipSeg Live Demo (Vercel Frontend)](https://email-segregation.vercel.app/)**
*(Backend served via Hugging Face Spaces)*

By pushing the boundaries of local ML, TF-IDF regression, and clever heuristic parsing, ShipSeg proves that you don't always need a massive GPU or an expensive API key to build highly intelligent, industry-disruptive software.
