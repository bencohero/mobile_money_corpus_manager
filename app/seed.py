from sqlalchemy.orm import Session
from .models import Language, ParticipantLanguageSequence, User, Utterance
from .languages import LANGUAGES
from .auth import hash_password
from .config import settings

SEED = [
("MOS_I01_U001","DAILY_SUMMARY","Demander le bilan des transactions d'aujourd'hui","TODAY",None,None,None,None),
("MOS_I02_U001","TOTAL_RECEIVED","Demander combien d'argent a été reçu aujourd'hui","TODAY",None,None,"RECEIVE",None),
("MOS_I03_U001","TOTAL_SENT","Demander combien d'argent a été envoyé aujourd'hui","TODAY",None,None,"SEND",None),
("MOS_I04_U001","TOTAL_SPENT","Demander le total dépensé aujourd'hui","TODAY",None,None,None,None),
("MOS_I05_U001","TOTAL_FEES","Demander combien de frais ont été payés aujourd'hui","TODAY",None,None,None,None),
("MOS_I06_U001","LAST_TRANSACTION","Demander quelle est la dernière transaction",None,None,None,None,None),
("MOS_I07_U001","SEARCH_TRANSACTION","Demander si 10 000 FCFA ont été reçus aujourd'hui","TODAY",10000,None,"RECEIVE",None),
("MOS_I07_U002","SEARCH_TRANSACTION","Demander si 25 000 FCFA ont été envoyés à Issa aujourd'hui","TODAY",25000,"Issa","SEND",None),
("MOS_I07_U003","SEARCH_TRANSACTION","Demander si 10 000 FCFA ont été reçus par Orange Money aujourd'hui","TODAY",10000,None,"RECEIVE","ORANGE_MONEY"),
("MOS_I08_U001","PERIOD_SUMMARY","Demander le bilan de cette semaine","THIS_WEEK",None,None,None,None),
("MOS_I09_U001","REPEAT","Demander à l'application de répéter",None,None,None,None,None),
("MOS_I10_U001","CANCEL","Annuler la commande en cours",None,None,None,None,None),
("MOS_OOS_U001","UNKNOWN","Demander l'heure",None,None,None,None,None),
]

def seed(db: Session):
    for language in LANGUAGES:
        if not db.get(Language, language.code):
            db.add(Language(code=language.code, name=language.name, is_active=True))
        if not db.get(ParticipantLanguageSequence, language.code):
            db.add(ParticipantLanguageSequence(language_code=language.code, last_number=0))
    if not db.query(User).filter_by(username=settings.admin_username).first():
        db.add(User(
            username=settings.admin_username,
            password_hash=hash_password(settings.admin_password),
            role="ADMIN",
        ))
    for code,intent,scenario,period,amount,cp,ttype,op in SEED:
        if not db.query(Utterance).filter_by(utterance_code=code).first():
            db.add(Utterance(
                utterance_code=code, language="mos", intent=intent, scenario_fr=scenario,
                period=period, amount=amount, counterparty=cp,
                transaction_type=ttype, operator=op
            ))
    db.commit()
