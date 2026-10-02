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
import urllib.request
import urllib.error
from typing import Dict, List, Optional, Any, Tuple


class AgroBotEngine:
    """Bilingual offline/hybrid agronomy chatbot engine."""

    def __init__(self):
        self.kb = self._build_knowledge_base()
        self.disease_class_map = self._build_disease_class_map()
        self.crop_aliases = self._build_crop_aliases()
        self.problem_keywords = self._build_problem_keywords()

    # -------------------------------------------------------------------------
    # Language Detection & Helpers
    # -------------------------------------------------------------------------
    @staticmethod
    def contains_bangla(text: str) -> bool:
        """Check if string contains Bengali script characters (U+0980 to U+09FF)."""
        return bool(re.search(r"[\u0980-\u09FF]", text))

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
        words = re.findall(r"\b\w+\b", text_lower)
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
        return [
            # 1. Rice Stem Borer
            {
                "id": "rice_stem_borer",
                "category": "Pest Management",
                "crops": ["rice", "paddy"],
                "keywords_en": ["stem borer", "yellow stem borer", "dead heart", "white earhead", "rice worm", "rice pest", "borer"],
                "keywords_bn": ["মাজরা", "মাজরা পোকা", "মরা ডিগ", "সাদা শিষ", "ধানের পোকা", "শীষ শুকিয়ে", "মাঝরা"],
                "title_en": "🌾 Rice Yellow Stem Borer (Scirpophaga incertulas)",
                "title_bn": "🌾 ধানের মাজরা পোকা দমন ব্যবস্থাপনা",
                "summary_en": "Stem borer larvae bore into rice stems. In early stages, the central shoot dies ('Dead Heart'). During flowering, it causes empty, pale white earheads ('Whitehead').",
                "summary_bn": "মাজরা পোকার কীড়া ধানের কাণ্ডের ভেতরে ঢুকে ভিতরের অংশ খেয়ে ফেলে। কুশি অবস্থায় 'মরা ডিগ' বা ডেডহার্ট এবং শিষ বের হওয়ার সময় সাদা ফাঁপা শিষ বা 'হোয়াইট হেড' দেখা যায়।",
                "organic_en": [
                    "Install Pheromone Traps @ 8 traps/acre to trap and kill male moths.",
                    "Release Trichogramma japonicum egg parasitoid cards @ 20,000 eggs/acre at 7-10 day intervals.",
                    "Perch T-shaped bamboo sticks (১০-১৫ টি প্রতি বিঘায়) for predatory birds to sit and eat adult moths.",
                    "Spray Neem Oil (5ml/L of water with soap) at initial moth appearance."
                ],
                "organic_bn": [
                    "বিঘা প্রতি ৩-৪টি ফেরোমন ফাঁদ (Pheromone Trap) স্থাপন করে পুরুষ মথ ধ্বংস করুন।",
                    "ক্ষেতে ডালপালা বা টি-আকৃতির বাঁশের কঞ্চি (প্রতি বিঘায় ১০-১২টি) পুঁতে দিন যেন শিকারী পাখিরা বসে পোকা খেতে পারে।",
                    "প্রাথমিক অবস্থায় নিম তেল (প্রতি লিটার জলে ৫ মিলি ও সামান্য সাবান জল) স্প্রে করুন।",
                    "ট্রাইকোগ্রামা পরজীবী ডিমের কার্ড ব্যবহার করুন।"
                ],
                "chemical_en": [
                    "If economic threshold level (ETL > 5% dead hearts) is crossed: Apply Cartap Hydrochloride 4G @ 10 kg/acre OR Chlorantraniliprole 0.4% G @ 4 kg/acre in standing water.",
                    "Foliar spray: Chlorantraniliprole 18.5% SC @ 0.3 ml/L or Flubendiamide 39.35% SC @ 0.2 ml/L of water."
                ],
                "chemical_bn": [
                    "ক্ষতির মাত্রা ৫% এর বেশি হলে: কার্টাপ হাইড্রোক্লোরাইড ৪জি (Cartap 4G) বিঘা প্রতি ৩-৩.৫ কেজি অথবা ক্লোরান্ট্রানিলিপ্রোল ০.৪জি জমিতে ছিটান।",
                    "স্প্রে করার জন্য: কোরাজেন (Chlorantraniliprole 18.5% SC) প্রতি লিটার জলে ০.৩ মিলি অথবা ফ্লুবেন্ডিয়ামাইড প্রতি লিটার জলে ০.২ মিলি মিশিয়ে স্প্রে করুন।"
                ],
                "suggestions_en": ["Brown planthopper in rice", "Rice blast disease", "Rice fertilizer schedule"],
                "suggestions_bn": ["ধানের কারেন্ট পোকা / বাদামী গাছফড়িং", "ধানের ব্লাস্ট রোগ প্রতিকার", "ধানের সারের সঠিক মাত্রা"]
            },

            # 2. Rice Blast Disease
            {
                "id": "rice_blast",
                "category": "Disease Control",
                "crops": ["rice", "paddy"],
                "keywords_en": ["blast", "rice blast", "neck blast", "leaf blast", "magnaporthe", "spindle shaped spots"],
                "keywords_bn": ["ব্লাস্ট", "ধানের ব্লাস্ট", "নেক ব্লাস্ট", "পাতা ব্লাস্ট", "ঘাড় পচা", "ধানের ছত্রাক"],
                "title_en": "🌾 Rice Blast Disease (Pyricularia oryzae)",
                "title_bn": "🌾 ধানের ব্লাস্ট রোগ (পাতা ও নেক ব্লাস্ট) প্রতিকার",
                "summary_en": "Fungal disease causing diamond or spindle-shaped eye-like lesions with gray centers on leaves. At heading stage, it attacks the neck node of the panicle ('Neck Blast'), causing breaking and unfilled grains.",
                "summary_bn": "এটি ধানের মারাত্মক ছত্রাকজনিত রোগ। পাতার ওপর চোখের মতো দুই প্রান্ত চোখা ও মাঝখানটা ছাই রঙের দাগ হয়। শিষের গোড়ায় আক্রমণ হলে (নেক ব্লাস্ট) শিষ কালো হয়ে ভেঙে পড়ে এবং ধান চিটা হয়ে যায়।",
                "organic_en": [
                    "Avoid excessive application of Urea (Nitrogen) fertilizer; apply Potash in split doses.",
                    "Keep water level at 2-3 inches in field continuously during early outbreak.",
                    "Treat seeds with Trichoderma viride @ 5-10g/kg seed before nursery sowing."
                ],
                "organic_bn": [
                    "জমিতে অতিরিক্ত ইউরিয়া সার প্রয়োগ একদম বন্ধ রাখুন; ইউরিয়া বেশি দিলে ব্লাস্টের প্রকোপ দ্রুত বাড়ে।",
                    "জমিতে পর্যাপ্ত পানি ধরে রাখুন; জমি শুকিয়ে গেলে রোগের আক্রমণ বাড়ে।",
                    "পটাশ সার দুই কিস্তিতে ভাগ করে দিন, এতে ধানের রোগ প্রতিরোধ ক্ষমতা বাড়ে।",
                    "বীজতলায় বোনার আগে ট্রাইকোডার্মা দিয়ে বীজ শোধন করুন।"
                ],
                "chemical_en": [
                    "At first notice of leaf blast: Spray Tricyclazole 75% WP @ 0.6 g/L water (e.g. Beam / Baan).",
                    "Alternative: Isoprothiolane 40% EC (Fujione) @ 1.5 ml/L water OR Kasugamycin 3% SL @ 2 ml/L water.",
                    "For Neck Blast: Spray once at booting/late heading and once after 50% flowering late afternoon."
                ],
                "chemical_bn": [
                    "পাতায় দাগ দেখামাত্র: ট্রাইসাইক্লাজোল ৭৫% ডব্লিউপি (যেমন ট্রুপার বা বিম) প্রতি লিটার জলে ০.৬ গ্রাম মিশিয়ে স্প্রে করুন।",
                    "বিকল্প ঔষধ: আইসোপ্রোথিওলেন ৪০% ইসি (ফুজিয়ন) প্রতি লিটার জলে ১.৫ মিলি অথবা কাসুগামাইসিন ২ মিলি/লিটার।",
                    "নেক ব্লাস্ট রোধে ধান থোড় অবস্থায় একবার এবং শিষ বের হলে বিকেলে আরেকবার স্প্রে করুন।"
                ],
                "suggestions_en": ["Rice fertilizer dosage", "Bacterial leaf blight in rice", "Rice stem borer"],
                "suggestions_bn": ["ধানের ইউরিয়া ও পটাশ সার প্রয়োগ", "ধানের ব্যাকটেরিয়াল পাতা পোড়া রোগ", "ধানের মাজরা পোকা দমন"]
            },

            # 3. Rice Brown Planthopper (BPH / Current Poka)
            {
                "id": "rice_bph",
                "category": "Pest Management",
                "crops": ["rice", "paddy"],
                "keywords_en": ["brown planthopper", "bph", "current poka", "hopper burn", "nilaparvata"],
                "keywords_bn": ["কারেন্ট পোকা", "বাদামী গাছফড়িং", "বিপিএইচ", "গাছফড়িং", "হপার বার্ন", "ধানের রস চোষা পোকা"],
                "title_en": "🌾 Rice Brown Planthopper (BPH / Current Poka)",
                "title_bn": "🌾 ধানের বাদামী গাছফড়িং (কারেন্ট পোকা) দমন",
                "summary_en": "BPH congregates at the base of rice tillers and sucks sap, turning circular patches of the crop dry and golden-brown like burnt grass ('Hopper Burn'). It spreads like wildfire ('current').",
                "summary_bn": "এই পোকা ধানের গোড়ায় দলবেঁধে বসে রস চুষে খায়। ফলে গাছ পুড়ে যাওয়ার মতো সোনালী-বাদামী হয়ে শুকিয়ে গোল গোল দাগে মরে যায় (হপার বার্ন)। খুব দ্রুত পুরো জমিতে ছড়িয়ে পড়ে বলে একে 'কারেন্ট পোকা' বলে।",
                "organic_en": [
                    "Practice 'Alley Farming' (বিলি কাটা) — leave an 8-10 inch empty row after every 10-12 rows for sunlight and aeration.",
                    "Drain standing water from the field completely for 3-4 days to disturb insect breeding.",
                    "Avoid broad-spectrum synthetic pyrethroids (like cypermethrin) which kill natural spiders that eat hoppers."
                ],
                "organic_bn": [
                    "বিলি বা 'আলি' পদ্ধতি: ধানের জমিতে প্রতি ১০-১২ সারি পর পর এক হাত ফাঁকা রাখুন যেন আলো-বাতাস ধানের গোড়া পর্যন্ত পৌঁছাতে পারে।",
                    "জমির পানি ৩-৪ দিনের জন্য পুরোপুরি বের করে দিয়ে জমি শুকিয়ে নিন, এতে পোকা দ্রুত মারা যায়।",
                    "সাইপারমেথ্রিন জাতীয় ঔষধ স্প্রে করবেন না, কারণ এতে উপকারী মাকড়সা মারা যায় এবং কারেন্ট পোকা বহুগুণ বেড়ে যায়।"
                ],
                "chemical_en": [
                    "Direct spray at the BASE OF THE PLANTS (not top canopy):",
                    "Pymetrozine 50% WDG (Chess) @ 0.6 g/L water OR Dinotefuran 20% SG (Token) @ 0.4 g/L water.",
                    "Alternative: Triflumezopyrim 10% SC (Pexalon) @ 0.5 ml/L water (very effective long-lasting control)."
                ],
                "chemical_bn": [
                    "ঔষধ স্প্রে করার সময় নজেল ধানের গোড়ার দিকে তাক করে স্প্রে করতে হবে:",
                    "পাইমেট্রোজিন ৫০% ডব্লিউডিজি (যেমন চেস) প্রতি লিটার জলে ০.৬ গ্রাম অথবা ডিনোটেফিউরান ২০% এসজি (টোকেন) ০.৪ গ্রাম/লিটার।",
                    "পেক্সালন (Triflumezopyrim 10% SC) প্রতি বিঘায় ২৩ মিলি (প্রতি লিটারে ০.৫ মিলি) প্রয়োগ করলে দীর্ঘমেয়াদী চমৎকার ফল মেলে।"
                ],
                "suggestions_en": ["Alternate Wetting & Drying (AWD)", "Rice stem borer", "Pesticide safety tips"],
                "suggestions_bn": ["পর্যায়ক্রমিক ভেজানো ও শুকানো (AWD) পদ্ধতি", "ধানের মাজরা পোকা", "কীটনাশক ব্যবহারের সতর্কতা"]
            },

            # 4. Rice Bacterial Leaf Blight (BLB / ব্যাকটেরিয়াল পাতা পোড়া)
            {
                "id": "rice_blb",
                "category": "Disease Control",
                "crops": ["rice", "paddy"],
                "keywords_en": ["blb", "bacterial leaf blight", "xanthomonas oryzae", "rice blight", "leaf burn"],
                "keywords_bn": ["বিএলবি", "ব্যাকটেরিয়াল পাতা পোড়া", "ধানের পাতা শুকিয়ে", "ধানের ব্লাইট"],
                "title_en": "🌾 Rice Bacterial Leaf Blight (BLB)",
                "title_bn": "🌾 ধানের ব্যাকটেরিয়াল পাতা পোড়া রোগ (BLB)",
                "summary_en": "Water-soaked yellow-orange wavy stripes along leaf margins starting from leaf tips, causing leaves to look bleached and scorched.",
                "summary_bn": "পাতার ডগা থেকে শুরু করে দুই পাশ দিয়ে ঢেউ খেলানো হলুদ বা হলদেটে-সাদা দাগ নিচের দিকে নামে। পাতা পুড়ে যাওয়ার মতো শুকিয়ে যায়।",
                "organic_en": ["Drain field water for 3 days.", "Stop Urea top dressing immediately; apply extra Muriate of Potash (MOP)."],
                "organic_bn": ["জমির পানি কয়েকদিনের জন্য বের করে দিন।", "ইউরিয়া সার দেওয়া পুরোপুরি বন্ধ রাখুন এবং বিঘা প্রতি ৪-৫ কেজি পটাশ সার প্রয়োগ করুন।"],
                "chemical_en": ["Spray Copper Oxychloride 50% WP @ 2.5 g/L + Streptocycline @ 0.1 g/L water twice at 7-day intervals."],
                "chemical_bn": ["কপার অক্সিক্লোরাইড ২.৫ গ্রাম এবং স্ট্রেপ্টোসাইক্লিন ০.১ গ্রাম প্রতি লিটার জলে মিশিয়ে ৭ দিন অন্তর দুইবার স্প্রে করুন।"],
                "suggestions_en": ["Rice blast disease", "Fertilizer guide", "Rice stem borer"],
                "suggestions_bn": ["ধানের ব্লাস্ট রোগ", "সারের সঠিক নিয়মাবলী", "ধানের মাজরা পোকা"]
            },

            # 5. Potato Late Blight (আলুর নাবি ধসা)
            {
                "id": "potato_late_blight",
                "category": "Disease Control",
                "crops": ["potato", "tomato"],
                "keywords_en": ["late blight", "potato late blight", "phytophthora", "water soaked spots", "potato blight", "rot"],
                "keywords_bn": ["নাবি ধসা", "আলুর নাবি ধসা", "লেট ব্লাইট", "আলুর ধসা", "আলু পচা", "আলুর পাতা পোড়া", "আলুর রোগ"],
                "title_en": "🥔 Potato Late Blight (Phytophthora infestans)",
                "title_bn": "🥔 আলুর নাবি ধসা (লেট ব্লাইট) রোগ ও চিকিৎসা",
                "summary_en": "The most destructive potato disease triggered by cold, foggy, overcast, humid weather. Dark water-soaked lesions appear on leaf tips/margins, with a whitish fungal ring on the underside during humid mornings.",
                "summary_bn": "কুয়াশাচ্ছন্ন, মেঘলা ও স্যাঁতসেঁতে ঠাণ্ডা আবহাওয়ায় এই রোগ মহামারী রূপ নেয়। পাতার কিনারায় ও ডগায় ভেজা ভেজা তেলের মতো কালো দাগ হয়। সকালে পাতার নিচে সাদা তুলোর মতো ছত্রাক দেখা যায় এবং কয়েক দিনে পুরো ক্ষেত পচে দুর্গন্ধ ছড়ায়।",
                "organic_en": [
                    "Plant certified disease-free and sprouted seed tubers.",
                    "Do not irrigate potato fields during dense foggy or cloudy periods.",
                    "Ensure high earthing-up (মাটি তোলা) so fungal spores cannot wash down into tubers.",
                    "Destroy and bury infected plant residue away from the field immediately."
                ],
                "organic_bn": [
                    "কুয়াশা বা মেঘলা আবহাওয়ায় আলুর জমিতে কখনোই সেচ দেবেন না।",
                    "গাছের গোড়ায় উঁচু করে ভেলি বেঁধে দিন (মাটি তুলুন) যাতে ছত্রাকের বীজ মাটির ভেতরের আলুতে পৌঁছাতে না পারে।",
                    "আক্রান্ত গাছ বা পাতা তুলে দূরে মাটিতে পুঁতে ফেলুন।",
                    "রোগের পূর্বাভাস পেলেই সতর্কতামূলক আগাম স্প্রে করুন।"
                ],
                "chemical_en": [
                    "Preventive (before disease appears in foggy weather): Mancozeb 75% WP @ 2.5 g/L OR Chlorothalonil 75% WP @ 2 g/L water.",
                    "Curative (after symptoms appear): Cymoxanil 8% + Mancozeb 64% WP (Curzate) @ 2.5 g/L OR Metalaxyl 8% + Mancozeb 64% WP (Ridomil Gold) @ 2 g/L water.",
                    "Severe stage: Dimethomorph 50% WP @ 1 g/L or Fenamidone + Mancozeb (Sectin) @ 2 g/L."
                ],
                "chemical_bn": [
                    "প্রতিরোধমূলক (কুয়াশা পড়ার সাথে সাথে): ম্যানকোজেব ৭৫% ডব্লিউপি (ডাইথেন এম-৪৫ বা ইন্ডোফিল) প্রতি লিটার জলে ২.৫ গ্রাম মিশিয়ে স্প্রে করুন।",
                    "রোগ দেখা দিলে তাৎক্ষণিক চিকিৎসা: সাইমোক্সানিল ৮% + ম্যানকোজেব ৬৪% (কারজেট) প্রতি লিটার জলে ২.৫ গ্রাম অথবা রিডোমিল গোল্ড (মেটালাক্সিল+ম্যানকোজেব) ২ গ্রাম/লিটার।",
                    "মারাত্মক অবস্থায়: সেকটিন (Sectin) বা এক্রোব্যাট (ডাইমেথোমর্ফ) ১-২ গ্রাম প্রতি লিটার জলে মিশিয়ে ৭ দিন অন্তর স্প্রে করুন।"
                ],
                "suggestions_en": ["Potato early blight", "Potato fertilizer guide", "Storage tips for potato"],
                "suggestions_bn": ["আলুর আগাম ধসা রোগ", "আলুর সুষম সার প্রয়োগের নিয়ম", "আলু সংরক্ষণের সঠিক উপায়"]
            },

            # 6. Tomato & Chilli Leaf Curl Virus & Whitefly
            {
                "id": "leaf_curl_whitefly",
                "category": "Pest & Disease",
                "crops": ["tomato", "chilli", "pepper", "papaya"],
                "keywords_en": ["leaf curl", "yellow leaf curl", "whitefly", "thrips", "curled leaves", "stunted", "virus"],
                "keywords_bn": ["পাতা কোঁকড়ানো", "টমেটোর পাতা কোঁকড়ানো", "মরিচের পাতা কোঁকড়ানো", "সাদা মাছি", "চুষি পোকা", "ভাইরাস", "পাতা কুঁকড়ে"],
                "title_en": "🍅 Tomato & Chilli Leaf Curl Virus & Whitefly Management",
                "title_bn": "🍅 টমেটো ও মরিচের পাতা কোঁকড়ানো রোগ ও সাদা মাছি দমন",
                "summary_en": "Leaves curl upward or downward, thicken, turn leathery with yellow veins, and plants become stunted. This viral disease is transmitted primarily by tiny Whiteflies (Bemisia tabaci) and Thrips.",
                "summary_bn": "গাছের পাতাগুলো উপরের বা নিচের দিকে কুঁকড়ে বাটি বা নৌকার মতো হয়ে যায়, পাতা পুরু ও শক্ত হয় এবং বৃদ্ধি থমকে যায়। এটি একটি ভাইরাস রোগ, যা মূলত ক্ষুদ্র 'সাদা মাছি' ও 'থ্রিপস' পোকার মাধ্যমে ছড়ায়।",
                "organic_en": [
                    "Install Yellow Sticky Traps @ 15-20 traps/acre to catch whiteflies, and Blue Sticky Traps for thrips.",
                    "Uproot and immediately bury severely infected viral plants (they cannot be cured, only removed to save others).",
                    "Spray Neem Seed Kernel Extract (NSKE 5%) or Neem Oil @ 5 ml/L water + mild soap every 7 days."
                ],
                "organic_bn": [
                    "জমিতে হলুদ আঠালো ফাঁদ (Yellow Sticky Trap) প্রতি বিঘায় ১০-১২টি টাঙান; এতে উড়ন্ত সাদা মাছি আটকে মারা যায়।",
                    "যেসব গাছে মারাত্মকভাবে ভাইরাস লেগেছে সেগুলো উপড়ে মাটিতে পুঁতে ফেলুন, কারণ ভাইরাস আক্রান্ত গাছ সুস্থ করা যায় না কিন্তু তা সুস্থ গাছে রোগ ছড়ায়।",
                    "নিম তেল ৫ মিলি প্রতি লিটার পানিতে সামান্য ডিটারজেন্ট মিশিয়ে প্রতি সপ্তাহে স্প্রে করুন।"
                ],
                "chemical_en": [
                    "Vector control (Whitefly & Thrips):",
                    "Spray Imidacloprid 17.8% SL (Confidor) @ 0.5 ml/L OR Acetamiprid 20% SP @ 0.5 g/L water.",
                    "For severe infestation: Diafenthiuron 50% WP (Pegasus) @ 1.2 g/L OR Spiromesifen 22.9% SC @ 1 ml/L."
                ],
                "chemical_bn": [
                    "বাহক পোকা (সাদা মাছি ও থ্রিপস) নিয়ন্ত্রণে ঔষধ স্প্রে করুন:",
                    "ইমিডাক্লোপ্রিড ১৭.৮% এসএল (যেমন কনফিডোর বা টিডো) প্রতি লিটার জলে ০.৫ মিলি অথবা এসিটামিপ্রিড ০.৫ গ্রাম/লিটার।",
                    "মারাত্মক আক্রমণের ক্ষেত্রে: ডায়াফেনথিউরন ৫০% ডব্লিউপি (পেগাসাস) প্রতি লিটার পানিতে ১.২ গ্রাম স্প্রে করুন।"
                ],
                "suggestions_en": ["Tomato early blight", "Fertilizer for vegetables", "Bio-pesticide preparation"],
                "suggestions_bn": ["টমেটোর আগাম ধসা", "সবজির সার প্রয়োগ পদ্ধতি", "জৈব বালাইনাশক তৈরি"]
            },

            # 7. Balanced Fertilizer Schedule
            {
                "id": "fertilizer_guide",
                "category": "Fertilizer & Soil",
                "crops": ["general", "rice", "potato", "wheat", "vegetables"],
                "keywords_en": ["fertilizer", "urea", "dap", "potash", "mop", "npk", "dosage", "zinc", "boron", "compost"],
                "keywords_bn": ["সার", "ইউরিয়া", "ডিএপি", "পটাশ", "এমওপি", "জিংক", "দস্তা", "বোরন", "সারের মাত্রা", "জৈব সার", "সার প্রয়োগ"],
                "title_en": "🧪 Balanced Fertilizer Management Guide (NPK & Micro-nutrients)",
                "title_bn": "🧪 সুষম সার ব্যবস্থাপনা নির্দেশিকা (ইউরিয়া, ডিএপি ও পটাশ)",
                "summary_en": "Balanced nutrition requires the 4R principle: Right Source, Right Rate, Right Time, and Right Place. Nitrogen (Urea) gives vegetative green growth; Phosphorus (DAP) develops strong roots; Potassium (Potash) builds grain weight and disease tolerance.",
                "summary_bn": "সুষম সার প্রয়োগে ফসলের উৎপাদন বাড়ে এবং রোগবালাই কমে। নাইট্রোজেন (ইউরিয়া) গাছের বৃদ্ধি করে; ফসফরাস (ডিএপি/টিএসপি) মজবুত শিকড় তৈরি করে; পটাশিয়াম (এমওপি) রোগ প্রতিরোধ ক্ষমতা ও দানার পুষ্টি নিশ্চিত করে।",
                "organic_en": [
                    "Apply Well-decomposed Cow dung manure or Vermicompost @ 2-3 tonnes/acre during final land preparation.",
                    "Incorporate Neem Cake @ 100 kg/acre to protect roots from nematodes and act as a natural slow-release nitrogen source.",
                    "Practice Green Manuring with Dhaincha (Sesbania) once every 2 years."
                ],
                "organic_bn": [
                    "জমি তৈরির শেষ চাষে প্রতি বিঘায় ৬০০-৮০০ কেজি পচা গোবর সার অথবা ২০০-২৫০ কেজি কেঁচো সার (ভার্মিকম্পোস্ট) মাটির সাথে মিশিয়ে দিন।",
                    "বিঘা প্রতি ১৫-২০ কেজি নিম খৈল প্রয়োগ করলে মাটির উর্বরতা বাড়ে এবং উঁইপোকা ও কৃমির আক্রমণ দূর হয়।",
                    "প্রতি বছর বা এক বছর অন্তর সবুজ সার হিসেবে ধৈঞ্চা চাষ করে মাটিতে মিশিয়ে দিন।"
                ],
                "chemical_en": [
                    "Basal Dose (at sowing/transplanting): Full DAP/TSP + Half MOP (Potash) + Zinc Sulphate. DO NOT apply entire Urea at once!",
                    "Top Dressing: Split Urea into 2-3 equal installments (e.g. at active tillering and panicle/flowering initiation).",
                    "Always top dress Urea on moist soil (not in deep stagnant water or bone-dry soil) and incorporate into soil."
                ],
                "chemical_bn": [
                    "আসল নিয়ম (শেষ চাষে): সম্পূর্ণ ডিএপি/টিএসপি, অর্ধেক পটাশ এবং পুরো জিংক বা দস্তা সার শেষ চাষের সময় মাটিতে দিতে হয়। কখনোই সব ইউরিয়া একসাথে দেবেন না!",
                    "ইউরিয়া উপরি প্রয়োগ: ইউরিয়া সার সবসময় ২-৩ কিস্তিতে ভাগ করে দিতে হয় (যেমন চারা রোপণের ১৫-২০ দিন পর এবং থোড় বা ফুল আসার আগে)।",
                    "ইউরিয়া সার জমিতে অতিরিক্ত পানি থাকা অবস্থায় বা একদম শুকনো মাটিতে দেওয়া নিষেধ। জমিতে হালকা রস থাকলে ছিটান।"
                ],
                "suggestions_en": ["Zinc deficiency in rice", "Soil testing methods", "Organic compost preparation"],
                "suggestions_bn": ["ধানের দস্তা বা খায়রা রোগ", "মাটি পরীক্ষার সহজ নিয়ম", "জৈব সার তৈরির উপায়"]
            },

            # 8. Zinc Deficiency (Rice Khaira Disease)
            {
                "id": "zinc_deficiency",
                "category": "Fertilizer & Soil",
                "crops": ["rice", "maize", "wheat"],
                "keywords_en": ["zinc", "khaira", "zinc deficiency", "rusty brown spots", "khaira disease", "yellowing"],
                "keywords_bn": ["দস্তা", "জিংক", "খায়রা রোগ", "মরিচা দাগ", "দস্তার অভাব", "পাতায় লালচে দাগ"],
                "title_en": "🌾 Zinc Deficiency & Khaira Disease in Rice",
                "title_bn": "🌾 ধানের দস্তার অভাব ও খায়রা রোগ প্রতিকার",
                "summary_en": "Zinc deficiency causes rusty brown/bronze patches on third or fourth young leaves 2-3 weeks after transplanting. Plants remain stunted with delayed maturity.",
                "summary_bn": "চারা রোপণের ২-৩ সপ্তাহ পর কচি পাতার গোড়া হলুদ হয়ে যায় এবং পাতায় মরিচা পড়ার মতো লালচে-বাদামী দাগ ফুটে ওঠে। গাছ বেঁটে হয়ে যায়। একে ধানের 'খায়রা রোগ' বা দস্তার অভাব বলে।",
                "organic_en": [
                    "Drain stagnant water from the field for 3-5 days to aerate soil.",
                    "Apply farmyard manure enriched with zinc sulphate before transplanting."
                ],
                "organic_bn": [
                    "জমির পানি সরিয়ে দিয়ে ৩-৪ দিন বাতাস লাগতে দিন; মাটির ভেতরে বায়ু চলাচলের সুযোগ হলে গাছ দস্তা সহজে গ্রহণ করতে পারে।",
                    "গোবর সারের সাথে মিশিয়ে জমিতে জিংক প্রয়োগ করুন।"
                ],
                "chemical_en": [
                    "Soil application (Basal): Zinc Sulphate 21% @ 10 kg/acre OR Zinc Sulphate 33% (monohydrate) @ 6 kg/acre during final land preparation.",
                    "Emergency Foliar spray: Dissolve 5g Zinc Sulphate (21%) + 2.5g Slaked Lime (চুন) per 1 Liter of water and spray twice at 7-day intervals."
                ],
                "chemical_bn": [
                    "মাটিতে প্রয়োগ: শেষ চাষের সময় বিঘা প্রতি ১.৫-২ কেজি জিংক সালফেট ৩৩% মাটির সাথে মিশিয়ে দিন।",
                    "জরুরি স্প্রে: প্রতি লিটার জলে ৫ গ্রাম জিংক সালফেট (২১%) এবং ২.৫ গ্রাম খাবার চুন বা ইউরিয়া মিশিয়ে আক্রান্ত পাতায় পরপর দুইবার স্প্রে করুন।"
                ],
                "suggestions_en": ["Fertilizer guide", "Rice blast disease", "Soil health"],
                "suggestions_bn": ["সার প্রয়োগ নির্দেশিকা", "ধানের ব্লাস্ট রোগ", "মাটির স্বাস্থ্য পরীক্ষা"]
            },

            # 9. Irrigation & Water Management (AWD)
            {
                "id": "irrigation_water",
                "category": "Water Management",
                "crops": ["general", "rice", "wheat", "potato", "vegetables"],
                "keywords_en": ["irrigation", "water", "watering", "awd", "alternate wetting and drying", "drip", "drought", "waterlogging"],
                "keywords_bn": ["সেচ", "পানি", "জল", "সেচ ব্যবস্থাপনা", "এডব্লিউডি", "খরা", "পানি নিষ্কাশন", "সেচের সময়", "পর্যায়ক্রমিক সেচ"],
                "title_en": "💧 Smart Irrigation & AWD Water Management",
                "title_bn": "💧 আধুনিক সেচ ব্যবস্থাপনা ও এডব্লিউডি (AWD) পদ্ধতি",
                "summary_en": "Over-irrigation wastes energy, leaches nutrients, and causes root rot. Alternate Wetting and Drying (AWD) saves 25-30% water in paddy without any yield loss. Critical stages for irrigation must never face drought.",
                "summary_bn": "অতিরিক্ত পানি দিলে শিকড় পচে যায় এবং সারের অপচয় হয়। ধানে এডব্লিউডি (পর্যায়ক্রমিক ভেজানো ও শুকানো) পদ্ধতি ব্যবহার করলে ২৫-৩০% পানি ও বিদ্যুৎ সাশ্রয় হয়। ফসলের সংকটকালীন মুহূর্তে সেচ দেওয়া অত্যন্ত জরুরি।",
                "organic_en": [
                    "Use AWD perforated plastic pipe (পানি পাইপ): Irrigate only when water level inside the pipe sinks 15 cm below soil surface.",
                    "Use Mulching (straw or plastic sheets) in vegetables and potato to retain soil moisture and reduce water needs by half.",
                    "Always create 6-inch deep drainage furrows around the field borders to flush out excess monsoon water."
                ],
                "organic_bn": [
                    "এডব্লিউডি পাইপ পদ্ধতি: জমিতে একটি ছিদ্রযুক্ত পাইপ পুঁতে রাখুন। পাইপের ভেতরে পানি যখন মাটি থেকে ১৫ সেমি নিচে নেমে যাবে, তখনই কেবল সেচ দিন।",
                    "সবজি ও আলুতে খড় বা পাতার মালচিং ব্যবহার করুন, এতে মাটির রস দীর্ঘদিন ধরে থাকে এবং অর্ধেক সেচ বাঁচে।",
                    "বর্ষাকালে জলাবদ্ধতা ঠেকাতে জমির চারধারে অবশ্যই নিকাশী নালা তৈরি রাখুন।"
                ],
                "chemical_en": [
                    "Critical irrigation stages:",
                    "Wheat: Crown root initiation (CRI at 21 days), tillering, and milk stage.",
                    "Rice: Active tillering and flowering to milk stage (ensure standing water at flowering).",
                    "Potato: Tuber formation and tuber enlargement stages."
                ],
                "chemical_bn": [
                    "বিভিন্ন ফসলের সেচের সবচেয়ে জরুরি সময়:",
                    "গম: চারার বয়স ২০-২১ দিন (শিকড় বের হওয়ার সময়) এবং দানা বাঁধার সময় সেচ দেওয়া বাধ্যতামূলক।",
                    "ধান: কুশি বের হওয়ার সময় এবং শিষ বের হওয়ার পর দানা বাঁধার সময় কোনোভাবেই যেন পানির ঘাটতি না হয়।",
                    "আলু: আলুর গুটি ধরার সময় এবং গুটি বড় হওয়ার সময় নিয়মিত হালকা সেচ দিন।"
                ],
                "suggestions_en": ["Fertilizer guide", "Weather protection tips", "Rice blast disease"],
                "suggestions_bn": ["সারের নিয়মাবলী", "দুর্যোগ ও আবহাওয়া সতর্কতা", "ধানের রোগবালাই"]
            },

            # 10. Organic Bio-Pesticide (Neem Oil Preparation)
            {
                "id": "organic_neem_spray",
                "category": "Organic Farming",
                "crops": ["general", "vegetables", "fruits"],
                "keywords_en": ["neem oil", "bio pesticide", "organic pesticide", "natural spray", "homemade spray", "organic"],
                "keywords_bn": ["নিম তেল", "জৈব বালাইনাশক", "জৈব কীটনাশক", "প্রাকৃতিক স্প্রে", "নিম পাতার স্প্রে", "বিষমুক্ত চাষ"],
                "title_en": "🌿 How to Prepare & Use Neem Oil Bio-Pesticide",
                "title_bn": "🌿 নিম তেল দিয়ে প্রাকৃতিক জৈব বালাইনাশক তৈরির নিয়ম",
                "summary_en": "Neem oil contains Azadirachtin, which disrupts insect feeding, egg-laying, and metamorphosis without harming beneficial honeybees, earthworms, or spiders.",
                "summary_bn": "নিম তেলে থাকা 'আজাদিরাকটিন' ক্ষতিকর পোকার প্রজনন, ডিম পাড়া ও খাবার ক্ষমতা নষ্ট করে। কিন্তু এটি পরিবেশবান্ধব এবং উপকারী মৌমাছি ও মাকড়সার কোনো ক্ষতি করে না।",
                "organic_en": [
                    "Recipe for 10 Liters of spray:",
                    "1. Take 50 ml cold-pressed Pure Neem Oil (10,000 ppm or 1500 ppm).",
                    "2. Take 15-20 ml liquid soap or mild shampoo as emulsifier (essential because oil does not mix with water).",
                    "3. Thoroughly mix the soap with neem oil until it turns milky white.",
                    "4. Dilute this milky mixture into 10 liters of clean water and shake well.",
                    "5. Spray in the late afternoon (avoid hot midday sun) covering both upper and lower leaf surfaces."
                ],
                "organic_bn": [
                    "১০ লিটার স্প্রে তৈরির ঘরোয়া সহজ নিয়ম:",
                    "১. ৫০ মিলি খাঁটি কোল্ড-প্রেসড নিম তেল নিন।",
                    "২. তেলের সাথে ১৫-২০ মিলি লিকুইড সাবান বা সাধারণ শ্যাম্পু ভালোভাবে গুলিয়ে নিন (সাবান না দিলে তেল পানির সাথে মিশবে না)।",
                    "৩. তেল ও সাবানের সাদাটে মিশ্রণটি ১০ লিটার পরিষ্কার পানিতে ঢেলে খুব ভালোভাবে ঝাঁকান।",
                    "৪. বিকেলে রোদ কমে গেলে গাছের পাতার ওপর ও নিচে ভিজিয়ে স্প্রে করুন। প্রতি ৭-১০ দিন পরপর ব্যবহার করলে পোকার আক্রমণ মুক্ত থাকা যায়।"
                ],
                "chemical_en": [
                    "Neem acts as a preventive repellent. For heavy pest epidemics already beyond ETL, consider targeted systemic solutions."
                ],
                "chemical_bn": [
                    "নিম তেল মূলত পোকার আক্রমণ প্রতিরোধে সেরা। কিন্তু পোকা যদি ইতোমধ্যে মহামারীর মতো রূপ নেয়, তবে তাত্ক্ষণিক রাসায়নিক প্রতিকার নিন।"
                ],
                "suggestions_en": ["Tomato leaf curl & whitefly", "Rice stem borer", "Balanced fertilizer"],
                "suggestions_bn": ["টমেটোর সাদা মাছি ও পোকা", "ধানের মাজরা পোকা", "সুষম সার প্রয়োগ"]
            },

            # 11. Acidic Soil & Lime Treatment (মাটি পরীক্ষা ও চুন প্রয়োগ)
            {
                "id": "soil_lime_treatment",
                "category": "Fertilizer & Soil",
                "crops": ["general"],
                "keywords_en": ["soil", "acidic soil", "lime", "ph", "soil testing", "dolomite", "saline"],
                "keywords_bn": ["মাটি", "মাটি পরীক্ষা", "চুন", "অম্লীয় মাটি", "মাটির পিএইচ", "ডলোমাইট", "লবণাক্ত মাটি"],
                "title_en": "🌱 Soil Health, Acidic Soil & Lime (Dolomite) Treatment",
                "title_bn": "🌱 মাটির স্বাস্থ্য, অম্লীয় মাটি ও চুন প্রয়োগের নিয়ম",
                "summary_en": "Soils with pH below 6.0 lock up Phosphorus and micronutrients, drastically reducing crop yield. Applying agricultural lime (Calcium Carbonate) or Dolomite neutralizes soil acidity.",
                "summary_bn": "মাটির পিএইচ (pH) ৬.০ এর কম হলে মাটি অম্লীয় বা টক হয়ে যায়। এতে ফসফেট সার ও অন্যান্য পুষ্টি উপাদান মাটিতে আটকে থাকে এবং গাছ গ্রহণ করতে পারে না। কৃষি চুন বা ডলোমাইট প্রয়োগে মাটির উর্বরতা ফিরে আসে।",
                "organic_en": [
                    "Test your soil pH every 2-3 years at local Krishi Vigyan Kendra or Agriculture Office.",
                    "Apply Agricultural Lime or Dolomite @ 25-30 kg per Bigha (75-90 kg/acre) depending on acidity.",
                    "Apply lime 15-20 days BEFORE sowing or transplanting and plough it into moist soil.",
                    "NEVER mix lime directly with Urea or DAP/SSP fertilizers simultaneously, as it leads to ammonia gas loss."
                ],
                "organic_bn": [
                    "প্রতি ২-৩ বছর পর পর কৃষি অফিসে গিয়ে মাটির স্বাস্থ্য ও পিএইচ পরীক্ষা করুন।",
                    "মাটি অতিরিক্ত অম্লীয় হলে শেষ চাষের ১৫-২০ দিন আগে বিঘা প্রতি ২৫-৩০ কেজি গুঁড়ো কৃষি চুন বা ডলোমাইট মাটিতে ছিটিয়ে চষে দিন।",
                    "চুন প্রয়োগের সময় মাটিতে হালকা রস থাকা ভালো।",
                    "সাবধান: চুনের সাথে একই দিনে কখনোই ইউরিয়া বা ডিএপি সার মেশাবেন না, এতে সারের কার্যক্ষমতা নষ্ট হয়ে গ্যাস হয়ে উড়ে যায়।"
                ],
                "chemical_en": [
                    "For saline (alkaline) soils (pH > 8.5): Apply Gypsum @ 50 kg/acre and provide good drainage channels."
                ],
                "chemical_bn": [
                    "লবণাক্ত বা ক্ষারীয় মাটির জন্য (pH ৮.৫ এর বেশি): চুন দেবেন না; পরিবর্তে জিপসাম সার এবং প্রচুর জৈব সার প্রয়োগ করুন।"
                ],
                "suggestions_en": ["Fertilizer dosage guide", "Compost making", "Smart irrigation"],
                "suggestions_bn": ["সারের সঠিক মাত্রা", "কেঁচো সার তৈরি", "সেচ ব্যবস্থাপনা"]
            },

            # 12. Brinjal Shoot and Fruit Borer (বেগুনের ডগা ও ফল ছিদ্রকারী পোকা)
            {
                "id": "brinjal_fruit_borer",
                "category": "Pest Management",
                "crops": ["brinjal", "eggplant"],
                "keywords_en": ["brinjal", "eggplant", "fruit borer", "shoot borer", "leucinodes", "borer"],
                "keywords_bn": ["বেগুন", "বেগুনের পোকা", "ডগা ছিদ্রকারী", "ফল ছিদ্রকারী", "বেগুনের ডগা ও ফল পচা"],
                "title_en": "🍆 Brinjal Shoot and Fruit Borer Management",
                "title_bn": "🍆 বেগুনের ডগা ও ফল ছিদ্রকারী পোকা দমন",
                "summary_en": "Caterpillars bore into tender shoots causing drooping, then bore inside developing eggplants leaving small holes plugged with excreta, making fruits unmarketable.",
                "summary_bn": "কীড়া বেগুনের কচি ডগায় ঢুকে খায়, ফলে ডগা নুয়ে পড়ে শুকিয়ে যায়। পরবর্তীতে ফলের ভেতরে ঢুকে খেয়ে ছিদ্র করে এবং মল ত্যাগ করে, যার ফলে বেগুন পচে ও খাওয়ার অনুপযোগী হয়ে যায়।",
                "organic_en": [
                    "Clip and destroy wilted shoot tips and infected fruits with larvae inside twice a week.",
                    "Install Lucinlure Pheromone Traps @ 12-15 traps/acre.",
                    "Spray Bacillus thuringiensis (Bt) formulation @ 2 g/L water.",
                    "Spray Neem Seed Kernel Extract (5%) or Neem Oil 5ml/L."
                ],
                "organic_bn": [
                    "সপ্তাহে দুইবার আক্রান্ত ডগা ও পোকা লাগা বেগুন ছিঁড়ে মাটিতে পুঁতে বা পুড়িয়ে ফেলুন।",
                    "জমিতে 'লিউসিনলুর' সেক্স ফেরোমন ফাঁদ বিঘা প্রতি ৪-৫টি স্থাপন করুন। এতে পুরুষ পোকা ফাঁদে পড়ে বংশবৃদ্ধি বন্ধ হয়।",
                    "জৈব বালাইনাশক যেমন বিটি (Bacillus thuringiensis) প্রতি লিটার পানিতে ২ গ্রাম মিশিয়ে স্প্রে করুন।",
                    "নিম তেল স্প্রে করুন।"
                ],
                "chemical_en": [
                    "Spray Emamectin Benzoate 5% SG (Proclaim) @ 0.5 g/L OR Chlorantraniliprole 18.5% SC @ 0.4 ml/L water.",
                    "Observe 3-day waiting period before harvesting fruits for market."
                ],
                "chemical_bn": [
                    "রাসায়নিক প্রতিকার: এমামেক্টিন বেনজয়েট ৫% এসজি (যেমন প্রোক্লেইম) প্রতি লিটার জলে ০.৫ গ্রাম অথবা কোরাজেন ০.৪ মিলি/লিটার স্প্রে করুন।",
                    "কীটনাশক স্প্রে করার পর অন্তত ৩-৫ দিন বেগুন তুলবেন না।"
                ],
                "suggestions_en": ["Bio-pesticide recipe", "Tomato fruit care", "Pesticide waiting periods"],
                "suggestions_bn": ["জৈব নিম তেল তৈরি", "টমেটোর রোগ দমন", "কীটনাশক ব্যবহারের সতর্কতা"]
            },

            # 13. Weather, Cyclone & Heavy Rain Precautions
            {
                "id": "weather_disaster",
                "category": "Weather Advisory",
                "crops": ["general", "rice", "potato", "vegetables"],
                "keywords_en": ["weather", "rain", "heavy rain", "cyclone", "flood", "storm", "fog", "frost", "cold wave"],
                "keywords_bn": ["আবহাওয়া", "বৃষ্টি", "ভারী বৃষ্টি", "ঘূর্ণিঝড়", "বন্যা", "তুফান", "কুয়াশা", "শীত", "ঠাণ্ডা", "দুর্যোগ"],
                "title_en": "⛈️ Weather Precautions: Heavy Rain, Storms & Frost Protection",
                "title_bn": "⛈️ আবহাওয়া ও দুর্যোগ সতর্কতা: ভারী বৃষ্টি, ঝড় ও কুয়াশা থেকে রক্ষা",
                "summary_en": "Sudden weather extremes can destroy standing crops. Proactive field preparation, clearing drainage, and timing sprays according to forecasts protects hard work.",
                "summary_bn": "হঠাৎ ঝড়-বৃষ্টি, কুয়াশা বা বন্যা ফসলের ব্যাপক ক্ষতি করে। আবহাওয়ার পূর্বাভাস দেখে আগে থেকেই পানি নিকাশের ব্যবস্থা রাখা এবং স্প্রে বন্ধ রাখা জরুরি।",
                "organic_en": [
                    "Before heavy rains/cyclones: Clear all peripheral field drains and channels so water drains out immediately.",
                    "Harvest ready crops (80-85% mature grains) immediately without waiting for full 100% maturity.",
                    "Do NOT spray pesticides or broadcast fertilizers if rain is forecast within 24 hours.",
                    "During heavy winter fog: Light small bonfires (ধোঁয়া দেওয়া) on the windward side of potato fields at night to raise temperature and deter fungal spores."
                ],
                "organic_bn": [
                    "ভারী বৃষ্টি বা ঝড়ের পূর্বাভাস পেলে: জমির চারপাশের নিকাশী নালাগুলো তাৎক্ষণিক পরিষ্কার করুন যেন পানি জমে না থাকে।",
                    "জমিতে ৮০-৮৫% ধান বা ফসল পেকে থাকলে দেরি না করে দ্রুত কেটে মাড়াই করে ঘরে তুলুন।",
                    "বৃষ্টির সম্ভাবনা থাকলে জমিতে সার বা কীটনাশক স্প্রে করা পুরোপুরি স্থগিত রাখুন।",
                    "আলুর জমিতে ঘন কুয়াশার রাতে জমির উত্তর-পশ্চিম কোণে খড়কুটোয় ধোঁয়া তৈরি করলে তাপমাত্রা কিছুটা বাড়ে এবং নাবি ধসার ঝুঁকি কমে।"
                ],
                "chemical_en": [
                    "Post-rain recovery: Drain all submerged fields within 24-48 hours. Spray 1% Urea solution (10g/L) or 0.5% Potash foliar spray to help plants regain root vigor."
                ],
                "chemical_bn": [
                    "বৃষ্টি বা পানি নেমে যাওয়ার পর: দ্রুত জমিতে জমা পানি বের করুন। গাছ চাঙ্গা করতে ১% ইউরিয়া বা পটাশ দ্রবণ পাতায় স্প্রে করুন।"
                ],
                "suggestions_en": ["Potato late blight in foggy weather", "Smart irrigation", "Farmer helplines"],
                "suggestions_bn": ["কুয়াশায় আলুর নাবি ধসা রক্ষা", "আধুনিক সেচ পদ্ধতি", "কৃষি হেল্পলাইন নম্বর"]
            },

            # 14. Government Helplines & Emergency Agri Support
            {
                "id": "helpline_support",
                "category": "Helpline & Schemes",
                "crops": ["general"],
                "keywords_en": ["helpline", "kisan call center", "support", "government", "contact", "scheme", "emergency", "expert", "phone"],
                "keywords_bn": ["হেল্পলাইন", "কৃষি হেল্পলাইন", "কিষাণ কল সেন্টার", "ফোন নম্বর", "সরকারি সহায়তা", "কৃষি অফিসার", "জরুরি নম্বর"],
                "title_en": "📞 Farmer Helpline & Agricultural Expert Contact Numbers",
                "title_bn": "📞 কৃষি হেল্পলাইন ও কৃষক সহায়তা জরুরি নম্বর",
                "summary_en": "Official toll-free telephone numbers where farmers can directly speak to agricultural scientists and agronomists in English, Bengali, or local languages free of cost.",
                "summary_bn": "সরকারি টোল-ফ্রি নম্বর যেখানে বিনামূল্যে কৃষি বিজ্ঞানী ও বিশেষজ্ঞদের সাথে সরাসরি বাংলা ও স্থানীয় ভাষায় কথা বলে ফসলের সমস্যা সমাধান পাওয়া যায়।",
                "organic_en": [
                    "India — Kisan Call Center: 1800-180-1551 (Toll-Free, 6 AM to 10 PM, supports Bengali/Hindi/English).",
                    "India — Short Code: 15533.",
                    "West Bengal — Matir Katha & Agri Help: Available through local Block Development Agricultural Office (ADA).",
                    "Bangladesh — Krishi Call Center: 16123 (Call from any mobile operator for expert farming solutions)."
                ],
                "organic_bn": [
                    "🇮🇳 ভারত — কিষাণ কল সেন্টার (Kisan Call Center): ১৮০০-১৮০-১৫৫১ (1800-180-1551, সম্পূর্ণ বিনামূল্যে সকাল ৬টা থেকে রাত ১০টা পর্যন্ত বাংলায় সহায়তা)।",
                    "🇮🇳 ভারতের শর্ট কোড: ১৫৫৩৩ (15533)।",
                    "পশ্চিমবঙ্গ: স্থানীয় ব্লক কৃষি আধিকারিক (ADA অফিস) ও মাটির কথা পোর্টাল।",
                    "🇧🇩 বাংলাদেশ — কৃষি কল সেন্টার: ১৬১২৩ (16123, যেকোনো মোবাইল অপারেটর থেকে কল করে কৃষি বিশেষজ্ঞদের পরামর্শ নিন)।"
                ],
                "chemical_en": [],
                "chemical_bn": [],
                "suggestions_en": ["Rice blast disease", "Urea & DAP fertilizer guide", "Potato late blight"],
                "suggestions_bn": ["ধানের ব্লাস্ট রোগ প্রতিকার", "ইউরিয়া ও ডিএপি সারের নিয়ম", "আলুর নাবি ধসা রোগ"]
            },

            # 15. Wheat Rust and Blight (গমের রোগ ও প্রতিকার)
            {
                "id": "wheat_rust",
                "category": "Disease Control",
                "crops": ["wheat"],
                "keywords_en": ["wheat", "wheat rust", "yellow rust", "brown rust", "wheat disease"],
                "keywords_bn": ["গম", "গমের রোগ", "হলুদ মরিচা", "গমের মরিচা রোগ", "গমের ব্লাস্ট", "গম চাষ"],
                "title_en": "🌾 Wheat Rust & Leaf Blight Management",
                "title_bn": "🌾 গমের মরিচা ও পাতা পোড়া রোগ ব্যবস্থাপনা",
                "summary_en": "Yellow/Stripe rust and Brown/Leaf rust produce powdery pustules on wheat leaves, reducing photosynthetic area and causing shriveled grains.",
                "summary_bn": "গমের পাতার ওপর হলুদ বা বাদামী রঙের গুঁড়ো গুঁড়ো মরিচার মতো দাগ হয়। স্পর্শ করলে আঙুলে গুঁড়ো পাউডারের মতো লেগে যায়। এতে দানা পুষ্ট হয় না ও চিটা হয়ে যায়।",
                "organic_en": [
                    "Sow resistant wheat varieties recommended for your region.",
                    "Ensure timely sowing (by mid-November) to avoid terminal heat and late rust attacks.",
                    "Avoid excessive Nitrogen fertilizers."
                ],
                "organic_bn": [
                    "রোগ প্রতিরোধী অনুমোদিত জাতের গমের বীজ বপন করুন।",
                    "সঠিক সময়ে (নভেম্বরের মাঝামাঝি) বীজ বপন সম্পন্ন করুন।",
                    "অতিরিক্ত ইউরিয়া প্রয়োগ থেকে বিরত থাকুন।"
                ],
                "chemical_en": [
                    "At first sign of rust: Spray Propiconazole 25% EC (Tilt) @ 1 ml/L OR Tebuconazole 25.9% EC @ 1 ml/L water.",
                    "Repeat after 15 days if cloudy humid conditions persist."
                ],
                "chemical_bn": [
                    "রোগের লক্ষণ দেখা মাত্র: প্রোপিকোনাজোল ২৫% ইসি (যেমন টিল্ট) প্রতি লিটার জলে ১ মিলি অথবা টেবুকোনাজোল ১ মিলি/লিটার স্প্রে করুন।",
                    "মেঘলা আবহাওয়া থাকলে ১৫ দিন পর আরেকবার স্প্রে করুন।"
                ],
                "suggestions_en": ["Fertilizer guide", "Irrigation at CRI stage", "Mustard aphid"],
                "suggestions_bn": ["সারের সঠিক ব্যবহার", "গমের সেচের সময়", "সরিষার জাব পোকা"]
            },

            # 16. Mustard Aphid / Jhab Poka (সরিষার জাব পোকা)
            {
                "id": "mustard_aphid",
                "category": "Pest Management",
                "crops": ["mustard"],
                "keywords_en": ["mustard", "aphid", "mustard aphid", "lipaphis", "jhab poka"],
                "keywords_bn": ["সরিষা", "সরিষার পোকা", "জাব পোকা", "সরিষার জাব পোকা", "মাছি পোকা"],
                "title_en": "🌼 Mustard Aphid (Lipaphis erysimi) Control",
                "title_bn": "🌼 সরিষার জাব পোকা (Aphid) দমন পদ্ধতি",
                "summary_en": "Colonies of tiny greenish-black aphids suck sap from mustard flowers, pods, and tender shoots during flowering, drastically reducing oil yield.",
                "summary_bn": "ফুল ও পড ধরার সময় হাজার হাজার ক্ষুদ্র সবুজ-কালো জাব পোকা দলবেঁধে কুঁড়ি ও কচি ডাল থেকে রস চুষে খায়। গাছ দুর্বল হয়ে যায় এবং ফলন ব্যাপক কমে যায়।",
                "organic_en": [
                    "Install Yellow Sticky Traps @ 10 traps/acre.",
                    "Spray Neem Oil @ 5 ml/L water with soap.",
                    "Conserve natural predators like Ladybird beetles."
                ],
                "organic_bn": [
                    "জমিতে হলুদ আঠালো ফাঁদ (Yellow Sticky Trap) বিঘা প্রতি ৪-৫টি টাঙান।",
                    "প্রাথমিক অবস্থায় নিম তেল ৫ মিলি প্রতি লিটার জলে সাবান মিশিয়ে স্প্রে করুন।",
                    "উপকারী বন্ধু পোকা (লেডিবার্ড বিটল) সংরক্ষণ করুন।"
                ],
                "chemical_en": [
                    "Spray Dimethoate 30% EC (Rogor) @ 1.7 ml/L OR Imidacloprid 17.8% SL @ 0.3 ml/L water.",
                    "Spray in the LATE AFTERNOON to avoid killing foraging honeybees."
                ],
                "chemical_bn": [
                    "রোগ বেশি হলে: ডাইমিথোয়েট ৩০% ইসি (রোগর) প্রতি লিটার পানিতে ১.৫-১.৭ মিলি অথবা ইমিডাক্লোপ্রিড ০.৩ মিলি/লিটার স্প্রে করুন।",
                    "অবশ্যই বিকেলে স্প্রে করবেন, যেন উপকারী মৌমাছির কোনো ক্ষতি না হয়।"
                ],
                "suggestions_en": ["Neem bio-spray recipe", "Wheat rust management", "Helpline numbers"],
                "suggestions_bn": ["জৈব নিম তেল তৈরি", "গমের রোগবালাই", "কৃষি হেল্পলাইন নম্বর"]
            }
        ]

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
                return diag_resp

        # 2. General greetings
        greeting_resp = self._check_greetings(q_lower, lang)
        if greeting_resp:
            return greeting_resp

        # 3. Check direct 38-class name match in query
        class_match_resp = self._match_disease_class(q_lower, lang)
        if class_match_resp:
            return class_match_resp

        # 4. Match against Knowledge Base items
        best_item, score = self._find_best_match(q_lower, diagnosis_context)
        if best_item and score >= 2:
            return self._format_kb_response(best_item, lang)

        # 5. Fallback to diagnosis context if present
        if diagnosis_context:
            diag_resp = self._handle_diagnosis_context(diagnosis_context, lang)
            if diag_resp:
                return diag_resp

        # 6. Optional LLM invocation if an API key is available
        llm_reply = self._try_llm_generation(query, lang)
        if llm_reply:
            return {
                "ok": True,
                "reply": llm_reply,
                "language": lang,
                "category": "Expert AI Advisory",
                "suggestions": [
                    "ধানের মাজরা পোকা দমন" if lang == "bn" else "Rice stem borer remedies",
                    "আলুর নাবি ধসা রোগ" if lang == "bn" else "Potato late blight control",
                    "সারের সঠিক মাত্রা" if lang == "bn" else "Fertilizer dosage guide",
                    "কিষাণ হেল্পলাইন নম্বর" if lang == "bn" else "Farmer helpline numbers"
                ],
                "helpline": "1800-180-1551 (IN) / 16123 (BD)"
            }

        # 7. Smart Fallback with guidance and quick prompts
        return self._build_smart_fallback(query, lang)

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
        words = set(re.findall(r"\b[\w\u0980-\u09FF]+\b", query))

        for item in self.kb:
            score = 0
            for crop in item.get("crops", []):
                aliases = self.crop_aliases.get(crop, [crop])
                for alias in aliases:
                    if alias.lower() in query:
                        score += 3
                        break

            for kw in item.get("keywords_en", []):
                if kw.lower() in query:
                    score += 4
                elif any(w == kw.lower() for w in words):
                    score += 2

            for kw in item.get("keywords_bn", []):
                if kw in query:
                    score += 5
                elif any(w == kw for w in words):
                    score += 3

            if context and item.get("crops"):
                for c in item["crops"]:
                    if c.lower() in context.lower():
                        score += 2

            if score > max_score:
                max_score = score
                best_item = item

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
        words = set(re.findall(r"\b[\w\u0980-\u09FF]+\b", query))

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
