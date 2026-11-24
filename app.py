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
