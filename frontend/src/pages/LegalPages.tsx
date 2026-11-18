import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";

import { currentLanguage, type Language } from "../i18n";
import { formatDate } from "../lib/labels";
import { SITE } from "../lib/site";

// The legal texts are kept whole per language (they must read as one document).
// The Spanish version is the binding one; the others say so.

function LegalPage({ title, children }: { title: string; children: ReactNode }) {
  const { t } = useTranslation();
  return (
    <article className="mx-auto max-w-3xl space-y-4 text-sm leading-relaxed text-slate-300 [&_h2]:mt-8 [&_h2]:text-lg [&_h2]:font-semibold [&_h2]:text-slate-100 [&_li]:ml-5 [&_li]:list-disc [&_a]:text-indigo-300 [&_a]:underline">
      <h1 className="text-2xl font-bold text-slate-50">{title}</h1>
      <p className="text-xs text-slate-500">
        {t("legal.updated", { date: formatDate(SITE.lastUpdated) })}
      </p>
      {currentLanguage() !== "es" && (
        <p className="rounded-lg border border-slate-800 bg-slate-900/60 p-3 text-xs text-slate-400">
          {t("legal.translationNote")}
        </p>
      )}
      {children}
    </article>
  );
}

const Contact = () => <a href={`mailto:${SITE.contactEmail}`}>{SITE.contactEmail}</a>;
const Aepd = () => (
  <a href="https://www.aepd.es" target="_blank" rel="noreferrer">
    aepd.es
  </a>
);
const Repo = () => (
  <a href={SITE.repoUrl} target="_blank" rel="noreferrer">
    GitHub
  </a>
);

const PRIVACY: Record<Language, { title: string; body: ReactNode }> = {
  es: {
    title: "Política de privacidad",
    body: (
      <>
        <h2>Responsable del tratamiento</h2>
        <p>
          {SITE.ownerName}, titular de {SITE.name}, un proyecto personal sin ánimo de lucro.
          Contacto: <Contact />.
        </p>

        <h2>Qué datos tratamos</h2>
        <ul>
          <li>
            Datos de cuenta: nombre de usuario, email y contraseña (guardada cifrada con un hash,
            nunca en claro).
          </li>
          <li>
            Si entras con Steam: tu SteamID, tu nombre público y tu avatar de Steam. Nunca vemos tu
            contraseña de Steam.
          </li>
          <li>
            Tu biblioteca: juegos, tienda, horas jugadas, fechas de última partida, logros,
            categorías, notas y favoritos.
          </li>
          <li>Tus amigos en {SITE.name} y las solicitudes de amistad.</li>
          <li>
            Los ficheros que importas solo se leen para extraer la lista de juegos; el fichero no se
            guarda.
          </li>
          <li>
            Tu IP se usa de forma temporal para limitar intentos de inicio de sesión (máx. 1 hora).
          </li>
        </ul>

        <h2>Para qué y con qué base legal</h2>
        <p>
          Únicamente para prestarte el servicio que pides: guardar y mostrar tu biblioteca y tus
          estadísticas. La base legal es la ejecución del servicio que solicitas al registrarte
          (art. 6.1.b del RGPD). No hay publicidad, no se venden datos y no se usan para elaborar
          perfiles comerciales.
        </p>

        <h2>Quién más interviene</h2>
        <ul>
          <li>
            Alojamiento: Oracle Cloud Infrastructure (región de Madrid, España). Los datos no salen
            de la Unión Europea.
          </li>
          <li>
            Steam Web API (Valve): se consulta con tu SteamID para leer tus juegos, logros y lista de
            amigos, solo si vinculas Steam.
          </li>
          <li>
            IGDB (Twitch/Amazon): se consulta con el título o el identificador del juego para obtener
            portadas y géneros. No se le envía ningún dato tuyo.
          </li>
        </ul>

        <h2>Cuánto tiempo</h2>
        <p>
          Mientras mantengas tu cuenta. Al eliminarla (Ajustes → Eliminar cuenta) se borran tus
          datos de inmediato; las copias de seguridad se renuevan y desaparecen en un máximo de 14
          días.
        </p>

        <h2>Perfil público</h2>
        <p>
          Tu perfil es privado por defecto. Solo si activas «Perfil público» cualquier persona podrá
          ver tu nombre de usuario, avatar, biblioteca, estadísticas y logros.
        </p>

        <h2>Cookies y almacenamiento local</h2>
        <p>
          Solo usamos una cookie técnica (<code>librachieve_refresh</code>) para mantener tu sesión
          iniciada. Además, tu navegador guarda el idioma que eliges (<code>lang</code>) y, si
          instalas la app, los ficheros de la web para que abra más rápido; nada de eso contiene
          datos personales. Todo es imprescindible para el funcionamiento y no requiere
          consentimiento. No hay cookies de analítica ni de publicidad.
        </p>

        <h2>Tus derechos</h2>
        <p>
          Puedes acceder, rectificar, suprimir, oponerte, limitar el tratamiento y pedir la
          portabilidad de tus datos escribiendo a <Contact />. Puedes cambiar tu nombre y la
          privacidad en Ajustes y borrar tu cuenta en cualquier momento. Si crees que no se respetan
          tus derechos, puedes reclamar ante la Agencia Española de Protección de Datos (<Aepd />
          ).
        </p>
      </>
    ),
  },
  en: {
    title: "Privacy policy",
    body: (
      <>
        <h2>Data controller</h2>
        <p>
          {SITE.ownerName}, owner of {SITE.name}, a non-profit personal project. Contact:{" "}
          <Contact />.
        </p>

        <h2>What data we process</h2>
        <ul>
          <li>
            Account data: username, email and password (stored as a salted hash, never in plain
            text).
          </li>
          <li>
            If you sign in with Steam: your SteamID, public name and Steam avatar. We never see your
            Steam password.
          </li>
          <li>
            Your library: games, store, hours played, last played dates, achievements, categories,
            scores and favourites.
          </li>
          <li>Your friends on {SITE.name} and friend requests.</li>
          <li>
            Files you import are only read to extract the list of games; the file itself is not
            stored.
          </li>
          <li>Your IP address is used temporarily to limit sign-in attempts (max. 1 hour).</li>
        </ul>

        <h2>Purpose and legal basis</h2>
        <p>
          Only to provide the service you ask for: storing and showing your library and statistics.
          The legal basis is the performance of the service you request when signing up (Art. 6(1)(b)
          GDPR). There are no ads, no data is sold and nothing is used for commercial profiling.
        </p>

        <h2>Third parties involved</h2>
        <ul>
          <li>
            Hosting: Oracle Cloud Infrastructure (Madrid region, Spain). Data does not leave the
            European Union.
          </li>
          <li>
            Steam Web API (Valve): queried with your SteamID to read your games, achievements and
            friends list, only if you link Steam.
          </li>
          <li>
            IGDB (Twitch/Amazon): queried with the game title or ID to get covers and genres. None of
            your data is sent to it.
          </li>
        </ul>

        <h2>How long</h2>
        <p>
          For as long as you keep your account. Deleting it (Settings → Delete account) erases your
          data immediately; backups rotate and disappear within 14 days at most.
        </p>

        <h2>Public profile</h2>
        <p>
          Your profile is private by default. Only if you turn on “Public profile” can anyone see
          your username, avatar, library, statistics and achievements.
        </p>

        <h2>Cookies and local storage</h2>
        <p>
          We only use one technical cookie (<code>librachieve_refresh</code>) to keep you signed in.
          Your browser also stores the language you choose (<code>lang</code>) and, if you install
          the app, the site files so it opens faster; none of that contains personal data. All of it
          is strictly necessary and needs no consent. There are no analytics or advertising cookies.
        </p>

        <h2>Your rights</h2>
        <p>
          You can access, rectify, erase, object to, restrict the processing of and port your data
          by writing to <Contact />. You can change your name and privacy in Settings and delete
          your account at any time. If you believe your rights are not respected, you can file a
          complaint with the Spanish Data Protection Agency (<Aepd />
          ).
        </p>
      </>
    ),
  },
  fr: {
    title: "Politique de confidentialité",
    body: (
      <>
        <h2>Responsable du traitement</h2>
        <p>
          {SITE.ownerName}, propriétaire de {SITE.name}, un projet personnel à but non lucratif.
          Contact : <Contact />.
        </p>

        <h2>Données traitées</h2>
        <ul>
          <li>
            Données de compte : nom d’utilisateur, e-mail et mot de passe (stocké sous forme de
            hachage, jamais en clair).
          </li>
          <li>
            Si vous vous connectez avec Steam : votre SteamID, votre nom public et votre avatar
            Steam. Nous ne voyons jamais votre mot de passe Steam.
          </li>
          <li>
            Votre bibliothèque : jeux, boutique, heures de jeu, dates de dernière partie, succès,
            catégories, notes et favoris.
          </li>
          <li>Vos amis sur {SITE.name} et les demandes d’ami.</li>
          <li>
            Les fichiers que vous importez ne sont lus que pour extraire la liste des jeux ; le
            fichier n’est pas conservé.
          </li>
          <li>
            Votre adresse IP est utilisée temporairement pour limiter les tentatives de connexion
            (1 heure max.).
          </li>
        </ul>

        <h2>Finalité et base légale</h2>
        <p>
          Uniquement pour fournir le service que vous demandez : enregistrer et afficher votre
          bibliothèque et vos statistiques. La base légale est l’exécution du service demandé lors de
          l’inscription (art. 6.1.b du RGPD). Pas de publicité, aucune donnée vendue ni utilisée à
          des fins de profilage commercial.
        </p>

        <h2>Tiers impliqués</h2>
        <ul>
          <li>
            Hébergement : Oracle Cloud Infrastructure (région de Madrid, Espagne). Les données ne
            quittent pas l’Union européenne.
          </li>
          <li>
            Steam Web API (Valve) : interrogée avec votre SteamID pour lire vos jeux, succès et liste
            d’amis, uniquement si vous liez Steam.
          </li>
          <li>
            IGDB (Twitch/Amazon) : interrogé avec le titre ou l’identifiant du jeu pour obtenir
            jaquettes et genres. Aucune de vos données ne lui est envoyée.
          </li>
        </ul>

        <h2>Durée de conservation</h2>
        <p>
          Tant que vous gardez votre compte. Sa suppression (Paramètres → Supprimer le compte) efface
          vos données immédiatement ; les sauvegardes sont renouvelées et disparaissent en 14 jours
          maximum.
        </p>

        <h2>Profil public</h2>
        <p>
          Votre profil est privé par défaut. Ce n’est que si vous activez « Profil public » que
          n’importe qui pourra voir votre nom d’utilisateur, avatar, bibliothèque, statistiques et
          succès.
        </p>

        <h2>Cookies et stockage local</h2>
        <p>
          Nous n’utilisons qu’un cookie technique (<code>librachieve_refresh</code>) pour maintenir
          votre session. Votre navigateur enregistre aussi la langue choisie (<code>lang</code>) et,
          si vous installez l’application, les fichiers du site pour qu’il s’ouvre plus vite ; rien
          de tout cela ne contient de données personnelles. Tout est strictement nécessaire et ne
          requiert pas de consentement. Aucun cookie d’analyse ni de publicité.
        </p>

        <h2>Vos droits</h2>
        <p>
          Vous pouvez accéder à vos données, les rectifier, les effacer, vous opposer à leur
          traitement, le limiter et demander leur portabilité en écrivant à <Contact />. Vous pouvez
          modifier votre nom et votre confidentialité dans Paramètres et supprimer votre compte à
          tout moment. Si vous estimez que vos droits ne sont pas respectés, vous pouvez saisir
          l’autorité espagnole de protection des données (<Aepd />
          ).
        </p>
      </>
    ),
  },
};

const NOTICE: Record<Language, { title: string; body: ReactNode }> = {
  es: {
    title: "Aviso legal",
    body: (
      <>
        <h2>Titular</h2>
        <p>
          {SITE.name} es un proyecto personal y gratuito de {SITE.ownerName}, sin actividad
          económica. Contacto: <Contact />. El código fuente es público en <Repo />.
        </p>

        <h2>Uso</h2>
        <p>
          El servicio se ofrece tal cual, sin garantías de disponibilidad. Te comprometes a no usarlo
          para fines ilícitos ni a intentar acceder a datos de otros usuarios.
        </p>

        <h2>Marcas y contenidos de terceros</h2>
        <p>
          Los nombres, portadas e iconos de juegos y logros pertenecen a sus respectivos
          propietarios. Los metadatos de juegos proceden de IGDB.com. Los logotipos de las tiendas se
          muestran solo para indicar en qué plataforma tienes cada juego; los iconos proceden de
          Simple Icons (CC0) y, el de Amazon, de Font Awesome Free (CC BY 4.0, fontawesome.com).
          Steam y el logotipo de Steam son marcas de Valve Corporation. {SITE.name} no está
          afiliado, patrocinado ni respaldado por Valve, Epic Games, GOG, Amazon ni Twitch.
        </p>
      </>
    ),
  },
  en: {
    title: "Legal notice",
    body: (
      <>
        <h2>Owner</h2>
        <p>
          {SITE.name} is a free personal project by {SITE.ownerName}, with no commercial activity.
          Contact: <Contact />. The source code is public on <Repo />.
        </p>

        <h2>Use</h2>
        <p>
          The service is provided as is, with no availability guarantees. You agree not to use it for
          unlawful purposes or to try to access other users’ data.
        </p>

        <h2>Third-party trademarks and content</h2>
        <p>
          Game and achievement names, covers and icons belong to their respective owners. Game
          metadata comes from IGDB.com. Store logos are shown only to indicate which platform you own
          each game on; the icons come from Simple Icons (CC0) and, for Amazon, from Font Awesome
          Free (CC BY 4.0, fontawesome.com). Steam and the Steam logo are trademarks of Valve
          Corporation. {SITE.name} is not affiliated with, sponsored or endorsed by Valve, Epic
          Games, GOG, Amazon or Twitch.
        </p>
      </>
    ),
  },
  fr: {
    title: "Mentions légales",
    body: (
      <>
        <h2>Propriétaire</h2>
        <p>
          {SITE.name} est un projet personnel et gratuit de {SITE.ownerName}, sans activité
          commerciale. Contact : <Contact />. Le code source est public sur <Repo />.
        </p>

        <h2>Utilisation</h2>
        <p>
          Le service est fourni tel quel, sans garantie de disponibilité. Vous vous engagez à ne pas
          l’utiliser à des fins illicites ni à tenter d’accéder aux données d’autres utilisateurs.
        </p>

        <h2>Marques et contenus de tiers</h2>
        <p>
          Les noms, jaquettes et icônes des jeux et des succès appartiennent à leurs propriétaires
          respectifs. Les métadonnées des jeux proviennent d’IGDB.com. Les logos des boutiques ne
          sont affichés que pour indiquer sur quelle plateforme vous possédez chaque jeu ; les icônes
          proviennent de Simple Icons (CC0) et, pour Amazon, de Font Awesome Free (CC BY 4.0,
          fontawesome.com). Steam et le logo Steam sont des marques de Valve Corporation.{" "}
          {SITE.name} n’est ni affilié, ni sponsorisé, ni approuvé par Valve, Epic Games, GOG, Amazon
          ou Twitch.
        </p>
      </>
    ),
  },
};

export function PrivacyPage() {
  useTranslation(); // re-render on language change
  const page = PRIVACY[currentLanguage()];
  return <LegalPage title={page.title}>{page.body}</LegalPage>;
}

export function LegalNoticePage() {
  useTranslation();
  const page = NOTICE[currentLanguage()];
  return <LegalPage title={page.title}>{page.body}</LegalPage>;
}
