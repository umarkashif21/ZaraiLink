# Top 150 Search Queries — Exhaustive Coverage Selection

Each query is annotated with the angle it represents.
Format: `query text` → **[ANGLE]**

---

## GROUP A — Bare / Minimal (What the engine handles when given almost nothing)

1. `sugar` → **[BARE KEYWORD, default BUY]**
2. `dex` → **[3-CHAR ABBREVIATION, trigram match]**
3. `1702` → **[BARE HS CODE, cascade lookup]**
4. `SEAWALL` → **[COMPANY NAME, transaction fallback]**
5. `s` → **[SINGLE CHAR, graceful no-match]**

---

## GROUP B — Basic BUY Intent (Simplest valid purchase queries)

6. `buy sugar` → **[BASIC BUY, single product]**
7. `i want to buy dextrose anhydrous` → **[EXPLICIT BUY, full product name]**
8. `i need basmati rice` → **[NEED = BUY, common phrasing]**
9. `purchase refined sugar` → **[PURCHASE VERB, BUY intent]**
10. `looking for wheat` → **[LOOKING FOR = BUY, no supplier mention]**
11. `find me cotton yarn` → **[FIND ME = BUY, imperative]**
12. `i am interested in buying palm oil` → **[INTERESTED IN BUYING phrase]**
13. `want to get urea fertilizer` → **[WANT TO GET, casual BUY]**

---

## GROUP C — Basic SELL Intent (Simplest valid selling queries)

14. `sugar for sale` → **[FOR SALE phrase = SELL]**
15. `we are selling wheat` → **[WE ARE SELLING = SELL]**
16. `i have dextrose anhydrous for sale` → **[I HAVE X FOR SALE = SELL]**
17. `basmati rice in stock` → **[IN STOCK = SELL]**
18. `we export cotton yarn` → **[WE EXPORT = SELL]**
19. `i am a supplier of refined sugar` → **[I AM A SUPPLIER = SELL]**
20. `our company produces urea and we want to sell` → **[WE PRODUCE + SELL = SELL]**

---

## GROUP D — Find Suppliers (Semantic reversal — engine must catch BUY inside "find sellers")

21. `find suppliers of dextrose anhydrous` → **[FIND SUPPLIERS = BUY]**
22. `looking for sellers of refined sugar` → **[SEMANTIC REVERSAL — sellers = BUY]**
23. `looking for exporters of basmati rice` → **[EXPORTERS = BUY, not SELL]**
24. `who sells cotton yarn` → **[WHO SELLS = BUY]**
25. `find manufacturers of urea fertilizer` → **[MANUFACTURERS = BUY]**

---

## GROUP E — Find Buyers (SELL intent hidden in "find buyers")

26. `find buyers for basmati rice` → **[FIND BUYERS = SELL]**
27. `looking for importers of cotton yarn` → **[IMPORTERS = SELL]**
28. `who buys refined sugar` → **[WHO BUYS = SELL]**
29. `find companies interested in buying our wheat` → **[OUR PRODUCT = SELL]**

---

## GROUP F — Price Operator Queries (Every operator type the engine supports)

30. `sugar under $500` → **[WORD LTE operator]**
31. `wheat above $250` → **[WORD GTE operator]**
32. `dextrose anhydrous around $700` → **[RANGE ±15% operator]**
33. `rice <= $600` → **[SYMBOL LTE operator]**
34. `cotton >= $1000` → **[SYMBOL GTE operator]**
35. `palm oil at most $900` → **[AT MOST = LTE]**
36. `urea at least $250` → **[AT LEAST = GTE]**
37. `refined sugar not exceeding $400` → **[NOT EXCEEDING = LTE]**
38. `wheat starting from $200` → **[STARTING FROM = GTE]**
39. `sugar under five hundred dollars` → **[WRITTEN NUMBER, no digit]**
40. `dextrose approximately $650` → **[APPROXIMATE = RANGE]**

---

## GROUP G — Ranking Hint Queries (No price number — just ranking signal)

41. `cheap sugar` → **[RANKING: price_asc, no number]**
42. `affordable wheat` → **[RANKING: price_asc synonym]**
43. `premium dextrose anhydrous` → **[RANKING: price_desc]**
44. `bulk basmati rice` → **[RANKING: volume-heavy preset]**
45. `high quality refined sugar` → **[RANKING: price_desc implicit]**
46. `cheapest cotton yarn` → **[SUPERLATIVE price_asc]**
47. `best quality palm oil` → **[BEST QUALITY = price_desc]**

---

## GROUP H — Country Queries (Geographic filter activation)

48. `sugar from China` → **[COUNTRY FILTER: China]**
49. `wheat from Russia` → **[COUNTRY FILTER: Russia]**
50. `basmati rice from India` → **[COUNTRY FILTER: India]**
51. `palm oil from Malaysia` → **[COUNTRY FILTER: Malaysia]**
52. `cotton from USA` → **[COUNTRY FILTER: USA]**
53. `soybean from Brazil` → **[COUNTRY FILTER: Brazil]**
54. `import wheat from Ukraine` → **[IMPORT verb + COUNTRY]**
55. `Chinese sugar suppliers` → **[DEMONYM form of country]**

---

## GROUP I — Combined Multi-Criteria Queries (Maximum filter stack)

56. `dextrose anhydrous from China under $700` → **[PRODUCT + COUNTRY + PRICE]**
57. `refined sugar from Brazil below $400` → **[PRODUCT + COUNTRY + LTE]**
58. `basmati rice from India under $600` → **[PRODUCT + COUNTRY + LTE]**
59. `bulk palm oil from Malaysia below $900` → **[RANKING + COUNTRY + PRICE]**
60. `cheap wheat from Russia` → **[RANKING + COUNTRY, no number]**
61. `premium cotton yarn from Pakistan above $1000` → **[RANKING + COUNTRY + GTE]**
62. `find suppliers of dextrose from China under $700` → **[FIND + COUNTRY + PRICE]**
63. `looking for cheap basmati rice from India` → **[INTENT + RANKING + COUNTRY]**

---

## GROUP J — HS Code Queries (Every notation format)

64. `1702.3090` → **[HS: dotted notation]**
65. `17021990` → **[HS: bare digit string]**
66. `1702 30 90` → **[HS: space-separated]**
67. `1702-30-90` → **[HS: dash-separated]**
68. `HS code 1701.991` → **[HS: with explicit label]**
69. `tariff code 1001` → **[HS: tariff code prefix]**
70. `chapter 17` → **[HS: chapter-level lookup]**
71. `heading 1701` → **[HS: heading prefix]**

---

## GROUP K — Procurement / Formal Institutional Language

72. `RFQ for dextrose anhydrous` → **[PROCUREMENT acronym]**
73. `request for quotation refined sugar` → **[FORMAL PROCUREMENT phrase]**
74. `our company requires urea fertilizer` → **[COMPANY REQUIRES = BUY]**
75. `we are procuring basmati rice for our operations` → **[PROCURING verb]**
76. `sourcing cotton yarn for our textile mill in Faisalabad` → **[SOURCING + LOCAL CITY]**
77. `tender for wheat supply 5000 MT` → **[TENDER + VOLUME]**
78. `invite quotations for palm oil` → **[INVITE QUOTATIONS = BUY]**
79. `seeking quotation for dextrose anhydrous 100 MT` → **[SEEKING QUOTATION + VOLUME]**

---

## GROUP L — Volume / Quantity Specific

80. `sugar 1000 MT` → **[BARE PRODUCT + VOLUME]**
81. `buy 5000 MT wheat` → **[BUY + LARGE VOLUME]**
82. `need 100 MT dextrose anhydrous urgently` → **[NEED + VOLUME + URGENCY]**
83. `trial shipment basmati rice` → **[TRIAL SHIPMENT, small qty signal]**
84. `sugar FCL` → **[CONTAINER LOAD abbreviation]**
85. `bulk vessel wheat` → **[BULK VESSEL, very large shipment]**
86. `sample cotton yarn` → **[SAMPLE = minimal quantity]**

---

## GROUP M — Sector / Use-Case Specific (Industry context)

87. `dextrose for pharmaceutical IV` → **[PHARMA USE-CASE]**
88. `sugar for confectionery manufacturing` → **[FOOD INDUSTRY USE-CASE]**
89. `wheat for flour milling` → **[MILLING USE-CASE]**
90. `palm oil for biodiesel production` → **[ENERGY USE-CASE]**
91. `cotton for yarn spinning mill` → **[TEXTILE USE-CASE]**
92. `urea for agricultural use` → **[AGRICULTURE USE-CASE]**
93. `soybean for animal feed formulation` → **[FEED INDUSTRY USE-CASE]**

---

## GROUP N — Scope / Geography (Local Pakistan vs worldwide)

94. `local sugar suppliers Pakistan` → **[SCOPE: domestic Pakistan]**
95. `sugar suppliers in Karachi` → **[SCOPE: Pakistani city triggers domestic]**
96. `import sugar for our Karachi plant` → **[CITY inside BUY = domestic]**
97. `international dextrose suppliers` → **[SCOPE: worldwide]**
98. `global basmati rice suppliers` → **[SCOPE: worldwide, global synonym]**
99. `foreign cotton yarn suppliers` → **[SCOPE: worldwide, foreign synonym]**
100. `domestic wheat suppliers` → **[SCOPE: Pakistan, domestic synonym]**

---

## GROUP O — Spelling Errors (Typos the engine must recover from)

101. `suagr` → **[TYPO: transposed letters → sugar]**
102. `whaet` → **[TYPO: transposed letters → wheat]**
103. `dextroze anhydrous` → **[TYPO: z/s swap → dextrose]**
104. `basmati rce` → **[TYPO: missing letter → rice]**
105. `cottan yarn` → **[TYPO: wrong vowel → cotton]**
106. `ureea fertilizer` → **[TYPO: doubled vowel → urea]**
107. `palmm oil` → **[TYPO: doubled consonant → palm oil]**
108. `soybeen` → **[TYPO: wrong vowel → soybean]**
109. `refind sugar` → **[TYPO: wrong suffix → refined]**
110. `chickpeaz` → **[TYPO: z/s swap → chickpeas]**
111. `fructoze syrup` → **[TYPO: z/s swap → fructose]**
112. `lactos monohydrate` → **[TYPO: missing e → lactose]**

---

## GROUP P — Broken / Uneducated English (Very low proficiency users)

113. `sugar buying i want` → **[REVERSED WORD ORDER, BUY intent]**
114. `give me wheat cheap` → **[IMPERATIVE + RANKING, no verb "buy"]**
115. `cotton seller find me` → **[REVERSED, find seller = BUY]**
116. `need sugar 500 ton urgent` → **[MISSING ARTICLES + VOLUME + URGENCY]**
117. `where buy dextrose` → **[MISSING "can I", bare question]**
118. `good quality rice give me contact` → **[BROKEN PHRASE, wants supplier]**
119. `1000 ton wheat need` → **[VOLUME FIRST, verb last]**
120. `sugar people contact me` → **[PEOPLE = supplier, informal SELL or BUY]**
121. `which country sugar comes` → **[WRONG GRAMMAR, origin question]**
122. `how much cost dextrose` → **[MISSING VERB, price inquiry = BUY]**

---

## GROUP Q — Super Creative / Lateral (Unusual but meaningful descriptions)

123. `sweetener for my factory` → **[FUNCTION DESCRIPTION → sugar/dextrose/fructose]**
124. `fermentation feedstock` → **[INDUSTRIAL FUNCTION → glucose/dextrose/molasses]**
125. `IV fluid ingredient` → **[MEDICAL FUNCTION → dextrose anhydrous]**
126. `textile raw material` → **[MATERIAL CATEGORY → cotton]**
127. `biofuel feedstock` → **[ENERGY FUNCTION → molasses/ethanol/palm oil]**
128. `bakery raw material bulk` → **[FOOD FUNCTION → wheat flour/sugar/fat]**
129. `animal feed ingredient high protein` → **[FEED FUNCTION → soybean meal/fish meal]**
130. `crop growth booster nitrogen` → **[AGRI FUNCTION → urea fertilizer]**

---

## GROUP R — Unrelated Language, Correct Final Meaning (Metaphors / Nicknames)

131. `white gold of Pakistan` → **[METAPHOR → sugar OR cotton]**
132. `liquid sunshine` → **[METAPHOR → sunflower oil / palm oil]**
133. `hospital sugar` → **[NICKNAME → dextrose anhydrous (IV use)]**
134. `perfumed rice` → **[NICKNAME → basmati rice]**
135. `staff of life` → **[IDIOM → wheat / bread flour]**
136. `nature's fertilizer` → **[METAPHOR → urea / organic fertilizer]**

---

## GROUP S — Conversational / Chatbot Style (Informal, human-like phrasing)

137. `hi i need sugar suppliers urgently` → **[GREETING + BUY + URGENCY]**
138. `can you show me top dextrose anhydrous suppliers` → **[TOP-N + CONVERSATIONAL]**
139. `who are the biggest wheat exporters from Russia` → **[QUESTION FORM + COUNTRY]**
140. `i am a new buyer looking for basmati rice from India` → **[PERSONA + BUY + COUNTRY]**
141. `please help me find cotton yarn under $1200` → **[POLITE REQUEST + PRICE]**

---

## GROUP T — Advanced / Technical / Multi-Specification (Expert user queries)

142. `dextrose anhydrous 99.5% purity USP grade from China under $700 per MT` → **[GRADE + PURITY + COUNTRY + PRICE + UNIT]**
143. `white sugar ICUMSA 45 from Brazil FOB below $400` → **[GRADE + TRADE TERM + COUNTRY + PRICE]**
144. `wheat HRW protein 12.5% from USA under $350 per MT` → **[VARIETY + SPEC + COUNTRY + PRICE]**
145. `RBD palm oil RSPO certified from Malaysia below $950 per MT` → **[GRADE + CERTIFICATION + COUNTRY + PRICE]**
146. `urea granular 46-0-0 prilled from China under $300 bulk vessel` → **[GRADE + NPK RATIO + FORM + COUNTRY + PRICE + VOLUME MODE]**

---

## GROUP U — Ambiguous Intent Edge Cases (Engine must resolve correctly)

147. `sugar export` → **[AMBIGUOUS: "export" keyword → SELL]**
148. `we are sugar suppliers looking for buyers` → **[SELL: we are suppliers + find buyers]**
149. `find someone who wants to buy our cotton` → **[SELL: our product + wants to buy = find buyers]**
150. `sugar trade inquiry` → **[AMBIGUOUS: no clear intent → defaults to BUY]**

---

## Summary: Angles Covered

| Angle | Query Numbers |
|-------|--------------|
| Bare keyword / minimal input | 1–5 |
| Basic BUY intent (all verb forms) | 6–13 |
| Basic SELL intent (all signal types) | 14–20 |
| Find suppliers (semantic reversal to BUY) | 21–25 |
| Find buyers (SELL hidden in "find buyers") | 26–29 |
| Price operators (every operator type) | 30–40 |
| Ranking hints without numbers | 41–47 |
| Country filters | 48–55 |
| Combined multi-criteria | 56–63 |
| HS code (every notation format) | 64–71 |
| Procurement / formal language | 72–79 |
| Volume / quantity | 80–86 |
| Sector / use-case | 87–93 |
| Scope: Pakistan vs worldwide | 94–100 |
| Spelling errors (typos) | 101–112 |
| Broken / uneducated English | 113–122 |
| Creative / lateral descriptions | 123–130 |
| Metaphors / unrelated language | 131–136 |
| Conversational / chatbot style | 137–141 |
| Advanced / technical / multi-spec | 142–146 |
| Ambiguous intent edge cases | 147–150 |
