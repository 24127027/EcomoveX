#import nessessary modules
from services.chatbot.context_manager import Context_Manager
from services.chatbot.rule_engine import RuleEngine


class ChatbotService:
    def __self_init__(self, context_manager, rule_engine):
        self.context_manager = context_manager
        self.rule_engine = rule_engine
        
    