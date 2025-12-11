# Link Prediction - Beginner's Guide 🔮

## What Does This Feature Do?

**Link Prediction** helps you discover potential trading partners by analyzing patterns in existing trade data. Think of it like a "recommended friends" feature on social media — but for business partnerships.

---

## How to Read the Results

### Confidence Score (0-95%)
This is how **likely** a company would be a good trading partner:

| Score | Meaning | Action |
|-------|---------|--------|
| **70-95%** (High) | Strong match based on multiple factors | Definitely worth contacting |
| **40-69%** (Medium) | Some indicators of compatibility | Consider reaching out |
| **0-39%** (Low) | Weak or limited data | Proceed with caution |

> **Note**: Scores never reach 100% because that would imply perfect certainty, which is impossible in predictions.

### Ranking (1st, 2nd, 3rd...)
Companies are ranked from most to least likely to be a good match.

### Methods Used
More methods = more confidence. If 5 methods agree, that's more reliable than if only 1 method found a match.

---

## The 5 Prediction Methods Explained

### 1. 🧠 Node2Vec Similarity (Weight: 30%)
**What it does**: Uses AI to create a "fingerprint" for each company based on who they trade with.

**Analogy**: Imagine every company has a unique "personality profile" based on their trading behavior. This method finds companies with similar profiles.

**Why it matters**: Companies with similar trading patterns often have overlapping needs.

---

### 2. 👥 Common Neighbors (Weight: 20%)
**What it does**: Finds companies that share mutual trading partners with you.

**Analogy**: If you and Company X both buy from the same 10 suppliers, you might also benefit from working with companies that Company X works with.

**Example**:
- Your company buys from Supplier A and Supplier B
- Company X also buys from Supplier A and Supplier B  
- Company X also buys from Supplier C
- → Supplier C is recommended to you!

---

### 3. 📦 Product Co-Trade (Weight: 25%)
**What it does**: Recommends companies that deal in the same products as you.

**Analogy**: If you import wheat and sugar, this method finds other importers/exporters of wheat and sugar who you haven't worked with yet.

**Why it matters**: Companies trading the same products understand your market and logistics.

---

### 4. 📊 Jaccard Coefficient (Weight: 15%)
**What it does**: Measures how much your trading network overlaps with potential partners.

**Formula**: (Shared Partners) ÷ (All Partners Combined)

**Analogy**: If you have 10 partners and they have 10 partners, and 5 are the same, you have 50% overlap. Higher overlap = stronger recommendation.

---

### 5. 🌟 Preferential Attachment (Weight: 10%)
**What it does**: Favors companies that are already well-connected in the trade network.

**Analogy**: Popular companies (with many partners) tend to attract even more partners — like how famous restaurants attract more customers.

**Caution**: This method can be biased toward big players, so it has the lowest weight.

---

## Combined Method (Recommended)

When you select **"Combined (All Methods)"**, the system:
1. Runs all 5 methods
2. Weighs each based on reliability (Node2Vec highest, PA lowest)
3. Calculates a weighted average
4. Applies a penalty if fewer methods contributed (more methods = more reliable)
5. Caps the maximum at 95%

---

## Practical Tips

1. **Use Combined method** for best results
2. **Higher score ≠ guaranteed success** - it's a recommendation, not a guarantee
3. **Check "Methods Used"** - a company scoring 70% from 4 methods is more reliable than one scoring 80% from 1 method
4. **Use autocomplete** when entering company names for exact matches
5. **No results?** The company may not have enough trading history in our database

---

## Verification Results

### Find Potential Sellers (Nestle Pakistan Ltd)
![Sellers Results](nestle_results_1765473928271.png)
- Confidence: 83%, 82% (capped at 95%)
- Rankings: 1st, 2nd, 3rd visible
- High confidence tier badges showing

### Find Potential Buyers (Nestle Pakistan Ltd)
![Buyers Results](find_buyers_results_1765474288521.png)
- Confidence: 80%, 68%, 67% (method coverage penalty applied)
- Only 1 method contributing → scores reduced from potential 95%
- Fix working correctly!

---

## Quick Reference

| If you see... | It means... |
|---------------|-------------|
| 70-95% + Multiple methods | Very reliable recommendation |
| 70-95% + 1 method | Good but limited data |
| 40-69% | Worth exploring but do research |
| <40% | Low confidence, limited evidence |
