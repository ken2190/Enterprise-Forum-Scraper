from templates.oday_template import OdayParser
from templates.bmr_template import BMRParser
from templates.evolution_template import EvolutionParser
from templates.agora_template import AgoraParser
from templates.therealdeal_template import TheRealDealParser
from templates.abraxas_template import AbraxasParser
from templates.kiss_template import KissParser
from templates.andromeda_template import AndromedaParser
from templates.darknetheroes_template import DarkNetHeroesParser
from templates.exploit_template import ExploitParser
from templates.antichat_template import AntichatParser
from templates.breachforums_template import BreachForumsParser
from templates.greysec_template import GreySecParser
from templates.pandora_template import PandoraParser
from templates.thehub_template import TheHubParser
from templates.utopia_template import UtopiaParser
from templates.kickass_template import KickAssParser
from templates.darkode_template import DarkodeParser
from templates.greyroad_template import GreyRoadParser
from templates.sentrymba_template import SentryMBAParser
from templates.bitcointalk_template import BitCoinTalkParser
from templates.blackbank_template import BlackBankParser
from templates.bungee54_template import Bungee54Parser
from templates.cannabisroad_template import CannabisRoadParser
from templates.hydra_template import HydraParser
from templates.kingdom_template import KingdomParser
from templates.nucleus_template import NucleusParser
from templates.verified_template import VerifiedParser
from templates.wallstreet_template import WallStreetParser
from templates.galaxy3_template import Galaxy3Parser
from templates.galaxy1_template import Galaxy1Parser
from templates.silkroad1_template import SilkRoad1Parser
from templates.silkroad2_template import SilkRoad2Parser
from templates.lolzteam_template import LolzTeamParser
from templates.galaxy2_template import Galaxy2Parser
from templates.genesis_template import GenesisParser
from templates.hell_template import HellParser
from templates.nulled_template import NulledParser
from templates.badkarma_template import BadKarmaParser
from templates.outlawmarket_template import OutLawMarketParser
from templates.alphabay_template import AlphaBayParser
from templates.sinister_template import SinisterParser
from templates.verified_carder_template import VerifiedCarderParser
from templates.carder_template import CarderParser
from templates.ccc_mn_template import CCCMNParser
from templates.cracked_to_template import CrackedToParser
from templates.sky_fraud_template import SkyFraudParser
from templates.omerta_template import OmertaParser
from templates.dark_skies_template import DarkSkiesParser
from templates.procrd_template import ProcrdParser
from templates.blackbox_template import BlackBoxParser
from templates.v3rmillion_template import V3RMillionParser
from templates.silk_road3_template import SilkRoad3Parser
from templates.hiddenhand_template import HiddenHandParser
from templates.prvtzone_template import PrvtZoneParser
from templates.hackforums_template import HackForumsParser
from templates.darkwebs_template import DarkWebsParser
from templates.nulledbb_template import NulledBBParser
from templates.russian_carder_template import RussianCarderParser
from templates.blackhatworld_template import BlackHatWorldParser
from templates.thecc_template import TheCCParser

PARSER_MAP = {
    '0day': OdayParser,
    'bmr': BMRParser,
    'evolution': EvolutionParser,
    'agora': AgoraParser,
    'therealdeal': TheRealDealParser,
    'abraxas': AbraxasParser,
    'kiss': KissParser,
    'andromeda': AndromedaParser,
    'darknetheroes': DarkNetHeroesParser,
    'diabolus': DarkNetHeroesParser,
    'exploit': ExploitParser,
    'antichat': AntichatParser,
    'breachforums': BreachForumsParser,
    'greysec': GreySecParser,
    'pandora': PandoraParser,
    'thehub': TheHubParser,
    'utopia': UtopiaParser,
    'ka': KickAssParser,
    'darkode': DarkodeParser,
    'greyroad': GreyRoadParser,
    'sentrymba': SentryMBAParser,
    'bitcointalk': BitCoinTalkParser,
    'blackbank': BlackBankParser,
    'bungee54': Bungee54Parser,
    'cannabisroad': CannabisRoadParser,
    'hydra': HydraParser,
    'kingdom': KingdomParser,
    'nucleus': NucleusParser,
    'verified': VerifiedParser,
    'wallstreet': WallStreetParser,
    'galaxy3': Galaxy3Parser,
    'galaxy1': Galaxy1Parser,
    'silkroad1': SilkRoad1Parser,
    'silkroad2': SilkRoad2Parser,
    'lolzteam': LolzTeamParser,
    'galaxy2': Galaxy2Parser,
    'genesis': GenesisParser,
    'hell': HellParser,
    'nulled': NulledParser,
    'badkarma': BadKarmaParser,
    'outlawmarket': OutLawMarketParser,
    'alphabay': AlphaBayParser,
    'sinister': SinisterParser,
    'verified_carder': VerifiedCarderParser,
    'carder': CarderParser,
    'ccc_mn': CCCMNParser,
    'cracked_to': CrackedToParser,
    'sky_fraud': SkyFraudParser,
    'omerta': OmertaParser,
    'dark_skies': DarkSkiesParser,
    'procrd': ProcrdParser,
    'blackbox': BlackBoxParser,
    'v3rmillion': V3RMillionParser,
    'silkroad3': SilkRoad3Parser,
    'hiddenhand': HiddenHandParser,
    'prvtzone': PrvtZoneParser,
    'hackforums': HackForumsParser,
    'darkwebs': DarkWebsParser,
    'nulledbb': NulledBBParser,
    'russian_carder': RussianCarderParser,
    'blackhatworld': BlackHatWorldParser,
    'thecc': TheCCParser,
}
