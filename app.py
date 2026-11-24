import json
import re
import random
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

HERE = Path(__file__).resolve().parent
if (HERE / "index.html").exists():
    DB_PATH = HERE / "music.db"
    FRONTEND_PATH = HERE / "index.html"
else:
    BASE_DIR = HERE.parent
    DB_PATH = BASE_DIR / "backend" / "music.db"
    FRONTEND_PATH = BASE_DIR / "frontend" / "index.html"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="고양이 뷔페 API")

import base64 as _b64
from fastapi.responses import Response as _Resp

_ICON_64_BYTES = _b64.b64decode("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")
_ICON_192_BYTES = _b64.b64decode("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")

@app.get("/favicon.ico")
@app.get("/favicon.png")
def serve_favicon():
    return _Resp(content=_ICON_64_BYTES, media_type="image/png", headers={"Cache-Control": "public, max-age=3600"})

@app.get("/apple-touch-icon.png")
@app.get("/apple-touch-icon-precomposed.png")
def serve_apple_touch_icon():
    return _Resp(content=_ICON_192_BYTES, media_type="image/png", headers={"Cache-Control": "public, max-age=3600"})
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

CLASSICAL_COMPOSER_WHITELIST_RE = re.compile(r"\balbeniz\b|\balbinoni\b|\balbéniz\b|\balfven\b|\balfvén\b|\balkan\b|\barensky\b|\bbach\b|\bbalakirev\b|\bbarber\b|\bbarrios\b|\bbartok\b|\bmilhaud\b|\bmassenet\b|\bgluck\b|\bbartók\b|\bbax\b|amy\s+beach|\bbeethoven\b|\bbellini\b|\bberlioz\b|\bbernstein\b|\bberwald\b|\bbiber\b|\bbizet\b|\bboccherini\b|\bborodin\b|\bbrahms\b|frank\s+bridge|\bbritten\b|\bbruch\b|\bbruckner\b|\bbusoni\b|\bbuxtehude\b|\bcarcassi\b|\bchabrier\b|\bchausson\b|\bchopin\b|\bclementi\b|\bcopland\b|\bcorelli\b|\bcouperin\b|\bcui\b|\bczerny\b|\bdebussy\b|\bdelibes\b|\bdelius\b|\bdiabelli\b|\bdittersdorf\b|\bdonizetti\b|\bdukas\b|\bdvorak\b|\bdvořák\b|\belgar\b|\benescu\b|\bfalla\b|\bfaure\b|\bfauré\b|\bfibich\b|\bfinzi\b|\bfranck\b|\bgershwin\b|\bginastera\b|\bgiuliani\b|\bglazunov\b|\bgluck\b|\bgounod\b|\bgranados\b|\bgrieg\b|\bhandel\b|\bhaydn\b|\bholst\b|\bhummel\b|john\s+ireland|\bjanacek\b|\bjanáček\b|\bjoachim\b|\bkalinnikov\b|\bkalman\b|\bkhachaturian\b|\bkodaly\b|\bkodály\b|\bkuhlau\b|\bkálmán\b|\blalo\b|\blehar\b|\blehár\b|\bleoncavallo\b|\bliadov\b|\bliszt\b|\blocatelli\b|\blully\b|\blyapunov\b|\bmacdowell\b|\bmahler\b|\bmarcello\b|\bmartinu\b|\bmartinů\b|\bmascagni\b|\bmassenet\b|\bmedtner\b|\bmendelssohn\b|\bmeyerbeer\b|\bmonteverdi\b|\bmozart\b|\bmussorgsky\b|\bnielsen\b|\boffenbach\b|\bpachelbel\b|\bpaganini\b|\bpergolesi\b|\bponce\b|\bprokofiev\b|\bpuccini\b|\bpurcell\b|\brachmaninoff\b|\brameau\b|\bravel\b|\breger\b|\brespighi\b|\brimsky\-korsakov\b|\brodrigo\b|\brossini\b|\bsaint\-saens\b|\bsaint\-saëns\b|\bsalieri\b|\bsarasate\b|\bsatie\b|\bscarlatti\b|\bschubert\b|\bschumann\b|\bscriabin\b|\bshostakovich\b|\bsibelius\b|\bsmetana\b|fernando\s+sor|\bspohr\b|\bstamitz\b|\bstenhammar\b|\bstrauss\b|\bstravinsky\b|josef\s+suk|\bsvendsen\b|\btaneyev\b|\btarrega\b|\btartini\b|\btchaikovsky\b|\btelemann\b|\bthalberg\b|\bturina\b|\btárrega\b|\bverdi\b|\bvieuxtemps\b|\bvilla\-lobos\b|\bviotti\b|\bvivaldi\b|\bwagner\b|\bwalton\b|\bweiss\b|\bwieniawski\b|vaughan\s+williams|hugo\s+wolf", re.I)
CLASSICAL_EXCLUDE_RE = re.compile(r"[\u3040-\u309F\u30A0-\u30FF]|k\.k\.|totakeke|animal crossing|nintendo|ghibli|zelda|final fantasy|touhou|vocaloid|hatsune|piano variation|piano arrangement|music box|bgm|instrumental version|acoustic version|piano version|오르골|피아노 버전|베리에이션|yiruma|hisaishi|sakamoto|einaudi|richter|tiersen|clayderman|2cellos|garrett|maksim|queen|beatles|coldplay|radiohead|muse|metallica|pink floyd|led zeppelin|oasis|nirvana|linkin park|imagine dragons|soundtrack|\bost\b|anime|\bgame\b|cover|tribute|karaoke|remix|8-bit|lullaby|medley|jazz|rock|metal|hip.?hop|\bpop\b|synth|electronic|new age|ambient|crossover|cinematic|lofi|lo-fi|avant.?garde|atonal|serialism|twelve.?tone|electroacoustic|musique concrète|microtonal|experimental|noise|\bcage\b|stockhausen|xenakis|boulez|penderecki|ligeti|ferneyhough|schoenberg|webern|\bberg\b|feldman|berio|\bnono\b|feat\.|이루마|히사이시|류이치|커버|리믹스|자장가|동물의 숲|지브리", re.I)

GENRE_ARTISTS = {
    "pop": [
        "Taylor Swift",
        "The Weeknd",
        "Bruno Mars",
        "Dua Lipa",
        "Ed Sheeran",
        "Billie Eilish",
        "Ariana Grande",
        "Charlie Puth",
        "Justin Bieber",
        "Coldplay",
        "Maroon 5",
        "Lauv",
        "Shawn Mendes",
        "Harry Styles",
        "Adele",
        "Sabrina Carpenter",
        "Olivia Rodrigo",
        "Troye Sivan"
    ],
    "kpop": [
        "IU",
        "BTS",
        "NewJeans",
        "DAY6",
        "AKMU",
        "Taeyeon",
        "aespa",
        "BLACKPINK",
        "SEVENTEEN",
        "Red Velvet",
        "EXO",
        "Paul Kim",
        "Heize",
        "10CM",
        "Jannabi",
        "Younha",
        "Crush",
        "Zion.T",
        "Baek Yerin",
        "BOL4"
    ],
    "rnb": [
        "Frank Ocean",
        "Daniel Caesar",
        "SZA",
        "H.E.R.",
        "Bruno Major",
        "The Weeknd",
        "Khalid",
        "Giveon",
        "Brent Faiyaz",
        "Mac Ayres",
        "Summer Walker",
        "Dean",
        "Crush",
        "Colde",
        "Usher",
        "Alicia Keys",
        "John Legend"
    ],
    "soul": [
        "Stevie Wonder",
        "Aretha Franklin",
        "Marvin Gaye",
        "Silk Sonic",
        "Leon Bridges",
        "Amy Winehouse",
        "Corinne Bailey Rae",
        "Sam Cooke",
        "Otis Redding",
        "Erykah Badu",
        "Al Green",
        "Bill Withers",
        "John Mayer",
        "Norah Jones",
        "Michael Kiwanuka"
    ],
    "indie": [
        "The 1975",
        "LANY",
        "Cigarettes After Sex",
        "Tame Impala",
        "Arctic Monkeys",
        "Mac DeMarco",
        "Men I Trust",
        "Clairo",
        "Rex Orange County",
        "Beach House",
        "The Black Skirts",
        "HYUKOH",
        "Jannabi",
        "Baek Yerin",
        "wave to earth",
        "Phoebe Bridgers"
    ],
    "rock": [
        "Queen",
        "Coldplay",
        "Oasis",
        "Radiohead",
        "Linkin Park",
        "Imagine Dragons",
        "Muse",
        "The Beatles",
        "Nirvana",
        "Green Day",
        "Foo Fighters",
        "Maroon 5",
        "DAY6",
        "Younha",
        "OneRepublic",
        "U2",
        "Red Hot Chili Peppers",
        "The Killers"
    ],
    "hiphop": [
        "Kendrick Lamar",
        "Drake",
        "Kanye West",
        "Travis Scott",
        "Tyler, The Creator",
        "J. Cole",
        "Post Malone",
        "Mac Miller",
        "Nujabes",
        "EPIK HIGH",
        "ZICO",
        "beenzino",
        "Kid Cudi",
        "A$AP Rocky",
        "Eminem",
        "Jay-Z"
    ],
    "jazz": [
        "Chet Baker",
        "Miles Davis",
        "Bill Evans",
        "John Coltrane",
        "Norah Jones",
        "Frank Sinatra",
        "Ella Fitzgerald",
        "Louis Armstrong",
        "Nat King Cole",
        "Stan Getz",
        "João Gilberto",
        "Nina Simone",
        "Herbie Hancock",
        "Kamasi Washington",
        "Robert Glasper",
        "Laufey"
    ],
    "lofi": [
        "Nujabes",
        "Jinsang",
        "Idealism",
        "potsu",
        "Kupla",
        "eevee",
        "SwuM",
        "Jhove",
        "Lofi Girl",
        "Tomppabeats",
        "Bsd.u",
        "In Love With a Ghost",
        "Ryuichi Sakamoto",
        "Joe Hisaishi",
        "Yiruma"
    ],
    "ambient": [
        "Brian Eno",
        "Ryuichi Sakamoto",
        "Max Richter",
        "Ludovico Einaudi",
        "Ólafur Arnalds",
        "Nils Frahm",
        "Yiruma",
        "Joe Hisaishi",
        "Hammock",
        "Stars of the Lid",
        "Tycho",
        "Aphex Twin",
        "Sigur Rós",
        "M83",
        "Explosions in the Sky",
        "Bonobo"
    ],
    "citypop": [
        "Tatsuro Yamashita",
        "Mariya Takeuchi",
        "Anri",
        "Miki Matsubara",
        "Taeko Onuki",
        "Junko Yagami",
        "Toshiki Kadomatsu",
        "Omega Tribe",
        "Meiko Nakahara",
        "Yukika",
        "Yubin",
        "Bronze",
        "Fujii Kaze",
        "Kirinji",
        "Casiopea"
    ],
    "acoustic": [
        "Jason Mraz",
        "Ed Sheeran",
        "John Mayer",
        "Jack Johnson",
        "10CM",
        "IU",
        "Jukjae",
        "Kwak Jin Eon",
        "Damien Rice",
        "James Taylor",
        "Simon & Garfunkel",
        "Norah Jones",
        "Ben Howard",
        "Bon Iver",
        "Sufjan Stevens",
        "Iron & Wine"
    ]
}

GENRE_TO_MB_TAGS = {
    "all": [
        "symphony",
        "concerto",
        "piano sonata",
        "string quartet",
        "nocturne",
        "baroque",
        "opera aria"
    ],
    "orchestra": [
        "symphony",
        "symphonic poem",
        "overture",
        "orchestral suite",
        "philharmonic"
    ],
    "piano": [
        "piano sonata",
        "nocturne",
        "etude",
        "prelude",
        "ballade",
        "impromptu"
    ],
    "strings": [
        "violin sonata",
        "cello suite",
        "violin concerto",
        "cello concerto",
        "solo violin"
    ],
    "winds": [
        "flute concerto",
        "clarinet concerto",
        "horn concerto",
        "oboe concerto",
        "bassoon",
        "wind quintet"
    ],
    "percussion": [
        "timpani",
        "marimba",
        "percussion concerto",
        "bartok percussion",
        "xylophone classical"
    ],
    "chamber": [
        "string quartet",
        "piano trio",
        "piano quintet",
        "chamber music",
        "octet"
    ],
    "concerto": [
        "piano concerto",
        "violin concerto",
        "cello concerto",
        "double concerto",
        "brandenburg"
    ],
    "opera": [
        "opera aria",
        "soprano aria",
        "puccini aria",
        "verdi opera",
        "mozart opera"
    ],
    "vocal": [
        "lied",
        "schubert lieder",
        "requiem",
        "cantata",
        "choral classical",
        "ave maria"
    ],
    "baroque": [
        "baroque",
        "harpsichord",
        "vivaldi",
        "handel",
        "telemann",
        "scarlatti"
    ]
}

SEED_SONGS = [
    [
        "c1",
        "Symphony No.9 'From the New World': II. Largo",
        "Antonín Dvořák",
        [
            "orchestra"
        ],
        [
            "early_morning",
            "sunset",
            "night"
        ],
        [
            "cloudy",
            "clear_breeze",
            "snowy"
        ],
        [
            "tired",
            "calm",
            "lonely"
        ],
        [
            "comfort",
            "rest",
            "reflective"
        ]
    ],
    [
        "c2",
        "Má vlast: Vltava (The Moldau)",
        "Bedřich Smetana",
        [
            "orchestra"
        ],
        [
            "early_morning",
            "morning",
            "afternoon"
        ],
        [
            "sunny",
            "clear_breeze",
            "windy"
        ],
        [
            "calm",
            "excited",
            "happy"
        ],
        [
            "refresh",
            "energize",
            "reflective"
        ]
    ],
    [
        "c3",
        "An der schönen blauen Donau, Op.314",
        "Johann Strauss II",
        [
            "orchestra"
        ],
        [
            "morning",
            "afternoon",
            "sunset"
        ],
        [
            "sunny",
            "clear_breeze",
            "partly_cloudy"
        ],
        [
            "happy",
            "excited",
            "drowsy"
        ],
        [
            "excited_up",
            "refresh",
            "energize"
        ]
    ],
    [
        "c4",
        "Symphony No.5 in C-Sharp Minor: IV. Adagietto",
        "Gustav Mahler",
        [
            "orchestra"
        ],
        [
            "sunset",
            "night",
            "late_night"
        ],
        [
            "rainy",
            "foggy",
            "cloudy"
        ],
        [
            "sad",
            "lonely",
            "tired"
        ],
        [
            "reflective",
            "comfort",
            "calm_down"
        ]
    ],
    [
        "c5",
        "Swan Lake, Op.20: Scene (Moderato)",
        "Pyotr Ilyich Tchaikovsky",
        [
            "orchestra"
        ],
        [
            "sunset",
            "night"
        ],
        [
            "snowy",
            "windy",
            "cloudy",
            "stormy"
        ],
        [
            "stressed",
            "frustrated",
            "sad",
            "focused"
        ],
        [
            "reflective",
            "confident",
            "comfort"
        ]
    ],
    [
        "c6",
        "Nocturne Op.9 No.2 in E-Flat Major",
        "Frédéric Chopin",
        [
            "piano"
        ],
        [
            "night",
            "late_night",
            "early_morning"
        ],
        [
            "rainy",
            "snowy",
            "foggy",
            "cloudy"
        ],
        [
            "calm",
            "lonely",
            "sad",
            "focused"
        ],
        [
            "sleep",
            "calm_down",
            "focus",
            "rest"
        ]
    ],
    [
        "c7",
        "Clair de Lune (Suite bergamasque)",
        "Claude Debussy",
        [
            "piano"
        ],
        [
            "early_morning",
            "late_night",
            "night"
        ],
        [
            "snowy",
            "foggy",
            "drizzle"
        ],
        [
            "calm",
            "focused",
            "tired"
        ],
        [
            "sleep",
            "focus",
            "calm_down",
            "rest"
        ]
    ],
    [
        "c8",
        "Piano Sonata No.14 'Moonlight': I. Adagio sostenuto",
        "Ludwig van Beethoven",
        [
            "piano"
        ],
        [
            "night",
            "late_night",
            "sunset"
        ],
        [
            "rainy",
            "snowy",
            "foggy",
            "cloudy"
        ],
        [
            "sad",
            "lonely",
            "focused",
            "calm"
        ],
        [
            "reflective",
            "sleep",
            "calm_down",
            "focus"
        ]
    ],
    [
        "c9",
        "Étude in C-Sharp Minor, Op.2 No.1",
        "Alexander Scriabin",
        [
            "piano"
        ],
        [
            "night",
            "late_night",
            "sunset"
        ],
        [
            "rainy",
            "snowy",
            "foggy",
            "cloudy"
        ],
        [
            "sad",
            "lonely",
            "focused"
        ],
        [
            "reflective",
            "comfort",
            "calm_down"
        ]
    ],
    [
        "c10",
        "Gymnopédie No.1",
        "Erik Satie",
        [
            "piano"
        ],
        [
            "early_morning",
            "afternoon",
            "late_night"
        ],
        [
            "drizzle",
            "rainy",
            "foggy",
            "snowy"
        ],
        [
            "tired",
            "calm",
            "drowsy",
            "focused"
        ],
        [
            "rest",
            "sleep",
            "calm_down",
            "focus"
        ]
    ],
    [
        "c11",
        "Liebestraum No.3 in A-Flat Major, S.541",
        "Franz Liszt",
        [
            "piano"
        ],
        [
            "sunset",
            "night",
            "late_night"
        ],
        [
            "clear_breeze",
            "rainy",
            "snowy",
            "cloudy"
        ],
        [
            "calm",
            "lonely",
            "sad",
            "excited"
        ],
        [
            "comfort",
            "reflective",
            "rest"
        ]
    ],
    [
        "c12",
        "Pavane pour une infante défunte",
        "Maurice Ravel",
        [
            "piano"
        ],
        [
            "early_morning",
            "sunset",
            "late_night"
        ],
        [
            "drizzle",
            "foggy",
            "rainy",
            "snowy"
        ],
        [
            "tired",
            "calm",
            "drowsy",
            "sad"
        ],
        [
            "calm_down",
            "sleep",
            "rest",
            "comfort"
        ]
    ],
    [
        "c13",
        "Cello Suite No.1 in G Major, BWV 1007: I. Prélude",
        "Johann Sebastian Bach",
        [
            "strings"
        ],
        [
            "early_morning",
            "morning",
            "afternoon",
            "night"
        ],
        [
            "sunny",
            "clear_breeze",
            "cloudy",
            "rainy"
        ],
        [
            "calm",
            "focused",
            "tired"
        ],
        [
            "focus",
            "calm_down",
            "rest"
        ]
    ],
    [
        "c14",
        "Thaïs: Méditation",
        "Jules Massenet",
        [
            "strings"
        ],
        [
            "sunset",
            "night",
            "late_night"
        ],
        [
            "rainy",
            "drizzle",
            "foggy"
        ],
        [
            "sad",
            "tired",
            "lonely"
        ],
        [
            "comfort",
            "calm_down",
            "rest"
        ]
    ],
    [
        "c15",
        "Caprice No.24 in A Minor, Op.1",
        "Niccolò Paganini",
        [
            "strings"
        ],
        [
            "morning",
            "afternoon"
        ],
        [
            "sunny",
            "windy",
            "stormy"
        ],
        [
            "stressed",
            "frustrated",
            "focused"
        ],
        [
            "energize",
            "confident",
            "excited_up"
        ]
    ],
    [
        "c16",
        "Le Cygne (The Swan) from Carnival of the Animals",
        "Camille Saint-Saëns",
        [
            "strings"
        ],
        [
            "early_morning",
            "sunset",
            "night"
        ],
        [
            "snowy",
            "clear_breeze",
            "drizzle"
        ],
        [
            "calm",
            "drowsy",
            "sad"
        ],
        [
            "calm_down",
            "rest",
            "sleep"
        ]
    ],
    [
        "c17",
        "Clarinet Concerto in A Major, K.622: II. Adagio",
        "Wolfgang Amadeus Mozart",
        [
            "winds"
        ],
        [
            "sunset",
            "night",
            "late_night"
        ],
        [
            "rainy",
            "cloudy",
            "foggy"
        ],
        [
            "tired",
            "calm",
            "lonely"
        ],
        [
            "comfort",
            "calm_down",
            "sleep"
        ]
    ],
    [
        "c18",
        "Prélude à l'après-midi d'un faune",
        "Claude Debussy",
        [
            "winds"
        ],
        [
            "afternoon",
            "sunset"
        ],
        [
            "clear_breeze",
            "partly_cloudy",
            "foggy"
        ],
        [
            "drowsy",
            "calm",
            "focused"
        ],
        [
            "rest",
            "reflective",
            "calm_down"
        ]
    ],
    [
        "c19",
        "Orfeo ed Euridice: Dance of the Blessed Spirits (Flute)",
        "Christoph Willibald Gluck",
        [
            "winds"
        ],
        [
            "early_morning",
            "morning"
        ],
        [
            "clear_breeze",
            "sunny",
            "drizzle"
        ],
        [
            "calm",
            "tired"
        ],
        [
            "calm_down",
            "rest",
            "comfort"
        ]
    ],
    [
        "c20",
        "Horn Concerto No.4 in E-Flat Major, K.495: III. Rondo",
        "Wolfgang Amadeus Mozart",
        [
            "winds"
        ],
        [
            "morning",
            "afternoon"
        ],
        [
            "sunny",
            "clear_breeze",
            "windy"
        ],
        [
            "happy",
            "excited",
            "drowsy"
        ],
        [
            "refresh",
            "energize",
            "excited_up"
        ]
    ],
    [
        "c21",
        "Sonata for Two Pianos and Percussion, Sz.110: I. Assai lento",
        "Béla Bartók",
        [
            "percussion"
        ],
        [
            "afternoon",
            "night"
        ],
        [
            "stormy",
            "windy",
            "cloudy"
        ],
        [
            "focused",
            "stressed",
            "frustrated"
        ],
        [
            "focus",
            "confident",
            "energize"
        ]
    ],
    [
        "c22",
        "Concerto for Marimba and Vibraphone",
        "Darius Milhaud",
        [
            "percussion"
        ],
        [
            "morning",
            "afternoon"
        ],
        [
            "sunny",
            "partly_cloudy"
        ],
        [
            "happy",
            "drowsy",
            "focused"
        ],
        [
            "refresh",
            "energize",
            "focus"
        ]
    ],
    [
        "c23",
        "Symphony No.94 'Surprise': II. Andante (Timpani)",
        "Joseph Haydn",
        [
            "percussion"
        ],
        [
            "morning",
            "afternoon"
        ],
        [
            "sunny",
            "clear_breeze"
        ],
        [
            "drowsy",
            "happy",
            "calm"
        ],
        [
            "refresh",
            "excited_up",
            "energize"
        ]
    ],
    [
        "c24",
        "The Nutcracker: Dance of the Sugar Plum Fairy (Celesta)",
        "Pyotr Ilyich Tchaikovsky",
        [
            "percussion"
        ],
        [
            "night",
            "early_morning"
        ],
        [
            "snowy",
            "foggy"
        ],
        [
            "excited",
            "calm",
            "happy"
        ],
        [
            "refresh",
            "rest",
            "sleep"
        ]
    ],
    [
        "c25",
        "String Quartet No.12 'American': II. Lento",
        "Antonín Dvořák",
        [
            "chamber"
        ],
        [
            "sunset",
            "night"
        ],
        [
            "clear_breeze",
            "rainy",
            "cloudy"
        ],
        [
            "lonely",
            "calm",
            "tired"
        ],
        [
            "comfort",
            "reflective",
            "rest"
        ]
    ],
    [
        "c26",
        "Piano Trio No.2 in E-Flat Major, D.929: II. Andante con moto",
        "Franz Schubert",
        [
            "chamber"
        ],
        [
            "sunset",
            "night",
            "late_night"
        ],
        [
            "rainy",
            "cloudy",
            "foggy"
        ],
        [
            "sad",
            "lonely",
            "focused"
        ],
        [
            "reflective",
            "comfort",
            "focus"
        ]
    ],
    [
        "c27",
        "String Quartet No.14 'Death and the Maiden': II. Andante",
        "Franz Schubert",
        [
            "chamber"
        ],
        [
            "night",
            "late_night"
        ],
        [
            "stormy",
            "rainy",
            "snowy"
        ],
        [
            "sad",
            "stressed",
            "lonely"
        ],
        [
            "reflective",
            "calm_down"
        ]
    ],
    [
        "c28",
        "String Quintet in E Major, Op.11 No.5: III. Minuetto",
        "Luigi Boccherini",
        [
            "chamber"
        ],
        [
            "morning",
            "afternoon"
        ],
        [
            "sunny",
            "clear_breeze",
            "partly_cloudy"
        ],
        [
            "happy",
            "calm",
            "drowsy"
        ],
        [
            "refresh",
            "excited_up",
            "rest"
        ]
    ],
    [
        "c29",
        "Piano Concerto No.21 in C Major, K.467: II. Andante",
        "Wolfgang Amadeus Mozart",
        [
            "concerto"
        ],
        [
            "early_morning",
            "morning",
            "afternoon"
        ],
        [
            "sunny",
            "clear_breeze",
            "partly_cloudy"
        ],
        [
            "calm",
            "happy",
            "focused"
        ],
        [
            "calm_down",
            "focus",
            "rest",
            "comfort"
        ]
    ],
    [
        "c30",
        "Violin Concerto in E Minor, Op.64: I. Allegro molto appassionato",
        "Felix Mendelssohn",
        [
            "concerto"
        ],
        [
            "morning",
            "afternoon",
            "sunset"
        ],
        [
            "windy",
            "clear_breeze",
            "cloudy"
        ],
        [
            "excited",
            "stressed",
            "focused"
        ],
        [
            "energize",
            "confident",
            "reflective"
        ]
    ],
    [
        "c31",
        "Cello Concerto in E Minor, Op.85: I. Adagio - Moderato",
        "Edward Elgar",
        [
            "concerto"
        ],
        [
            "sunset",
            "night",
            "late_night"
        ],
        [
            "rainy",
            "foggy",
            "cloudy",
            "windy"
        ],
        [
            "sad",
            "lonely",
            "tired"
        ],
        [
            "reflective",
            "comfort",
            "calm_down"
        ]
    ],
    [
        "c32",
        "Piano Concerto No.2 in C Minor, Op.18: II. Adagio sostenuto",
        "Sergei Rachmaninoff",
        [
            "concerto"
        ],
        [
            "sunset",
            "night",
            "late_night"
        ],
        [
            "snowy",
            "rainy",
            "cloudy"
        ],
        [
            "sad",
            "lonely",
            "tired"
        ],
        [
            "comfort",
            "reflective",
            "rest"
        ]
    ],
    [
        "c33",
        "Turandot: Nessun dorma",
        "Giacomo Puccini",
        [
            "opera"
        ],
        [
            "sunset",
            "night"
        ],
        [
            "sunny",
            "windy",
            "stormy"
        ],
        [
            "stressed",
            "frustrated",
            "excited"
        ],
        [
            "confident",
            "energize",
            "excited_up"
        ]
    ],
    [
        "c34",
        "La Traviata: Brindisi (Libiamo ne' lieti calici)",
        "Giuseppe Verdi",
        [
            "opera"
        ],
        [
            "afternoon",
            "sunset",
            "night"
        ],
        [
            "sunny",
            "clear_breeze"
        ],
        [
            "happy",
            "excited"
        ],
        [
            "excited_up",
            "refresh",
            "energize"
        ]
    ],
    [
        "c35",
        "Carmen: Habanera",
        "Georges Bizet",
        [
            "opera"
        ],
        [
            "afternoon",
            "sunset"
        ],
        [
            "sunny",
            "windy",
            "partly_cloudy"
        ],
        [
            "excited",
            "stressed",
            "happy"
        ],
        [
            "confident",
            "excited_up",
            "refresh"
        ]
    ],
    [
        "c36",
        "Gianni Schicchi: O mio babbino caro",
        "Giacomo Puccini",
        [
            "opera"
        ],
        [
            "early_morning",
            "sunset",
            "night"
        ],
        [
            "clear_breeze",
            "drizzle",
            "cloudy"
        ],
        [
            "calm",
            "sad",
            "lonely"
        ],
        [
            "comfort",
            "calm_down",
            "rest"
        ]
    ],
    [
        "c37",
        "Morgen!, Op.27 No.4",
        "Richard Strauss",
        [
            "vocal"
        ],
        [
            "early_morning",
            "sunset",
            "night"
        ],
        [
            "clear_breeze",
            "drizzle",
            "cloudy"
        ],
        [
            "calm",
            "tired",
            "lonely"
        ],
        [
            "comfort",
            "calm_down",
            "rest"
        ]
    ],
    [
        "c38",
        "Requiem in D Minor, K.626: Lacrimosa",
        "Wolfgang Amadeus Mozart",
        [
            "vocal"
        ],
        [
            "night",
            "late_night"
        ],
        [
            "stormy",
            "rainy",
            "foggy",
            "cloudy"
        ],
        [
            "sad",
            "lonely",
            "stressed"
        ],
        [
            "reflective",
            "comfort"
        ]
    ],
    [
        "c39",
        "Erlkönig, D.328",
        "Franz Schubert",
        [
            "vocal"
        ],
        [
            "night",
            "afternoon"
        ],
        [
            "stormy",
            "windy",
            "foggy"
        ],
        [
            "stressed",
            "frustrated",
            "focused"
        ],
        [
            "energize",
            "confident",
            "reflective"
        ]
    ],
    [
        "c40",
        "Stabat Mater: Quando corpus morietur",
        "Giovanni Battista Pergolesi",
        [
            "vocal"
        ],
        [
            "early_morning",
            "night",
            "late_night"
        ],
        [
            "rainy",
            "snowy",
            "cloudy"
        ],
        [
            "sad",
            "tired",
            "calm"
        ],
        [
            "calm_down",
            "comfort",
            "sleep"
        ]
    ],
    [
        "c41",
        "The Four Seasons: Spring, Op.8 No.1: I. Allegro",
        "Antonio Vivaldi",
        [
            "baroque"
        ],
        [
            "early_morning",
            "morning",
            "afternoon"
        ],
        [
            "sunny",
            "clear_breeze",
            "partly_cloudy"
        ],
        [
            "happy",
            "excited",
            "drowsy"
        ],
        [
            "energize",
            "refresh",
            "excited_up"
        ]
    ],
    [
        "c42",
        "Goldberg Variations, BWV 988: Aria",
        "Johann Sebastian Bach",
        [
            "baroque"
        ],
        [
            "early_morning",
            "night",
            "late_night"
        ],
        [
            "snowy",
            "drizzle",
            "cloudy",
            "foggy"
        ],
        [
            "calm",
            "tired",
            "focused"
        ],
        [
            "sleep",
            "calm_down",
            "focus",
            "rest"
        ]
    ],
    [
        "c43",
        "Canon and Gigue in D Major",
        "Johann Pachelbel",
        [
            "baroque"
        ],
        [
            "morning",
            "afternoon",
            "sunset"
        ],
        [
            "sunny",
            "clear_breeze",
            "partly_cloudy"
        ],
        [
            "calm",
            "happy",
            "tired"
        ],
        [
            "comfort",
            "calm_down",
            "rest"
        ]
    ],
    [
        "c44",
        "Water Music Suite No.2 in D Major: Alla Hornpipe",
        "George Frideric Handel",
        [
            "baroque"
        ],
        [
            "morning",
            "afternoon"
        ],
        [
            "sunny",
            "windy",
            "clear_breeze"
        ],
        [
            "happy",
            "excited",
            "drowsy"
        ],
        [
            "energize",
            "excited_up",
            "confident"
        ]
    ]
]


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS songs (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            artist TEXT NOT NULL,
            genres TEXT NOT NULL,
            times TEXT NOT NULL,
            weathers TEXT NOT NULL,
            current_moods TEXT NOT NULL,
            target_moods TEXT NOT NULL,
            source TEXT DEFAULT 'seed'
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS saved_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            time_id TEXT NOT NULL,
            time_label TEXT NOT NULL,
            weather_id TEXT NOT NULL,
            weather_label TEXT NOT NULL,
            current_mood_id TEXT NOT NULL,
            current_mood_label TEXT NOT NULL,
            target_mood_id TEXT NOT NULL,
            target_mood_label TEXT NOT NULL,
            genre_label TEXT NOT NULL,
            song_id TEXT NOT NULL,
            title TEXT NOT NULL,
            artist TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS recent_history (
            song_id TEXT PRIMARY KEY,
            shown_at TEXT NOT NULL
        )
        """
    )
    for row in SEED_SONGS:
        cur.execute(
            """
            INSERT OR REPLACE INTO songs
            (id, title, artist, genres, times, weathers, current_moods, target_moods, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'seed')
            """,
            (
                row[0], row[1], row[2],
                json.dumps(row[3], ensure_ascii=False),
                json.dumps(row[4], ensure_ascii=False),
                json.dumps(row[5], ensure_ascii=False),
                json.dumps(row[6], ensure_ascii=False),
                json.dumps(row[7], ensure_ascii=False),
            ),
        )
    conn.commit()
    conn.close()


init_db()


class RecommendRequest(BaseModel):
    timeOfDay: str
    weather: str
    currentMood: str
    targetMood: str
    genre: str = "all"
    excludeIds: List[str] = []
    favArtists: List[str] = []


class SaveRecordRequest(BaseModel):
    date: str
    timeId: str
    timeLabel: str
    weatherId: str
    weatherLabel: str
    currentMoodId: str
    currentMoodLabel: str
    targetMoodId: str
    targetMoodLabel: str
    genreLabel: str = "전체"
    songId: str
    title: str
    artist: str


async def fetch_artist_tags(name: str) -> List[str]:
    try:
        async with httpx.AsyncClient(timeout=2.5, headers={"User-Agent": "TodaysMusicWeb/1.0 (https://github.com/CNchanhoe/Today_music)"}) as client:
            res = await client.get("https://musicbrainz.org/ws/2/artist/", params={"query": name, "limit": 1, "fmt": "json"})
            if res.status_code != 200:
                return []
            artists = res.json().get("artists") or []
            if not artists:
                return []
            tags = sorted(artists[0].get("tags") or [], key=lambda t: t.get("count", 0), reverse=True)
            return [t["name"] for t in tags[:4] if t.get("name")]
    except Exception:
        return []


async def sync_musicbrainz_into_db(genre: str, fav_artists: List[str]) -> int:
    tags = GENRE_TO_MB_TAGS.get(genre, ["pop", "indie", "jazz"]) if genre != "all" else ["pop", "indie", "jazz", "rnb", "classical"]
    queries = []
    if fav_artists and genre != "classical":
        pick_fav = random.choice(fav_artists)
        queries.append((f'artist:"{pick_fav}"', random.randint(0, 20)))
        taste_tags = await fetch_artist_tags(pick_fav)
        if taste_tags:
            queries.append((f'tag:"{random.choice(taste_tags)}"', random.randint(0, 120)))
    if True:
        composers = ["Johann Sebastian Bach", "Antonio Vivaldi", "George Frideric Handel", "Domenico Scarlatti", "Alessandro Scarlatti", "Henry Purcell", "Arcangelo Corelli", "Georg Philipp Telemann", "Jean-Philippe Rameau", "Claudio Monteverdi", "Tomaso Albinoni", "Dieterich Buxtehude", "Johann Pachelbel", "Giovanni Battista Pergolesi", "François Couperin", "Jean-Baptiste Lully", "Giuseppe Tartini", "Alessandro Marcello", "Benedetto Marcello", "Pietro Locatelli", "Sylvius Leopold Weiss", "Heinrich Ignaz Franz Biber", "Wolfgang Amadeus Mozart", "Ludwig van Beethoven", "Joseph Haydn", "Christoph Willibald Gluck", "Muzio Clementi", "Luigi Boccherini", "Carl Philipp Emanuel Bach", "Johann Christian Bach", "Carl Stamitz", "Antonio Salieri", "Johann Nepomuk Hummel", "Carl Czerny", "Friedrich Kuhlau", "Anton Diabelli", "Karl Ditters von Dittersdorf", "Giovanni Battista Viotti", "Louis Spohr", "Frédéric Chopin", "Franz Schubert", "Robert Schumann", "Clara Schumann", "Franz Liszt", "Johannes Brahms", "Felix Mendelssohn", "Fanny Mendelssohn", "Pyotr Ilyich Tchaikovsky", "Sergei Rachmaninoff", "Alexander Scriabin", "Bedřich Smetana", "Antonín Dvořák", "Richard Strauss", "Johann Strauss II", "Johann Strauss I", "Josef Strauss", "Gustav Mahler", "Hector Berlioz", "Georges Bizet", "Camille Saint-Saëns", "Gabriel Fauré", "César Franck", "Edvard Grieg", "Jean Sibelius", "Edward Elgar", "Niccolò Paganini", "Modest Mussorgsky", "Nikolai Rimsky-Korsakov", "Alexander Borodin", "Gioachino Rossini", "Giuseppe Verdi", "Giacomo Puccini", "Richard Wagner", "Anton Bruckner", "Max Bruch", "Pablo de Sarasate", "Henryk Wieniawski", "Isaac Albéniz", "Enrique Granados", "Vincenzo Bellini", "Gaetano Donizetti", "Charles-Valentin Alkan", "Sigismond Thalberg", "Giacomo Meyerbeer", "Charles Gounod", "Jacques Offenbach", "Édouard Lalo", "Ernest Chausson", "Paul Dukas", "Emmanuel Chabrier", "Jules Massenet", "Léo Delibes", "Henri Vieuxtemps", "Joseph Joachim", "Max Reger", "Ferruccio Busoni", "Hugo Wolf", "Alexander Glazunov", "Sergei Lyapunov", "Mily Balakirev", "César Cui", "Vasily Kalinnikov", "Anton Arensky", "Sergei Taneyev", "Anatoly Liadov", "Nikolai Medtner", "Leoš Janáček", "Josef Suk", "Zdeněk Fibich", "Bohuslav Martinů", "Zoltán Kodály", "George Enescu", "Carl Nielsen", "Johan Svendsen", "Hugo Alfvén", "Wilhelm Stenhammar", "Franz Berwald", "Franz Lehár", "Emmerich Kálmán", "Pietro Mascagni", "Ruggero Leoncavallo", "Claude Debussy", "Maurice Ravel", "Erik Satie", "Igor Stravinsky", "Sergei Prokofiev", "Dmitri Shostakovich", "Béla Bartók", "Gustav Holst", "Ralph Vaughan Williams", "Ottorino Respighi", "Manuel de Falla", "Samuel Barber", "Aaron Copland", "William Walton", "Benjamin Britten", "Frank Bridge", "Gerald Finzi", "Arnold Bax", "John Ireland", "Frederick Delius", "Joaquín Rodrigo", "Joaquín Turina", "Francisco Tárrega", "Agustín Barrios", "Fernando Sor", "Mauro Giuliani", "Matteo Carcassi", "Heitor Villa-Lobos", "Alberto Ginastera", "Manuel Ponce", "George Gershwin", "Leonard Bernstein", "Amy Beach", "Edward MacDowell", "Aram Khachaturian"]
        comp = random.choice(composers)
        queries.append((f'artist:"{comp}" AND status:official', random.randint(0, 120)))
    else:
        chosen_tag = random.choice(tags)
        queries.append((f'tag:"{chosen_tag}" AND status:official', random.randint(0, 300)))

    recordings = []
    try:
        async with httpx.AsyncClient(timeout=8.0, headers={"User-Agent": "TodaysMusicWeb/1.0 (https://github.com/CNchanhoe/Today_music)"}) as client:
            for q_str, off in queries:
                res = await client.get("https://musicbrainz.org/ws/2/recording/", params={"query": q_str, "limit": 50, "offset": off, "fmt": "json"})
                if res.status_code == 200:
                    items = res.json().get("recordings", [])
                    if not items and off > 0:
                        res2 = await client.get("https://musicbrainz.org/ws/2/recording/", params={"query": q_str, "limit": 50, "offset": 0, "fmt": "json"})
                        if res2.status_code == 200:
                            items = res2.json().get("recordings", [])
                    if q_str.startswith('artist:"'):
                        last_name = q_str[8:-1].strip().split()[-1].lower()
                        filtered_items = []
                        for it in items:
                            ac = "".join((c.get("name") or (c.get("artist") or {}).get("name") or "") for c in (it.get("artist-credit") or [])).lower()
                            if last_name in ac:
                                filtered_items.append(it)
                        recordings.extend(filtered_items)
                    else:
                        recordings.extend(items)
    except Exception:
        pass
    if not recordings:
        return 0
    data = {"recordings": recordings}

    conn = get_conn()
    cur = conn.cursor()
    added = 0
    for r in data.get("recordings", []):
        title = (r.get("title") or "").strip()
        credits = r.get("artist-credit") or []
        artist = "".join((c.get("name") or (c.get("artist") or {}).get("name") or "") + (c.get("joinphrase") or "") for c in credits).strip()
        if not title or not artist or artist == "[unknown]":
            continue
        if genre == "classical":
            if CLASSICAL_EXCLUDE_RE.search(f"{title} {artist}"):
                continue
            r_tags = [(t.get("name") or "").lower() for t in (r.get("tags") or [])]
            if any(re.search(r"rock|pop|metal|jazz|hip hop|electronic|soundtrack|new age|ambient|punk|indie|folk|rnb|soul", rt) for rt in r_tags):
                continue
        mb_id = f"mb_{r['id']}"
        genres = [genre] if genre != "all" else [chosen_tag]
        cur.execute(
            """
            INSERT OR IGNORE INTO songs
            (id, title, artist, genres, times, weathers, current_moods, target_moods, source)
            VALUES (?, ?, ?, ?, '[]', '[]', '[]', '[]', 'musicbrainz')
            """,
            (mb_id, title, artist, json.dumps(genres, ensure_ascii=False)),
        )
        if cur.rowcount > 0:
            added += 1
    conn.commit()
    conn.close()
    return added


@app.post("/api/recommend")
async def recommend(req: RecommendRequest):
    await sync_musicbrainz_into_db(req.genre, req.favArtists)

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT song_id FROM recent_history ORDER BY shown_at DESC LIMIT 100")
    recent_ids = {r["song_id"] for r in cur.fetchall()}

    cur.execute("SELECT * FROM songs")
    rows = cur.fetchall()

    candidates = []
    for r in rows:
        genres = json.loads(r["genres"])
        if req.genre != "all" and req.genre not in genres:
            continue
        if True:
            if CLASSICAL_EXCLUDE_RE.search(f"{r['title']} {r['artist']}"):
                continue
            if not CLASSICAL_COMPOSER_WHITELIST_RE.search(r['artist']):
                continue
        score = 0.0
        if req.timeOfDay in json.loads(r["times"]):
            score += 2.5
        if req.weather in json.loads(r["weathers"]):
            score += 2.5
        if req.currentMood in json.loads(r["current_moods"]):
            score += 2.5
        if req.targetMood in json.loads(r["target_moods"]):
            score += 3.5
        if r["source"] == "musicbrainz":
            score += 12.0
        if req.favArtists:
            hay = f"{r['artist']} {r['title']}".lower()
            if any(f.lower() in hay for f in req.favArtists):
                score += 4.0

        penalty = 0.0
        if r["id"] in req.excludeIds:
            penalty -= 200.0
        elif r["id"] in recent_ids:
            penalty -= 180.0

        total = score + penalty + random.uniform(0.0, 4.5)
        candidates.append((total, {"id": r["id"], "title": r["title"], "artist": r["artist"]}))

    unseen = [c for c in candidates if c[1]["id"] not in req.excludeIds and c[1]["id"] not in recent_ids]
    active_candidates = unseen if len(unseen) >= 4 else candidates
    active_candidates.sort(key=lambda x: x[0], reverse=True)
    top_pool = [c[1] for c in active_candidates[:25]]
    random.shuffle(top_pool)
    picked = []
    seen_artists = set()
    for c in top_pool:
        ak = c["artist"].lower()
        if ak in seen_artists:
            continue
        seen_artists.add(ak)
        picked.append(c)
        if len(picked) >= 4:
            break

    now = datetime.utcnow().isoformat()
    for p in picked:
        cur.execute("INSERT OR REPLACE INTO recent_history (song_id, shown_at) VALUES (?, ?)", (p["id"], now))
    conn.commit()
    conn.close()
    return {"tracks": picked}


@app.get("/api/saved")
def list_saved():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM saved_records ORDER BY id DESC").fetchall()
    conn.close()
    return {"records": [dict(r) for r in rows]}


@app.post("/api/saved")
def add_saved(req: SaveRecordRequest):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO saved_records
        (date, time_id, time_label, weather_id, weather_label, current_mood_id, current_mood_label, target_mood_id, target_mood_label, genre_label, song_id, title, artist)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            req.date, req.timeId, req.timeLabel, req.weatherId, req.weatherLabel,
            req.currentMoodId, req.currentMoodLabel, req.targetMoodId, req.targetMoodLabel,
            req.genreLabel, req.songId, req.title, req.artist,
        ),
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return {"id": new_id}


@app.delete("/api/saved/{record_id}")
def delete_saved(record_id: int):
    conn = get_conn()
    conn.execute("DELETE FROM saved_records WHERE id = ?", (record_id,))
    conn.commit()
    conn.close()
    return {"ok": True}


@app.delete("/api/saved")
def clear_saved():
    conn = get_conn()
    conn.execute("DELETE FROM saved_records")
    conn.commit()
    conn.close()
    return {"ok": True}


@app.get("/")
def serve_frontend():
    if not FRONTEND_PATH.exists():
        raise HTTPException(status_code=404, detail="Frontend not found")
    return FileResponse(FRONTEND_PATH)
