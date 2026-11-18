"""User-facing API messages in Spanish, English and French.

The language comes from the request's Accept-Language header (the frontend sends the language
chosen in the app). `LanguageMiddleware` stores it in a context variable for the whole request,
so errors are translated where they are raised:

    raise ApiError(status.HTTP_404_NOT_FOUND, "user_not_found")
"""

from contextvars import ContextVar

from fastapi import HTTPException

LANGUAGES = ("es", "en", "fr")
DEFAULT_LANGUAGE = "en"

_language: ContextVar[str] = ContextVar("language", default=DEFAULT_LANGUAGE)

MESSAGES: dict[str, dict[str, str]] = {
    # Auth and permissions
    "not_authenticated": {
        "es": "Tienes que iniciar sesión.",
        "en": "You need to sign in.",
        "fr": "Tu dois te connecter.",
    },
    "admin_required": {
        "es": "Solo para administradores.",
        "en": "Administrators only.",
        "fr": "Réservé aux administrateurs.",
    },
    "invalid_credentials": {
        "es": "Usuario o contraseña incorrectos.",
        "en": "Wrong username or password.",
        "fr": "Nom d’utilisateur ou mot de passe incorrect.",
    },
    "session_expired": {
        "es": "La sesión ha caducado. Vuelve a iniciar sesión.",
        "en": "Your session has expired. Please sign in again.",
        "fr": "Ta session a expiré. Reconnecte-toi.",
    },
    "username_or_email_taken": {
        "es": "Ese nombre de usuario o email ya está en uso.",
        "en": "That username or email is already in use.",
        "fr": "Ce nom d’utilisateur ou cet e-mail est déjà utilisé.",
    },
    "username_taken": {
        "es": "Ese nombre de usuario ya está en uso.",
        "en": "That username is already in use.",
        "fr": "Ce nom d’utilisateur est déjà utilisé.",
    },
    "wrong_password": {
        "es": "La contraseña actual no es correcta.",
        "en": "Your current password is not correct.",
        "fr": "Ton mot de passe actuel n’est pas correct.",
    },
    "rate_limited": {
        "es": "Demasiados intentos. Espera unos minutos y vuelve a probar.",
        "en": "Too many attempts. Wait a few minutes and try again.",
        "fr": "Trop de tentatives. Attends quelques minutes et réessaie.",
    },
    # Users and friends
    "user_not_found": {
        "es": "Ese usuario no existe.",
        "en": "That user doesn't exist.",
        "fr": "Cet utilisateur n’existe pas.",
    },
    "cannot_modify_self": {
        "es": "No puedes modificar tu propia cuenta aquí.",
        "en": "You can't change your own account here.",
        "fr": "Tu ne peux pas modifier ton propre compte ici.",
    },
    "friendship_not_found": {
        "es": "Esa amistad o solicitud ya no existe.",
        "en": "That friendship or request no longer exists.",
        "fr": "Cette amitié ou cette demande n’existe plus.",
    },
    "cannot_add_self": {
        "es": "No puedes añadirte a ti mismo.",
        "en": "You can't add yourself.",
        "fr": "Tu ne peux pas t’ajouter toi-même.",
    },
    "already_friends": {
        "es": "Ya sois amigos.",
        "en": "You're already friends.",
        "fr": "Vous êtes déjà amis.",
    },
    "request_already_sent": {
        "es": "Ya le enviaste una solicitud.",
        "en": "You already sent them a request.",
        "fr": "Tu lui as déjà envoyé une demande.",
    },
    "no_request_to_accept": {
        "es": "No hay ninguna solicitud que aceptar.",
        "en": "There's no request to accept.",
        "fr": "Il n’y a aucune demande à accepter.",
    },
    # Steam
    "link_steam_first": {
        "es": "Vincula tu cuenta de Steam primero.",
        "en": "Link your Steam account first.",
        "fr": "Lie d’abord ton compte Steam.",
    },
    "steam_unavailable": {
        "es": "Steam no responde. Prueba otra vez en un rato.",
        "en": "Steam isn't responding. Try again in a while.",
        "fr": "Steam ne répond pas. Réessaie dans un moment.",
    },
    "steam_not_configured": {
        "es": "La sincronización con Steam no está configurada en este servidor.",
        "en": "Steam sync is not configured on this server.",
        "fr": "La synchronisation Steam n’est pas configurée sur ce serveur.",
    },
    "steam_sync_running": {
        "es": "Ya hay una sincronización con Steam en marcha.",
        "en": "A Steam sync is already in progress.",
        "fr": "Une synchronisation Steam est déjà en cours.",
    },
    "steam_friends_private": {
        "es": "Tu lista de amigos de Steam es privada. Ponla como pública en la privacidad de "
        "Steam.",
        "en": "Your Steam friends list is private. Make it public in your Steam privacy settings.",
        "fr": "Ta liste d’amis Steam est privée. Rends-la publique dans la confidentialité de "
        "Steam.",
    },
    "steam_games_private": {
        "es": "Steam no ha devuelto ningún juego. Pon los «Detalles de juegos» como públicos en "
        "la privacidad de Steam.",
        "en": "Steam returned no games. Set “Game details” to Public in your Steam privacy "
        "settings.",
        "fr": "Steam n’a renvoyé aucun jeu. Rends les « Détails des jeux » publics dans la "
        "confidentialité de Steam.",
    },
    # Games and library
    "game_not_found": {
        "es": "Ese juego no existe.",
        "en": "That game doesn't exist.",
        "fr": "Ce jeu n’existe pas.",
    },
    "game_not_in_library": {
        "es": "Ese juego no está en tu biblioteca.",
        "en": "That game isn't in your library.",
        "fr": "Ce jeu n’est pas dans ta bibliothèque.",
    },
    "entry_not_found": {
        "es": "Ese juego ya no está en la biblioteca.",
        "en": "That game is no longer in the library.",
        "fr": "Ce jeu n’est plus dans la bibliothèque.",
    },
    "game_already_in_library": {
        "es": "Ya tienes ese juego en esa plataforma.",
        "en": "You already have that game on that platform.",
        "fr": "Tu as déjà ce jeu sur cette plateforme.",
    },
    "igdb_not_configured": {
        "es": "La búsqueda en IGDB no está configurada en este servidor.",
        "en": "IGDB search is not configured on this server.",
        "fr": "La recherche IGDB n’est pas configurée sur ce serveur.",
    },
    "igdb_failed": {
        "es": "IGDB no responde. Prueba otra vez en un rato.",
        "en": "IGDB isn't responding. Try again in a while.",
        "fr": "IGDB ne répond pas. Réessaie dans un moment.",
    },
    "igdb_game_not_found": {
        "es": "IGDB no tiene ese juego.",
        "en": "IGDB doesn't have that game.",
        "fr": "IGDB n’a pas ce jeu.",
    },
    # Imports
    "use_steam_sync": {
        "es": "Para Steam usa «Sincronizar con Steam».",
        "en": "For Steam, use “Sync with Steam”.",
        "fr": "Pour Steam, utilise « Synchroniser avec Steam ».",
    },
    "file_too_large": {
        "es": "El fichero es demasiado grande (máximo 5 MB).",
        "en": "The file is too large (5 MB max).",
        "fr": "Le fichier est trop volumineux (5 Mo maximum).",
    },
    "invalid_json": {
        "es": "El JSON no es válido: {error}",
        "en": "Invalid JSON: {error}",
        "fr": "JSON non valide : {error}",
    },
    "json_shape": {
        "es": "El JSON debe ser una lista de juegos o un objeto con una lista «games».",
        "en": "The JSON must be a list of games or an object with a “games” list.",
        "fr": "Le JSON doit être une liste de jeux ou un objet avec une liste « games ».",
    },
    "too_many_rows": {
        "es": "Demasiadas filas (máximo {max}).",
        "en": "Too many rows ({max} max).",
        "fr": "Trop de lignes ({max} maximum).",
    },
    "no_games_found": {
        "es": "No se ha encontrado ningún juego. Hace falta una columna «title» o «name».",
        "en": "No games found. A “title” or “name” column is required.",
        "fr": "Aucun jeu trouvé. Une colonne « title » ou « name » est nécessaire.",
    },
    "job_not_found": {
        "es": "Esa importación no existe.",
        "en": "That import doesn't exist.",
        "fr": "Cette importation n’existe pas.",
    },
    "undo_only_last": {
        "es": "Solo se puede deshacer la última importación de fichero completada.",
        "en": "Only the latest completed file import can be undone.",
        "fr": "Seule la dernière importation de fichier terminée peut être annulée.",
    },
}

# French typography: narrow no-break space before ? ! : ; and inside « »
_NNBSP = " "
for _texts in MESSAGES.values():
    _fr = _texts["fr"]
    for _mark in "?!:;":
        _fr = _fr.replace(f" {_mark}", f"{_NNBSP}{_mark}")
    _texts["fr"] = _fr.replace("« ", f"«{_NNBSP}").replace(" »", f"{_NNBSP}»")


def parse_accept_language(header: str | None) -> str:
    """First supported language in the header, by preference (q values honoured)."""
    if not header:
        return DEFAULT_LANGUAGE
    ranked: list[tuple[float, int, str]] = []
    for i, part in enumerate(header.split(",")):
        tag, _, params = part.strip().partition(";")
        q = 1.0
        if params.strip().startswith("q="):
            try:
                q = float(params.strip()[2:])
            except ValueError:
                q = 0.0
        lang = tag.strip().lower()[:2]
        if lang in LANGUAGES and q > 0:
            ranked.append((-q, i, lang))
    return min(ranked)[2] if ranked else DEFAULT_LANGUAGE


def current_language() -> str:
    return _language.get()


def tr(code: str, lang: str | None = None, **params) -> str:
    """Message for `code` in `lang` (default: the current request's language)."""
    texts = MESSAGES.get(code)
    if texts is None:
        return code
    text = texts.get(lang or current_language()) or texts[DEFAULT_LANGUAGE]
    return text.format(**params) if params else text


class ApiError(HTTPException):
    """HTTPException whose detail is the message for `code` in the request's language."""

    def __init__(
        self, status_code: int, code: str, headers: dict[str, str] | None = None, **params
    ):
        super().__init__(status_code, tr(code, **params), headers=headers)
        self.code = code


class LanguageMiddleware:
    """Pure ASGI middleware: sets the language for the rest of the request."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        header = dict(scope.get("headers") or []).get(b"accept-language", b"").decode("latin-1")
        token = _language.set(parse_accept_language(header))
        try:
            await self.app(scope, receive, send)
        finally:
            _language.reset(token)
