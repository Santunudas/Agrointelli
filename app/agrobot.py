"""AgroBot - Bilingual Smart Farm Assistant Engine.

Provides instant, farmer-friendly agronomic guidance in English and Bangla (বাংলা).
Operates 100% offline using a comprehensive agricultural knowledge base covering
all 38 plant-disease classes from AgroIntelli, plus everyday farmer issues:
- Rice, Potato, Tomato, Wheat, Mustard, Brinjal, and vegetable diseases & pests
- Fertilizer dosages (Urea, DAP, Potash, Zinc, Boron, Compost)
- Irrigation management & AWD (Alternate Wetting and Drying)
- Acidic soil management & liming
- Organic bio-pesticide preparation (Neem oil, Trichoderma)
- Weather precautions (Rain, storm, frost, and dense fog)
- Official agricultural helplines (India & Bangladesh)
- Optional LLM integration (Gemini / Groq) if API keys are configured.
"""

import os
import re
import json
import datetime
import urllib.request
import urllib.error
from typing import Dict, List, Optional, Any, Tuple


class AgroBotEngine:
    """Bilingual offline/hybrid agronomy chatbot engine."""

    # Pre-compiled regex for performance
    _BANGLA_RE = re.compile(r"[\u0980-\u09FF]")
    _WORD_RE = re.compile(r"\b[\w\u0980-\u09FF]+\b")

    def __init__(self):
        self.kb = self._build_knowledge_base()
        self.disease_class_map = self._build_disease_class_map()
        self.crop_aliases = self._build_crop_aliases()
        self.problem_keywords = self._build_problem_keywords()
        # Pre-build flattened keyword sets for fast out-of-scope detection
        self._all_agri_keywords = self._build_agri_keyword_set()
        # Edge-case keyword patterns
        self._edge_case_patterns = self._build_edge_case_patterns()

    # -------------------------------------------------------------------------
    # Language Detection & Helpers
    # -------------------------------------------------------------------------
    @classmethod
    def contains_bangla(cls, text: str) -> bool:
        """Check if string contains Bengali script characters (U+0980 to U+09FF)."""
        return bool(cls._BANGLA_RE.search(text))

    def detect_language(self, text: str, user_pref: Optional[str] = None) -> str:
        """Determine language ('bn' for Bangla, 'en' for English)."""
        if user_pref in ("bn", "en"):
            return user_pref
        if self.contains_bangla(text):
            return "bn"

        # Check common romanized Bangla words
        banglish_indicators = [
            "dhan", "alu", "tometo", "morich", "poka", "majra", "shorisa", "begun",
            "kivabe", "sar", "sech", "rog", "beej", "chas", "shomosya", "dhosa",
            "pani", "mati", "jomi", "gach", "pata", "pokamakor", "dusta", "potash"
        ]
        text_lower = text.lower()
        words = self._WORD_RE.findall(text_lower)
        banglish_matches = sum(1 for w in words if w in banglish_indicators)
        if banglish_matches >= 2:
            return "bn"

        return "en"

    # -------------------------------------------------------------------------
    # Disease Class Mapping (Supports all 38 AgroIntelli Classes)
    # -------------------------------------------------------------------------
    def _build_disease_class_map(self) -> Dict[str, Dict[str, Any]]:
        return {
            "Apple___Apple_scab": {
                "title_en": "🍎 Apple Scab (Venturia inaequalis)",
                "title_bn": "🍎 আপেলের স্ক্যাব রোগ",
                "desc_en": "Causes olive-green to black velvety spots on leaves and scabby brown lesions on fruit.",
                "desc_bn": "আপেল গাছে জলপাই-সবুজ থেকে কালো মখমলের মতো দাগ হয় এবং ফলের ওপর খসখসে বাদামী দাগ পড়ে।",
                "organic_en": ["Rake and destroy fallen leaves in autumn.", "Prune orchard trees to improve aeration."],
                "organic_bn": ["শীতকালে গাছের ঝরে পড়া সব পাতা পুড়িয়ে ফেলুন।", "ডালপালা ছেঁটে আলো-বাতাস চলাচলের ব্যবস্থা করুন।"],
                "chemical_en": ["Spray Captan 50% WP @ 2.5 g/L OR Difenoconazole 25% EC @ 0.5 ml/L at green tip stage."],
                "chemical_bn": ["ক্যাপটান ৫০% ডব্লিউপি প্রতি লিটার জলে ২.৫ গ্রাম অথবা ডাইফেনোকোনাজোল ০.৫ মিলি/লিটার স্প্রে করুন।"],
            },
            "Apple___Black_rot": {
                "title_en": "🍎 Apple Black Rot & Canker (Botryosphaeria obtusa)",
                "title_bn": "🍎 আপেলের ব্ল্যাক রট ও ক্যাংকার রোগ",
                "desc_en": "Produces 'frog-eye' leaf spots and dark, sunken rot on developing fruit and woody cankers.",
                "desc_bn": "পাতায় ব্যাঙের চোখের মতো গোল দাগ হয় এবং আপেল ফল কালো হয়ে পচে যায়।",
                "organic_en": ["Prune out dead wood and mummified fruits left hanging on trees."],
                "organic_bn": ["শুকিয়ে যাওয়া আক্রান্ত ডাল ও মরা ফল গাছ থেকে ছেঁটে ধ্বংস করুন।"],
                "chemical_en": ["Spray Mancozeb 75% WP @ 2.5 g/L OR Thiophanate-methyl 70% WP @ 1 g/L water."],
                "chemical_bn": ["ম্যানকোজেব ৭৫% ডব্লিউপি প্রতি লিটার জলে ২.৫ গ্রাম মিশিয়ে স্প্রে করুন।"],
            },
            "Apple___Cedar_apple_rust": {
                "title_en": "🍎 Cedar Apple Rust (Gymnosporangium juniperi-virginianae)",
                "title_bn": "🍎 আপেলের সিডার মরিচা রোগ",
                "desc_en": "Bright orange-yellow circular spots develop on upper leaf surfaces.",
                "desc_bn": "আপেল পাতার ওপর উজ্জ্বল কমলা-হলুদ রঙের বৃত্তাকার ফোস্কার মতো দাগ দেখা যায়।",
                "organic_en": ["Remove nearby red cedar or juniper trees that serve as alternate fungal hosts."],
                "organic_bn": ["বাগানের আশেপাশে থাকা বিকল্প পোষক গাছ কেটে পরিষ্কার রাখুন।"],
                "chemical_en": ["Apply Myclobutanil 10% WP @ 1 g/L OR Mancozeb 75% WP @ 2.5 g/L at pink bud stage."],
                "chemical_bn": ["মাইক্লোবুটানিল অথবা ম্যানকোজেব ফুল আসার শুরুতে স্প্রে করুন।"],
            },
            "Cherry___Powdery_mildew": {
                "title_en": "🍒 Cherry Powdery Mildew (Podosphaera clandestina)",
                "title_bn": "🍒 চেরির পাউডারি মিলডিউ রোগ",
                "desc_en": "White powdery fungal growth covers young leaves, causing leaf curling and distorted shoots.",
                "desc_bn": "পাতার ওপর সাদা পাউডার বা ময়দার মতো আস্তরণ পড়ে এবং পাতা বিকৃত হয়ে কুঁকড়ে যায়।",
                "organic_en": ["Avoid overhead irrigation; prune inner branches for direct sunlight.", "Spray Potassium Bicarbonate @ 3 g/L."],
                "organic_bn": ["গাছের ওপর পানি ছিটাবেন না; ডালপালা ছেঁটে রোদ প্রবেশের ব্যবস্থা করুন।", "নিম তেল স্প্রে করুন।"],
                "chemical_en": ["Spray Wettable Sulphur 80% WP @ 2.5 g/L OR Hexaconazole 5% SC @ 1 ml/L water."],
                "chemical_bn": ["সালফার ৮০% ডব্লিউপি প্রতি লিটার জলে ২.৫ গ্রাম অথবা হেক্সাকোনাজোল ১ মিলি/লিটার স্প্রে করুন।"],
            },
            "Corn___Cercospora_leaf_spot Gray_leaf_spot": {
                "title_en": "🌽 Corn Gray Leaf Spot (Cercospora zeae-maydis)",
                "title_bn": "🌽 ভুট্টার গ্রে লিফ স্পট (ধূসর পাতা দাগ রোগ)",
                "desc_en": "Rectangular grayish-tan lesions running parallel to leaf veins, coalescing into blighted leaves.",
                "desc_bn": "ভুট্টার পাতার শিরার সমান্তরালে লম্বাটে ধূসর-বাদামী দাগ হয় এবং পুরো পাতা শুকিয়ে যায়।",
                "organic_en": ["Practice crop rotation with non-host crops (soybean/pulses).", "Plough under crop residues deep into soil."],
                "organic_bn": ["পরপর এক জমিতে ভুট্টা চাষ না করে ডালজাতীয় ফসলের সাথে ফসল পর্যায় অবলম্বন করুন।", "ফসল তোলার পর ফসলের অবশিষ্টাংশ মাটির গভীরে পুঁতে ফেলুন।"],
                "chemical_en": ["Spray Azoxystrobin + Difenoconazole (Amistar Top) @ 1 ml/L OR Propiconazole 25% EC @ 1 ml/L."],
                "chemical_bn": ["এমিস্টার টপ (এজোক্সিস্ট্রোবিন + ডাইফেনোকোনাজোল) প্রতি লিটার জলে ১ মিলি অথবা টিল্ট ১ মিলি/লিটার স্প্রে করুন।"],
            },
            "Corn___Common_rust": {
                "title_en": "🌽 Corn Common Rust (Puccinia sorghi)",
                "title_bn": "🌽 ভুট্টার মরিচা রোগ (কমন রাস্ট)",
                "desc_en": "Small, powdery golden-brown to cinnamon pustules scatter across both upper and lower leaf surfaces.",
                "desc_bn": "পাতার উভয় পিঠে লালচে-বাদামী রঙের পাউডারের মতো ফোস্কা বা মরিচা দাগ হয়।",
                "organic_en": ["Plant certified rust-resistant corn hybrid varieties."],
                "organic_bn": ["মরিচা প্রতিরোধী হাইব্রিড জাতের ভুট্টা চাষ করুন।"],
                "chemical_en": ["Spray Mancozeb 75% WP @ 2.5 g/L OR Tebuconazole 25% WG @ 1 g/L water."],
                "chemical_bn": ["ম্যানকোজেব ৭৫% ডব্লিউপি প্রতি লিটার পানিতে ২.৫ গ্রাম মিশিয়ে স্প্রে করুন।"],
            },
            "Corn___Northern_Leaf_Blight": {
                "title_en": "🌽 Corn Northern Leaf Blight (Exserohilum turcicum)",
                "title_bn": "🌽 ভুট্টার নর্দার্ন লিফ ব্লাইট (পাতা পোড়া রোগ)",
                "desc_en": "Long cigar-shaped or elliptical grayish-green water-soaked lesions that later turn tan and brittle.",
                "desc_bn": "পাতার ওপর সিগার বা নৌকার আকৃতির লম্বাটে ছাই রঙের দাগ দেখা যায় এবং পাতা পুড়ে যাওয়ার মতো শুকিয়ে যায়।",
                "organic_en": ["Bury crop debris through deep tillage.", "Rotate with non-grass crops."],
                "organic_bn": ["জমি গভীর চাষ দিন এবং রবি মৌসুমে ফসল বদল করুন।"],
                "chemical_en": ["Apply Azoxystrobin 18.2% + Difenoconazole 11.4% SC @ 1 ml/L OR Propiconazole 25% EC @ 1 ml/L."],
                "chemical_bn": ["প্রোপিকোনাজোল ২৫% ইসি (যেমন টিল্ট) প্রতি লিটার পানিতে ১ মিলি মিশিয়ে স্প্রে করুন।"],
            },
            "Grape___Black_rot": {
                "title_en": "🍇 Grape Black Rot (Guignardia bidwellii)",
                "title_bn": "🍇 আঙুরের ব্ল্যাক রট (কালো পচা রোগ)",
                "desc_en": "Berries shrivel into hard, black, wrinkled mummies; leaves exhibit reddish-brown spots with black dots.",
                "desc_bn": "আঙুরের ফল কুঁচকে শক্ত ও কালো শুঁটকির মতো হয়ে পচে যায় এবং পাতায় বাদামী দাগ হয়।",
                "organic_en": ["Prune out all dried mummified grape clusters and destroy them."],
                "organic_bn": ["আক্রান্ত সব শুকনা আঙুরের থোকা কেটে পুড়িয়ে ফেলুন।"],
                "chemical_en": ["Spray Mancozeb 75% WP @ 2.5 g/L OR Kresoxim-methyl 44.3% SC @ 0.7 ml/L water."],
                "chemical_bn": ["ম্যানকোজেব ২.৫ গ্রাম অথবা ক্রেসক্সিম-মিথাইল ০.৭ মিলি প্রতি লিটার জলে স্প্রে করুন।"],
            },
            "Grape___Esca_(Black_Measles)": {
                "title_en": "🍇 Grape Esca / Black Measles (Fomitiporia / Phaeomoniella complex)",
                "title_bn": "🍇 আঙুরের এসকা / ব্ল্যাক মিজলস রোগ",
                "desc_en": "Tiger-stripe patterns on leaves and dark spotted 'measles' appearance on berries with vascular wood necrosis.",
                "desc_bn": "পাতায় বাঘের ডোরাকাটা দাগ দেখা যায় এবং আঙুর ফলের ওপর ছোট ছোট কালো তিলের মতো দাগ হয়।",
                "organic_en": ["Protect pruning wounds with wound sealant paste.", "Disinfect pruning shears between vines."],
                "organic_bn": ["ছাঁটাই করার পর কাটা অংশে বর্দো পেস্ট বা ছত্রাকনাশকের প্রলেপ দিন।"],
                "chemical_en": ["Paint wounds with Thiophanate-methyl paste. Soil drenching with systemic Trichoderma."],
                "chemical_bn": ["ছাঁটাইয়ের মুখে থায়োফেনেট-মিথাইল পেস্ট লাগান এবং ট্রাইকোডার্মা মাটিতে প্রয়োগ করুন।"],
            },
            "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)": {
                "title_en": "🍇 Grape Leaf Blight / Isariopsis Spot",
                "title_bn": "🍇 আঙুরের পাতা পোড়া রোগ",
                "desc_en": "Sub-circular to irregular dark brown spots that expand, causing premature defoliation.",
                "desc_bn": "পাতার ওপর বাদামী রঙের অনিয়মিত দাগ হয় এবং পাতা অকালে ঝরে পড়ে।",
                "organic_en": ["Improve canopy ventilation by training vines on trellises properly."],
                "organic_bn": ["মাচায় লতা ভালোভাবে ছড়িয়ে দিন যাতে প্রচুর আলো-বাতাস পায়।"],
                "chemical_en": ["Spray Copper Oxychloride 50% WP @ 3 g/L OR Mancozeb 75% WP @ 2.5 g/L."],
                "chemical_bn": ["কপার অক্সিক্লোরাইড ৫০% ডব্লিউপি প্রতি লিটার জলে ৩ গ্রাম মিশিয়ে স্প্রে করুন।"],
            },
            "Orange___Haunglongbing_(Citrus_greening)": {
                "title_en": "🍊 Citrus Greening / Huanglongbing (Candidatus Liberibacter)",
                "title_bn": "🍊 লেবু ও কমলার সাইট্রাস গ্রিনিং রোগ",
                "desc_en": "Asymmetrical blotchy yellow mottling on leaves; fruits remain small, lopsided, sour, and fail to color evenly.",
                "desc_bn": "পাতার শিরাগুলো হলুদ হয়ে অসমান ছোপ ছোপ হলুদ দাগ হয়। ফল ছোট, টক ও বাঁকা হয় এবং ঠিকমতো পাকে না।",
                "organic_en": ["Use certified disease-free nursery saplings.", "Install yellow sticky traps to capture Asian Citrus Psyllids (the insect vector)."],
                "organic_bn": ["রোগমুক্ত নার্সারি থেকে কলম চারা সংগ্রহ করুন।", "হলুদ আঠালো ফাঁদ ব্যবহার করে রোগ ছড়ানো সাইলিড মাছি দমন করুন।"],
                "chemical_en": ["Control the psyllid vector: Spray Imidacloprid 17.8% SL @ 0.5 ml/L OR Thiamethoxam 25% WG @ 0.3 g/L."],
                "chemical_bn": ["মাছি পোকা দমনে ইমিডাক্লোপ্রিড ১৭.৮% এসএল ০.৫ মিলি অথবা থায়ামেথোক্সাম ০.৩ গ্রাম প্রতি লিটার জলে স্প্রে করুন।"],
            },
            "Peach___Bacterial_spot": {
                "title_en": "🍑 Peach Bacterial Spot (Xanthomonas arboricola pv. pruni)",
                "title_bn": "🍑 পীচের ব্যাকটেরিয়াল স্পট রোগ",
                "desc_en": "Small water-soaked angular leaf spots that drop out, giving a 'shot-hole' appearance. Cracks appear on fruit.",
                "desc_bn": "পাতায় ছোট ছোট ভেজা দাগ হয় যা শুকিয়ে খসে পড়ে চালুনির মতো ফুটো (শট হোল) তৈরি করে।",
                "organic_en": ["Plant windbreaks around the orchard to minimize sandblast injury on leaves."],
                "organic_bn": ["বাগানের চারধারে বাতাসের গতি রোধে সীমানা গাছ লাগান।"],
                "chemical_en": ["Spray Copper Hydroxide @ 2 g/L during dormancy or early bud swell stage."],
                "chemical_bn": ["কপার হাইড্রোক্সাইড প্রতি লিটার পানিতে ২ গ্রাম মিশিয়ে স্প্রে করুন।"],
            },
            "Pepper,_bell___Bacterial_spot": {
                "title_en": "🫑 Bell Pepper & Chilli Bacterial Spot (Xanthomonas campestris)",
                "title_bn": "🫑 ক্যাপসিকাম ও মরিচের ব্যাকটেরিয়াল স্পট রোগ",
                "desc_en": "Small, water-soaked, blister-like dark spots on leaves with yellow halos, causing extensive leaf drop.",
                "desc_bn": "পাতায় ছোট ছোট পানির মতো ভেজা ফোস্কার মতো কালচে দাগ হয় এবং পাতার চারধারে হলুদ বলয় থাকে। পাতা ঝরে যায়।",
                "organic_en": ["Treat seeds in hot water (50°C for 25 min) or with Trichoderma before nursery sowing.", "Avoid overhead irrigation."],
                "organic_bn": ["বীজ শোধন করে রোপণ করুন। গাছের ওপর জল ছিটাবেন না, গোড়ায় সেচ দিন।"],
                "chemical_en": ["Spray Copper Oxychloride 50% WP @ 2.5 g/L + Streptocycline @ 0.1 g/L water."],
                "chemical_bn": ["কপার অক্সিক্লোরাইড ২.৫ গ্রাম এবং স্ট্রেপ্টোসাইক্লিন ০.১ গ্রাম প্রতি লিটার পানিতে মিশিয়ে স্প্রে করুন।"],
            },
            "Potato___Early_blight": {
                "title_en": "🥔 Potato Early Blight (Alternaria solani)",
                "title_bn": "🥔 আলুর আগাম ধসা (আর্লি ব্লাইট) রোগ",
                "desc_en": "Brown-black circular spots with distinct concentric rings ('target board pattern') on older lower leaves.",
                "desc_bn": "নিচের পুরোনো পাতায় বাদামী বা কালচে চক্রাকার গোল রিং বা টার্গেট বোর্ডের মতো দাগ দেখা যায়।",
                "organic_en": ["Prune bottom diseased foliage.", "Apply straw mulch to prevent soil splashing onto leaves."],
                "organic_bn": ["নিচের আক্রান্ত পাতাগুলো তুলে ফেলুন। গোড়ায় খড়ের মালচিং দিন।"],
                "chemical_en": ["Spray Difenoconazole 25% EC (Score) @ 0.5 ml/L OR Azoxystrobin 23% SC @ 1 ml/L water."],
                "chemical_bn": ["ডাইফেনোকোনাজোল ২৫% ইসি (স্কোর) ০.৫ মিলি অথবা ম্যানকোজেব ২.৫ গ্রাম প্রতি লিটার জলে স্প্রে করুন।"],
            },
            "Potato___Late_blight": {
                "title_en": "🥔 Potato Late Blight (Phytophthora infestans)",
                "title_bn": "🥔 আলুর নাবি ধসা (লেট ব্লাইট) মহামারী রোগ",
                "desc_en": "Dark water-soaked lesions on leaf margins with white downy mold on undersides during cool, humid, foggy weather.",
                "desc_bn": "কুয়াশাচ্ছন্ন ঠাণ্ডা আবহাওয়ায় পাতার ডগায় ভেজা কালো দাগ হয় এবং পাতার নিচে সাদা তুলোর মতো ছত্রাক গজায়। দ্রুত পুরো গাছ পচে যায়।",
                "organic_en": ["Do not irrigate fields during dense fog or cloudy weather.", "Earth up soil high around plant bases."],
                "organic_bn": ["কুয়াশার সময় জমিতে সেচ দেবেন না। গাছের গোড়ায় মাটি উঁচু করে ভেলি বেঁধে দিন।"],
                "chemical_en": ["Preventive: Mancozeb 75% WP @ 2.5 g/L.", "Curative: Cymoxanil 8% + Mancozeb 64% WP (Curzate) @ 2.5 g/L OR Metalaxyl + Mancozeb (Ridomil Gold) @ 2 g/L."],
                "chemical_bn": ["কুয়াশা শুরু হলে: ম্যানকোজেব ২.৫ গ্রাম/লিটার। রোগ দেখা দিলে: কারজেট ২.৫ গ্রাম অথবা রিডোমিল গোল্ড ২ গ্রাম প্রতি লিটার জলে স্প্রে করুন।"],
            },
            "Squash___Powdery_mildew": {
                "title_en": "🎃 Squash & Pumpkin Powdery Mildew (Podosphaera xanthii)",
                "title_bn": "🎃 কুমড়া ও লাউয়ের পাউডারি মিলডিউ রোগ",
                "desc_en": "White, talcum powder-like fungal patches on leaf surfaces that cause yellowing, browning, and premature drying.",
                "desc_bn": "পাতার ওপর সাদা পাউডার বা চকের গুঁড়োর মতো আস্তরণ পড়ে এবং পাতা হলদে হয়ে শুকিয়ে যায়।",
                "organic_en": ["Spray Baking Soda solution (5g/L water + few drops of dish soap).", "Spray diluted milk (1 part milk : 9 parts water) in morning sun."],
                "organic_bn": ["বেকিং সোডা দ্রবণ (প্রতি লিটার জলে ৫ গ্রাম বেকিং সোডা ও সামান্য লিকুইড সাবান) স্প্রে করুন।", "নিম তেল স্প্রে করুন।"],
                "chemical_en": ["Spray Hexaconazole 5% SC @ 1 ml/L OR Wettable Sulphur 80% WP @ 2.5 g/L water."],
                "chemical_bn": ["হেক্সাকোনাজোল ৫% এসসি প্রতি লিটার পানিতে ১ মিলি অথবা সালফার ২.৫ গ্রাম/লিটার স্প্রে করুন।"],
            },
            "Strawberry___Leaf_scorch": {
                "title_en": "🍓 Strawberry Leaf Scorch (Diplocarpon earlianum)",
                "title_bn": "🍓 স্ট্রবেরির লিফ স্কর্চ (পাতা ঝলসানো রোগ)",
                "desc_en": "Irregular purple to reddish-brown blotches without bright centers that coalesce, making leaves look scorched by fire.",
                "desc_bn": "পাতার ওপর বেগুনী থেকে লালচে-বাদামী ছোপ হয় এবং পুরো পাতা আগুনে ঝলসানোর মতো পুড়ে যায়।",
                "organic_en": ["Remove old, infected foliage immediately after harvesting.", "Avoid wetting leaves while watering."],
                "organic_bn": ["ফল তোলার পর পুরোনো আক্রান্ত পাতা কেটে নষ্ট করুন। গাছের পাতায় পানি না ফেলে গোড়ায় ড্রিপ দিয়ে জল দিন।"],
                "chemical_en": ["Spray Captan 50% WP @ 2.5 g/L OR Pyraclostrobin 20% WG @ 1 g/L water."],
                "chemical_bn": ["ক্যাপটান ৫০% ডব্লিউপি প্রতি লিটার জলে ২.৫ গ্রাম মিশিয়ে স্প্রে করুন।"],
            },
            "Tomato___Bacterial_spot": {
                "title_en": "🍅 Tomato Bacterial Spot (Xanthomonas vesicatoria)",
                "title_bn": "🍅 টমেটোর ব্যাকটেরিয়াল স্পট রোগ",
                "desc_en": "Small, greasy, dark brown spots on leaves and scabby raised pimple-like spots on green tomatoes.",
                "desc_bn": "পাতার ওপর ছোট ছোট তেলতেলে কালো দাগ হয় এবং কাঁচা টমেটোর গায়ে খসখসে গুটি গুটি দাগ দেখা যায়।",
                "organic_en": ["Mulch under plants and avoid touching plants when they are wet with dew."],
                "organic_bn": ["গাছের গোড়ায় খড় দিয়ে মালচিং করুন এবং সকালে শিশির থাকা অবস্থায় গাছে হাত দেবেন না।"],
                "chemical_en": ["Spray Copper Oxychloride 50% WP @ 2.5 g/L + Streptocycline @ 0.1 g/L water."],
                "chemical_bn": ["কপার অক্সিক্লোরাইড ২.৫ গ্রাম ও স্ট্রেপ্টোসাইক্লিন ০.১ গ্রাম প্রতি লিটার জলে স্প্রে করুন।"],
            },
            "Tomato___Early_blight": {
                "title_en": "🍅 Tomato Early Blight (Alternaria solani)",
                "title_bn": "🍅 টমেটোর আগাম ধসা (আর্লি ব্লাইট)",
                "desc_en": "Brown circular spots with concentric rings starting on lower mature leaves, expanding upwards.",
                "desc_bn": "নিচের পুরোনো পাতায় গোল গোল চক্রাকার দাগ হয় এবং পাতার চারপাশ হলুদ হয়ে পাতা ঝরে পড়ে।",
                "organic_en": ["Remove the bottom 12 inches of leaves to prevent soil-borne fungal splash.", "Stake plants upright."],
                "organic_bn": ["গাছের নিচের দিকের পুরোনো পাতা কেটে ফেলে দিন এবং গাছ খুঁটি দিয়ে সোজা করে বেঁধে রাখুন।"],
                "chemical_en": ["Spray Azoxystrobin 23% SC @ 1 ml/L OR Mancozeb 75% WP @ 2.5 g/L water."],
                "chemical_bn": ["এজোক্সিস্ট্রোবিন ১ মিলি অথবা ম্যানকোজেব ২.৫ গ্রাম প্রতি লিটার জলে মিশিয়ে স্প্রে করুন।"],
            },
            "Tomato___Late_blight": {
                "title_en": "🍅 Tomato Late Blight (Phytophthora infestans)",
                "title_bn": "🍅 টমেটোর নাবি ধসা (লেট ব্লাইট)",
                "desc_en": "Large greasy water-soaked brown lesions on leaves and hard brown greasy rot on tomato fruits.",
                "desc_bn": "পাতায় দ্রুত ছড়িয়ে পড়া ভেজা বাদামী দাগ এবং ফলের ওপর শক্ত চামড়ার মতো বাদামী পচন সৃষ্টি হয়।",
                "organic_en": ["Destroy severely infected plants immediately.", "Grow in well-ventilated raised beds."],
                "organic_bn": ["মারাত্মক আক্রান্ত গাছ তুলে মাটিতে পুঁতে ফেলুন। বাতাস চলাচল উপযোগী উঁচু বেডে চারা লাগান।"],
                "chemical_en": ["Spray Cymoxanil + Mancozeb (Curzate) @ 2.5 g/L OR Metalaxyl + Mancozeb (Ridomil) @ 2 g/L water."],
                "chemical_bn": ["কারজেট ২.৫ গ্রাম অথবা রিডোমিল গোল্ড ২ গ্রাম প্রতি লিটার পানিতে মিশিয়ে স্প্রে করুন।"],
            },
            "Tomato___Leaf_Mold": {
                "title_en": "🍅 Tomato Leaf Mold (Passalora fulva)",
                "title_bn": "🍅 টমেটোর লিফ মোল্ড (পাতার ছত্রাক)",
                "desc_en": "Pale green or yellow spots on the upper leaf surface with olive-brown velvety fungal mold underneath.",
                "desc_bn": "পাতার উপরিভাগে ফ্যাকাসে হলুদ দাগ হয় এবং নিচের পিঠে জলপাই-সবুজ মখমলের মতো ছত্রাক জন্মায়।",
                "organic_en": ["Reduce greenhouse humidity below 85% with fans.", "Prune excess suckers for good air flow."],
                "organic_bn": ["গাছের অতিরিক্ত ডালপালা ও সাকার ছাঁটাই করুন যাতে প্রচুর বাতাস চলাচল করতে পারে।"],
                "chemical_en": ["Spray Difenoconazole 25% EC @ 0.5 ml/L OR Chlorothalonil 75% WP @ 2 g/L water."],
                "chemical_bn": ["ডাইফেনোকোনাজোল ০.৫ মিলি অথবা ক্লোরোথ্যালোনিল ২ গ্রাম প্রতি লিটার পানিতে স্প্রে করুন।"],
            },
            "Tomato___Septoria_leaf_spot": {
                "title_en": "🍅 Tomato Septoria Leaf Spot (Septoria lycopersici)",
                "title_bn": "🍅 টমেটোর সেপ্টোরিয়া পাতার দাগ",
                "desc_en": "Numerous small circular spots with gray/white centers and dark brown borders with tiny black dots.",
                "desc_bn": "পাতায় অসংখ্য ছোট ছোট গোল দাগ দেখা যায় যার মাঝখানটা ছাই রঙের এবং কিনারা কালচে-বাদামী।",
                "organic_en": ["Avoid overhead watering; disinfect garden stakes and cages with bleach."],
                "organic_bn": ["পাতায় জল ছিটানো বন্ধ রাখুন; মাটির ওপর মালচিং ব্যবহার করুন।"],
                "chemical_en": ["Spray Chlorothalonil 75% WP @ 2 g/L OR Mancozeb 75% WP @ 2.5 g/L water."],
                "chemical_bn": ["ক্লোরোথ্যালোনিল ২ গ্রাম অথবা ম্যানকোজেব ২.৫ গ্রাম প্রতি লিটার জলে মিশিয়ে স্প্রে করুন।"],
            },
            "Tomato___Spider_mites Two-spotted_spider_mite": {
                "title_en": "🍅 Tomato Two-Spotted Spider Mites (Tetranychus urticae)",
                "title_bn": "🍅 টমেটোর লাল মাকড় (স্পাইডার মাইট)",
                "desc_en": "Fine yellow stippling on leaves, severe bronzing, and delicate silk webbing on leaf undersides.",
                "desc_bn": "পাতায় অজস্র ক্ষুদ্র হলুদ বিন্দুর মতো দাগ হয়, পাতা তামাটে রঙ ধারণ করে এবং পাতার নিচে সূক্ষ্ম জালের সৃষ্টি হয়।",
                "organic_en": ["Spray powerful water jet to wash webbing off undersides.", "Spray Neem Oil @ 5 ml/L with soap."],
                "organic_bn": ["জোরে পানির স্প্রে করে পাতার নিচের জাল ধুয়ে ফেলুন। নিম তেল ৫ মিলি প্রতি লিটার জলে মিশিয়ে স্প্রে করুন।"],
                "chemical_en": ["Spray Spiromesifen 22.9% SC (Oberon) @ 1 ml/L OR Abamectin 1.9% EC @ 1 ml/L water."],
                "chemical_bn": ["ওবেরন (স্পাইরোমেসিফেন) প্রতি লিটার পানিতে ১ মিলি অথবা এবামেকটিন ১ মিলি/লিটার স্প্রে করুন।"],
            },
            "Tomato___Target_Spot": {
                "title_en": "🍅 Tomato Target Spot (Corynespora cassiicola)",
                "title_bn": "🍅 টমেটোর টার্গেট স্পট রোগ",
                "desc_en": "Small necrotic brown lesions that enlarge with concentric target-board rings on leaves and fruit.",
                "desc_bn": "পাতায় ও ফলের ওপর গোল বাদামী রিং রিং দাগ হয় যা দেখতে লক্ষ্যভেদী নিশানা বা টার্গেটের মতো।",
                "organic_en": ["Ensure good field spacing and prune lower leaves."],
                "organic_bn": ["গাছ থেকে গাছের পর্যাপ্ত দূরত্ব বজায় রাখুন এবং নিচের পাতা কেটে দিন।"],
                "chemical_en": ["Spray Azoxystrobin + Difenoconazole @ 1 ml/L OR Chlorothalonil @ 2 g/L water."],
                "chemical_bn": ["এমিস্টার টপ ১ মিলি অথবা ম্যানকোজেব ২.৫ গ্রাম প্রতি লিটার জলে স্প্রে করুন।"],
            },
            "Tomato___Tomato_Yellow_Leaf_Curl_Virus": {
                "title_en": "🍅 Tomato Yellow Leaf Curl Virus (TYLCV)",
                "title_bn": "🍅 টমেটোর পাতা কোঁকড়ানো ভাইরাস রোগ",
                "desc_en": "Severe upward leaf curling, yellowing of leaf margins, stunted growth, and heavy flower drop transmitted by Whiteflies.",
                "desc_bn": "পাতাগুলো উপরের দিকে নৌকার মতো কুঁকড়ে যায়, পাতার কিনার হলুদ হয় এবং গাছের বৃদ্ধি থমকে যায়। সাদা মাছি এই ভাইরাস ছড়ায়।",
                "organic_en": ["Install Yellow Sticky Traps @ 15 traps/acre.", "Uproot and bury infected plants immediately."],
                "organic_bn": ["হলুদ আঠালো ফাঁদ বিঘা প্রতি ৪-৫টি টাঙান। মারাত্মক আক্রান্ত গাছ তুলে মাটিতে পুঁতে ফেলুন।"],
                "chemical_en": ["Control the Whitefly vector: Spray Imidacloprid 17.8% SL @ 0.5 ml/L OR Acetamiprid 20% SP @ 0.5 g/L."],
                "chemical_bn": ["বাহক সাদা মাছি দমনে ইমিডাক্লোপ্রিড ০.৫ মিলি অথবা এসিটামিপ্রিড ০.৫ গ্রাম প্রতি লিটার পানিতে স্প্রে করুন।"],
            },
            "Tomato___Tomato_mosaic_virus": {
                "title_en": "🍅 Tomato Mosaic Virus (ToMV)",
                "title_bn": "🍅 টমেটোর মোজাইক ভাইরাস রোগ",
                "desc_en": "Mottled light and dark green patterns on leaves with distortion and fern-like leaf growth, spread mechanically.",
                "desc_bn": "পাতায় হালকা ও গাঢ় সবুজ রঙের ছোপ ছোপ মোজাইক নকশার মতো দাগ ফুটে ওঠে এবং পাতা সরু হয়ে যায়।",
                "organic_en": ["Wash hands with milk or soap before touching plants (smokers must avoid touching plants).", "Rogue infected plants."],
                "organic_bn": ["গাছে হাত দেওয়ার আগে সাবান দিয়ে হাত ধুয়ে নিন (ধূমপায়ী ব্যক্তিরা গাছে হাত দেওয়া থেকে বিরত থাকুন)।"],
                "chemical_en": ["No chemical cures viruses. Focus on eliminating aphids and preventing sap transmission."],
                "chemical_bn": ["ভাইরাস সরাসরি মারার কোনো ঔষধ নেই। রোগাক্রান্ত গাছ তুলে ফেলুন ও চুষি পোকা দমন করুন।"],
            }
        }

    # -------------------------------------------------------------------------
    # Comprehensive Bilingual Agronomy Knowledge Base
    # -------------------------------------------------------------------------
    def _build_knowledge_base(self) -> List[Dict[str, Any]]:
        """Load and validate the versioned, source-aware knowledge dataset."""
        data_path = os.path.join(os.path.dirname(__file__), "data", "agrobot_knowledge.json")
        with open(data_path, encoding="utf-8") as knowledge_file:
            dataset = json.load(knowledge_file)

        if not isinstance(dataset, dict):
            raise ValueError("AgroBot knowledge base root must be an object")
        if type(dataset.get("schema_version")) is not int or dataset["schema_version"] != 1:
            raise ValueError("Unsupported AgroBot knowledge base schema version")
        if not isinstance(dataset.get("dataset_version"), str) or not dataset["dataset_version"].strip():
            raise ValueError("AgroBot knowledge base must have a dataset_version")
        if not isinstance(dataset.get("target_geography"), str) or not dataset["target_geography"].strip():
            raise ValueError("AgroBot knowledge base must have a target_geography")

        entries = dataset.get("entries")
        if not isinstance(entries, list):
            raise ValueError("AgroBot knowledge base 'entries' must be a list")

        required_fields = {
            "id", "category", "crops", "keywords_en", "keywords_bn",
            "title_en", "title_bn", "summary_en", "summary_bn",
            "organic_en", "organic_bn", "chemical_en", "chemical_bn",
            "suggestions_en", "suggestions_bn", "provenance",
        }
        text_fields = {
            "category", "title_en", "title_bn", "summary_en", "summary_bn",
        }
        list_fields = {
            "crops", "keywords_en", "keywords_bn", "organic_en", "organic_bn",
            "chemical_en", "chemical_bn", "suggestions_en", "suggestions_bn",
        }
        provenance_fields = {"source_name", "source_url", "region", "review_status", "last_reviewed"}
        seen_ids = set()
        for index, item in enumerate(entries):
            if not isinstance(item, dict):
                raise ValueError(f"AgroBot knowledge entry {index} must be an object")
            missing = required_fields.difference(item)
            if missing:
                raise ValueError(
                    f"AgroBot knowledge entry {index} is missing fields: {', '.join(sorted(missing))}"
                )
            if not isinstance(item["id"], str) or not item["id"].strip():
                raise ValueError(f"AgroBot knowledge entry {index} has an invalid id")
            if item["id"] in seen_ids:
                raise ValueError(f"Duplicate AgroBot knowledge entry id: {item['id']}")
            seen_ids.add(item["id"])
            for field in text_fields:
                if not isinstance(item[field], str):
                    raise ValueError(f"AgroBot knowledge entry '{item['id']}' field '{field}' must be a string")
            for field in list_fields:
                if not isinstance(item[field], list) or not all(isinstance(value, str) for value in item[field]):
                    raise ValueError(f"AgroBot knowledge entry '{item['id']}' field '{field}' must be a list of strings")

            provenance = item["provenance"]
            if not isinstance(provenance, dict) or not provenance_fields.issubset(provenance):
                raise ValueError(f"AgroBot knowledge entry '{item['id']}' has incomplete provenance metadata")
            if not isinstance(provenance["source_name"], str) or not provenance["source_name"].strip():
                raise ValueError(f"AgroBot knowledge entry '{item['id']}' must identify its source")
            if provenance["source_url"] is not None and not isinstance(provenance["source_url"], str):
                raise ValueError(f"AgroBot knowledge entry '{item['id']}' has an invalid source_url")
            if not isinstance(provenance["region"], list) or not all(
                isinstance(region, str) for region in provenance["region"]
            ):
                raise ValueError(f"AgroBot knowledge entry '{item['id']}' region must be a list of strings")
            if provenance["review_status"] not in {"unverified", "reviewed"}:
                raise ValueError(f"AgroBot knowledge entry '{item['id']}' has an invalid review_status")
            if provenance["last_reviewed"] is not None and not isinstance(provenance["last_reviewed"], str):
                raise ValueError(f"AgroBot knowledge entry '{item['id']}' has an invalid last_reviewed date")

        return entries

    def _build_crop_aliases(self) -> Dict[str, List[str]]:
        return {
            "rice": ["rice", "paddy", "dhan", "ধান", "ধানের", "বোরো", "আমন", "আউশ"],
            "potato": ["potato", "potatoes", "alu", "আলু", "আলুর"],
            "tomato": ["tomato", "tomatoes", "tometo", "টমেটো", "টমেটোর"],
            "wheat": ["wheat", "gom", "গম", "গমের"],
            "chilli": ["chilli", "chili", "pepper", "morich", "মরিচ", "মরিচের", "লঙ্কা"],
            "brinjal": ["brinjal", "eggplant", "aubergine", "begun", "বেগুন", "বেগুনের"],
            "mustard": ["mustard", "shorisa", "sarson", "সরিষা", "সরিষার"],
            "corn": ["corn", "maize", "vutta", "ভুট্টা", "ভুট্টার"],
            "apple": ["apple", "আপেল", "আপেলের"],
            "grape": ["grape", "grapes", "আঙুর", "আঙ্গুর"],
            "citrus": ["orange", "citrus", "lemon", "লেবু", "কমলা"]
        }

    def _build_problem_keywords(self) -> Dict[str, List[str]]:
        return {
            "pest": ["pest", "insect", "worm", "caterpillar", "borer", "fly", "aphid", "bug", "পোকা", "মাজরা", "মাছি", "কীটপতঙ্গ", "লেদা", "কারেন্ট"],
            "disease": ["disease", "blight", "blast", "rot", "mold", "fungus", "spot", "virus", "রোগ", "ধসা", "ব্লাস্ট", "পচন", "দাগ", "ছত্রাক", "ভাইরাস"],
            "fertilizer": ["fertilizer", "urea", "dap", "potash", "manure", "compost", "nutrient", "zinc", "boron", "সার", "ইউরিয়া", "পটাশ", "খৈল", "গোবর"],
            "irrigation": ["irrigation", "water", "watering", "dry", "drought", "awd", "flood", "সেচ", "পানি", "জল", "খরা", "জলাবদ্ধতা"],
            "soil": ["soil", "lime", "ph", "acidic", "saline", "testing", "মাটি", "চুন", "অম্লীয়", "ক্ষারীয়"],
            "weather": ["weather", "rain", "storm", "cyclone", "fog", "frost", "cold", "আবহাওয়া", "বৃষ্টি", "ঝড়", "কুয়াশা", "তুফান"],
            "helpline": ["helpline", "phone", "number", "call", "center", "expert", "support", "help", "হেল্পলাইন", "নম্বর", "ফোন", "সহায়তা"]
        }

    # -------------------------------------------------------------------------
    # Edge-Case Pattern Builder
    # -------------------------------------------------------------------------
    def _build_edge_case_patterns(self) -> Dict[str, List[str]]:
        """Keywords that trigger edge-case (non-agri utility) responses."""
        return {
            "time": [
                "what time", "current time", "time now", "whats the time", "what's the time",
                "tell me the time", "show time", "what is the time", "কয়টা বাজে",
                "সময় কত", "এখন কয়টা", "টাইম কত", "time koto", "koyota baje"
            ],
            "date": [
                "what date", "today's date", "todays date", "current date", "what is the date",
                "date today", "today date", "আজকে কত তারিখ", "আজকের তারিখ",
                "তারিখ কত", "date koto", "aj ki tarikh", "what day is it", "what day is today",
                "আজ কি বার", "আজকে কোন দিন"
            ],
            "year": [
                "what year", "current year", "which year", "কোন সাল", "বর্তমান সাল",
                "this year", "কত সাল"
            ],
            "month": [
                "what month", "current month", "which month", "কোন মাস", "এই মাস",
                "this month"
            ],
        }

    # -------------------------------------------------------------------------
    # Aggregated Agricultural Keywords for Scope Detection
    # -------------------------------------------------------------------------
    def _build_agri_keyword_set(self) -> set:
        """Build a flat set of all agriculture-related keywords for fast scope check."""
        keywords = set()
        # From problem_keywords
        for category_words in self.problem_keywords.values():
            keywords.update(w.lower() for w in category_words)
        # From KB
        for item in self.kb:
            keywords.update(w.lower() for w in item.get("keywords_en", []))
            keywords.update(w for w in item.get("keywords_bn", []))
            keywords.update(c.lower() for c in item.get("crops", []))
        # From crop aliases
        for aliases in self.crop_aliases.values():
            keywords.update(a.lower() for a in aliases)
        # From disease class map
        for cls_name in self.disease_class_map:
            parts = cls_name.lower().replace("___", " ").replace("_", " ").split()
            keywords.update(p for p in parts if len(p) > 2)
        # Common agri words
        keywords.update([
            "crop", "farm", "farming", "field", "harvest", "seed", "sow", "plant",
            "garden", "organic", "compost", "mulch", "greenhouse", "nursery",
            "ফসল", "চাষ", "জমি", "বীজ", "গাছ", "ক্ষেত", "কৃষি", "বাগান"
        ])
        return keywords

    # -------------------------------------------------------------------------
    # Edge-Case Handler (Time, Date, Day, Year, Month)
    # -------------------------------------------------------------------------
    def _handle_edge_cases(self, query: str, lang: str) -> Optional[Dict[str, Any]]:
        """Handle utility queries like time, date, day, year, month."""
        q = query.lower()
        now = datetime.datetime.now()
        is_bn = (lang == "bn")

        # --- TIME ---
        if any(kw in q for kw in self._edge_case_patterns["time"]):
            time_str = now.strftime("%I:%M %p")
            if is_bn:
                # Translate AM/PM
                period = "সকাল" if now.hour < 12 else ("দুপুর" if now.hour < 17 else "সন্ধ্যা" if now.hour < 20 else "রাত")
                reply = f"🕐 এখন সময় **{time_str}** ({period})।\n\nআপনার ফসল সম্পর্কে কিছু জানতে চাইলে নিচের বাটন চাপুন বা প্রশ্ন করুন!"
            else:
                reply = f"🕐 The current time is **{time_str}**.\n\nFeel free to ask me any agriculture-related question!"
            return self._edge_case_response(reply, lang, "Utility")

        # --- DATE ---
        if any(kw in q for kw in self._edge_case_patterns["date"]):
            # Also check for "what day" queries
            day_name_en = now.strftime("%A")
            date_str_en = now.strftime("%d %B %Y")
            bn_days = {"Monday": "সোমবার", "Tuesday": "মঙ্গলবার", "Wednesday": "বুধবার",
                       "Thursday": "বৃহস্পতিবার", "Friday": "শুক্রবার", "Saturday": "শনিবার", "Sunday": "রবিবার"}
            bn_months = {"January": "জানুয়ারি", "February": "ফেব্রুয়ারি", "March": "মার্চ",
                         "April": "এপ্রিল", "May": "মে", "June": "জুন", "July": "জুলাই",
                         "August": "আগস্ট", "September": "সেপ্টেম্বর", "October": "অক্টোবর",
                         "November": "নভেম্বর", "December": "ডিসেম্বর"}
            if is_bn:
                day_bn = bn_days.get(day_name_en, day_name_en)
                month_bn = bn_months.get(now.strftime("%B"), now.strftime("%B"))
                reply = f"📅 আজকের তারিখ: **{now.day} {month_bn} {now.year}** ({day_bn})।\n\nআপনার ফসলের কোনো সমস্যা থাকলে জিজ্ঞাসা করুন!"
            else:
                reply = f"📅 Today is **{day_name_en}, {date_str_en}**.\n\nNeed help with your crops? Just ask!"
            return self._edge_case_response(reply, lang, "Utility")

        # --- YEAR ---
        if any(kw in q for kw in self._edge_case_patterns["year"]):
            if is_bn:
                reply = f"📆 বর্তমান সাল: **{now.year}**।\n\nআপনার কৃষি সংক্রান্ত কোনো প্রশ্ন থাকলে জানান!"
            else:
                reply = f"📆 The current year is **{now.year}**.\n\nAsk me anything about farming!"
            return self._edge_case_response(reply, lang, "Utility")

        # --- MONTH ---
        if any(kw in q for kw in self._edge_case_patterns["month"]):
            bn_months = {"January": "জানুয়ারি", "February": "ফেব্রুয়ারি", "March": "মার্চ",
                         "April": "এপ্রিল", "May": "মে", "June": "জুন", "July": "জুলাই",
                         "August": "আগস্ট", "September": "সেপ্টেম্বর", "October": "অক্টোবর",
                         "November": "নভেম্বর", "December": "ডিসেম্বর"}
            month_en = now.strftime("%B")
            if is_bn:
                month_bn = bn_months.get(month_en, month_en)
                reply = f"📆 বর্তমান মাস: **{month_bn} {now.year}**।\n\nএই মাসে আপনার ফসলের যত্ন সম্পর্কে জানতে প্রশ্ন করুন!"
            else:
                reply = f"📆 The current month is **{month_en} {now.year}**.\n\nAsk me about seasonal crop care for this month!"
            return self._edge_case_response(reply, lang, "Utility")

        return None

    def _edge_case_response(self, reply: str, lang: str, category: str) -> Dict[str, Any]:
        """Build a standardized response for edge-case utility queries."""
        is_bn = (lang == "bn")
        return {
            "ok": True,
            "reply": reply,
            "language": lang,
            "category": category,
            "thinking_delay": 2000,
            "suggestions": [
                "ধানের মাজরা পোকা দমন" if is_bn else "Rice stem borer remedies",
                "আলুর নাবি ধসা রোগ" if is_bn else "Potato late blight control",
                "সারের সঠিক মাত্রা" if is_bn else "Fertilizer dosage guide",
            ],
            "helpline": "1800-180-1551 (IN) / 16123 (BD)"
        }

    # -------------------------------------------------------------------------
    # Out-of-Scope Detector
    # -------------------------------------------------------------------------
    def _is_out_of_scope(self, query: str, lang: str) -> Optional[Dict[str, Any]]:
        """Detect non-agricultural complex questions and politely deflect."""
        q = query.lower()
        words = set(self._WORD_RE.findall(q))
        is_bn = (lang == "bn")

        # Check if query has ANY agriculture-related keyword
        has_agri_keyword = bool(words & self._all_agri_keywords) or any(
            kw in q for kw in self._all_agri_keywords if len(kw) > 3
        )

        if has_agri_keyword:
            return None  # Likely agriculture-related, don't block

        # Non-agri topics: coding, math, politics, entertainment, general knowledge, etc.
        out_of_scope_markers = [
            # English
            "who is the president", "who is the prime minister", "capital of",
            "code", "programming", "python", "javascript", "java", "html", "css",
            "write a program", "write code", "algorithm", "data structure",
            "movie", "song", "music", "actor", "actress", "cricket", "football",
            "recipe", "cook", "bake",
            "math", "equation", "solve", "calculate", "algebra", "calculus",
            "history", "geography", "physics", "chemistry", "biology",
            "stock market", "bitcoin", "crypto", "investment",
            "love", "relationship", "joke", "story", "poem",
            "translate", "meaning of", "define", "definition",
            "who invented", "who discovered", "who won",
            "how tall", "how old", "net worth", "salary",
            "what is ai", "what is machine learning", "what is blockchain",
            "write an essay", "write a letter", "summarize", "explain quantum",
            # Bangla non-agri
            "গান", "সিনেমা", "রান্না", "রেসিপি", "ক্রিকেট", "ফুটবল",
            "গণিত", "অঙ্ক", "কবিতা", "গল্প", "কোড", "প্রোগ্রামিং",
            "রাজধানী", "প্রধানমন্ত্রী", "রাষ্ট্রপতি",
        ]

        if any(marker in q for marker in out_of_scope_markers):
            if is_bn:
                reply = (
                    "🙏 দুঃখিত, আমি এই বিষয়ে প্রশিক্ষিত নই।\n\n"
                    "আমি **এগ্রো মিত্র (AgroBot)** — শুধুমাত্র কৃষি ও ফসল সম্পর্কিত সমস্যার সমাধান দিতে পারি। "
                    "যেমন:\n"
                    "- 🐛 পোকা দমন ও রোগ প্রতিকার\n"
                    "- 🧪 সার প্রয়োগের সঠিক মাত্রা\n"
                    "- 💧 সেচ ব্যবস্থাপনা\n"
                    "- 🌿 জৈব বালাইনাশক তৈরি\n\n"
                    "আপনার ফসলের সমস্যা নিয়ে প্রশ্ন করুন, আমি সাহায্য করতে প্রস্তুত! 🌾"
                )
            else:
                reply = (
                    "🙏 Sorry, I am not trained for that kind of question.\n\n"
                    "I am **AgroBot** — a specialized agricultural assistant. I can only help with:\n"
                    "- 🐛 Pest control & disease management\n"
                    "- 🧪 Fertilizer dosage & application\n"
                    "- 💧 Irrigation & water management\n"
                    "- 🌿 Organic farming & bio-pesticides\n\n"
                    "You can try asking about your crop problems — I'm here to help! 🌾"
                )
            return {
                "ok": True,
                "reply": reply,
                "language": lang,
                "category": "Out of Scope",
                "thinking_delay": 2000,
                "suggestions": [
                    "ধানের মাজরা পোকা দমন" if is_bn else "Rice stem borer remedies",
                    "আলুর নাবি ধসা রোগ" if is_bn else "Potato late blight control",
                    "সারের সঠিক মাত্রা" if is_bn else "Fertilizer dosage guide",
                    "কিষাণ হেল্পলাইন নম্বর" if is_bn else "Farmer helpline numbers"
                ],
                "helpline": "1800-180-1551 (IN) / 16123 (BD)"
            }

        return None

    # -------------------------------------------------------------------------
    # Core Answering Logic
    # -------------------------------------------------------------------------
    def answer_query(
        self,
        query: str,
        lang_pref: Optional[str] = None,
        diagnosis_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate a structured bilingual response for the farmer's query."""
        lang = self.detect_language(query, lang_pref)
        q_clean = query.strip()
        q_lower = q_clean.lower()

        # 1. Direct class match or contextual question about diagnosis
        if diagnosis_context and any(w in q_lower for w in [
            "this", "diagnosis", "it", "disease", "cure", "help", "treatment", "medicine",
            "রোগ", "এটা", "কী করব", "কি করব", "প্রতিকার", "ওষুধ", "চিকিৎসা", "উপায়"
        ]):
            diag_resp = self._handle_diagnosis_context(diagnosis_context, lang)
            if diag_resp:
                diag_resp["thinking_delay"] = 2000
                return diag_resp

        # 2. General greetings
        greeting_resp = self._check_greetings(q_lower, lang)
        if greeting_resp:
            greeting_resp["thinking_delay"] = 2000
            return greeting_resp

        # 3. Edge-case utility queries (time, date, day, year, month)
        edge_resp = self._handle_edge_cases(q_lower, lang)
        if edge_resp:
            return edge_resp

        # 4. Out-of-scope detection (non-agriculture questions)
        oos_resp = self._is_out_of_scope(q_lower, lang)
        if oos_resp:
            return oos_resp

        # 5. Check direct 38-class name match in query
        class_match_resp = self._match_disease_class(q_lower, lang)
        if class_match_resp:
            class_match_resp["thinking_delay"] = 2000
            return class_match_resp

        # 6. Match against Knowledge Base items
        best_item, score = self._find_best_match(q_lower, diagnosis_context)
        if best_item and score >= 2:
            resp = self._format_kb_response(best_item, lang)
            resp["thinking_delay"] = 2000
            return resp

        # 7. Fallback to diagnosis context if present
        if diagnosis_context:
            diag_resp = self._handle_diagnosis_context(diagnosis_context, lang)
            if diag_resp:
                diag_resp["thinking_delay"] = 2000
                return diag_resp

        # 8. Optional LLM invocation if an API key is available
        llm_reply = self._try_llm_generation(query, lang)
        if llm_reply:
            return {
                "ok": True,
                "reply": llm_reply,
                "language": lang,
                "category": "Expert AI Advisory",
                "thinking_delay": 2000,
                "suggestions": [
                    "ধানের মাজরা পোকা দমন" if lang == "bn" else "Rice stem borer remedies",
                    "আলুর নাবি ধসা রোগ" if lang == "bn" else "Potato late blight control",
                    "সারের সঠিক মাত্রা" if lang == "bn" else "Fertilizer dosage guide",
                    "কিষাণ হেল্পলাইন নম্বর" if lang == "bn" else "Farmer helpline numbers"
                ],
                "helpline": "1800-180-1551 (IN) / 16123 (BD)"
            }

        # 9. Smart Fallback with guidance and quick prompts
        resp = self._build_smart_fallback(query, lang)
        resp["thinking_delay"] = 2000
        return resp

    # -------------------------------------------------------------------------
    # Optional LLM Fallback (Gemini or Groq)
    # -------------------------------------------------------------------------
    def _try_llm_generation(self, query: str, lang: str) -> Optional[str]:
        gemini_key = os.environ.get("GEMINI_API_KEY")
        if gemini_key:
            try:
                system_prompt = (
                    "You are AgroBot (কৃষি মিত্র), an empathetic, highly knowledgeable agricultural expert assistant. "
                    "Your role is to give practical, actionable agronomy advice to farmers facing daily field challenges. "
                    f"Respond strictly in {'natural Bengali (বাংলা)' if lang == 'bn' else 'clear English'}. "
                    "Include organic/cultural practices first, then safe chemical solutions with exact doses if necessary, "
                    "along with safety instructions. Keep the format clean with bullet points and friendly emojis."
                )
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
                payload = {
                    "contents": [
                        {"role": "user", "parts": [{"text": f"{system_prompt}\n\nFarmer Query: {query}"}]}
                    ],
                    "generationConfig": {"temperature": 0.3, "maxOutputTokens": 800}
                }
                data = json.dumps(payload).encode("utf-8")
                req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=7) as response:
                    res_json = json.loads(response.read().decode("utf-8"))
                    text = res_json["candidates"][0]["content"]["parts"][0]["text"]
                    return text.strip()
            except Exception:
                pass
        return None

    # -------------------------------------------------------------------------
    # Disease Class Matcher
    # -------------------------------------------------------------------------
    def _match_disease_class(self, query: str, lang: str) -> Optional[Dict[str, Any]]:
        norm_query = query.strip().lower().replace(" ", "_")

        # 1. Exact or direct substring class key match
        for cls_name, details in self.disease_class_map.items():
            cls_key = cls_name.lower()
            if cls_key == norm_query or cls_key in norm_query:
                return self._format_class_response(cls_name, details, lang)

        # 2. Check full disease name match
        best_match = None
        best_score = 0
        for cls_name, details in self.disease_class_map.items():
            parts = cls_name.split("___")
            crop = parts[0].replace("_", " ").lower()
            disease = parts[1].replace("_", " ").lower()

            score = 0
            if crop in query:
                score += 2
            if disease in query or disease.replace(" ", "_") in query:
                score += 5
            elif any(w in query for w in disease.split() if len(w) > 4):
                score += 1

            # Check Bengali title match
            if details["title_bn"] in query or any(w in query for w in details["title_bn"].split() if len(w) > 3):
                score += 4

            if score > best_score:
                best_score = score
                best_match = (cls_name, details)

        if best_match and best_score >= 4:
            return self._format_class_response(best_match[0], best_match[1], lang)

        return None

    def _handle_diagnosis_context(self, class_name: str, lang: str) -> Optional[Dict[str, Any]]:
        if class_name in self.disease_class_map:
            return self._format_class_response(class_name, self.disease_class_map[class_name], lang, is_context=True)
        # Check partial
        low = class_name.lower()
        for k, v in self.disease_class_map.items():
            if k.lower() == low or k.lower() in low or low in k.lower():
                return self._format_class_response(k, v, lang, is_context=True)
        return None

    def _format_class_response(
        self,
        class_name: str,
        details: Dict[str, Any],
        lang: str,
        is_context: bool = False
    ) -> Dict[str, Any]:
        is_bn = (lang == "bn")
        title = details["title_bn"] if is_bn else details["title_en"]
        desc = details["desc_bn"] if is_bn else details["desc_en"]
        organic = details["organic_bn"] if is_bn else details["organic_en"]
        chemical = details["chemical_bn"] if is_bn else details["chemical_en"]

        parts = []
        if is_context:
            clean_name = class_name.replace("___", " : ").replace("_", " ")
            if is_bn:
                parts.append(f"🔍 **শনাক্তকৃত ফসলের রোগ:** `{clean_name}`")
                parts.append("এই রোগের জন্য তাৎক্ষণিক প্রতিকার ও করণীয় নির্দেশিকা নিচে দেওয়া হলো:\n")
            else:
                parts.append(f"🔍 **Diagnosed Condition:** `{clean_name}`")
                parts.append("Here is the practical action plan for your crop:\n")

        parts.append(f"### {title}\n")
        parts.append(f"{desc}\n")

        if organic:
            parts.append("🌱 **জৈব ও প্রতিরোধমূলক ব্যবস্থা (Organic & Cultural Care):**" if is_bn else "🌱 **Organic & Cultural Care:**")
            for item in organic:
                parts.append(f"- {item}")
            parts.append("")

        if chemical:
            parts.append("🧪 **প্রয়োজনে ঔষধ ও সঠিক মাত্রা (Chemical Treatment & Dosage):**" if is_bn else "🧪 **Recommended Chemical Control & Dosage:**")
            for item in chemical:
                parts.append(f"- {item}")
            parts.append("")

        if is_bn:
            parts.append("⚠️ *সতর্কতা: যেকোনো কীটনাশক বা ছত্রাকনাশক বিকেলে স্প্রে করবেন এবং মুখে মাস্ক পরিধান করবেন।*")
        else:
            parts.append("⚠️ *Safety Notice: Always apply sprays in late afternoon using protective masks and gloves.*")

        suggestions = [
            "কীটনাশক ব্যবহারের সতর্কতা" if is_bn else "Pesticide safety tips",
            "সারের সঠিক প্রয়োগ নির্দেশিকা" if is_bn else "Fertilizer dosage guide",
            "কৃষি হেল্পলাইন নম্বর" if is_bn else "Agri helpline numbers"
        ]

        return {
            "ok": True,
            "reply": "\n".join(parts),
            "language": lang,
            "category": "Disease Management",
            "suggestions": suggestions,
            "helpline": "1800-180-1551 (IN) / 16123 (BD)"
        }

    # -------------------------------------------------------------------------
    # Matching Algorithm
    # -------------------------------------------------------------------------
    def _find_best_match(self, query: str, context: Optional[str]) -> Tuple[Optional[Dict[str, Any]], int]:
        best_item = None
        max_score = 0
        words = set(self._WORD_RE.findall(query))
        context_lower = context.lower() if context else None

        for item in self.kb:
            score = 0
            for crop in item.get("crops", []):
                aliases = self.crop_aliases.get(crop, [crop])
                for alias in aliases:
                    if alias.lower() in query:
                        score += 3
                        break

            for kw in item.get("keywords_en", []):
                kw_low = kw.lower()
                if kw_low in query:
                    score += 4
                elif kw_low in words:
                    score += 2

            for kw in item.get("keywords_bn", []):
                if kw in query:
                    score += 5
                elif kw in words:
                    score += 3

            if context_lower and item.get("crops"):
                for c in item["crops"]:
                    if c.lower() in context_lower:
                        score += 2

            if score > max_score:
                max_score = score
                best_item = item
                # Early exit for very high confidence matches
                if max_score >= 12:
                    break

        return best_item, max_score

    # -------------------------------------------------------------------------
    # Knowledge Base Response Formatter
    # -------------------------------------------------------------------------
    def _format_kb_response(self, item: Dict[str, Any], lang: str) -> Dict[str, Any]:
        is_bn = (lang == "bn")
        title = item["title_bn"] if is_bn else item["title_en"]
        summary = item["summary_bn"] if is_bn else item["summary_en"]
        organic_list = item["organic_bn"] if is_bn else item["organic_en"]
        chemical_list = item["chemical_bn"] if is_bn else item["chemical_en"]
        suggestions = item["suggestions_bn"] if is_bn else item["suggestions_en"]

        parts = [f"### {title}\n", f"{summary}\n"]

        if organic_list:
            header = "🌱 **জৈব ও প্রতিরোধমূলক ব্যবস্থা (Organic & Cultural Management):**" if is_bn else "🌱 **Organic & Cultural Management:**"
            parts.append(header)
            for step in organic_list:
                parts.append(f"- {step}")
            parts.append("")

        if chemical_list:
            header = "🧪 **প্রয়োজনে রাসায়নিক ঔষধ ও সঠিক মাত্রা (Chemical Treatment & Dosage):**" if is_bn else "🧪 **Recommended Chemical Control & Dosage:**"
            parts.append(header)
            for step in chemical_list:
                parts.append(f"- {step}")
            parts.append("")

        if is_bn:
            parts.append("⚠️ *পরামর্শ: যেকোনো কীটনাশক বিকেলে স্প্রে করুন এবং মুখে মাস্ক ও হাতে গ্লাভস ব্যবহার করুন।*")
        else:
            parts.append("⚠️ *Safety tip: Always spray in the late afternoon, wearing a mask and gloves. Observe proper pre-harvest intervals.*")

        return {
            "ok": True,
            "reply": "\n".join(parts),
            "language": lang,
            "category": item.get("category", "General Advisory"),
            "suggestions": suggestions,
            "helpline": "1800-180-1551 (IN) / 16123 (BD)"
        }

    # -------------------------------------------------------------------------
    # Greetings & Common Queries
    # -------------------------------------------------------------------------
    def _check_greetings(self, query: str, lang: str) -> Optional[Dict[str, Any]]:
        greet_bn = ["নমস্কার", "সালাম", "হ্যালো", "কেমন আছো", "কেমন আছেন", "ধন্যবাদ", "হাই", "কেমন আছ"]
        greet_en = ["hello", "hi", "hey", "good morning", "good evening", "assalamu alaikum", "namaste", "thank you", "thanks"]
        words = set(self._WORD_RE.findall(query))

        is_bn_greet = any(w in words for w in greet_bn) or any(g in query for g in greet_bn)
        is_en_greet = any(w in words for w in greet_en)

        if not (is_bn_greet or is_en_greet):
            return None

        if lang == "bn" or is_bn_greet:
            reply = (
                "🌾 **নমস্কার ও আসসালামু আলাইকুম! আমি এগ্রো মিত্র (AgroBot)**।\n\n"
                "আমি আপনার প্রতিদিনের কৃষিকাজের বিভিন্ন সমস্যা সমাধানে সহায়তা করতে প্রস্তুত। "
                "আপনি যেকোনো বিষয়ে প্রশ্ন করতে পারেন:\n\n"
                "- 🐛 **পোকা দমন:** ধানের মাজরা পোকা, কারেন্ট পোকা, সাদা মাছি, বেগুনের ডগা পোকা ইত্যাদি।\n"
                "- 🍂 **রোগ প্রতিকার:** ধানের ব্লাস্ট, আলুর নাবি ধসা, পাতা কোঁকড়ানো রোগ ইত্যাদি।\n"
                "- 🧪 **সার প্রয়োগ:** ইউরিয়া, ডিএপি ও পটাশ সারের সঠিক মাত্রা ও প্রয়োগের নিয়ম।\n"
                "- 💧 **সেচ ও পানি:** ধান ও অন্যান্য ফসলে সেচ দেওয়ার সঠিক সময়।\n"
                "- 🌿 **জৈব বালাইনাশক:** নিম তেল তৈরি ও মাটির অম্লতায় চুন প্রয়োগ।\n\n"
                "নিচের বাটনগুলোতে চাপ দিন অথবা আপনার সমস্যা সরাসরি বাংলায় বা ইংরেজিতে লিখুন!"
            )
            suggestions = [
                "ধানের মাজরা পোকা দমন",
                "আলুর নাবি ধসা রোগ",
                "ইউরিয়া ও ডিএপি সারের নিয়ম",
                "কিষাণ হেল্পলাইন নম্বর"
            ]
        else:
            reply = (
                "🌾 **Hello! I am AgroBot — Your Bilingual Smart Farm Assistant.**\n\n"
                "I am here to help you solve everyday farming challenges:\n\n"
                "- 🐛 **Pest Control:** Stem borer, brown planthopper, aphids, whiteflies, fruit borers.\n"
                "- 🍂 **Plant Diseases:** Rice blast, potato late blight, early blight, tomato leaf curl.\n"
                "- 🧪 **Fertilizer Management:** Balanced Urea, DAP, Potash, Zinc, and compost application.\n"
                "- 💧 **Water Management:** Critical irrigation timing & AWD (Alternate Wetting & Drying).\n"
                "- 🌿 **Organic Farming:** Homemade neem oil spray & lime application for acidic soils.\n\n"
                "Ask me any question in English or বাংলা, or tap the quick buttons below!"
            )
            suggestions = [
                "Rice stem borer remedies",
                "Potato late blight control",
                "Fertilizer dosage guide",
                "Farmer helpline numbers"
            ]

        return {
            "ok": True,
            "reply": reply,
            "language": lang,
            "category": "Welcome",
            "suggestions": suggestions,
            "helpline": "1800-180-1551 (IN) / 16123 (BD)"
        }

    # -------------------------------------------------------------------------
    # Smart Fallback
    # -------------------------------------------------------------------------
    def _build_smart_fallback(self, query: str, lang: str) -> Dict[str, Any]:
        if lang == "bn":
            reply = (
                f"🌾 আপনার প্রশ্নটি পেয়েছি: *\"{query}\"*\n\n"
                "সঠিক সমাধানের জন্য আপনার ফসলের নাম ও সমস্যার নির্দিষ্ট লক্ষণগুলো উল্লেখ করুন। "
                "যেমন:\n"
                "- **ধানের সমস্যা:** মাজরা পোকা, বাদামী গাছফড়িং (কারেন্ট পোকা), বা ব্লাস্ট রোগ।\n"
                "- **আলু বা সবজি:** নাবি ধসা, পাতা কোঁকড়ানো, বা ডগা ছিদ্রকারী পোকা।\n"
                "- **সার ও মাটি:** ইউরিয়া/ডিএপি সারের পরিমাণ বা মাটির চুন প্রয়োগ।\n"
                "- **জরুরি সহায়তা:** কিষাণ কল সেন্টারের টোল-ফ্রি নম্বর **1800-180-1551** (ভারত) বা **16123** (বাংলাদেশ)-এ কল করতে পারেন।"
            )
            suggestions = [
                "ধানের মাজরা পোকা দমন",
                "আলুর নাবি ধসা রোগ",
                "সারের সঠিক প্রয়োগ নির্দেশিকা",
                "জৈব নিম তেল তৈরি"
            ]
        else:
            reply = (
                f"🌾 Thank you for your question: *\"{query}\"*\n\n"
                "To give you the most accurate dosage and advice, please specify your crop and symptom. For example:\n"
                "- **Paddy/Rice:** Stem borer, brown planthopper, or blast disease.\n"
                "- **Potato/Vegetables:** Late blight, leaf curl, or fruit borer.\n"
                "- **Fertilizer & Soil:** Urea/DAP scheduling or soil liming.\n"
                "- **Urgent Expert Call:** Call Kisan Call Center toll-free at **1800-180-1551** (India) or **16123** (Bangladesh) for live scientist consultation."
            )
            suggestions = [
                "Rice stem borer remedies",
                "Potato late blight control",
                "Fertilizer dosage guide",
                "Farmer helpline numbers"
            ]

        return {
            "ok": True,
            "reply": reply,
            "language": lang,
            "category": "Advisory Assistance",
            "suggestions": suggestions,
            "helpline": "1800-180-1551 (IN) / 16123 (BD)"
        }

    # -------------------------------------------------------------------------
    # Starter Topics for Quick-Action Chips
    # -------------------------------------------------------------------------
    def get_quick_topics(self) -> Dict[str, List[Dict[str, str]]]:
        return {
            "bn": [
                {"id": "rice_borer", "label": "🌾 ধানের মাজরা পোকা", "query": "ধানের মাজরা পোকা দমন করার উপায় কী?"},
                {"id": "potato_blight", "label": "🥔 আলুর নাবি ধসা", "query": "আলুর নাবি ধসা রোগ হলে কী ওষুধ দেব?"},
                {"id": "fertilizer", "label": "🧪 ইউরিয়া ও সারের নিয়ম", "query": "ইউরিয়া ও ডিএপি সার প্রয়োগের সঠিক নিয়ম বলুন"},
                {"id": "rice_blast", "label": "🌾 ধানের ব্লাস্ট রোগ", "query": "ধানের ব্লাস্ট রোগের লক্ষণ ও প্রতিকার"},
                {"id": "leaf_curl", "label": "🍅 পাতা কোঁকড়ানো রোগ", "query": "টমেটো ও মরিচের পাতা কোঁকড়ানো রোগ কীভাবে দমন করব?"},
                {"id": "neem_spray", "label": "🌿 নিম তেল তৈরি", "query": "ঘরে কীভাবে নিম তেলের জৈব কীটনাশক তৈরি করব?"},
                {"id": "irrigation", "label": "💧 সেচ ও পানি পদ্ধতি", "query": "ফসলে সেচ দেওয়ার সঠিক সময় ও এডব্লিউডি পদ্ধতি কী?"},
                {"id": "helpline", "label": "📞 কিষাণ হেল্পলাইন", "query": "কৃষি পরামর্শ নেওয়ার সরকারি হেল্পলাইন নম্বর কত?"}
            ],
            "en": [
                {"id": "rice_borer", "label": "🌾 Rice Stem Borer", "query": "How to control yellow stem borer in paddy?"},
                {"id": "potato_blight", "label": "🥔 Potato Late Blight", "query": "What is the best medicine for potato late blight?"},
                {"id": "fertilizer", "label": "🧪 Fertilizer Dosage", "query": "What is the balanced schedule for Urea, DAP, and Potash?"},
                {"id": "rice_blast", "label": "🌾 Rice Blast Disease", "query": "How to identify and treat rice blast disease?"},
                {"id": "leaf_curl", "label": "🍅 Leaf Curl Virus", "query": "How to manage whitefly and leaf curl in tomato and chilli?"},
                {"id": "neem_spray", "label": "🌿 Neem Bio-Pesticide", "query": "How to prepare organic neem oil spray at home?"},
                {"id": "irrigation", "label": "💧 Smart Irrigation", "query": "When is the critical time for irrigation and what is AWD?"},
                {"id": "helpline", "label": "📞 Agri Helplines", "query": "What are the official farmer toll-free helpline numbers?"}
            ]
        }
