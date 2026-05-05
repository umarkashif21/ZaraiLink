import rapidfuzz

words = ['help', 'find', 'sugar', 'suppliers']
STANDARD_COUNTRIES = ['Pakistan', 'China', 'United States', 'India', 'Afghanistan', 'United Arab Emirates', 'Saudi Arabia', 'Germany', 'United Kingdom', 'Australia', 'Canada', 'Singapore', 'Malaysia', 'Indonesia', 'Turkey', 'Brazil', 'France', 'Italy', 'Spain', 'Japan', 'South Korea', 'Vietnam', 'Thailand', 'Egypt', 'South Africa', 'Nigeria', 'Kenya']

for w in words:
    print(w, rapidfuzz.process.extractOne(w, STANDARD_COUNTRIES, scorer=rapidfuzz.fuzz.WRatio, processor=rapidfuzz.utils.default_process, score_cutoff=75.0))
