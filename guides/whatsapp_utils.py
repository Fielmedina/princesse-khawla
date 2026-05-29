import logging
import re
from django.conf import settings

logger = logging.getLogger(__name__)


def _normalize_phone(phone: str) -> str | None:
    """
    Normalise un numéro tunisien vers le format E.164 (+216XXXXXXXX).
    Retourne None si le numéro est vide ou invalide.
    """
    if not phone:
        return None

    # Supprime tout ce qui n'est pas chiffre ou +
    cleaned = re.sub(r"[^\d+]", "", phone.strip())

    # Déjà en format international
    if cleaned.startswith("+"):
        return cleaned if len(cleaned) >= 8 else None

    # Préfixe tunisien par défaut si 8 chiffres
    if re.match(r"^\d{8}$", cleaned):
        return f"+216{cleaned}"

    # Commence par 216 sans le +
    if cleaned.startswith("216") and len(cleaned) == 11:
        return f"+{cleaned}"

    return cleaned if cleaned else None


import requests

def send_whatsapp_message_cloud_api(to_phone: str, message: str) -> bool:
    """
    Envoie un message WhatsApp via l'API Cloud officielle de WhatsApp (Meta).
    """
    token = getattr(settings, "WHATSAPP_API_TOKEN", None)
    phone_number_id = getattr(settings, "WHATSAPP_PHONE_NUMBER_ID", None)

    if not all([token, phone_number_id]):
        logger.warning("[WhatsApp API] Configuration WhatsApp Cloud API incomplète dans settings.py.")
        return False

    normalized = _normalize_phone(to_phone)
    if not normalized:
        logger.warning("[WhatsApp API] Numéro de téléphone invalide ou vide : %s", to_phone)
        return False

    # L'API Cloud WhatsApp requiert le numéro sans le signe '+' devant.
    clean_phone = normalized.replace("+", "")

    url = f"https://graph.facebook.com/v20.0/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": clean_phone,
        "type": "text",
        "text": {
            "preview_url": False,
            "body": message
        }
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        res_json = response.json()
        if response.status_code == 200:
            msg_id = res_json.get("messages", [{}])[0].get("id")
            logger.info("[WhatsApp API] Message envoyé à %s — ID : %s", clean_phone, msg_id)
            return True
        else:
            logger.error("[WhatsApp API] Échec de l'envoi à %s : %s", clean_phone, res_json)
            return False
    except Exception as exc:
        logger.error("[WhatsApp API] Erreur lors de l'envoi à %s : %s", clean_phone, exc)
        return False


def send_whatsapp_message(to_phone: str, message: str) -> bool:
    """
    Envoie un message WhatsApp via l'API Cloud officielle de WhatsApp (Meta).
    """
    if not getattr(settings, "WHATSAPP_ENABLED", False):
        logger.info("[WhatsApp] Désactivé (WHATSAPP_ENABLED=False). Message non envoyé.")
        return False

    return send_whatsapp_message_cloud_api(to_phone, message)


def send_new_suggestion_whatsapp(guide, suggestion) -> bool:
    """
    Notifie le guide par WhatsApp d'une nouvelle demande de réservation.
    La langue du message suit guide.preferred_language ('fr' ou 'en').
    """
    guide_name = guide.user.get_full_name() or guide.user.username
    lang = getattr(guide, 'preferred_language', 'fr')

    # Calcul du montant (total_price = 0 à la création, avant approve())
    adults_subtotal   = round(suggestion.nb_adults * float(guide.price_adult), 3)
    children_subtotal = round(suggestion.nb_children_over_6 * float(guide.price_child), 3)
    total_price       = round(adults_subtotal + children_subtotal, 3)
    commission        = float(suggestion.commission_rate)
    net_amount        = round(total_price * (1 - commission / 100), 3)

    site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')

    if lang == 'en':
        # ── English message ───────────────────────────────────────────────
        group_line = f"{suggestion.nb_adults} adult(s)"
        if suggestion.nb_children_over_6:
            group_line += f", {suggestion.nb_children_over_6} child(ren) >6 yrs"
        if suggestion.nb_children_under_6:
            group_line += f", {suggestion.nb_children_under_6} child(ren) <6 yrs"

        message = (
            f"🔔 *New Booking Request — FielMedina*\n\n"
            f"Hello *{guide_name}*,\n\n"
            f"You have received a new guided tour request:\n\n"
            f"👤 *Client:* {suggestion.client_name}\n"
            f"📅 *Requested date:* {suggestion.date.strftime('%d/%m/%Y')}\n"
            f"👥 *Group:* {group_line}\n"
            f"💰 *Estimated amount:* {total_price:.3f} TND\n"
            f"💵 *Net after commission ({commission:.0f}%):* {net_amount:.3f} TND\n\n"
            f"Log in to your dashboard to accept or decline this request.\n"
            f"{site_url}/guides/suggestions/"
        )
    else:
        # ── French message (default) ──────────────────────────────────────
        group_line = f"{suggestion.nb_adults} adulte(s)"
        if suggestion.nb_children_over_6:
            group_line += f", {suggestion.nb_children_over_6} enfant(s) >6 ans"
        if suggestion.nb_children_under_6:
            group_line += f", {suggestion.nb_children_under_6} enfant(s) <6 ans"

        message = (
            f"🔔 *Nouvelle demande de réservation — FielMedina*\n\n"
            f"Bonjour *{guide_name}*,\n\n"
            f"Vous avez reçu une nouvelle demande de visite guidée :\n\n"
            f"👤 *Client :* {suggestion.client_name}\n"
            f"📅 *Date souhaitée :* {suggestion.date.strftime('%d/%m/%Y')}\n"
            f"👥 *Groupe :* {group_line}\n"
            f"💰 *Montant estimé :* {total_price:.3f} TND\n"
            f"💵 *Net après commission ({commission:.0f}%) :* {net_amount:.3f} TND\n\n"
            f"Connectez-vous à votre tableau de bord pour accepter ou refuser cette demande.\n"
            f"{site_url}/guides/suggestions/"
        )

    return send_whatsapp_message(guide.phone, message)