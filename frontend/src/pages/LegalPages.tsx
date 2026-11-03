import type { ReactNode } from "react";

import { SITE } from "../lib/site";

function LegalPage({ title, children }: { title: string; children: ReactNode }) {
  return (
    <article className="mx-auto max-w-3xl space-y-4 text-sm leading-relaxed text-slate-300 [&_h2]:mt-8 [&_h2]:text-lg [&_h2]:font-semibold [&_h2]:text-slate-100 [&_li]:ml-5 [&_li]:list-disc [&_a]:text-indigo-300 [&_a]:underline">
      <h1 className="text-2xl font-bold text-slate-50">{title}</h1>
      <p className="text-xs text-slate-500">Última actualización: {SITE.lastUpdated}</p>
      {children}
    </article>
  );
}

const Contact = () => <a href={`mailto:${SITE.contactEmail}`}>{SITE.contactEmail}</a>;

export function PrivacyPage() {
  return (
    <LegalPage title="Política de privacidad">
      <h2>Responsable del tratamiento</h2>
      <p>
        {SITE.ownerName}, titular de {SITE.name}, un proyecto personal sin ánimo de lucro.
        Contacto: <Contact />.
      </p>

      <h2>Qué datos tratamos</h2>
      <ul>
        <li>Datos de cuenta: nombre de usuario, email y contraseña (guardada cifrada con un hash, nunca en claro).</li>
        <li>
          Si entras con Steam: tu SteamID, tu nombre público y tu avatar de Steam. Nunca vemos tu
          contraseña de Steam.
        </li>
        <li>
          Tu biblioteca: juegos, tienda, horas jugadas, fechas de última partida, logros, categorías
          y favoritos.
        </li>
        <li>
          Los ficheros que importas solo se leen para extraer la lista de juegos; el fichero no se
          guarda.
        </li>
        <li>Tu IP se usa de forma temporal para limitar intentos de inicio de sesión (máx. 1 hora).</li>
      </ul>

      <h2>Para qué y con qué base legal</h2>
      <p>
        Únicamente para prestarte el servicio que pides: guardar y mostrar tu biblioteca y tus
        estadísticas. La base legal es la ejecución del servicio que solicitas al registrarte (art.
        6.1.b del RGPD). No hay publicidad, no se venden datos y no se usan para elaborar perfiles
        comerciales.
      </p>

      <h2>Quién más interviene</h2>
      <ul>
        <li>Alojamiento: {SITE.hosting}. Los datos no salen de la Unión Europea.</li>
        <li>
          Steam Web API (Valve): se consulta con tu SteamID para leer tus juegos y logros, solo si
          vinculas Steam.
        </li>
        <li>
          IGDB (Twitch/Amazon): se consulta con el título o el identificador del juego para obtener
          portadas y géneros. No se le envía ningún dato tuyo.
        </li>
      </ul>

      <h2>Cuánto tiempo</h2>
      <p>
        Mientras mantengas tu cuenta. Al eliminarla (Ajustes → Eliminar cuenta) se borran tus datos
        de inmediato; las copias de seguridad se renuevan y desaparecen en un máximo de 14 días.
      </p>

      <h2>Perfil público</h2>
      <p>
        Tu perfil es privado por defecto. Solo si activas «Perfil público» cualquier persona podrá
        ver tu nombre de usuario, avatar, biblioteca, estadísticas y logros.
      </p>

      <h2>Cookies</h2>
      <p>
        Solo usamos una cookie técnica (<code>librachieve_refresh</code>) para mantener tu sesión
        iniciada. Es imprescindible para el funcionamiento y no requiere consentimiento. No hay
        cookies de analítica ni de publicidad.
      </p>

      <h2>Tus derechos</h2>
      <p>
        Puedes acceder, rectificar, suprimir, oponerte, limitar el tratamiento y pedir la
        portabilidad de tus datos escribiendo a <Contact />. Puedes cambiar tu nombre y la privacidad
        en Ajustes y borrar tu cuenta en cualquier momento. Si crees que no se respetan tus derechos,
        puedes reclamar ante la Agencia Española de Protección de Datos (
        <a href="https://www.aepd.es" target="_blank" rel="noreferrer">
          aepd.es
        </a>
        ).
      </p>
    </LegalPage>
  );
}

export function LegalNoticePage() {
  return (
    <LegalPage title="Aviso legal">
      <h2>Titular</h2>
      <p>
        {SITE.name} es un proyecto personal y gratuito de {SITE.ownerName}, sin actividad económica.
        Contacto: <Contact />. El código fuente es público en{" "}
        <a href={SITE.repoUrl} target="_blank" rel="noreferrer">
          GitHub
        </a>
        .
      </p>

      <h2>Uso</h2>
      <p>
        El servicio se ofrece tal cual, sin garantías de disponibilidad. Te comprometes a no usarlo
        para fines ilícitos ni a intentar acceder a datos de otros usuarios.
      </p>

      <h2>Marcas y contenidos de terceros</h2>
      <p>
        Los nombres, portadas e iconos de juegos y logros pertenecen a sus respectivos propietarios.
        Los metadatos de juegos proceden de IGDB.com. Steam y el logotipo de Steam son marcas de
        Valve Corporation. {SITE.name} no está afiliado, patrocinado ni respaldado por Valve, Epic
        Games, GOG, Amazon ni Twitch.
      </p>
    </LegalPage>
  );
}
