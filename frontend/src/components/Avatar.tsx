/** User picture, or the first letter of the name when there is none. */
export default function Avatar({
  user,
  className = "h-10 w-10 text-base",
}: {
  user: { username: string; avatar_url: string | null };
  className?: string;
}) {
  if (user.avatar_url) {
    return <img src={user.avatar_url} alt="" className={`shrink-0 rounded-full ${className}`} />;
  }
  return (
    <div
      className={`flex shrink-0 items-center justify-center rounded-full bg-indigo-600 font-bold ${className}`}
    >
      {user.username[0]?.toUpperCase()}
    </div>
  );
}
