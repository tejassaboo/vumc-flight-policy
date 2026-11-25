"""The simulated flight world of the original-handbook template, shared byte for byte by the tools
(src/plugin/world.py) and the verifier (verifier/world.py).

Real airports (approximate coordinates, standard-time UTC offsets all year) and real airline names with
their main hubs; every flight, time and fare is synthetic. A search on a route and local date returns:

- the scenario's pinned offers, when the search is the scenario's own route and travel date: flights the
  scenario describes (carrier, hubs flown through, local departure time, and optionally exact scheduled
  minutes and layovers) with the exact fares and seat availability its expected answer depends on; and
- background offers from a SHA-256 stream keyed by the scenario, route and date: the airlines whose hubs
  plausibly serve the route, distance-based times and fares, priced above every pinned fare of their cabin
  band by a wide margin so they never change a pinned answer.

The same search gives the same offers on every machine. Offer ids are hashes of the scenario, route, date
and offer slot, so they say nothing about price, cabin or the answer. It imports only modules a verifier
may use and contract.
"""

import hashlib
import itertools
import math
from functools import cache

from contract import Airport, Cabin, Offer, Segment, TripType

NOTE = "Simulated schedules and fares: real airports and airline names, synthetic flights and prices."
NO_ROUND_TRIP = "No round-trip fares are listed for this case."
NO_OFFERS = "No fares are listed for this route and date in this case."
STREAM = "handbook-world-v1"
CABIN_RANK = {Cabin.ECONOMY: 1, Cabin.PREMIUM_ECONOMY: 2, Cabin.BUSINESS: 3, Cabin.FIRST: 4}

# (IATA code, name, city, ISO country, latitude, longitude, standard-time UTC offset in minutes)
AIRPORTS = (
    ("ATL", "Hartsfield-Jackson Atlanta International Airport", "Atlanta", "US", 33.6367, -84.4281, -300),
    ("BOS", "Boston Logan International Airport", "Boston", "US", 42.3656, -71.0096, -300),
    ("ORD", "Chicago O'Hare International Airport", "Chicago", "US", 41.9786, -87.9048, -360),
    ("DFW", "Dallas Fort Worth International Airport", "Dallas-Fort Worth", "US", 32.8968, -97.0380, -360),
    ("DEN", "Denver International Airport", "Denver", "US", 39.8561, -104.6737, -420),
    ("JFK", "John F. Kennedy International Airport", "New York", "US", 40.6413, -73.7781, -300),
    ("EWR", "Newark Liberty International Airport", "Newark", "US", 40.6895, -74.1745, -300),
    ("LGA", "LaGuardia Airport", "New York", "US", 40.7769, -73.8740, -300),
    ("IAD", "Washington Dulles International Airport", "Dulles", "US", 38.9531, -77.4565, -300),
    ("DCA", "Ronald Reagan Washington National Airport", "Washington", "US", 38.8512, -77.0402, -300),
    ("PHL", "Philadelphia International Airport", "Philadelphia", "US", 39.8744, -75.2424, -300),
    ("CLT", "Charlotte Douglas International Airport", "Charlotte", "US", 35.2140, -80.9431, -300),
    ("MIA", "Miami International Airport", "Miami", "US", 25.7959, -80.2870, -300),
    ("MCO", "Orlando International Airport", "Orlando", "US", 28.4312, -81.3081, -300),
    ("IAH", "George Bush Intercontinental Airport", "Houston", "US", 29.9902, -95.3368, -360),
    ("AUS", "Austin-Bergstrom International Airport", "Austin", "US", 30.1975, -97.6664, -360),
    ("MSY", "Louis Armstrong New Orleans International Airport", "New Orleans", "US", 29.9934, -90.2580, -360),
    ("BTR", "Baton Rouge Metropolitan Airport", "Baton Rouge", "US", 30.5332, -91.1496, -360),
    ("SHV", "Shreveport Regional Airport", "Shreveport", "US", 32.4466, -93.8256, -360),
    ("AEX", "Alexandria International Airport", "Alexandria", "US", 31.3274, -92.5486, -360),
    ("MSP", "Minneapolis-Saint Paul International Airport", "Minneapolis", "US", 44.8848, -93.2223, -360),
    ("DTW", "Detroit Metropolitan Wayne County Airport", "Detroit", "US", 42.2162, -83.3554, -300),
    ("PHX", "Phoenix Sky Harbor International Airport", "Phoenix", "US", 33.4342, -112.0116, -420),
    ("SLC", "Salt Lake City International Airport", "Salt Lake City", "US", 40.7899, -111.9791, -420),
    ("LAS", "Harry Reid International Airport", "Las Vegas", "US", 36.0840, -115.1537, -480),
    ("LAX", "Los Angeles International Airport", "Los Angeles", "US", 33.9416, -118.4085, -480),
    ("SFO", "San Francisco International Airport", "San Francisco", "US", 37.6213, -122.3790, -480),
    ("SEA", "Seattle-Tacoma International Airport", "Seattle", "US", 47.4502, -122.3088, -480),
    ("SAN", "San Diego International Airport", "San Diego", "US", 32.7338, -117.1933, -480),
    ("PDX", "Portland International Airport", "Portland", "US", 45.5898, -122.5951, -480),
    ("HNL", "Daniel K. Inouye International Airport", "Honolulu", "US", 21.3187, -157.9225, -600),
    ("ANC", "Ted Stevens Anchorage International Airport", "Anchorage", "US", 61.1743, -149.9963, -540),
    ("SJU", "Luis Munoz Marin International Airport", "San Juan", "PR", 18.4394, -66.0018, -240),
    ("GUM", "Antonio B. Won Pat International Airport", "Hagatna", "GU", 13.4834, 144.7960, 600),
    ("YYZ", "Toronto Pearson International Airport", "Toronto", "CA", 43.6777, -79.6248, -300),
    ("YOW", "Ottawa Macdonald-Cartier International Airport", "Ottawa", "CA", 45.3225, -75.6692, -300),
    ("YUL", "Montreal-Trudeau International Airport", "Montreal", "CA", 45.4706, -73.7408, -300),
    ("YQB", "Quebec City Jean Lesage International Airport", "Quebec City", "CA", 46.7911, -71.3933, -300),
    ("YHZ", "Halifax Stanfield International Airport", "Halifax", "CA", 44.8808, -63.5086, -240),
    ("YYT", "St. John's International Airport", "St. John's", "CA", 47.6186, -52.7519, -210),
    ("YWG", "Winnipeg James Armstrong Richardson International Airport", "Winnipeg", "CA", 49.9100, -97.2399, -360),
    ("YQR", "Regina International Airport", "Regina", "CA", 50.4319, -104.6658, -360),
    ("YXE", "Saskatoon John G. Diefenbaker International Airport", "Saskatoon", "CA", 52.1708, -106.6997, -360),
    ("YEG", "Edmonton International Airport", "Edmonton", "CA", 53.3097, -113.5800, -420),
    ("YYC", "Calgary International Airport", "Calgary", "CA", 51.1215, -114.0076, -420),
    ("YVR", "Vancouver International Airport", "Vancouver", "CA", 49.1967, -123.1815, -480),
    ("YYJ", "Victoria International Airport", "Victoria", "CA", 48.6469, -123.4258, -480),
    ("YXY", "Erik Nielsen Whitehorse International Airport", "Whitehorse", "CA", 60.7096, -135.0670, -420),
    ("YZF", "Yellowknife Airport", "Yellowknife", "CA", 62.4628, -114.4403, -420),
    ("YFB", "Iqaluit Airport", "Iqaluit", "CA", 63.7564, -68.5558, -300),
    ("LHR", "London Heathrow Airport", "London", "GB", 51.4700, -0.4543, 0),
    ("LGW", "London Gatwick Airport", "London", "GB", 51.1537, -0.1821, 0),
    ("EDI", "Edinburgh Airport", "Edinburgh", "GB", 55.9508, -3.3615, 0),
    ("DUB", "Dublin Airport", "Dublin", "IE", 53.4264, -6.2499, 0),
    ("CDG", "Paris Charles de Gaulle Airport", "Paris", "FR", 49.0097, 2.5479, 60),
    ("AMS", "Amsterdam Airport Schiphol", "Amsterdam", "NL", 52.3105, 4.7683, 60),
    ("FRA", "Frankfurt Airport", "Frankfurt", "DE", 50.0379, 8.5622, 60),
    ("MUC", "Munich Airport", "Munich", "DE", 48.3537, 11.7750, 60),
    ("ZRH", "Zurich Airport", "Zurich", "CH", 47.4582, 8.5555, 60),
    ("MAD", "Adolfo Suarez Madrid-Barajas Airport", "Madrid", "ES", 40.4983, -3.5676, 60),
    ("BCN", "Josep Tarradellas Barcelona-El Prat Airport", "Barcelona", "ES", 41.2974, 2.0833, 60),
    ("FCO", "Rome Fiumicino Airport", "Rome", "IT", 41.8003, 12.2389, 60),
    ("CPH", "Copenhagen Airport", "Copenhagen", "DK", 55.6180, 12.6508, 60),
    ("IST", "Istanbul Airport", "Istanbul", "TR", 41.2753, 28.7519, 180),
    ("DXB", "Dubai International Airport", "Dubai", "AE", 25.2532, 55.3657, 240),
    ("AUH", "Zayed International Airport", "Abu Dhabi", "AE", 24.4330, 54.6511, 240),
    ("DOH", "Hamad International Airport", "Doha", "QA", 25.2731, 51.6081, 180),
    ("BOM", "Chhatrapati Shivaji Maharaj International Airport", "Mumbai", "IN", 19.0896, 72.8656, 330),
    ("DEL", "Indira Gandhi International Airport", "Delhi", "IN", 28.5562, 77.1000, 330),
    ("SIN", "Singapore Changi Airport", "Singapore", "SG", 1.3644, 103.9915, 480),
    ("HKG", "Hong Kong International Airport", "Hong Kong", "HK", 22.3080, 113.9185, 480),
    ("PVG", "Shanghai Pudong International Airport", "Shanghai", "CN", 31.1443, 121.8083, 480),
    ("PEK", "Beijing Capital International Airport", "Beijing", "CN", 40.0799, 116.6031, 480),
    ("ICN", "Incheon International Airport", "Seoul", "KR", 37.4602, 126.4407, 540),
    ("HND", "Tokyo Haneda Airport", "Tokyo", "JP", 35.5494, 139.7798, 540),
    ("NRT", "Narita International Airport", "Tokyo", "JP", 35.7720, 140.3929, 540),
    ("SYD", "Sydney Kingsford Smith Airport", "Sydney", "AU", -33.9399, 151.1753, 600),
    ("MEL", "Melbourne Airport", "Melbourne", "AU", -37.6690, 144.8410, 600),
    ("AKL", "Auckland Airport", "Auckland", "NZ", -37.0082, 174.7850, 720),
    ("MEX", "Mexico City International Airport", "Mexico City", "MX", 19.4361, -99.0719, -360),
    ("GRU", "Sao Paulo/Guarulhos International Airport", "Sao Paulo", "BR", -23.4356, -46.4731, -180),
    ("BOG", "El Dorado International Airport", "Bogota", "CO", 4.7016, -74.1469, -300),
    ("SCL", "Arturo Merino Benitez International Airport", "Santiago", "CL", -33.3930, -70.7858, -240),
    ("JNB", "O. R. Tambo International Airport", "Johannesburg", "ZA", -26.1392, 28.2460, 120),
    ("CAI", "Cairo International Airport", "Cairo", "EG", 30.1219, 31.4056, 120),
    ("NBO", "Jomo Kenyatta International Airport", "Nairobi", "KE", -1.3192, 36.9278, 180),
)

# (IATA code, name, hubs among AIRPORTS, longest nonstop in km, shortest route in km on which a business
# cabin is sold, or None). Names are for realism only; nothing here is real schedule or fare data.
AIRLINES = (
    ("AA", "American Airlines", ("DFW", "CLT", "ORD", "MIA", "PHL", "PHX", "JFK", "LAX", "DCA", "LGA"), 14000, 2500),
    ("DL", "Delta Air Lines", ("ATL", "DTW", "MSP", "SLC", "JFK", "LAX", "SEA", "BOS", "LGA"), 14000, 2500),
    ("UA", "United Airlines", ("ORD", "DEN", "IAH", "EWR", "SFO", "IAD", "LAX"), 14500, 2500),
    ("AS", "Alaska Airlines", ("SEA", "ANC", "SFO", "LAX", "SAN", "PDX", "HNL"), 5500, None),
    ("B6", "JetBlue", ("JFK", "BOS", "MCO"), 5800, 3500),
    ("WN", "Southwest Airlines", ("LAS", "DEN", "PHX", "AUS", "MCO"), 4400, None),
    ("AC", "Air Canada", ("YYZ", "YUL", "YVR", "YYC"), 14000, 1500),
    ("WS", "WestJet", ("YYC", "YVR", "YYZ", "YEG"), 7500, 2500),
    ("BA", "British Airways", ("LHR", "LGW"), 14000, 1500),
    ("VS", "Virgin Atlantic", ("LHR",), 12000, 5000),
    ("AF", "Air France", ("CDG",), 14000, 1500),
    ("KL", "KLM", ("AMS",), 14000, 1500),
    ("LH", "Lufthansa", ("FRA", "MUC"), 14000, 1500),
    ("LX", "Swiss", ("ZRH",), 14000, 1500),
    ("IB", "Iberia", ("MAD",), 12000, 1500),
    ("EI", "Aer Lingus", ("DUB",), 8000, 4000),
    ("TK", "Turkish Airlines", ("IST",), 14000, 1500),
    ("EK", "Emirates", ("DXB",), 15500, 1500),
    ("QR", "Qatar Airways", ("DOH",), 15500, 1500),
    ("EY", "Etihad Airways", ("AUH",), 14000, 1500),
    ("AI", "Air India", ("DEL", "BOM"), 14000, 1500),
    ("SQ", "Singapore Airlines", ("SIN",), 16000, 1500),
    ("CX", "Cathay Pacific", ("HKG",), 15000, 1500),
    ("MU", "China Eastern Airlines", ("PVG",), 13000, 1500),
    ("CA", "Air China", ("PEK",), 13000, 1500),
    ("KE", "Korean Air", ("ICN",), 13000, 1500),
    ("NH", "All Nippon Airways", ("HND", "NRT"), 14000, 1500),
    ("JL", "Japan Airlines", ("HND", "NRT"), 14000, 1500),
    ("QF", "Qantas", ("SYD", "MEL"), 15000, 1500),
    ("NZ", "Air New Zealand", ("AKL",), 14000, 2000),
    ("AM", "Aeromexico", ("MEX",), 12000, 1500),
    ("LA", "LATAM Airlines", ("GRU", "SCL"), 12000, 1500),
    ("AV", "Avianca", ("BOG",), 9000, 1500),
    ("SA", "South African Airways", ("JNB",), 12000, 1500),
    ("MS", "EgyptAir", ("CAI",), 11000, 1500),
    ("KQ", "Kenya Airways", ("NBO",), 13000, 1500),
)

EARTH_RADIUS_KM = 6371.0
BLOCK_KMH = 840  # scheduled minutes = TAXI_MINUTES + distance at this speed, rounded to 5 minutes
TAXI_MINUTES = 30
FIRST_DEPARTURE, LAST_DEPARTURE = 6 * 60, 22 * 60  # background flights leave 06:00-21:55 local time
MIN_LAYOVER, MAX_LAYOVER = 55, 150
SHORTEST_LEG_KM = 250
DETOUR = 1.35  # a background connection flies at most this times the direct distance
BACKGROUND = 3  # background itineraries per search when neither the scenario nor handbook.json sets a number
LONGEST_BOOKING_DAYS = 330  # how far ahead of the booking date a search may look

# ----- calendar: whole days since 1970-01-01 (no datetime: a verifier may not import it) -----


def day_number(text):
    """Days since 1970-01-01 of a YYYY-MM-DD date; raises ValueError on anything else."""
    if not isinstance(text, str) or len(text) != 10 or text[4] != "-" or text[7] != "-":
        raise ValueError(f"not a YYYY-MM-DD date: {text!r}")
    try:
        year, month, day = int(text[:4]), int(text[5:7]), int(text[8:])
    except ValueError:
        raise ValueError(f"not a YYYY-MM-DD date: {text!r}") from None
    if not 1 <= month <= 12 or not 1 <= day <= month_length(year, month) or year < 1970:
        raise ValueError(f"no such date: {text!r}")
    y = year - (month <= 2)
    era = y // 400
    yoe = y - era * 400
    doy = (153 * (month + (-3 if month > 2 else 9)) + 2) // 5 + day - 1
    doe = yoe * 365 + yoe // 4 - yoe // 100 + doy
    return era * 146097 + doe - 719468


def month_length(year, month):
    if month == 2:
        return 29 if (year % 4 == 0 and year % 100 != 0) or year % 400 == 0 else 28
    return 30 if month in (4, 6, 9, 11) else 31


def date_of(day):
    """The YYYY-MM-DD date of a day number."""
    z = day + 719468
    era = z // 146097
    doe = z - era * 146097
    yoe = (doe - doe // 1460 + doe // 36524 - doe // 146096) // 365
    doy = doe - (365 * yoe + yoe // 4 - yoe // 100)
    mp = (5 * doy + 2) // 153
    d = doy - (153 * mp + 2) // 5 + 1
    m = mp + (3 if mp < 10 else -9)
    y = yoe + era * 400 + (m <= 2)
    return f"{y:04d}-{m:02d}-{d:02d}"


def days_between(earlier, later):
    """Calendar days from one YYYY-MM-DD date to another (negative when ``later`` is earlier)."""
    return day_number(later) - day_number(earlier)


def clock_minutes(text):
    """Minutes after midnight of an HH:MM time."""
    if not isinstance(text, str) or len(text) != 5 or text[2] != ":":
        raise ValueError(f"not an HH:MM time: {text!r}")
    hours, minutes = int(text[:2]), int(text[3:])
    if not 0 <= hours <= 23 or not 0 <= minutes <= 59:
        raise ValueError(f"no such time: {text!r}")
    return hours * 60 + minutes


def minute_text(minute):
    """YYYY-MM-DD HH:MM of a minute number (minutes since 1970-01-01 00:00)."""
    return f"{date_of(minute // 1440)} {minute % 1440 // 60:02d}:{minute % 60:02d}"


# ----- the deterministic stream -----


class Rng:
    """Pseudo-random numbers from SHA-256: the same on every machine and Python version."""

    def __init__(self, label):
        self.prefix = f"{STREAM}:{label}:"
        self.count = 0

    def bits(self):
        digest = hashlib.sha256(f"{self.prefix}{self.count}".encode()).digest()
        self.count += 1
        return int.from_bytes(digest[:8], "big")

    def randint(self, low, high):
        if high < low:
            raise ValueError(f"empty range {low}..{high}")
        return low + self.bits() % (high - low + 1)

    def shuffled(self, items):
        items = list(items)
        for index in range(len(items) - 1, 0, -1):
            other = self.randint(0, index)
            items[index], items[other] = items[other], items[index]
        return items


# ----- airports and airlines -----


@cache
def airport_table():
    return {row[0]: row for row in AIRPORTS}


@cache
def airline_table():
    return {row[0]: row for row in AIRLINES}


def is_airport(code):
    return code in airport_table()


def airport(code):
    row = airport_table().get(code)
    if row is None:
        raise ValueError(f"unknown airport {code!r}")
    return Airport(code=row[0], name=row[1], city=row[2], country=row[3])


def airline(code):
    row = airline_table().get(code)
    if row is None:
        raise ValueError(f"unknown airline {code!r}")
    return row


def utc_offset(code):
    return airport_table()[code][6]


@cache
def distance_km(origin, destination):
    """Great-circle distance between two airports, in whole km."""
    a, b = airport_table()[origin], airport_table()[destination]
    lat1, lon1, lat2, lon2 = (math.radians(value) for value in (a[4], a[5], b[4], b[5]))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return round(2 * EARTH_RADIUS_KM * math.asin(math.sqrt(h)))


def block_minutes(origin, destination):
    """A nonstop's scheduled minutes: taxi time plus the distance at block speed, to the nearest 5."""
    raw = TAXI_MINUTES + distance_km(origin, destination) * 60 / BLOCK_KMH
    return 5 * round(raw / 5)


def fare_model(km):
    """A one-way economy fare in cents for a trip of ``km``: $50 plus a concave per-distance part."""
    return 5_000 + round(30 * km**0.85)


def flight_number(carrier, origin, destination, depart_utc):
    digest = hashlib.sha256(f"{STREAM}:flight:{carrier}:{origin}:{destination}:{depart_utc % 1440}".encode()).digest()
    return f"{carrier} {10 + int.from_bytes(digest[:4], 'big') % 2990}"


def offer_id(scenario_id, origin, destination, date, return_date, slot):
    """An id that is a hash of the scenario, search and slot: it reveals nothing about the offer."""
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    key = f"{STREAM}:offer:{scenario_id}:{origin}:{destination}:{date}:{return_date}:{slot}"
    digest = hashlib.sha256(key.encode()).digest()
    number = int.from_bytes(digest[:8], "big")
    text = ""
    for _ in range(8):
        text += alphabet[number % 32]
        number //= 32
    return f"{text[:4]}-{text[4:]}"


def plausible_path(carrier, path):
    """Whether ``carrier`` plausibly flies ``path``: every leg touches one of its hubs, and every leg is
    within its range and long enough to fly."""
    row = airline(carrier)
    for a, b in itertools.pairwise(path):
        if a not in row[2] and b not in row[2]:
            return False
        km = distance_km(a, b)
        if not SHORTEST_LEG_KM <= km <= row[3]:
            return False
    return True


# ----- building offers -----
#
# A scenario's "world" (see TEMPLATE_GUIDE.md) holds "searches": each names a route and local date (and a
# return date for a round trip), its pinned "flights" and "offers", and optionally its own "background"
# count. A pinned flight is {"carrier", "depart" (HH:MM local), optional "via" (hub codes), "minutes"
# (exact scheduled minutes per flight), "layovers" (ground minutes per connection), "stopovers" (true per
# connection that is a ticketed stopover with a booked hotel night), and for a round trip "return" with the
# same keys for the flights back}. A pinned offer is {"slot", "flight", "cabin", "fare_cents", optional
# "seats" (default true) and "refundable" (default false)}.


def build_segments(carrier, path, date, depart, minutes, layovers, seed):
    """The flights of an itinerary leaving ``path[0]`` at local time ``depart`` (HH:MM) on local date
    ``date``; ``minutes`` and ``layovers`` give exact scheduled minutes per flight and ground minutes per
    connection, or None for the distance model and the seeded stream."""
    legs = list(itertools.pairwise(path))
    if minutes is None:
        minutes = [block_minutes(a, b) for a, b in legs]
    if layovers is None:
        rng = Rng(f"layover:{seed}")
        layovers = [rng.randint(MIN_LAYOVER // 5, MAX_LAYOVER // 5) * 5 for _ in legs[1:]]
    if len(minutes) != len(legs) or len(layovers) != len(legs) - 1:
        raise ValueError(f"{carrier} {'-'.join(path)}: one scheduled time per flight and one layover per connection")
    if any(type(value) is not int or value <= 0 for value in [*minutes, *layovers]):
        raise ValueError(f"{carrier} {'-'.join(path)}: scheduled minutes and layovers are positive whole minutes")
    start = day_number(date) * 1440 + clock_minutes(depart) - utc_offset(path[0])
    segments = []
    for index, (a, b) in enumerate(legs):
        end = start + minutes[index]
        segments.append(Segment(
            flight_number=flight_number(carrier, a, b, start),
            origin=a,
            destination=b,
            depart_local=minute_text(start + utc_offset(a)),
            arrive_local=minute_text(end + utc_offset(b)),
            depart_utc=minute_text(start),
            arrive_utc=minute_text(end),
            scheduled_minutes=minutes[index],
        ))
        if index < len(layovers):
            start = end + layovers[index]
    return segments, [*layovers]


def utc_minute(text):
    return day_number(text[:10]) * 1440 + clock_minutes(text[11:])


def leg(carrier, path, date, spec, seed):
    """(segments, layovers, stopovers) of one direction of a pinned or background itinerary."""
    if not plausible_path(carrier, path):
        raise ValueError(f"{seed}: {carrier} {'-'.join(path)} is not plausible (every flight touches a hub)")
    segments, layovers = build_segments(carrier, path, date, spec["depart"], spec.get("minutes"),
                                        spec.get("layovers"), seed)
    stopovers = spec.get("stopovers", [False] * len(layovers))
    if len(stopovers) != len(layovers) or any(type(value) is not bool for value in stopovers):
        raise ValueError(f"{seed}: one true or false stopover per connection")
    return segments, layovers, [*stopovers]


def elapsed(segments):
    return utc_minute(segments[-1].arrive_utc) - utc_minute(segments[0].depart_utc) if segments else 0


def make_offer(identifier, carrier, cabin, fare, seats, refundable, out, back):
    """An Offer from its outbound (segments, layovers, stopovers) and, for a round trip, its return."""
    segments, layovers, stopovers = out
    back_segments, back_layovers, back_stopovers = back if back is not None else ([], [], [])
    return Offer(
        offer_id=identifier,
        carrier=airline(carrier)[1],
        trip_type=TripType.ROUND_TRIP if back is not None else TripType.ONE_WAY,
        cabin=cabin,
        fare_cents=fare,
        seats_available=seats,
        refundable=refundable,
        stops=len(segments) - 1,
        segments=[*segments],
        layover_minutes=[*layovers],
        stopover_nights=[*stopovers],
        flying_minutes=sum(segment.scheduled_minutes for segment in segments),
        elapsed_minutes=elapsed(segments),
        return_segments=[*back_segments],
        return_layover_minutes=[*back_layovers],
        return_stopover_nights=[*back_stopovers],
        return_flying_minutes=sum(segment.scheduled_minutes for segment in back_segments),
        return_elapsed_minutes=elapsed(back_segments),
    )


def search_key(search_spec):
    return (search_spec["origin"], search_spec["destination"], search_spec["date"], search_spec.get("return_date", ""))


def pinned_offers(scenario_id, search_spec):
    """The offers a scenario pins on one of its searches, as (slot, Offer)."""
    origin, destination, date, back_date = search_key(search_spec)
    flights = {}
    for name, spec in search_spec["flights"].items():
        seed = f"{scenario_id}:{name}"
        path = [origin, *spec.get("via", []), destination]
        out = leg(spec["carrier"], path, date, spec, seed)
        back = None
        if back_date:
            if "return" not in spec:
                raise ValueError(f"{seed}: a round-trip search needs a return for every flight")
            back_spec = spec["return"]
            back = leg(spec["carrier"], [destination, *back_spec.get("via", []), origin], back_date, back_spec,
                       f"{seed}:return")
        elif "return" in spec:
            raise ValueError(f"{seed}: a return on a one-way search")
        flights[name] = (spec["carrier"], out, back)
    made = []
    for spec in search_spec["offers"]:
        carrier, out, back = flights[spec["flight"]]
        fare = spec["fare_cents"]
        if type(fare) is not int or fare <= 0:
            raise ValueError(f"{scenario_id}: offer {spec['slot']} needs a positive whole fare in cents")
        identifier = offer_id(scenario_id, origin, destination, date, back_date, spec["slot"])
        made.append((spec["slot"], make_offer(identifier, carrier, Cabin(spec["cabin"]), fare, spec.get("seats", True),
                                              spec.get("refundable", False), out, back)))
    return made


@cache
def background_itineraries(origin, destination):
    """(airline, path) an airline plausibly sells: a nonstop touching its hub, and connections through
    its hubs that add little distance."""
    direct = distance_km(origin, destination)
    found = []
    for row in AIRLINES:
        code, hubs = row[0], row[2]
        if plausible_path(code, (origin, destination)):
            found.append((code, (origin, destination)))
        if direct < 600:
            continue
        via = [
            hub for hub in hubs
            if hub not in (origin, destination) and plausible_path(code, (origin, hub, destination))
            and distance_km(origin, hub) + distance_km(hub, destination) <= DETOUR * direct
        ]
        via.sort(key=lambda hub: (distance_km(origin, hub) + distance_km(hub, destination), hub))
        found.extend((code, (origin, hub, destination)) for hub in via[:1])
    return tuple(found)


def floors(pinned):
    """The lowest background fare by cabin band: far above every pinned fare of that band and below, so a
    background offer is never the cheapest, never within any handbook's fare window of a pinned fare, and
    never the cheapest offer of its cabin."""
    if not pinned:
        return 0, 0
    economy = [offer.fare_cents for offer in pinned if CABIN_RANK[offer.cabin] <= 2]
    premium = [offer.fare_cents for offer in pinned if CABIN_RANK[offer.cabin] >= 3]
    top = max(economy or [offer.fare_cents for offer in pinned])
    economy_floor = top * 160 // 100 + 25_000
    business_floor = max(max(premium or [0]) * 140 // 100 + 25_000, economy_floor * 2)
    return economy_floor, business_floor


def departure_text(rng):
    minute = rng.randint(FIRST_DEPARTURE // 5, (LAST_DEPARTURE - 5) // 5) * 5
    return f"{minute // 60:02d}:{minute % 60:02d}"


def background_offers(scenario_id, key, count, pinned):
    """``count`` seeded itineraries on the search, each sold in economy and, where the airline sells one on
    a route this long, in business: as (slot, Offer). Always non-refundable, always with seats."""
    origin, destination, date, back_date = key
    rng = Rng(f"background:{scenario_id}:{origin}:{destination}:{date}:{back_date}")
    options = rng.shuffled(background_itineraries(origin, destination))[:count]
    economy_floor, business_floor = floors(pinned)
    km = distance_km(origin, destination)
    trips = 2 if back_date else 1
    made = []
    for index, (code, path) in enumerate(options):
        seed = f"{scenario_id}:{origin}:{destination}:{date}:{back_date}:{index}"
        out = leg(code, list(path), date, {"depart": departure_text(rng)}, seed)
        back = leg(code, list(reversed(path)), back_date, {"depart": departure_text(rng)}, f"{seed}:return") if back_date else None
        economy = max(trips * fare_model(km) * rng.randint(85, 135) // 100, economy_floor) * rng.randint(100, 118) // 100
        if len(path) == 3:
            economy = max(economy * rng.randint(85, 97) // 100, economy_floor)
        slot = f"background-{index}-economy"
        made.append((slot, make_offer(offer_id(scenario_id, origin, destination, date, back_date, slot), code,
                                      Cabin.ECONOMY, economy, True, False, out, back)))
        business_from = airline(code)[4]
        if business_from is not None and km >= business_from:
            business = max(economy * rng.randint(260, 380) // 100, business_floor)
            slot = f"background-{index}-business"
            made.append((slot, make_offer(offer_id(scenario_id, origin, destination, date, back_date, slot), code,
                                          Cabin.BUSINESS, business, True, False, out, back)))
    return made


def ordered(offers):
    return sorted(offers, key=lambda item: (item[1].segments[0].depart_utc, CABIN_RANK[item[1].cabin],
                                            item[1].fare_cents, item[1].offer_id))


def default_background(scenario):
    world = scenario["world"]
    return world.get("background", world.get("handbook_background", BACKGROUND))


def search_slots(scenario, origin, destination, date, return_date=""):
    """Every (slot, Offer) of a search in the scenario's world, in departure order: the pinned offers when
    the search is one the scenario pins, plus background offers."""
    if not is_airport(origin) or not is_airport(destination):
        raise ValueError(f"unknown route {origin!r} -> {destination!r}")
    if origin == destination:
        raise ValueError("origin and destination are the same airport")
    booking = scenario["trip"]["booking_date"]
    ahead = days_between(booking, date)
    if not 0 <= ahead <= LONGEST_BOOKING_DAYS:
        raise ValueError(f"the date must be on or after the booking date {booking} and within the year")
    if return_date and not 0 <= days_between(date, return_date) <= LONGEST_BOOKING_DAYS:
        raise ValueError("the return date must be on or after the departure date")
    key = (origin, destination, date, return_date)
    count = default_background(scenario)
    if return_date and not any(search_spec.get("return_date", "") for search_spec in scenario["world"]["searches"]):
        count = 0  # a case whose ticket is one way lists no round-trip fares at all (see search_note)
    pinned = []
    for search_spec in scenario["world"]["searches"]:
        if search_key(search_spec) == key:
            pinned = pinned_offers(scenario["id"], search_spec)
            count = search_spec.get("background", count)
    background = background_offers(scenario["id"], key, count, [offer for _, offer in pinned])
    return ordered(pinned + background)


def search(scenario, origin, destination, date, return_date=""):
    """Every Offer of a search in the scenario's world, in departure order."""
    return [offer for _, offer in search_slots(scenario, origin, destination, date, return_date)]


def search_note(return_date, offers):
    """search_flights' note: where the offers come from, and, for a search that lists nothing, that this case
    lists no round-trip fares (a round-trip search) or no fares on that route and date (a one-way search)."""
    if offers:
        return NOTE
    return f"{NOTE} {NO_ROUND_TRIP if return_date else NO_OFFERS}"


def trip_offers(scenario):
    """Every offer on every search the scenario pins, in the scenario's search order, and each offer's slot
    by id. Pinned slots are unique within a scenario; a background slot is prefixed with its search's index."""
    offers, slots = [], {}
    for index, search_spec in enumerate(scenario["world"]["searches"]):
        for slot, offer in search_slots(scenario, *search_key(search_spec)):
            if slot.startswith("background-"):
                slot = f"search-{index}:{slot}"
            elif slot in slots.values():
                raise ValueError(f"{scenario['id']}: offer slot {slot!r} is used twice")
            offers.append(offer)
            slots[offer.offer_id] = slot
    return offers, slots
