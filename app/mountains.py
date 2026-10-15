from dataclasses import dataclass


@dataclass(frozen=True)
class Mountain:
    slug: str
    name: str
    province: str
    region: str
    lat: float
    lon: float
    summit_m: int
    ikon: bool = False
    default: bool = False  # the original six: shown up top and pre-picked in the sign-up form

    @property
    def maps_url(self):
        return f"https://www.google.com/maps/search/?api=1&query={self.lat},{self.lon}"


# summit heights mostly from skiresort.info, coordinates from wikipedia / the resorts.
# private clubs (craigleith, osler bluff, georgian peaks...) are left out since you can't just buy a ticket.
MOUNTAINS = [
    # --- Ontario ---
    Mountain("blue", "Blue Mountain", "Ontario", "Blue Mountains & Barrie", 44.5028, -80.3119, 450, ikon=True, default=True),
    Mountain("horseshoe", "Horseshoe Valley Resort", "Ontario", "Blue Mountains & Barrie", 44.5519, -79.6719, 406, default=True),
    Mountain("st-louis", "Mount St. Louis Moonstone", "Ontario", "Blue Mountains & Barrie", 44.6267, -79.6686, 382, default=True),
    Mountain("snow-valley", "Snow Valley", "Ontario", "Blue Mountains & Barrie", 44.4114, -79.7926, 320),

    Mountain("glen-eden", "Glen Eden", "Ontario", "Toronto area", 43.5056, -79.9440, 320),
    Mountain("hockley", "Hockley Valley", "Ontario", "Toronto area", 43.9779, -80.0471, 396),
    Mountain("brimacombe", "Brimacombe", "Ontario", "Toronto area", 44.0269, -78.5732, 310),
    Mountain("lakeridge", "Lakeridge", "Ontario", "Toronto area", 44.0278, -79.0630, 375),

    Mountain("calabogie", "Calabogie Peaks", "Ontario", "Ottawa Valley & Haliburton", 45.2750, -76.7819, 392),
    Mountain("pakenham", "Mount Pakenham", "Ontario", "Ottawa Valley & Haliburton", 45.3206, -76.3381, 217),
    Mountain("sir-sams", "Sir Sam's", "Ontario", "Ottawa Valley & Haliburton", 45.1298, -78.4832, 447),

    Mountain("antoine", "Antoine Mountain", "Ontario", "Northern Ontario", 46.3681, -78.7347, 366),
    Mountain("searchmont", "Searchmont", "Ontario", "Northern Ontario", 46.7682, -84.0465, 488),
    Mountain("loch-lomond", "Loch Lomond", "Ontario", "Northern Ontario", 48.2935, -89.3466, 430),
    Mountain("mount-baldy", "Mount Baldy", "Ontario", "Northern Ontario", 48.5251, -89.1273, 490),

    # --- Quebec ---
    Mountain("tremblant", "Mont Tremblant", "Quebec", "Laurentians", 46.2097, -74.5850, 875, ikon=True, default=True),
    Mountain("mont-blanc", "Mont Blanc", "Quebec", "Laurentians", 46.1010, -74.4838, 556),
    Mountain("saint-sauveur", "Sommet Saint-Sauveur", "Quebec", "Laurentians", 45.8856, -74.1511, 416),
    Mountain("olympia", "Sommet Olympia", "Quebec", "Laurentians", 45.9142, -74.1239, 440),
    Mountain("morin-heights", "Sommet Morin-Heights", "Quebec", "Laurentians", 45.8994, -74.2683, 465),
    Mountain("gabriel", "Sommet Gabriel", "Quebec", "Laurentians", 45.9239, -74.1545, 433),

    Mountain("val-saint-come", "Val Saint-Côme", "Quebec", "Lanaudière", 46.2725, -73.8694, 600),
    Mountain("garceau", "Mont Garceau", "Quebec", "Lanaudière", 46.3375, -74.2202, 667),
    Mountain("la-reserve", "Ski La Réserve", "Quebec", "Lanaudière", 46.2866, -74.1808, 690),

    Mountain("camp-fortune", "Camp Fortune", "Quebec", "Outaouais", 45.5090, -75.8510, 360),
    Mountain("cascades", "Mont Cascades", "Quebec", "Outaouais", 45.5929, -75.8489, 294),
    Mountain("edelweiss", "Sommet Edelweiss", "Quebec", "Outaouais", 45.6458, -75.8514, 345),
    Mountain("ste-marie", "Mont Ste-Marie", "Quebec", "Outaouais", 45.9408, -75.8748, 500),

    Mountain("bromont", "Bromont", "Quebec", "Eastern Townships", 45.3011, -72.6372, 553),
    Mountain("sutton", "Mont Sutton", "Quebec", "Eastern Townships", 45.1042, -72.5581, 860),
    Mountain("owls-head", "Owl's Head", "Quebec", "Eastern Townships", 45.0742, -72.2981, 714),
    Mountain("orford", "Mont Orford", "Quebec", "Eastern Townships", 45.3333, -72.2167, 850),

    Mountain("stoneham", "Stoneham Mountain Resort", "Quebec", "Quebec City & Charlevoix", 47.0279, -71.3806, 593, default=True),
    Mountain("le-massif", "Le Massif de Charlevoix", "Quebec", "Quebec City & Charlevoix", 47.2789, -70.6099, 806, ikon=True, default=True),
    Mountain("sainte-anne", "Mont-Sainte-Anne", "Quebec", "Quebec City & Charlevoix", 47.0723, -70.9082, 800),
    Mountain("le-relais", "Le Relais", "Quebec", "Quebec City & Charlevoix", 46.9369, -71.2975, 429),
    Mountain("grand-fonds", "Mont Grand-Fonds", "Quebec", "Quebec City & Charlevoix", 47.7714, -70.1025, 735),
    Mountain("massif-du-sud", "Massif du Sud", "Quebec", "Quebec City & Charlevoix", 46.6142, -70.4853, 915),

    Mountain("valinouet", "Le Valinouët", "Quebec", "Saguenay & Lower St. Lawrence", 48.6551, -70.8947, 810),
    Mountain("mont-edouard", "Mont Édouard", "Quebec", "Saguenay & Lower St. Lawrence", 48.1678, -70.2879, 633),
    Mountain("comi", "Mont Comi", "Quebec", "Saguenay & Lower St. Lawrence", 48.4674, -68.1956, 575),
    Mountain("val-direne", "Val d'Irène", "Quebec", "Saguenay & Lower St. Lawrence", 48.4718, -67.5724, 700),
]

DEFAULT_SLUGS = [m.slug for m in MOUNTAINS if m.default]


def by_region(mountains):
    # [(province, region, [mountains...]), ...] in the order they appear above
    groups = {}
    for m in mountains:
        groups.setdefault((m.province, m.region), []).append(m)
    return [(province, region, ms) for (province, region), ms in groups.items()]


REGIONS = by_region(MOUNTAINS)
