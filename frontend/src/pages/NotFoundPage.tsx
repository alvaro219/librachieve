import { Link } from "react-router-dom";

export default function NotFoundPage() {
  return (
    <div className="card mx-auto max-w-md text-center">
      <p className="mb-4 text-slate-300">Esta página no existe.</p>
      <Link to="/" className="btn-primary">
        Volver a la biblioteca
      </Link>
    </div>
  );
}
