import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { friendsApi } from "../api/endpoints";
import type { FriendsOverview, FriendState } from "../api/types";

export function useFriends(enabled = true) {
  return useQuery({
    queryKey: ["friends"],
    queryFn: friendsApi.list,
    enabled,
    refetchInterval: 60_000, // new requests show up without reloading
  });
}

/** How the current user relates to `userId`, from the friends overview. */
export function relationTo(
  overview: FriendsOverview | undefined,
  userId: number,
): { state: FriendState; id: number | null } {
  for (const state of ["friends", "incoming", "outgoing"] as const) {
    const match = overview?.[state].find((f) => f.user.id === userId);
    if (match) return { state, id: match.id };
  }
  return { state: "none", id: null };
}

export function useFriendActions() {
  const queryClient = useQueryClient();
  const onSuccess = () => {
    void queryClient.invalidateQueries({ queryKey: ["friends"] });
    void queryClient.invalidateQueries({ queryKey: ["userSearch"] });
  };
  return {
    request: useMutation({ mutationFn: friendsApi.request, onSuccess }),
    accept: useMutation({ mutationFn: friendsApi.accept, onSuccess }),
    remove: useMutation({ mutationFn: friendsApi.remove, onSuccess }),
  };
}

/** Add / accept / cancel / remove, depending on the current relation. */
export default function FriendButton({ userId, username }: { userId: number; username: string }) {
  const friends = useFriends();
  const { request, accept, remove } = useFriendActions();
  const { state, id } = relationTo(friends.data, userId);
  const busy = request.isPending || accept.isPending || remove.isPending || friends.isLoading;
  const error = request.error ?? accept.error ?? remove.error;

  let button;
  if (state === "friends") {
    button = (
      <button
        className="btn-secondary group px-3 py-1.5"
        disabled={busy}
        onClick={() => confirm(`¿Quitar a ${username} de tus amigos?`) && remove.mutate(id!)}
      >
        <span className="group-hover:hidden">✓ Amigos</span>
        <span className="hidden text-red-300 group-hover:inline">Quitar amigo</span>
      </button>
    );
  } else if (state === "incoming") {
    button = (
      <span className="flex gap-2">
        <button
          className="btn-primary px-3 py-1.5"
          disabled={busy}
          onClick={() => accept.mutate(id!)}
        >
          Aceptar
        </button>
        <button
          className="btn-secondary px-3 py-1.5"
          disabled={busy}
          onClick={() => remove.mutate(id!)}
        >
          Rechazar
        </button>
      </span>
    );
  } else if (state === "outgoing") {
    button = (
      <button
        className="btn-secondary group px-3 py-1.5"
        disabled={busy}
        onClick={() => remove.mutate(id!)}
      >
        <span className="group-hover:hidden">Solicitud enviada</span>
        <span className="hidden group-hover:inline">Cancelar solicitud</span>
      </button>
    );
  } else {
    button = (
      <button
        className="btn-primary px-3 py-1.5"
        disabled={busy}
        onClick={() => request.mutate(username)}
      >
        + Añadir amigo
      </button>
    );
  }

  return (
    <span className="flex flex-col items-end gap-1">
      {button}
      {error && <span className="text-xs text-red-400">{error.message}</span>}
    </span>
  );
}
